"""Testes para o motor de aprendizagem adaptativa e dashboard.

Todos os testes funcionam offline (sem chaves de API).
"""

from __future__ import annotations

import json
import os
import tempfile

import pytest

from mega.learning.engine import LearningEngine, SkillMastery, StudentProfile, ECG_SKILL_TREE
from mega.learning.dashboard import DashboardData


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_data_dir(tmp_path):
    """Diretório temporário para dados de aprendizagem."""
    return str(tmp_path / "learning_data")


@pytest.fixture
def engine(tmp_data_dir):
    """Motor de aprendizagem com diretório temporário."""
    eng = LearningEngine(data_dir=tmp_data_dir, student_id="test_student")
    yield eng
    eng.reset_profile()


@pytest.fixture
def engine_with_data(tmp_data_dir):
    """Motor com dados de progresso pré-carregados."""
    eng = LearningEngine(data_dir=tmp_data_dir, student_id="test_loaded")

    # Registra respostas em vários tópicos
    skills = [
        ("fundamentos::Ondas e Intervalos::Onda P", True, 0.3),
        ("fundamentos::Ondas e Intervalos::Onda P", True, 0.5),
        ("fundamentos::Ondas e Intervalos::Onda P", True, 0.7),
        ("fundamentos::Ondas e Intervalos::Complexo QRS", True, 0.5),
        ("fundamentos::Ondas e Intervalos::Complexo QRS", False, 0.5),
        ("ritmos::Ritmos Normais::Ritmo sinusal", True, 0.3),
        ("ritmos::Ritmos Normais::Ritmo sinusal", True, 0.5),
        ("ritmos::Ritmos Atriais::Fibrilação atrial", False, 0.7),
        ("ritmos::Ritmos Atriais::Fibrilação atrial", False, 0.5),
        ("ritmos::Ritmos Atriais::Fibrilação atrial", True, 0.3),
        ("bloqueios::Bloqueios AV::BAV 1° grau", False, 0.5),
    ]

    for skill_id, correct, diff in skills:
        eng.record_answer(skill_id=skill_id, correct=correct, difficulty=diff)

    yield eng
    eng.reset_profile()


# ---------------------------------------------------------------------------
# Testes do SkillMastery e StudentProfile
# ---------------------------------------------------------------------------

class TestSkillMastery:
    def test_default_values(self):
        sm = SkillMastery()
        assert sm.mastery_score == 0.0
        assert sm.total_attempts == 0
        assert sm.ease_factor == 2.5

    def test_to_dict_roundtrip(self):
        sm = SkillMastery(skill_id="test", skill_name="Teste", mastery_score=75.0)
        d = sm.to_dict()
        sm2 = SkillMastery.from_dict(d)
        assert sm2.skill_id == "test"
        assert sm2.mastery_score == 75.0


class TestStudentProfile:
    def test_default_creation(self):
        p = StudentProfile(student_id="aluno1")
        assert p.student_id == "aluno1"
        assert p.created_at != ""
        assert p.skills == {}

    def test_to_dict_roundtrip(self):
        p = StudentProfile(student_id="aluno2")
        p.skills["s1"] = SkillMastery(skill_id="s1", skill_name="Skill 1")
        d = p.to_dict()
        p2 = StudentProfile.from_dict(d)
        assert p2.student_id == "aluno2"
        assert "s1" in p2.skills
        assert p2.skills["s1"].skill_name == "Skill 1"


# ---------------------------------------------------------------------------
# Testes do LearningEngine — registro de respostas
# ---------------------------------------------------------------------------

class TestLearningEngineRecordAnswer:
    def test_record_correct_answer(self, engine):
        result = engine.record_answer(
            skill_id="fundamentos::Derivações::Derivações dos membros",
            correct=True,
            difficulty=0.5,
        )
        assert result["correct"] is True
        assert result["mastery_after"] > 0
        assert result["skill_id"] == "fundamentos::Derivações::Derivações dos membros"
        assert "feedback" in result

    def test_record_wrong_answer(self, engine):
        # Primeiro acerto para ter maestria > 0
        engine.record_answer(
            skill_id="fundamentos::Derivações::Derivações dos membros",
            correct=True, difficulty=0.5,
        )
        result = engine.record_answer(
            skill_id="fundamentos::Derivações::Derivações dos membros",
            correct=False,
            difficulty=0.5,
        )
        assert result["correct"] is False
        assert "feedback" in result

    def test_streak_tracking(self, engine):
        sid = "ritmos::Ritmos Normais::Ritmo sinusal"
        for _ in range(3):
            result = engine.record_answer(skill_id=sid, correct=True, difficulty=0.5)
        assert result["streak"] == 3

    def test_streak_resets_on_wrong(self, engine):
        sid = "ritmos::Ritmos Normais::Ritmo sinusal"
        engine.record_answer(skill_id=sid, correct=True, difficulty=0.5)
        engine.record_answer(skill_id=sid, correct=True, difficulty=0.5)
        result = engine.record_answer(skill_id=sid, correct=False, difficulty=0.5)
        assert result["streak"] == 0

    def test_mastery_increases_with_correct(self, engine):
        sid = "fundamentos::Ondas e Intervalos::Onda P"
        r1 = engine.record_answer(skill_id=sid, correct=True, difficulty=0.5)
        engine.record_answer(skill_id=sid, correct=True, difficulty=0.5)
        r3 = engine.record_answer(skill_id=sid, correct=True, difficulty=0.7)
        # Maestria deve aumentar com acertos consecutivos
        assert r3["mastery_after"] >= r1["mastery_after"]

    def test_creates_new_skill_on_first_answer(self, engine):
        sid = "patologias::Isquemia e Infarto::Supra de ST"
        assert sid not in engine.profile.skills
        engine.record_answer(skill_id=sid, correct=True, difficulty=0.5)
        assert sid in engine.profile.skills


# ---------------------------------------------------------------------------
# Testes do LearningEngine — maestria
# ---------------------------------------------------------------------------

class TestLearningEngineMastery:
    def test_get_mastery_unknown_skill(self, engine):
        assert engine.get_mastery("skill_inexistente") == 0.0

    def test_get_mastery_after_answers(self, engine_with_data):
        mastery = engine_with_data.get_mastery(
            "fundamentos::Ondas e Intervalos::Onda P"
        )
        assert mastery > 0  # Teve 3 acertos

    def test_get_all_masteries(self, engine_with_data):
        all_m = engine_with_data.get_all_masteries()
        assert isinstance(all_m, dict)
        assert len(all_m) > 0
        assert all(isinstance(v, float) for v in all_m.values())


# ---------------------------------------------------------------------------
# Testes do LearningEngine — áreas fracas e recomendações
# ---------------------------------------------------------------------------

class TestLearningEngineRecommendations:
    def test_get_weak_areas(self, engine_with_data):
        weak = engine_with_data.get_weak_areas(threshold=90.0)
        assert isinstance(weak, list)
        # Deve ter áreas fracas (limiar alto)
        assert len(weak) > 0
        # Ordenadas por maestria (menor primeiro)
        if len(weak) >= 2:
            assert weak[0]["mastery"] <= weak[1]["mastery"]

    def test_weak_areas_have_required_keys(self, engine_with_data):
        weak = engine_with_data.get_weak_areas(threshold=100.0)
        if weak:
            area = weak[0]
            assert "skill_id" in area
            assert "skill_name" in area
            assert "mastery" in area
            assert "attempts" in area

    def test_get_recommendations(self, engine_with_data):
        recs = engine_with_data.get_recommendations(n=5)
        assert isinstance(recs, list)
        assert len(recs) <= 5
        for rec in recs:
            assert "tipo" in rec
            assert rec["tipo"] in ("revisão", "reforço", "novo_tópico")
            assert "skill_id" in rec
            assert "razão" in rec
            assert "prioridade" in rec

    def test_recommendations_include_new_topics(self, engine):
        # Motor vazio deve recomendar novos tópicos
        recs = engine.get_recommendations(n=3)
        assert len(recs) > 0
        assert any(r["tipo"] == "novo_tópico" for r in recs)


# ---------------------------------------------------------------------------
# Testes do LearningEngine — persistência
# ---------------------------------------------------------------------------

class TestLearningEnginePersistence:
    def test_save_and_load(self, tmp_data_dir):
        # Salva dados
        eng1 = LearningEngine(data_dir=tmp_data_dir, student_id="persist_test")
        eng1.record_answer(
            skill_id="fundamentos::Ondas e Intervalos::Onda P",
            correct=True, difficulty=0.5,
        )
        mastery1 = eng1.get_mastery("fundamentos::Ondas e Intervalos::Onda P")

        # Carrega em nova instância
        eng2 = LearningEngine(data_dir=tmp_data_dir, student_id="persist_test")
        mastery2 = eng2.get_mastery("fundamentos::Ondas e Intervalos::Onda P")

        assert mastery2 == mastery1

        # Cleanup
        eng1.reset_profile()

    def test_reset_profile(self, engine):
        engine.record_answer(
            skill_id="fundamentos::Ondas e Intervalos::Onda P",
            correct=True, difficulty=0.5,
        )
        assert len(engine.profile.skills) > 0
        engine.reset_profile()
        assert len(engine.profile.skills) == 0


# ---------------------------------------------------------------------------
# Testes do LearningEngine — utilitários
# ---------------------------------------------------------------------------

class TestLearningEngineUtils:
    def test_get_skill_tree(self):
        tree = LearningEngine.get_skill_tree()
        assert "fundamentos" in tree
        assert "ritmos" in tree
        assert "bloqueios" in tree
        assert "patologias" in tree

    def test_list_all_skills(self):
        skills = LearningEngine.list_all_skills()
        assert isinstance(skills, list)
        assert len(skills) > 10  # Deve ter muitas habilidades

    def test_get_skill_info(self, engine):
        info = engine.get_skill_info("fundamentos::Ondas e Intervalos::Onda P")
        assert info is not None
        assert info["skill_name"] == "Onda P"
        assert info["categoria"] == "fundamentos"

    def test_get_skill_info_unknown(self, engine):
        info = engine.get_skill_info("inexistente")
        assert info is None


# ---------------------------------------------------------------------------
# Testes de qualidade SM-2
# ---------------------------------------------------------------------------

class TestSpacedRepetition:
    def test_quality_correct_easy_fast(self, engine):
        q = engine._quality_from_answer(correct=True, difficulty=0.8, time_sec=10)
        assert q == 5  # Difícil e rápido

    def test_quality_correct_medium(self, engine):
        q = engine._quality_from_answer(correct=True, difficulty=0.6, time_sec=20)
        assert q == 4

    def test_quality_correct_slow(self, engine):
        q = engine._quality_from_answer(correct=True, difficulty=0.3, time_sec=60)
        assert q == 3

    def test_quality_wrong_slow(self, engine):
        q = engine._quality_from_answer(correct=False, difficulty=0.5, time_sec=90)
        assert q == 0  # Apagão

    def test_quality_wrong_medium(self, engine):
        q = engine._quality_from_answer(correct=False, difficulty=0.5, time_sec=45)
        assert q == 1

    def test_quality_wrong_fast(self, engine):
        q = engine._quality_from_answer(correct=False, difficulty=0.5, time_sec=10)
        assert q == 2


# ---------------------------------------------------------------------------
# Testes do DashboardData
# ---------------------------------------------------------------------------

class TestDashboardData:
    def test_competency_map_empty(self, engine):
        dash = DashboardData(engine)
        cmap = dash.get_competency_map()
        assert "labels" in cmap
        assert "parents" in cmap
        assert "values" in cmap
        assert "colors" in cmap
        assert "ids" in cmap
        assert cmap["chart_type"] == "sunburst"
        assert len(cmap["labels"]) == len(cmap["parents"])
        assert len(cmap["labels"]) == len(cmap["values"])

    def test_competency_map_with_data(self, engine_with_data):
        dash = DashboardData(engine_with_data)
        cmap = dash.get_competency_map()
        assert len(cmap["labels"]) > 0
        # Raiz deve ser "ECG"
        assert cmap["labels"][0] == "ECG"
        assert cmap["parents"][0] == ""

    def test_progress_timeline(self, engine_with_data):
        dash = DashboardData(engine_with_data)
        timeline = dash.get_progress_timeline(days=7)
        assert "dates" in timeline
        assert "overall_mastery" in timeline
        assert "sessions" in timeline
        assert timeline["chart_type"] == "line"
        assert len(timeline["dates"]) == 8  # 7 dias + hoje

    def test_weak_areas_dashboard(self, engine_with_data):
        dash = DashboardData(engine_with_data)
        weak = dash.get_weak_areas()
        assert "skills" in weak
        assert "masteries" in weak
        assert "colors" in weak
        assert weak["chart_type"] == "bar_horizontal"
        assert len(weak["skills"]) == len(weak["masteries"])

    def test_recommendations_dashboard(self, engine_with_data):
        dash = DashboardData(engine_with_data)
        recs = dash.get_recommendations(n=3)
        assert "items" in recs
        assert "summary" in recs
        assert isinstance(recs["summary"], str)
        assert len(recs["summary"]) > 0

    def test_summary(self, engine_with_data):
        dash = DashboardData(engine_with_data)
        summary = dash.get_summary()
        assert "maestria_geral" in summary
        assert "total_habilidades" in summary
        assert "revisoes_pendentes" in summary
        assert summary["total_habilidades"] > 0

    def test_mastery_color(self):
        assert DashboardData._mastery_color(90) == "#2ecc71"
        assert DashboardData._mastery_color(70) == "#27ae60"
        assert DashboardData._mastery_color(50) == "#f39c12"
        assert DashboardData._mastery_color(30) == "#e67e22"
        assert DashboardData._mastery_color(10) == "#e74c3c"

    def test_recommendations_empty_engine(self, engine):
        dash = DashboardData(engine)
        recs = dash.get_recommendations()
        assert "Bem-vindo" in recs["summary"]

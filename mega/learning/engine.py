"""Motor de aprendizagem adaptativa para ECG.

Rastreia competência do aluno por habilidade/sub-habilidade,
implementa pontuação de maestria (0-100) por tópico,
usa agendamento de repetição espaçada e recomenda conteúdo/quiz
com base nas áreas mais fracas.

Integra-se com quiz/spaced_repetition.py quando disponível.
"""

from __future__ import annotations

import json
import time
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

# Tentativa de integração com o módulo de repetição espaçada existente
try:
    from quiz.spaced_repetition import SpacedRepetitionScheduler, QuestionState
    _HAS_SR = True
except ImportError:
    _HAS_SR = False


# ======================================================================
# Estruturas de dados
# ======================================================================

@dataclass
class SkillMastery:
    """Estado de maestria de uma habilidade específica."""

    skill_id: str = ""
    skill_name: str = ""
    parent_skill: str = ""
    mastery_score: float = 0.0  # 0-100
    total_attempts: int = 0
    correct_attempts: int = 0
    streak: int = 0  # acertos consecutivos
    last_attempt_ts: str = ""
    ease_factor: float = 2.5  # fator SM-2
    interval_days: int = 1
    next_review: str = ""
    history: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "SkillMastery":
        valid = {k: v for k, v in d.items() if k in cls.__dataclass_fields__}
        return cls(**valid)


@dataclass
class StudentProfile:
    """Perfil completo do aluno com todas as competências."""

    student_id: str = "default"
    name: str = "Aluno"
    created_at: str = ""
    skills: dict[str, SkillMastery] = field(default_factory=dict)
    overall_mastery: float = 0.0
    total_study_time_min: float = 0.0
    sessions_count: int = 0

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

    def to_dict(self) -> dict:
        d = {
            "student_id": self.student_id,
            "name": self.name,
            "created_at": self.created_at,
            "overall_mastery": self.overall_mastery,
            "total_study_time_min": self.total_study_time_min,
            "sessions_count": self.sessions_count,
            "skills": {k: v.to_dict() for k, v in self.skills.items()},
        }
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "StudentProfile":
        skills_raw = d.pop("skills", {})
        valid = {k: v for k, v in d.items() if k in cls.__dataclass_fields__ and k != "skills"}
        profile = cls(**valid)
        profile.skills = {
            k: SkillMastery.from_dict(v) for k, v in skills_raw.items()
        }
        return profile


# ======================================================================
# Currículo de habilidades ECG
# ======================================================================

ECG_SKILL_TREE: dict[str, dict[str, list[str]]] = {
    "fundamentos": {
        "Anatomia Elétrica": [
            "Sistema de condução",
            "Nó sinusal",
            "Nó AV",
            "Feixe de His",
        ],
        "Derivações": [
            "Derivações dos membros",
            "Derivações precordiais",
            "Plano frontal vs horizontal",
        ],
        "Ondas e Intervalos": [
            "Onda P",
            "Complexo QRS",
            "Onda T",
            "Intervalo PR",
            "Intervalo QT",
            "Segmento ST",
        ],
    },
    "ritmos": {
        "Ritmos Normais": [
            "Ritmo sinusal",
            "Bradicardia sinusal",
            "Taquicardia sinusal",
            "Arritmia sinusal",
        ],
        "Ritmos Atriais": [
            "Fibrilação atrial",
            "Flutter atrial",
            "Taquicardia atrial",
        ],
        "Ritmos Ventriculares": [
            "Taquicardia ventricular",
            "Fibrilação ventricular",
            "Ritmo idioventricular",
        ],
    },
    "bloqueios": {
        "Bloqueios AV": [
            "BAV 1° grau",
            "BAV 2° grau Mobitz I",
            "BAV 2° grau Mobitz II",
            "BAV 3° grau (BAVT)",
        ],
        "Bloqueios de Ramo": [
            "BRD",
            "BRE",
            "Hemibloqueios",
        ],
    },
    "patologias": {
        "Isquemia e Infarto": [
            "Supra de ST",
            "Infra de ST",
            "Onda Q patológica",
            "Inversão de T",
        ],
        "Hipertrofias": [
            "HVE",
            "HVD",
            "Sobrecarga atrial",
        ],
        "Síndromes": [
            "WPW",
            "Brugada",
            "QT longo",
            "Pericardite",
        ],
    },
}


def _flatten_skills() -> dict[str, tuple[str, str]]:
    """Retorna mapeamento skill_id -> (categoria, habilidade_pai)."""
    flat: dict[str, tuple[str, str]] = {}
    for categoria, habilidades in ECG_SKILL_TREE.items():
        for hab_pai, sub_habs in habilidades.items():
            key_pai = f"{categoria}::{hab_pai}"
            flat[key_pai] = (categoria, "")
            for sub in sub_habs:
                key_sub = f"{categoria}::{hab_pai}::{sub}"
                flat[key_sub] = (categoria, hab_pai)
    return flat


_SKILL_MAP = _flatten_skills()


# ======================================================================
# Motor de Aprendizagem Adaptativa
# ======================================================================

class LearningEngine:
    """Motor de aprendizagem adaptativa para ECG.

    Rastreia competência do aluno por habilidade e sub-habilidade,
    calcula pontuação de maestria (0-100) e recomenda próximos
    conteúdos com base nas áreas mais fracas.

    Parameters
    ----------
    data_dir : str
        Diretório para armazenar dados de progresso em JSON.
    student_id : str
        Identificador do aluno.
    """

    # Constantes de configuração
    MASTERY_THRESHOLD = 80.0      # Pontuação para considerar habilidade dominada
    DECAY_RATE = 0.02             # Taxa de decaimento diário da maestria
    MIN_ATTEMPTS_FOR_MASTERY = 3  # Mínimo de tentativas para maestria
    STREAK_BONUS = 5.0            # Bônus por acertos consecutivos (máx 3 streaks)
    WRONG_PENALTY = 10.0          # Penalidade por erro

    def __init__(
        self,
        data_dir: str = "data/learning",
        student_id: str = "default",
    ) -> None:
        self.data_dir = Path(data_dir)
        self.student_id = student_id
        self._profile: StudentProfile | None = None
        self._sr_scheduler: Any = None

        # Inicializa integração com repetição espaçada se disponível
        if _HAS_SR:
            sr_path = str(self.data_dir / f"{student_id}_sr.json")
            try:
                self._sr_scheduler = SpacedRepetitionScheduler(data_path=sr_path)
            except Exception:
                self._sr_scheduler = None

    @property
    def profile(self) -> StudentProfile:
        """Perfil do aluno (carrega sob demanda)."""
        if self._profile is None:
            self._profile = self._load_profile()
        return self._profile

    # ------------------------------------------------------------------
    # Registro de respostas e atualização de maestria
    # ------------------------------------------------------------------

    def record_answer(
        self,
        skill_id: str,
        correct: bool,
        difficulty: float = 0.5,
        time_spent_sec: float = 0.0,
        question_id: str = "",
    ) -> dict:
        """Registra a resposta do aluno e atualiza a maestria.

        Parameters
        ----------
        skill_id : str
            Identificador da habilidade (ex: "ritmos::Ritmos Normais::Ritmo sinusal").
        correct : bool
            Se a resposta foi correta.
        difficulty : float
            Dificuldade da questão (0.0 a 1.0).
        time_spent_sec : float
            Tempo gasto na resposta em segundos.
        question_id : str
            ID opcional da questão para integração com repetição espaçada.

        Returns
        -------
        dict
            Dicionário com a maestria atualizada e feedback.
        """
        profile = self.profile

        # Garante que a habilidade existe no perfil
        if skill_id not in profile.skills:
            parts = skill_id.split("::")
            parent = "::".join(parts[:-1]) if len(parts) > 1 else ""
            profile.skills[skill_id] = SkillMastery(
                skill_id=skill_id,
                skill_name=parts[-1] if parts else skill_id,
                parent_skill=parent,
            )

        skill = profile.skills[skill_id]
        old_mastery = skill.mastery_score

        # Atualiza contadores
        skill.total_attempts += 1
        now = datetime.now()
        skill.last_attempt_ts = now.isoformat()

        if correct:
            skill.correct_attempts += 1
            skill.streak += 1
        else:
            skill.streak = 0

        # Calcula nova maestria
        skill.mastery_score = self._compute_mastery(skill, correct, difficulty)

        # Registra no histórico da habilidade
        skill.history.append({
            "ts": now.isoformat(),
            "correct": correct,
            "difficulty": difficulty,
            "time_sec": time_spent_sec,
            "mastery_after": skill.mastery_score,
            "question_id": question_id,
        })
        # Manter apenas os últimos 100 registros
        if len(skill.history) > 100:
            skill.history = skill.history[-100:]

        # Atualiza repetição espaçada (SM-2)
        quality = self._quality_from_answer(correct, difficulty, time_spent_sec)
        self._update_spaced_repetition(skill, quality)

        # Integra com o scheduler existente se disponível
        if self._sr_scheduler and question_id:
            try:
                self._sr_scheduler.record_answer(question_id, quality)
            except Exception:
                pass

        # Atualiza maestria geral
        self._update_overall_mastery()

        # Salva progresso
        self._save_profile()

        # Gera feedback
        delta = skill.mastery_score - old_mastery
        feedback = self._generate_feedback(skill, correct, delta)

        return {
            "skill_id": skill_id,
            "correct": correct,
            "mastery_before": round(old_mastery, 1),
            "mastery_after": round(skill.mastery_score, 1),
            "mastery_delta": round(delta, 1),
            "streak": skill.streak,
            "feedback": feedback,
        }

    def _compute_mastery(
        self, skill: SkillMastery, correct: bool, difficulty: float
    ) -> float:
        """Calcula a nova pontuação de maestria (0-100).

        Usa uma média ponderada entre a taxa de acerto histórica e
        ajustes por dificuldade, streak e tentativas recentes.
        """
        # Taxa de acerto base
        accuracy = (
            skill.correct_attempts / skill.total_attempts
            if skill.total_attempts > 0
            else 0.0
        )
        base_mastery = accuracy * 100.0

        # Ajuste por dificuldade: questões difíceis valem mais
        diff_bonus = 0.0
        if correct:
            diff_bonus = difficulty * 15.0  # até +15 para questões difíceis
        else:
            diff_bonus = -(1.0 - difficulty) * self.WRONG_PENALTY

        # Bônus por streak (máximo de 3 streaks contam)
        streak_bonus = min(skill.streak, 3) * self.STREAK_BONUS if correct else 0.0

        # Fator de confiança (mais tentativas = mais confiável)
        confidence = min(1.0, skill.total_attempts / self.MIN_ATTEMPTS_FOR_MASTERY)

        # Combina os fatores
        raw = base_mastery * confidence + diff_bonus + streak_bonus

        # Suaviza com a maestria anterior (inércia)
        if skill.total_attempts > 1:
            alpha = 0.3  # peso da nova medição
            raw = alpha * raw + (1.0 - alpha) * skill.mastery_score

        # Aplica decaimento temporal
        if skill.last_attempt_ts:
            try:
                last = datetime.fromisoformat(skill.last_attempt_ts)
                days_since = (datetime.now() - last).total_seconds() / 86400.0
                if days_since > 1.0:
                    decay = self.DECAY_RATE * days_since
                    raw -= decay
            except (ValueError, TypeError):
                pass

        return max(0.0, min(100.0, raw))

    def _quality_from_answer(
        self, correct: bool, difficulty: float, time_sec: float
    ) -> int:
        """Converte resposta para qualidade SM-2 (0-5).

        0 = apagão total, 5 = resposta perfeita.
        """
        if not correct:
            if time_sec > 60:
                return 0  # Errou e demorou — apagão
            elif time_sec > 30:
                return 1  # Errou mas tentou
            else:
                return 2  # Errou rápido — reconhece o conteúdo

        # Correto
        if difficulty >= 0.7 and time_sec < 30:
            return 5  # Difícil e rápido — perfeito
        elif difficulty >= 0.5 and time_sec < 45:
            return 4  # Bom desempenho
        else:
            return 3  # Correto com dificuldade

    def _update_spaced_repetition(self, skill: SkillMastery, quality: int) -> None:
        """Atualiza agendamento de repetição espaçada (algoritmo SM-2)."""
        if quality < 3:
            skill.interval_days = 1
        else:
            if skill.total_attempts <= 1:
                skill.interval_days = 1
            elif skill.total_attempts == 2:
                skill.interval_days = 6
            else:
                skill.interval_days = round(
                    skill.interval_days * skill.ease_factor
                )

        # Atualiza fator de facilidade
        skill.ease_factor = max(
            1.3,
            skill.ease_factor
            + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)),
        )

        # Define próxima revisão
        next_review = datetime.now() + timedelta(days=skill.interval_days)
        skill.next_review = next_review.strftime("%Y-%m-%d")

    def _generate_feedback(
        self, skill: SkillMastery, correct: bool, delta: float
    ) -> str:
        """Gera feedback textual para o aluno."""
        name = skill.skill_name

        if correct:
            if skill.streak >= 3:
                return (
                    f"Excelente! Sequência de {skill.streak} acertos em '{name}'! "
                    f"Sua maestria subiu para {skill.mastery_score:.0f}/100. "
                    "Continue assim — como um fotógrafo que domina cada ângulo da câmera!"
                )
            elif delta > 5:
                return (
                    f"Muito bem! Sua maestria em '{name}' subiu "
                    f"{delta:+.0f} pontos para {skill.mastery_score:.0f}/100."
                )
            else:
                return (
                    f"Correto! Maestria em '{name}': "
                    f"{skill.mastery_score:.0f}/100."
                )
        else:
            if skill.mastery_score < 30:
                return (
                    f"Não desanime! '{name}' é um tópico que exige prática. "
                    f"Maestria atual: {skill.mastery_score:.0f}/100. "
                    "Revise o conceito usando a analogia da câmera e tente novamente."
                )
            else:
                return (
                    f"Quase! Revise '{name}' — maestria: "
                    f"{skill.mastery_score:.0f}/100. "
                    "Cada erro é uma oportunidade de aprendizado."
                )

    # ------------------------------------------------------------------
    # Maestria e recomendações
    # ------------------------------------------------------------------

    def get_mastery(self, skill_id: str) -> float:
        """Retorna a maestria atual (0-100) para uma habilidade.

        Aplica decaimento temporal desde a última interação.
        """
        profile = self.profile
        if skill_id not in profile.skills:
            return 0.0

        skill = profile.skills[skill_id]
        mastery = skill.mastery_score

        # Aplica decaimento temporal
        if skill.last_attempt_ts:
            try:
                last = datetime.fromisoformat(skill.last_attempt_ts)
                days = (datetime.now() - last).total_seconds() / 86400.0
                if days > 1.0:
                    mastery -= self.DECAY_RATE * days
                    mastery = max(0.0, mastery)
            except (ValueError, TypeError):
                pass

        return round(mastery, 1)

    def get_all_masteries(self) -> dict[str, float]:
        """Retorna maestria de todas as habilidades rastreadas."""
        return {
            sid: self.get_mastery(sid)
            for sid in self.profile.skills
        }

    def get_weak_areas(self, threshold: float | None = None) -> list[dict]:
        """Identifica as áreas mais fracas do aluno.

        Parameters
        ----------
        threshold : float, optional
            Limiar de maestria (default: MASTERY_THRESHOLD).

        Returns
        -------
        list[dict]
            Lista de áreas fracas ordenadas pela maestria (menor primeiro).
        """
        if threshold is None:
            threshold = self.MASTERY_THRESHOLD

        weak = []
        for sid, skill in self.profile.skills.items():
            mastery = self.get_mastery(sid)
            if mastery < threshold:
                weak.append({
                    "skill_id": sid,
                    "skill_name": skill.skill_name,
                    "mastery": mastery,
                    "attempts": skill.total_attempts,
                    "accuracy": (
                        round(skill.correct_attempts / skill.total_attempts * 100, 1)
                        if skill.total_attempts > 0
                        else 0.0
                    ),
                    "next_review": skill.next_review,
                })

        weak.sort(key=lambda x: x["mastery"])
        return weak

    def get_recommendations(self, n: int = 5) -> list[dict]:
        """Recomenda próximos conteúdos/quizzes para estudo.

        Prioriza:
        1. Habilidades com revisão vencida (repetição espaçada)
        2. Áreas fracas com maior necessidade
        3. Tópicos novos ainda não estudados

        Parameters
        ----------
        n : int
            Número máximo de recomendações.

        Returns
        -------
        list[dict]
            Lista de recomendações com tipo, skill_id, razão e prioridade.
        """
        recommendations: list[dict] = []
        today = datetime.now().strftime("%Y-%m-%d")
        studied_skills = set(self.profile.skills.keys())

        # 1. Revisões vencidas (repetição espaçada)
        for sid, skill in self.profile.skills.items():
            if skill.next_review and skill.next_review <= today:
                priority = 1.0
                # Quanto mais atrasada a revisão, maior a prioridade
                try:
                    review_date = datetime.strptime(skill.next_review, "%Y-%m-%d")
                    days_overdue = (datetime.now() - review_date).days
                    priority += days_overdue * 0.1
                except ValueError:
                    pass

                recommendations.append({
                    "tipo": "revisão",
                    "skill_id": sid,
                    "skill_name": skill.skill_name,
                    "mastery": self.get_mastery(sid),
                    "razão": (
                        f"Revisão de '{skill.skill_name}' está pendente. "
                        "A repetição espaçada garante retenção a longo prazo."
                    ),
                    "prioridade": priority,
                })

        # 2. Áreas fracas
        weak = self.get_weak_areas()
        for area in weak:
            # Evita duplicatas com revisões vencidas
            if any(r["skill_id"] == area["skill_id"] for r in recommendations):
                continue
            priority = 0.8 - (area["mastery"] / 100.0) * 0.5
            recommendations.append({
                "tipo": "reforço",
                "skill_id": area["skill_id"],
                "skill_name": area["skill_name"],
                "mastery": area["mastery"],
                "razão": (
                    f"Sua maestria em '{area['skill_name']}' está em "
                    f"{area['mastery']:.0f}/100. Pratique mais para consolidar."
                ),
                "prioridade": priority,
            })

        # 3. Tópicos novos (ainda não estudados)
        for skill_id, (cat, parent) in _SKILL_MAP.items():
            if skill_id not in studied_skills:
                # Verifica se pré-requisitos estão satisfeitos
                priority = 0.3
                if parent:
                    parent_key = f"{cat}::{parent}"
                    parent_mastery = self.get_mastery(parent_key)
                    if parent_mastery >= 50:
                        priority = 0.5  # Pai com boa maestria — hora de avançar
                    else:
                        priority = 0.1  # Pai ainda fraco — esperar

                parts = skill_id.split("::")
                skill_name = parts[-1] if parts else skill_id

                recommendations.append({
                    "tipo": "novo_tópico",
                    "skill_id": skill_id,
                    "skill_name": skill_name,
                    "mastery": 0.0,
                    "razão": (
                        f"Novo tópico disponível: '{skill_name}'. "
                        "Expandir o conhecimento é como aprender um novo ângulo da câmera."
                    ),
                    "prioridade": priority,
                })

        # Ordena por prioridade (maior primeiro) e retorna top N
        recommendations.sort(key=lambda x: x["prioridade"], reverse=True)
        return recommendations[:n]

    def get_due_reviews(self) -> list[str]:
        """Retorna IDs de habilidades com revisão vencida."""
        today = datetime.now().strftime("%Y-%m-%d")
        due = []
        for sid, skill in self.profile.skills.items():
            if skill.next_review and skill.next_review <= today:
                due.append(sid)
        return due

    # ------------------------------------------------------------------
    # Maestria geral
    # ------------------------------------------------------------------

    def _update_overall_mastery(self) -> None:
        """Recalcula a maestria geral do aluno."""
        profile = self.profile
        if not profile.skills:
            profile.overall_mastery = 0.0
            return

        total = sum(self.get_mastery(sid) for sid in profile.skills)
        profile.overall_mastery = round(total / len(profile.skills), 1)

    # ------------------------------------------------------------------
    # Persistência em JSON
    # ------------------------------------------------------------------

    def _profile_path(self) -> Path:
        """Caminho do arquivo JSON do perfil."""
        return self.data_dir / f"{self.student_id}_profile.json"

    def _load_profile(self) -> StudentProfile:
        """Carrega o perfil do aluno do disco."""
        path = self._profile_path()
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                return StudentProfile.from_dict(data)
            except (json.JSONDecodeError, TypeError, KeyError):
                pass
        return StudentProfile(student_id=self.student_id)

    def _save_profile(self) -> None:
        """Salva o perfil do aluno no disco."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        path = self._profile_path()
        data = self.profile.to_dict()
        path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def reset_profile(self) -> None:
        """Reseta o perfil do aluno (útil para testes)."""
        self._profile = StudentProfile(student_id=self.student_id)
        path = self._profile_path()
        if path.exists():
            path.unlink()

    # ------------------------------------------------------------------
    # Utilitários
    # ------------------------------------------------------------------

    @staticmethod
    def get_skill_tree() -> dict:
        """Retorna a árvore completa de habilidades ECG."""
        return ECG_SKILL_TREE

    @staticmethod
    def list_all_skills() -> list[str]:
        """Lista todos os IDs de habilidades disponíveis."""
        return list(_SKILL_MAP.keys())

    def get_skill_info(self, skill_id: str) -> dict | None:
        """Retorna informações sobre uma habilidade."""
        if skill_id not in _SKILL_MAP:
            return None
        cat, parent = _SKILL_MAP[skill_id]
        parts = skill_id.split("::")
        return {
            "skill_id": skill_id,
            "skill_name": parts[-1] if parts else skill_id,
            "categoria": cat,
            "habilidade_pai": parent,
            "mastery": self.get_mastery(skill_id),
        }

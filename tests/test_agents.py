"""Testes para o orquestrador multi-agente e agentes especializados.

Todos os testes funcionam offline (sem chaves de API).
"""

from __future__ import annotations

import pytest

from mega.agents.orchestrator import AgentOrchestrator, PipelineResult
from mega.agents.tutor import TutorAgent
from mega.agents.critic import CriticAgent
from mega.agents.explainer import ExplainerAgent


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tutor():
    """TutorAgent em modo offline."""
    return TutorAgent(llm_backend=None)


@pytest.fixture
def critic():
    """CriticAgent em modo offline."""
    return CriticAgent(llm_backend=None)


@pytest.fixture
def explainer():
    """ExplainerAgent em modo offline."""
    return ExplainerAgent(llm_backend=None)


@pytest.fixture
def orchestrator():
    """AgentOrchestrator em modo offline."""
    return AgentOrchestrator(llm_backend=None, student_level="iniciante")


# ---------------------------------------------------------------------------
# Testes do TutorAgent
# ---------------------------------------------------------------------------

class TestTutorAgent:
    def test_guide_returns_dict(self):
        tutor = TutorAgent()
        result = tutor.guide("A onda P representa a despolarização atrial")
        assert isinstance(result, dict)

    def test_guide_returns_message(self, tutor):
        result = tutor.guide("O que é a onda P?")
        assert "message" in result
        assert isinstance(result["message"], str)
        assert len(result["message"]) > 0

    def test_guide_has_response(self):
        tutor = TutorAgent()
        result = tutor.guide("Não sei", context={"topic": "onda_p"})
        assert any(key in result for key in ("response", "hint", "message", "feedback"))

    def test_guide_detects_topic(self, tutor):
        result = tutor.guide("Explique o complexo QRS")
        assert result["topic"] is not None

    def test_provide_hint(self, tutor):
        hint = tutor.provide_hint("onda P")
        assert isinstance(hint, str)
        assert len(hint) > 0
        assert "câmera" in hint.lower() or "flash" in hint.lower()

    def test_hints_progress(self, tutor):
        h1 = tutor.provide_hint("QRS")
        h2 = tutor.provide_hint("QRS")
        assert h1 != h2

    def test_provide_hint_unknown_topic(self, tutor):
        hint = tutor.provide_hint("tema_desconhecido")
        assert isinstance(hint, str)
        assert len(hint) > 0

    def test_encouragement_correct(self, tutor):
        msg = tutor.get_encouragement(correct=True, streak=1)
        assert isinstance(msg, str)
        assert len(msg) > 0

    def test_encouragement_wrong(self, tutor):
        msg = tutor.get_encouragement(correct=False)
        assert isinstance(msg, str)
        assert any(w in msg.lower() for w in ["aprendizado", "prática", "desanime", "quase", "erro"])

    def test_encouragement_streak(self, tutor):
        msg = tutor.get_encouragement(correct=True, streak=5)
        assert "5" in msg

    def test_conversation_summary(self, tutor):
        assert "Nenhuma" in tutor.conversation_summary
        tutor.guide("teste")
        assert "1" in tutor.conversation_summary

    def test_reset(self, tutor):
        tutor.guide("teste")
        tutor.reset()
        assert "Nenhuma" in tutor.conversation_summary

    def test_guide_with_context(self, tutor):
        context = {
            "skill_id": "ritmos::Ritmos Normais::Ritmo sinusal",
            "question": "Qual a FC normal?",
            "correct_answer": "60-100 bpm",
            "is_correct": False,
        }
        result = tutor.guide("50 bpm", context=context)
        assert "message" in result


# ---------------------------------------------------------------------------
# Testes do CriticAgent
# ---------------------------------------------------------------------------

class TestCriticAgent:
    def test_evaluate_returns_dict(self):
        critic = CriticAgent()
        result = critic.evaluate(
            question="O que a onda P representa?",
            student_answer="A onda P é a despolarização atrial",
            correct_answer="Despolarização atrial",
            skill_id="onda_p",
        )
        assert isinstance(result, dict)

    def test_evaluate_correct_answer(self):
        critic = CriticAgent()
        result = critic.evaluate(
            question="O que a onda P representa?",
            student_answer="Despolarização atrial",
            correct_answer="Despolarização atrial",
            skill_id="onda_p",
        )
        assert result.get("correct") or result.get("is_correct") or result.get("score", 0) > 50

    def test_evaluate_incorrect_answer(self):
        critic = CriticAgent()
        result = critic.evaluate(
            question="O que a onda P representa?",
            student_answer="Despolarização ventricular",
            correct_answer="Despolarização atrial",
            skill_id="onda_p",
        )
        has_feedback = any(
            key in result for key in ("feedback", "misconceptions", "explanation", "correction")
        )
        assert has_feedback or not result.get("correct", True)

    def test_evaluate_has_score(self, critic):
        result = critic.evaluate(
            question="Qual é o intervalo PR normal?",
            student_answer="O intervalo PR normal é de 120 a 200 ms",
            correct_answer="120-200 ms",
        )
        assert "score" in result
        assert 0 <= result["score"] <= 100

    def test_evaluate_wrong_answer_feedback(self, critic):
        result = critic.evaluate(
            question="Qual é o intervalo PR normal?",
            student_answer="O intervalo PR normal é de 300 a 500 ms",
            correct_answer="120-200 ms",
        )
        assert "feedback" in result
        assert len(result["feedback"]) > 0

    def test_identify_misconceptions(self, critic):
        misconceptions = critic.identify_misconceptions(
            student_answer="A fibrilação atrial é regular",
            topic="fibrilação atrial",
        )
        assert isinstance(misconceptions, list)

    def test_structured_feedback_excellent(self, critic):
        feedback = critic.provide_structured_feedback(
            score=95,
            correct_points=["ritmo", "frequência", "intervalos"],
            missing_points=[],
            misconceptions=[],
        )
        assert "Excelente" in feedback
        assert "95/100" in feedback

    def test_structured_feedback_poor(self, critic):
        feedback = critic.provide_structured_feedback(
            score=30,
            correct_points=[],
            missing_points=["ritmo", "frequência"],
            misconceptions=[{"description": "Equívoco teste"}],
        )
        assert "Equívoco teste" in feedback

    def test_extract_keywords(self):
        keywords = CriticAgent._extract_keywords(
            "o intervalo PR normal é de 120-200 ms"
        )
        assert isinstance(keywords, list)
        assert len(keywords) > 0


# ---------------------------------------------------------------------------
# Testes do ExplainerAgent
# ---------------------------------------------------------------------------

class TestExplainerAgent:
    def test_explain_returns_dict(self):
        explainer = ExplainerAgent()
        result = explainer.explain("onda_p")
        assert isinstance(result, dict)
        assert "explanation" in result or "text" in result

    def test_explain_known_topic(self, explainer):
        result = explainer.explain("onda P", level="iniciante")
        assert "explanation" in result
        assert len(result["explanation"]) > 50
        assert result["level"] == "iniciante"
        assert "câmera" in result["explanation"].lower() or "flash" in result["explanation"].lower()

    def test_explain_different_levels(self):
        explainer = ExplainerAgent()
        for level in ["iniciante", "intermediario", "avancado"]:
            result = explainer.explain("complexo_qrs", level=level)
            assert isinstance(result, dict)

    def test_explain_intermediate(self, explainer):
        result = explainer.explain("QRS", level="intermediário")
        assert result["level"] == "intermediário"
        assert len(result["explanation"]) > 50

    def test_explain_advanced(self, explainer):
        result = explainer.explain("fibrilação atrial", level="avançado")
        assert result["level"] == "avançado"
        assert len(result["explanation"]) > 100

    def test_explain_unknown_topic(self, explainer):
        result = explainer.explain("tema_desconhecido")
        assert "explanation" in result
        assert len(result["explanation"]) > 0

    def test_explain_multilevel(self):
        explainer = ExplainerAgent()
        result = explainer.explain_all_levels("eixo_eletrico")
        assert isinstance(result, dict)

    def test_explain_all_levels(self, explainer):
        result = explainer.explain_all_levels("onda P")
        assert "iniciante" in result
        assert "intermediário" in result
        assert "avançado" in result
        assert result["iniciante"]["explanation"] != result["avançado"]["explanation"]

    def test_visual_description(self, explainer):
        desc = explainer.generate_visual_description("onda P")
        assert isinstance(desc, str)
        assert len(desc) > 20

    def test_visual_description_unknown(self, explainer):
        desc = explainer.generate_visual_description("achado_raro")
        assert isinstance(desc, str)
        assert len(desc) > 0

    def test_explain_finding_qrs_alargado(self, explainer):
        text = explainer.explain_finding("QRS alargado")
        assert "120" in text or "bloqueio" in text.lower()

    def test_explain_finding_with_report(self, explainer):
        report = {
            "intervals_refined": {
                "median": {"QRS_ms": 140, "PR_ms": 220},
            },
        }
        text = explainer.explain_finding("QRS alargado", report=report)
        assert "140" in text

    def test_available_topics(self):
        topics = ExplainerAgent.available_topics()
        assert isinstance(topics, list)
        assert len(topics) > 0
        assert "onda_p" in topics

    def test_camera_analogy_present(self, explainer):
        result = explainer.explain("onda P", level="iniciante")
        assert result["camera_analogy"] != "" or "câmera" in result["explanation"].lower()

    def test_explain_with_english_level(self, explainer):
        result = explainer.explain("QRS", level="beginner")
        assert result["level"] == "iniciante"


# ---------------------------------------------------------------------------
# Testes do AgentOrchestrator
# ---------------------------------------------------------------------------

class TestAgentOrchestrator:
    def test_init(self):
        orch = AgentOrchestrator()
        assert orch is not None

    def test_process_answer(self):
        orch = AgentOrchestrator()
        result = orch.process_answer(
            question="O que a onda P representa?",
            student_answer="Despolarização atrial",
            correct_answer="Despolarização atrial",
            skill_id="onda_p",
        )
        assert result is not None

    def test_process_incorrect_answer(self):
        orch = AgentOrchestrator()
        result = orch.process_answer(
            question="O que a onda P representa?",
            student_answer="Contração ventricular",
            correct_answer="Despolarização atrial",
            skill_id="onda_p",
        )
        assert result is not None

    def test_process_answer_correct(self, orchestrator):
        result = orchestrator.process_answer(
            question="Qual é o intervalo PR normal?",
            student_answer="O intervalo PR normal é de 120 a 200 ms",
            correct_answer="120-200 ms",
            skill_id="fundamentos::Ondas e Intervalos::Intervalo PR",
        )
        assert isinstance(result, PipelineResult)
        assert result.pipeline_complete is True
        assert result.score >= 0
        assert "CriticAgent" in result.agents_used
        assert "TutorAgent" in result.agents_used

    def test_process_answer_wrong(self, orchestrator):
        result = orchestrator.process_answer(
            question="Qual é a frequência cardíaca normal?",
            student_answer="200 bpm",
            correct_answer="60-100 bpm",
            skill_id="fundamentos::Ondas e Intervalos::Intervalo RR",
        )
        assert result.pipeline_complete is True
        assert result.critic_feedback != ""
        assert result.tutor_guidance != ""

    def test_pipeline_result_to_dict(self, orchestrator):
        result = orchestrator.process_answer(
            question="Teste",
            student_answer="Resposta teste",
            correct_answer="Resposta correta",
        )
        d = result.to_dict()
        assert isinstance(d, dict)
        assert "is_correct" in d
        assert "score" in d
        assert "pipeline_complete" in d

    def test_ask_question(self, orchestrator):
        result = orchestrator.ask_question("O que é fibrilação atrial?")
        assert "tutor_response" in result
        assert isinstance(result["tutor_response"], str)
        assert len(result["tutor_response"]) > 0

    def test_session_summary_empty(self, orchestrator):
        summary = orchestrator.get_session_summary()
        assert summary["total_questions"] == 0
        assert "Nenhuma" in summary["message"]

    def test_session_summary_with_data(self, orchestrator):
        orchestrator.process_answer(
            question="PR normal?",
            student_answer="120-200 ms",
            correct_answer="120-200 ms",
        )
        orchestrator.process_answer(
            question="QRS normal?",
            student_answer="200 ms",
            correct_answer="<120 ms",
        )
        summary = orchestrator.get_session_summary()
        assert summary["total_questions"] == 2
        assert summary["correct"] + summary["incorrect"] == 2
        assert summary["average_score"] >= 0

    def test_reset_session(self, orchestrator):
        orchestrator.process_answer(
            question="teste",
            student_answer="resp",
            correct_answer="correta",
        )
        assert len(orchestrator.history) == 1
        orchestrator.reset_session()
        assert len(orchestrator.history) == 0

    def test_orchestrator_offline_mode(self):
        orch = AgentOrchestrator(llm_backend=None)
        result = orch.process_answer(
            question="O que a onda T representa?",
            student_answer="A repolarização ventricular",
            correct_answer="A repolarização ventricular",
        )
        assert result.pipeline_complete is True
        assert len(result.agents_used) >= 2

    def test_multiple_interactions(self, orchestrator):
        for i in range(5):
            result = orchestrator.process_answer(
                question=f"Pergunta {i}",
                student_answer=f"Resposta {i}",
                correct_answer=f"Correta {i}",
            )
            assert result.pipeline_complete is True
        assert len(orchestrator.history) == 5

    def test_student_level_affects_explanation(self):
        orch_init = AgentOrchestrator(student_level="iniciante")
        orch_adv = AgentOrchestrator(student_level="avançado")

        r_init = orch_init.process_answer(
            question="Explique a onda P",
            student_answer="não sei",
            correct_answer="despolarização atrial",
            topic="onda_p",
        )
        r_adv = orch_adv.process_answer(
            question="Explique a onda P",
            student_answer="não sei",
            correct_answer="despolarização atrial",
            topic="onda_p",
        )
        if r_init.explanation and r_adv.explanation:
            assert r_init.explanation != r_adv.explanation


# ---------------------------------------------------------------------------
# Testes de integração
# ---------------------------------------------------------------------------

class TestIntegration:
    def test_full_pipeline_flow(self):
        orch = AgentOrchestrator(student_level="intermediário")
        result = orch.process_answer(
            question="Qual é o ritmo quando os intervalos RR são irregularmente irregulares?",
            student_answer="Flutter atrial",
            correct_answer="Fibrilação atrial — ritmo irregularmente irregular",
            skill_id="ritmos::Ritmos Atriais::Fibrilação atrial",
            topic="fibrilação atrial",
        )
        assert result.pipeline_complete
        assert result.critic_feedback != ""
        assert result.tutor_guidance != ""
        assert result.score >= 0

    def test_pipeline_with_correct_answer(self):
        orch = AgentOrchestrator()
        result = orch.process_answer(
            question="Duração normal do QRS?",
            student_answer="Menor que 120 ms",
            correct_answer="<120 ms",
        )
        assert result.pipeline_complete
        assert result.score > 0

    def test_agents_independent(self):
        tutor = TutorAgent()
        critic = CriticAgent()
        explainer = ExplainerAgent()

        t_result = tutor.guide("O que é QRS?")
        assert t_result["message"]

        c_result = critic.evaluate(
            "QRS?", "despolarização ventricular",
            "despolarização ventricular",
        )
        assert "score" in c_result

        e_result = explainer.explain("QRS")
        assert e_result["explanation"]

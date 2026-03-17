"""AgentOrchestrator — orquestrador multi-agente para tutoria de ECG.

Coordena os agentes especializados (TutorAgent, CriticAgent, ExplainerAgent)
em um pipeline integrado: aluno submete resposta → Critic avalia →
Tutor guia → Explainer fornece explicação detalhada.

Todos os agentes possuem fallback offline (baseado em regras).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .tutor import TutorAgent
from .critic import CriticAgent
from .explainer import ExplainerAgent


@dataclass
class PipelineResult:
    """Resultado do pipeline de avaliação multi-agente."""

    # Dados da submissão
    question: str = ""
    student_answer: str = ""
    correct_answer: str = ""
    skill_id: str = ""

    # Resultado do CriticAgent
    is_correct: bool = False
    score: int = 0
    critic_feedback: str = ""
    misconceptions: list[str] = field(default_factory=list)
    missing_points: list[str] = field(default_factory=list)
    correct_points: list[str] = field(default_factory=list)

    # Resultado do TutorAgent
    tutor_guidance: str = ""
    hint_level: int = 0
    should_reveal: bool = False

    # Resultado do ExplainerAgent
    explanation: str = ""
    visual_description: str = ""
    camera_analogy: str = ""

    # Metadados
    agents_used: list[str] = field(default_factory=list)
    pipeline_complete: bool = False

    def to_dict(self) -> dict:
        """Converte para dicionário."""
        return {
            "question": self.question,
            "student_answer": self.student_answer,
            "is_correct": self.is_correct,
            "score": self.score,
            "critic_feedback": self.critic_feedback,
            "misconceptions": self.misconceptions,
            "missing_points": self.missing_points,
            "correct_points": self.correct_points,
            "tutor_guidance": self.tutor_guidance,
            "hint_level": self.hint_level,
            "should_reveal": self.should_reveal,
            "explanation": self.explanation,
            "visual_description": self.visual_description,
            "camera_analogy": self.camera_analogy,
            "agents_used": self.agents_used,
            "pipeline_complete": self.pipeline_complete,
        }


class AgentOrchestrator:
    """Orquestrador multi-agente para tutoria interativa de ECG.

    Coordena três agentes especializados em um pipeline integrado:

    1. **CriticAgent**: avalia a resposta do aluno (correção, equívocos)
    2. **TutorAgent**: guia o aluno com abordagem socrática
    3. **ExplainerAgent**: fornece explicação detalhada no nível adequado

    Parameters
    ----------
    llm_backend : Any, optional
        Backend de LLM compartilhado pelos agentes. Se None, todos
        usam fallback offline (baseado em regras).
    student_level : str
        Nível do aluno: ``"iniciante"``, ``"intermediário"`` ou ``"avançado"``.
    """

    def __init__(
        self,
        llm_backend: Any = None,
        student_level: str = "iniciante",
    ) -> None:
        self.llm_backend = llm_backend
        self.student_level = student_level

        # Inicializa os agentes
        self.tutor = TutorAgent(llm_backend=llm_backend)
        self.critic = CriticAgent(llm_backend=llm_backend)
        self.explainer = ExplainerAgent(llm_backend=llm_backend)

        # Histórico de interações
        self._history: list[PipelineResult] = []

    def process_answer(
        self,
        question: str,
        student_answer: str,
        correct_answer: str,
        skill_id: str = "",
        topic: str = "",
    ) -> PipelineResult:
        """Processa a resposta do aluno pelo pipeline completo.

        Pipeline:
        1. CriticAgent avalia correção e identifica equívocos
        2. TutorAgent fornece orientação socrática baseada na avaliação
        3. ExplainerAgent gera explicação detalhada se necessário

        Parameters
        ----------
        question : str
            A pergunta que foi feita ao aluno.
        student_answer : str
            A resposta submetida pelo aluno.
        correct_answer : str
            A resposta correta esperada.
        skill_id : str
            ID da habilidade (para rastreamento de progresso).
        topic : str
            Tópico ECG relacionado.

        Returns
        -------
        PipelineResult
            Resultado completo do pipeline com feedback de todos os agentes.
        """
        result = PipelineResult(
            question=question,
            student_answer=student_answer,
            correct_answer=correct_answer,
            skill_id=skill_id,
        )

        # --- Etapa 1: CriticAgent avalia a resposta ---
        critic_result = self.critic.evaluate(
            question=question,
            student_answer=student_answer,
            correct_answer=correct_answer,
            skill_id=skill_id,
        )

        result.is_correct = critic_result["is_correct"]
        result.score = critic_result["score"]
        result.critic_feedback = critic_result["feedback"]
        result.misconceptions = critic_result["misconceptions"]
        result.missing_points = critic_result["missing_points"]
        result.correct_points = critic_result["correct_points"]
        result.agents_used.append("CriticAgent")

        # --- Etapa 2: TutorAgent guia o aluno ---
        tutor_context = {
            "skill_id": skill_id,
            "question": question,
            "correct_answer": correct_answer,
            "is_correct": result.is_correct,
            "score": result.score,
            "misconceptions": result.misconceptions,
        }

        tutor_result = self.tutor.guide(
            student_answer=student_answer,
            context=tutor_context,
        )

        result.tutor_guidance = tutor_result["message"]
        result.hint_level = tutor_result["hint_level"]
        result.should_reveal = tutor_result["should_reveal"]
        result.agents_used.append("TutorAgent")

        # --- Etapa 3: ExplainerAgent fornece explicação ---
        # Sempre explica se errou; explica se acertou mas com equívocos
        needs_explanation = (
            not result.is_correct
            or result.misconceptions
            or result.score < 80
        )

        if needs_explanation:
            explain_topic = topic or self._extract_topic(skill_id, question)
            explain_result = self.explainer.explain(
                topic=explain_topic,
                level=self.student_level,
                include_visual=True,
            )

            result.explanation = explain_result["explanation"]
            result.visual_description = explain_result.get("visual_description", "")
            result.camera_analogy = explain_result.get("camera_analogy", "")
            result.agents_used.append("ExplainerAgent")

        result.pipeline_complete = True
        self._history.append(result)

        return result

    def ask_question(self, question: str) -> dict:
        """Aluno faz uma pergunta livre (sem contexto de resposta).

        O TutorAgent responde com abordagem socrática e o ExplainerAgent
        complementa se necessário.

        Parameters
        ----------
        question : str
            Pergunta do aluno.

        Returns
        -------
        dict
            Resposta com ``tutor_response``, ``explanation`` e
            ``visual_description``.
        """
        # TutorAgent responde
        tutor_result = self.tutor.guide(student_answer=question)

        # ExplainerAgent complementa se o tópico for identificado
        topic = tutor_result.get("topic", "")
        explanation = ""
        visual = ""

        if topic:
            explain_result = self.explainer.explain(
                topic=topic,
                level=self.student_level,
                include_visual=True,
            )
            explanation = explain_result["explanation"]
            visual = explain_result.get("visual_description", "")

        return {
            "tutor_response": tutor_result["message"],
            "explanation": explanation,
            "visual_description": visual,
            "topic": topic,
        }

    def get_session_summary(self) -> dict:
        """Gera resumo da sessão de tutoria.

        Returns
        -------
        dict
            Resumo com estatísticas da sessão.
        """
        if not self._history:
            return {
                "total_questions": 0,
                "correct": 0,
                "incorrect": 0,
                "average_score": 0.0,
                "topics_covered": [],
                "common_misconceptions": [],
                "message": "Nenhuma interação registrada nesta sessão.",
            }

        total = len(self._history)
        correct = sum(1 for r in self._history if r.is_correct)
        scores = [r.score for r in self._history]
        avg_score = sum(scores) / len(scores) if scores else 0.0

        # Tópicos cobertos
        topics = set()
        for r in self._history:
            if r.skill_id:
                parts = r.skill_id.split("::")
                topics.add(parts[-1] if parts else r.skill_id)

        # Equívocos mais comuns
        all_misconceptions: list[str] = []
        for r in self._history:
            all_misconceptions.extend(r.misconceptions)

        # Conta frequência
        mc_counts: dict[str, int] = {}
        for mc in all_misconceptions:
            mc_counts[mc] = mc_counts.get(mc, 0) + 1
        common_mc = sorted(mc_counts.items(), key=lambda x: x[1], reverse=True)

        # Mensagem de resumo
        accuracy = correct / total * 100 if total > 0 else 0
        if accuracy >= 80:
            message = (
                f"Excelente sessão! Você acertou {correct}/{total} "
                f"({accuracy:.0f}%). Continue praticando para manter a maestria!"
            )
        elif accuracy >= 50:
            message = (
                f"Boa sessão! {correct}/{total} corretas ({accuracy:.0f}%). "
                "Revise os tópicos em que teve dificuldade."
            )
        else:
            message = (
                f"Sessão de aprendizado: {correct}/{total} corretas ({accuracy:.0f}%). "
                "Não desanime — cada erro é uma oportunidade. "
                "Revise os conceitos usando as analogias da câmera."
            )

        return {
            "total_questions": total,
            "correct": correct,
            "incorrect": total - correct,
            "average_score": round(avg_score, 1),
            "topics_covered": sorted(topics),
            "common_misconceptions": [mc for mc, _ in common_mc[:5]],
            "message": message,
        }

    def reset_session(self) -> None:
        """Reseta a sessão de tutoria."""
        self._history = []
        self.tutor.reset()

    @property
    def history(self) -> list[PipelineResult]:
        """Histórico de interações da sessão."""
        return self._history

    # ------------------------------------------------------------------
    # Utilitários
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_topic(skill_id: str, question: str) -> str:
        """Extrai tópico do skill_id ou da pergunta."""
        if skill_id:
            parts = skill_id.split("::")
            return parts[-1] if parts else skill_id

        # Tenta extrair da pergunta
        q_lower = question.lower()
        topic_hints = {
            "onda p": "onda_p",
            "qrs": "complexo_qrs",
            "onda t": "onda_t",
            "pr": "intervalo_pr",
            "qt": "intervalo_qt",
            "st": "segmento_st",
            "ritmo": "ritmo_sinusal",
            "fibrilação": "fibrilacao_atrial",
            "bloqueio": "bloqueio_ramo",
            "eixo": "eixo_eletrico",
        }
        for hint, topic in topic_hints.items():
            if hint in q_lower:
                return topic

        return "ECG geral"

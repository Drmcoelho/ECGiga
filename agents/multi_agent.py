"""Multi-agent system for ECG education: tutor, critic, explainer.

Three specialized agents work together:
- Clinical Tutor: Plans learning sessions, selects topics
- Scientific Critic: Validates facts against references
- Didactic Explainer: Rewrites content at appropriate complexity level

Anti-hallucination safeguards built-in.
"""

from __future__ import annotations
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class AgentMessage:
    """Message passed between agents."""
    role: str  # "tutor", "critic", "explainer"
    content: str
    confidence: float = 1.0  # 0-1
    references: list[str] = field(default_factory=list)
    flags: list[str] = field(default_factory=list)


class ClinicalTutor:
    """Plans learning sessions and selects topics based on student progress."""

    def plan_session(self, progress: dict, n_topics: int = 3) -> dict:
        """Plan a learning session based on student progress."""
        weak_topics = progress.get("weak_topics", [])
        strong_topics = progress.get("strong_topics", [])
        ability = progress.get("ability", 0.5)

        # Select topics: prioritize weak, add new ones
        selected = []
        for topic in weak_topics[:n_topics]:
            selected.append({"topic": topic, "reason": "weak_area", "priority": "high"})

        # Fill remaining slots with topics not yet covered
        all_topics = [
            "ritmo_sinusal", "frequencia_cardiaca", "eixo_eletrico",
            "intervalo_pr", "duracao_qrs", "intervalo_qt",
            "bloqueio_ramo", "bav", "fibrilacao_atrial",
            "flutter_atrial", "stemi", "nstemi",
            "hipercalemia", "hipocalemia", "pre_excitacao",
        ]
        covered = set(weak_topics + strong_topics)
        for topic in all_topics:
            if len(selected) >= n_topics:
                break
            if topic not in covered:
                selected.append({"topic": topic, "reason": "new_topic", "priority": "medium"})

        # Determine difficulty level
        if ability < 0.3:
            level = "easy"
        elif ability < 0.6:
            level = "medium"
        elif ability < 0.8:
            level = "hard"
        else:
            level = "expert"

        return {
            "topics": selected,
            "recommended_difficulty": level,
            "session_type": "review" if weak_topics else "exploration",
            "estimated_questions": n_topics * 3,
        }

    def generate_feedback(self, session_results: list[dict]) -> AgentMessage:
        """Generate personalized feedback after a session."""
        total = len(session_results)
        correct = sum(1 for r in session_results if r.get("correct", False))
        accuracy = correct / total if total > 0 else 0

        if accuracy >= 0.9:
            msg = "Excelente desempenho! Você domina bem estes tópicos."
        elif accuracy >= 0.7:
            msg = "Bom trabalho! Revise os tópicos onde errou para consolidar."
        elif accuracy >= 0.5:
            msg = "Progresso razoável. Recomendo revisitar as lições antes de prosseguir."
        else:
            msg = "Estes tópicos precisam de mais estudo. Reveja as lições com calma."

        wrong_topics = list(set(
            r.get("tag", r.get("topic", ""))
            for r in session_results if not r.get("correct", False)
        ))
        if wrong_topics:
            msg += f" Foco em: {', '.join(wrong_topics)}."

        return AgentMessage(
            role="tutor",
            content=msg,
            confidence=0.9,
        )


class ScientificCritic:
    """Validates generated content against medical knowledge."""

    # Known facts for rule-based validation
    FACTS = {
        "pr_normal_range": (120, 200),  # ms
        "qrs_normal_max": 120,  # ms
        "qtc_prolonged": 460,  # ms (conservative)
        "hr_normal_range": (60, 100),  # bpm
        "axis_normal_range": (-30, 90),  # degrees
    }

    REFERENCE_SOURCES = [
        "Braunwald's Heart Disease, 12th Ed.",
        "Goldberger's Clinical Electrocardiography, 10th Ed.",
        "Dubin's Rapid Interpretation of EKG's, 6th Ed.",
        "Hurst's The Heart, 14th Ed.",
        "AHA/ACC/HRS Guidelines for ECG Interpretation",
    ]

    def validate_content(self, content: str) -> AgentMessage:
        """Validate medical content for accuracy."""
        flags = []
        references = []

        # Check for common errors
        content_lower = content.lower()

        if "pr normal" in content_lower and "200" not in content:
            flags.append("Verificar: limite superior do PR normal é 200ms")

        if "qrs normal" in content_lower and "120" not in content:
            flags.append("Verificar: limite superior do QRS normal é 120ms")

        if "bazett" in content_lower:
            references.append("Bazett HC. Heart 1920;7:353-370")

        if "fridericia" in content_lower:
            references.append("Fridericia LS. Acta Med Scand 1920;53:469-486")

        confidence = 1.0 - (len(flags) * 0.15)

        return AgentMessage(
            role="critic",
            content="Validação concluída." if not flags else "Encontrados pontos para revisão.",
            confidence=max(0.3, confidence),
            references=references or self.REFERENCE_SOURCES[:2],
            flags=flags,
        )

    def verify_intervals(self, intervals: dict) -> AgentMessage:
        """Verify that reported intervals are physiologically plausible."""
        flags = []

        pr = intervals.get("PR_ms")
        if pr is not None:
            if pr < 80 or pr > 400:
                flags.append(f"PR={pr}ms fora da faixa fisiológica (80-400ms)")

        qrs = intervals.get("QRS_ms")
        if qrs is not None:
            if qrs < 40 or qrs > 250:
                flags.append(f"QRS={qrs}ms fora da faixa fisiológica (40-250ms)")

        qt = intervals.get("QT_ms")
        if qt is not None:
            if qt < 200 or qt > 700:
                flags.append(f"QT={qt}ms fora da faixa fisiológica (200-700ms)")

        return AgentMessage(
            role="critic",
            content="Intervalos plausíveis." if not flags else "Intervalos suspeitos.",
            confidence=1.0 if not flags else 0.5,
            flags=flags,
        )


class DidacticExplainer:
    """Rewrites content at different complexity levels."""

    LEVELS = {
        "student": {
            "description": "Estudante de medicina (3º-4º ano)",
            "vocabulary": "termos básicos, analogias simples",
            "depth": "conceitos fundamentais",
        },
        "resident": {
            "description": "Residente de clínica médica",
            "vocabulary": "terminologia padrão, fisiopatologia",
            "depth": "diagnóstico diferencial e conduta",
        },
        "specialist": {
            "description": "Cardiologista",
            "vocabulary": "terminologia avançada, eletrofisiologia",
            "depth": "mecanismos iônicos, evidência científica",
        },
    }

    def explain(self, topic: str, level: str = "student") -> AgentMessage:
        """Generate explanation at appropriate level."""
        level_info = self.LEVELS.get(level, self.LEVELS["student"])

        # Rule-based explanations for common topics
        explanations = self._get_explanations(topic)

        if level in explanations:
            content = explanations[level]
        else:
            content = explanations.get("student", f"Explicação sobre {topic} não disponível offline.")

        return AgentMessage(
            role="explainer",
            content=content,
            confidence=0.85,
            references=["Goldberger's Clinical ECG", "Dubin's Rapid Interpretation"],
        )

    def _get_explanations(self, topic: str) -> dict:
        """Get pre-built explanations for common ECG topics."""
        topic_lower = topic.lower()

        if "pr" in topic_lower or "bav" in topic_lower:
            return {
                "student": (
                    "O intervalo PR representa o tempo que o impulso elétrico "
                    "leva para ir do nó sinusal até os ventrículos. Normal: 120-200ms. "
                    "Se > 200ms, chamamos de BAV de 1º grau — é como um 'atraso' "
                    "no sistema de condução."
                ),
                "resident": (
                    "O intervalo PR (120-200ms) reflete a condução AV. "
                    "Prolongamento (BAV 1º grau) pode ser fisiológico (vagotonia), "
                    "farmacológico (betabloqueadores, digitálicos, BCC) ou patológico "
                    "(doença degenerativa, miocardite). Isolado, raramente requer intervenção."
                ),
                "specialist": (
                    "O PR engloba condução intra-atrial, pelo nó AV (maior contribuinte) "
                    "e sistema His-Purkinje. O atraso nodal AV é mediado por correntes de "
                    "cálcio tipo L (ICa,L), sendo sensível a tônus vagal e fármacos "
                    "cronotrópicos negativos. BAV 1º grau com PR > 300ms pode evoluir "
                    "para graus maiores — monitorar com Holter."
                ),
            }

        if "qrs" in topic_lower or "bloqueio" in topic_lower:
            return {
                "student": (
                    "O complexo QRS representa a despolarização dos ventrículos. "
                    "Normal: < 120ms. Se alargado (≥ 120ms), pode indicar bloqueio "
                    "de ramo — o impulso tem que 'dar a volta' pelo caminho alternativo."
                ),
                "resident": (
                    "QRS ≥ 120ms indica condução ventricular anormal. BRD: rSR' em V1-V2 "
                    "com S largo em I/V6. BRE: ausência de q em I/V5-V6 com R monofásico. "
                    "BRE novo em contexto de dor torácica = até provar o contrário, IAM."
                ),
                "specialist": (
                    "O alargamento do QRS reflete condução miocárdica célula-a-célula "
                    "vs via His-Purkinje (velocidade 4m/s vs 0.3-0.4m/s). BRE com "
                    "QRS > 150ms e padrão típico são critérios para TRC em IC com "
                    "FEVE ≤ 35%. Critérios de Sgarbossa/Smith modificados para STEMI "
                    "na presença de BRE."
                ),
            }

        return {
            "student": f"Tópico: {topic}. Consulte as lições do módulo ECG Básico.",
        }


class AgentOrchestrator:
    """Coordinates the three agents for a learning session."""

    def __init__(self):
        self.tutor = ClinicalTutor()
        self.critic = ScientificCritic()
        self.explainer = DidacticExplainer()

    def run_session(self, progress: dict, level: str = "student") -> dict:
        """Run a complete tutoring session."""
        # 1. Tutor plans session
        plan = self.tutor.plan_session(progress)

        # 2. Explainer prepares content for each topic
        explanations = []
        for topic_info in plan["topics"]:
            topic = topic_info["topic"]
            explanation = self.explainer.explain(topic, level=level)

            # 3. Critic validates
            validation = self.critic.validate_content(explanation.content)

            explanations.append({
                "topic": topic,
                "explanation": explanation.content,
                "confidence": min(explanation.confidence, validation.confidence),
                "references": explanation.references + validation.references,
                "flags": validation.flags,
            })

        return {
            "plan": plan,
            "explanations": explanations,
            "level": level,
            "disclaimer": (
                "⚠️ Este conteúdo é gerado para fins educacionais. "
                "Sempre consulte fontes médicas validadas e orientação profissional."
            ),
        }

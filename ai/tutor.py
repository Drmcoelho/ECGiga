"""
Interactive ECG tutor with LLM and offline modes.

Phase 22 (p22) - AI/LLM integration for interactive tutoring.
"""

from __future__ import annotations

import random
from typing import Any

from .prompts import (
    SYSTEM_PROMPT_TUTOR,
    CAMERA_ANALOGY_CONTEXT,
    build_tutor_prompt,
    build_interpretation_prompt,
    build_quiz_feedback_prompt,
)
from .offline_rules import interpret_report


class ECGTutor:
    """Interactive ECG tutor powered by an LLM backend.

    Uses an :class:`~ai.interpreter.ECGInterpreter` instance for LLM calls.
    Falls back to :class:`OfflineTutor` when no interpreter is available.

    Parameters
    ----------
    interpreter : ECGInterpreter | None
        An optional interpreter instance. If ``None``, all methods fall
        back to offline rule-based responses.
    """

    def __init__(self, interpreter: Any | None = None) -> None:
        self.interpreter = interpreter
        self._session_topic: str | None = None
        self._session_level: str = "beginner"
        self._conversation: list[dict[str, str]] = []
        self._offline = OfflineTutor()

    def start_session(self, topic: str, level: str = "beginner") -> str:
        """Start a tutoring session on a given ECG topic.

        Parameters
        ----------
        topic : str
            The ECG topic to study (e.g. "Fibrilação Atrial").
        level : str
            Student level: ``"beginner"``, ``"intermediate"``, or ``"advanced"``.

        Returns
        -------
        str
            An introductory lesson for the topic.
        """
        self._session_topic = topic
        self._session_level = level
        self._conversation = []

        prompt = build_tutor_prompt(topic, level)

        if self.interpreter and self.interpreter.backend != "offline":
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT_TUTOR},
                {"role": "user", "content": prompt},
            ]
            try:
                response = self.interpreter._dispatch(messages)
                self._conversation.append({"role": "assistant", "content": response})
                return response
            except Exception:
                pass

        # Offline fallback
        return self._offline_start_session(topic, level)

    def ask_question(self, question: str) -> str:
        """Student asks a question during a tutoring session.

        Parameters
        ----------
        question : str
            The student's question.

        Returns
        -------
        str
            The tutor's answer.
        """
        self._conversation.append({"role": "user", "content": question})

        if self.interpreter and self.interpreter.backend != "offline":
            context = (
                f"Tópico da sessão: {self._session_topic or 'Geral'}\n"
                f"Nível: {self._session_level}\n\n"
                f"Pergunta do aluno: {question}\n\n"
                "Responda de forma didática, usando analogias com câmera quando possível."
            )
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT_TUTOR},
            ]
            # Include conversation history (last 10 exchanges)
            for msg in self._conversation[-10:]:
                messages.append(msg)
            messages.append({"role": "user", "content": context})

            try:
                response = self.interpreter._dispatch(messages)
                self._conversation.append({"role": "assistant", "content": response})
                return response
            except Exception:
                pass

        # Offline fallback
        answer = self._offline_answer(question)
        self._conversation.append({"role": "assistant", "content": answer})
        return answer

    def explain_report(self, report: dict) -> str:
        """Explain an ECG report step by step.

        Parameters
        ----------
        report : dict
            ECG report dictionary.

        Returns
        -------
        str
            Step-by-step explanation of the report.
        """
        if self.interpreter and self.interpreter.backend != "offline":
            prompt = build_interpretation_prompt(report)
            tutor_prompt = (
                f"{prompt}\n\n"
                "Por favor, explique este ECG passo a passo para um estudante "
                f"de nível {self._session_level}. "
                "Use analogias com câmera fotográfica em cada passo."
            )
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT_TUTOR},
                {"role": "user", "content": tutor_prompt},
            ]
            try:
                return self.interpreter._dispatch(messages)
            except Exception:
                pass

        # Offline fallback
        return self._offline_explain_report(report)

    def generate_practice_case(self, difficulty: str = "medium") -> dict:
        """Generate a practice ECG case for the student.

        Parameters
        ----------
        difficulty : str
            Case difficulty: ``"easy"``, ``"medium"``, or ``"hard"``.

        Returns
        -------
        dict
            A practice case with ``"scenario"``, ``"report"``, ``"questions"``,
            and ``"expected_findings"`` keys.
        """
        cases = _PRACTICE_CASES.get(difficulty, _PRACTICE_CASES["medium"])
        case = random.choice(cases)
        return case

    def evaluate_student_interpretation(
        self, report: dict, student_text: str
    ) -> dict:
        """Evaluate a student's ECG interpretation.

        Parameters
        ----------
        report : dict
            The ECG report that the student interpreted.
        student_text : str
            The student's free-text interpretation.

        Returns
        -------
        dict
            Evaluation with ``"score"``, ``"feedback"``, ``"missed_findings"``,
            and ``"correct_findings"`` keys.
        """
        # Get reference interpretation
        reference = interpret_report(report)
        ref_findings = reference["interpretation"]

        if self.interpreter and self.interpreter.backend != "offline":
            prompt = (
                f"## Avaliação de Interpretação de ECG\n\n"
                f"### Relatório ECG:\n{build_interpretation_prompt(report)}\n\n"
                f"### Interpretação do aluno:\n{student_text}\n\n"
                f"### Interpretação de referência:\n{ref_findings}\n\n"
                "Avalie a interpretação do aluno:\n"
                "1. Quais achados o aluno identificou corretamente?\n"
                "2. Quais achados o aluno perdeu?\n"
                "3. Há erros na interpretação?\n"
                "4. Dê uma nota de 0-100.\n"
                "5. Forneça feedback construtivo usando analogias com câmera."
            )
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT_TUTOR},
                {"role": "user", "content": prompt},
            ]
            try:
                response = self.interpreter._dispatch(messages)
                return {
                    "score": self._extract_score(response),
                    "feedback": response,
                    "missed_findings": [],
                    "correct_findings": [],
                }
            except Exception:
                pass

        # Offline evaluation
        return self._offline_evaluate(report, student_text, reference)

    # ------------------------------------------------------------------
    # Offline fallbacks
    # ------------------------------------------------------------------

    def _offline_start_session(self, topic: str, level: str) -> str:
        """Generate offline session intro."""
        level_labels = {
            "beginner": "Iniciante",
            "intermediate": "Intermediário",
            "advanced": "Avançado",
        }
        level_pt = level_labels.get(level, "Iniciante")

        # Check if we have an offline explanation for the topic
        explanation = self._offline.explain_finding(topic)

        intro = (
            f"# Sessão de Tutoria: {topic}\n"
            f"**Nível:** {level_pt}\n\n"
            "Bem-vindo à sessão de tutoria de ECG! Vamos usar analogias com "
            "câmeras fotográficas para entender melhor este tema.\n\n"
            f"{explanation}\n\n"
            "Sinta-se à vontade para fazer perguntas sobre este tema."
        )
        return intro

    def _offline_answer(self, question: str) -> str:
        """Generate offline answer to a question."""
        q_lower = question.lower()

        # Try to match question to known findings
        for key in self._offline.EXPLANATIONS:
            if key.lower() in q_lower:
                return self._offline.explain_finding(key)

        return (
            "Esta é uma ótima pergunta! No modo offline, minhas respostas são "
            "limitadas a explicações pré-definidas. Para uma resposta mais "
            "detalhada e personalizada, ative o modo online com uma API de LLM.\n\n"
            "Enquanto isso, aqui vai uma dica geral:\n"
            "Lembre-se de que cada derivação do ECG é como uma câmera fotográfica "
            "em um ângulo diferente. Para interpretar qualquer achado, pense em "
            "como ele apareceria em diferentes câmeras (derivações) e o que isso "
            "diz sobre a localização e natureza do problema."
        )

    def _offline_explain_report(self, report: dict) -> str:
        """Generate offline step-by-step report explanation."""
        result = interpret_report(report)

        parts = [
            "# Explicação Passo a Passo do ECG\n",
            "## Passo 1: Verificar o Ritmo",
            "Primeiro, olhamos se a câmera (derivação) está capturando fotos "
            "em intervalos regulares. Isso equivale a verificar se o ritmo é regular.\n",
        ]

        # Heart rate
        iv = report.get("intervals_refined") or report.get("intervals") or {}
        med = iv.get("median", {})
        rr = med.get("RR_s", 0)
        if rr and rr > 0:
            hr = 60.0 / rr
            parts.append(
                f"## Passo 2: Frequência Cardíaca\n"
                f"A câmera dispara a cada {rr:.2f} segundos, resultando em "
                f"~{hr:.0f} fotos (batimentos) por minuto.\n"
            )

        # PR interval
        pr = med.get("PR_ms")
        if pr:
            parts.append(
                f"## Passo 3: Intervalo PR ({pr:.0f} ms)\n"
                f"O tempo entre o flash (onda P) e o obturador (QRS) é de {pr:.0f} ms. "
            )
            if pr > 200:
                parts.append("Está prolongado — a câmera demora mais que o normal para disparar.\n")
            elif pr < 120:
                parts.append("Está curto — existe um possível atalho no mecanismo.\n")
            else:
                parts.append("Dentro do normal.\n")

        # QRS
        qrs = med.get("QRS_ms")
        if qrs:
            parts.append(
                f"## Passo 4: Complexo QRS ({qrs:.0f} ms)\n"
                f"O tempo de abertura do obturador é de {qrs:.0f} ms. "
            )
            if qrs > 120:
                parts.append("Está alargado — o obturador demora mais que o normal.\n")
            else:
                parts.append("Duração normal.\n")

        # QTc
        qtc = med.get("QTc_B")
        if qtc:
            parts.append(
                f"## Passo 5: Intervalo QTc ({qtc:.0f} ms)\n"
                f"O ciclo completo da câmera é de {qtc:.0f} ms. "
            )
            if qtc > 460:
                parts.append("Está prolongado — risco de a câmera não resetar a tempo.\n")
            elif qtc < 340:
                parts.append("Está curto — reset precoce.\n")
            else:
                parts.append("Dentro do normal.\n")

        # Axis
        axis = report.get("axis", {})
        angle = axis.get("angle_deg")
        if angle is not None:
            parts.append(
                f"## Passo 6: Eixo Elétrico ({angle:.0f}°)\n"
                f"O ângulo principal captado pelas câmeras frontais é de {angle:.0f}°. "
            )
            if -30 <= angle <= 90:
                parts.append("Está na faixa normal.\n")
            else:
                parts.append("Há desvio — as câmeras de um lado captam sinais mais fortes.\n")

        # Summary
        parts.append("## Conclusão\n")
        parts.append(result["interpretation"].split("### Achados")[-1] if "### Achados" in result["interpretation"] else result["interpretation"])

        return "\n".join(parts)

    def _offline_evaluate(
        self, report: dict, student_text: str, reference: dict
    ) -> dict:
        """Offline student evaluation."""
        student_lower = student_text.lower()
        ref_findings = reference.get("interpretation", "").lower()

        # Simple keyword matching
        keywords = [
            "normal", "taquicardia", "bradicardia", "prolongado", "curto",
            "alargado", "desvio", "eixo", "bloqueio", "ritmo",
        ]
        correct = []
        missed = []

        for kw in keywords:
            if kw in ref_findings:
                if kw in student_lower:
                    correct.append(kw)
                else:
                    missed.append(kw)

        total_relevant = len(correct) + len(missed)
        score = int(100 * len(correct) / total_relevant) if total_relevant > 0 else 50

        feedback = (
            f"Sua interpretação identificou {len(correct)} de "
            f"{total_relevant} achados relevantes.\n\n"
        )
        if correct:
            feedback += f"Achados corretos: {', '.join(correct)}\n"
        if missed:
            feedback += f"Achados não mencionados: {', '.join(missed)}\n"
        feedback += (
            "\nDica: Pense em cada derivação como uma câmera. Analise "
            "sistematicamente ritmo, frequência, intervalos, eixo e morfologia."
        )

        return {
            "score": score,
            "feedback": feedback,
            "missed_findings": missed,
            "correct_findings": correct,
        }

    @staticmethod
    def _extract_score(response: str) -> int:
        """Try to extract a numeric score from LLM response."""
        import re
        match = re.search(r"(\d{1,3})\s*/?\s*100", response)
        if match:
            return min(100, int(match.group(1)))
        match = re.search(r"nota[:\s]+(\d{1,3})", response, re.IGNORECASE)
        if match:
            return min(100, int(match.group(1)))
        return 50


# ======================================================================
# OfflineTutor — rule-based tutor that works without any API
# ======================================================================

class OfflineTutor:
    """Rule-based ECG tutor that works entirely offline.

    Uses camera analogies to explain ECG findings and guide study.
    """

    EXPLANATIONS: dict[str, str] = {
        # --- Waves ---
        "Onda P": (
            "A onda P é como o flash da câmera fotográfica se acendendo. "
            "Representa a despolarização atrial — o sinal elétrico que percorre os átrios "
            "antes de chegar aos ventrículos. Normalmente é arredondada, positiva em DII "
            "e dura menos de 120 ms (menos de 3 quadradinhos)."
        ),
        "Complexo QRS": (
            "O complexo QRS é como o obturador da câmera disparando — é o momento "
            "principal da captura elétrica. Representa a despolarização ventricular. "
            "Deve durar menos de 120 ms. Se for mais largo, o obturador está lento "
            "(possível bloqueio de ramo)."
        ),
        "Onda T": (
            "A onda T é como a câmera reiniciando para a próxima foto. Representa "
            "a repolarização ventricular. Normalmente é concordante com o QRS "
            "(positiva onde o QRS é positivo). Inversões podem indicar isquemia — "
            "como se a câmera tivesse dificuldade em resetar."
        ),
        "Onda U": (
            "A onda U é como um pequeno brilho residual após o reset da câmera. "
            "Às vezes visível após a onda T, pode ser normal ou indicar hipocalemia. "
            "É como uma reverberação do flash."
        ),
        # --- Intervals ---
        "Intervalo PR": (
            "O intervalo PR é o tempo entre o flash (onda P) e o disparo do obturador "
            "(complexo QRS). Normal: 120-200 ms. Se >200 ms, há bloqueio AV de 1.° grau "
            "(a câmera demora para disparar). Se <120 ms, pode haver pré-excitação "
            "(atalho no mecanismo)."
        ),
        "Intervalo QRS": (
            "A duração do QRS é o tempo que o obturador leva para abrir e fechar. "
            "Normal: <120 ms. Se alargado, pode indicar bloqueio de ramo (obturador lento) "
            "ou ritmo ventricular (disparo manual em vez de automático)."
        ),
        "Intervalo QT": (
            "O intervalo QT é o ciclo completo: do disparo do obturador (QRS) até o reset "
            "total (fim da onda T). Deve ser corrigido pela frequência (QTc). "
            "QTc >460 ms é prolongado — risco de arritmias (a câmera pode não estar "
            "pronta para a próxima foto)."
        ),
        "Intervalo RR": (
            "O intervalo RR é o tempo entre duas fotos consecutivas. Determina a "
            "frequência cardíaca: FC = 60/RR. RR regular = ritmo regular. "
            "RR irregular = ritmo irregular (como um fotógrafo sem ritmo)."
        ),
        # --- Rhythms ---
        "Ritmo Sinusal": (
            "Ritmo sinusal é como uma câmera automática funcionando perfeitamente: "
            "o flash (onda P) precede cada disparo (QRS) com intervalo constante, "
            "o eixo da onda P é normal, e a frequência está entre 60-100 bpm."
        ),
        "Fibrilação Atrial": (
            "Na fibrilação atrial, o flash da câmera dispara caoticamente — centenas "
            "de flashes por minuto, sem padrão definido. As ondas P desaparecem, "
            "substituídas por ondulações irregulares. O obturador (QRS) dispara "
            "em intervalos irregulares: ritmo irregularmente irregular."
        ),
        "Flutter Atrial": (
            "No flutter atrial, o flash da câmera dispara em frequência fixa muito "
            "alta (~300/min), criando um padrão de dente de serra. O obturador "
            "responde apenas a cada 2.° ou 3.° flash (condução 2:1 ou 3:1)."
        ),
        "Taquicardia Sinusal": (
            "A câmera está em modo burst — disparando mais de 100 fotos por minuto, "
            "mas cada foto é perfeita (onda P normal antes de cada QRS). Causas: "
            "exercício, febre, ansiedade, dor, hipertireoidismo."
        ),
        "Bradicardia Sinusal": (
            "A câmera está em modo lento — menos de 60 disparos por minuto, "
            "mas cada foto é perfeita. Pode ser fisiológico em atletas ou "
            "patológico (disfunção do nó sinusal, efeito medicamentoso)."
        ),
        "Taquicardia Ventricular": (
            "O obturador disparou por conta própria, sem comando do flash — "
            "como se a câmera tivesse sido hackeada. QRS alargado (>120 ms), "
            "FC >100 bpm. É uma emergência: a câmera pode travar completamente."
        ),
        # --- Blocks ---
        "Bloqueio AV 1° Grau": (
            "O timer entre o flash e o obturador está mais lento que o normal — "
            "PR >200 ms. Cada flash ainda produz uma foto, mas com atraso. "
            "Como uma câmera que demora para processar o sinal do flash."
        ),
        "Bloqueio AV 2° Grau": (
            "Alguns flashes não conseguem acionar o obturador — o sinal se perde "
            "no caminho. No tipo Mobitz I (Wenckebach), o atraso aumenta "
            "progressivamente até um flash ser perdido. No tipo Mobitz II, "
            "o obturador falha subitamente sem aviso."
        ),
        "Bloqueio AV 3° Grau": (
            "O flash e o obturador estão completamente desconectados — cada um "
            "trabalha no seu próprio ritmo. Os átrios disparam flashes, mas os "
            "ventrículos seguem um ritmo de escape independente. Dissociação AV completa."
        ),
        "Bloqueio de Ramo Direito": (
            "O lado direito do obturador está lento — a imagem do lado direito "
            "é capturada com atraso. QRS >120 ms com padrão RSR' em V1 "
            "(como um duplo clique do obturador)."
        ),
        "Bloqueio de Ramo Esquerdo": (
            "O lado esquerdo do obturador está lento — a imagem do lado esquerdo "
            "é capturada com atraso. QRS >120 ms com QS ou rS em V1 e R largo "
            "em V5-V6. Como se o obturador abrisse pela direita e lentamente "
            "completasse o lado esquerdo."
        ),
        # --- Pathologies ---
        "Hipertrofia Ventricular Esquerda": (
            "O ventrículo esquerdo está tão grande que domina as fotos de todas as "
            "câmeras do lado esquerdo. As câmeras V5-V6 captam voltagens muito altas "
            "(R alto), enquanto V1-V2 mostram S profundo. Como fotografar um objeto "
            "que cresceu demais para um lado."
        ),
        "Infarto Agudo": (
            "Algumas câmeras mostram uma área brilhante demais (supra de ST) — "
            "sinal de que parte do coração está sofrendo lesão aguda. As derivações "
            "afetadas indicam qual parede do coração está comprometida, como câmeras "
            "apontando para a região danificada."
        ),
        "Pericardite": (
            "Todas as câmeras mostram brilho difuso (supra de ST difuso e côncavo) — "
            "como se houvesse uma inflamação ao redor de todo o coração, afetando "
            "a foto de todos os ângulos igualmente."
        ),
        "Wolff-Parkinson-White": (
            "Existe um atalho secreto no mecanismo da câmera: o sinal do flash "
            "chega ao obturador por um caminho alternativo (feixe acessório), "
            "causando PR curto e uma onda delta (início lento do QRS). Como se o "
            "obturador começasse a abrir antes de receber o comando oficial."
        ),
        "Embolia Pulmonar": (
            "Uma obstrução súbita faz o lado direito do coração inchar, dominando "
            "as câmeras do lado direito. Padrão clássico S1Q3T3: S profundo em DI, "
            "Q em DIII, T invertida em DIII. As câmeras V1-V4 podem mostrar T invertida."
        ),
    }

    def explain_finding(self, finding: str) -> str:
        """Explain an ECG finding using camera analogies.

        Parameters
        ----------
        finding : str
            The ECG finding to explain (e.g. "Fibrilação Atrial").

        Returns
        -------
        str
            Explanation text using camera analogies.
        """
        # Direct match
        if finding in self.EXPLANATIONS:
            return self.EXPLANATIONS[finding]

        # Case-insensitive search
        finding_lower = finding.lower()
        for key, explanation in self.EXPLANATIONS.items():
            if key.lower() == finding_lower or finding_lower in key.lower() or key.lower() in finding_lower:
                return explanation

        # Partial keyword match
        for key, explanation in self.EXPLANATIONS.items():
            key_words = key.lower().split()
            if any(w in finding_lower for w in key_words if len(w) > 3):
                return f"Sobre '{key}':\n{explanation}"

        return (
            f"Não encontrei uma explicação offline específica para '{finding}'. "
            "Dica geral: pense em cada derivação como uma câmera posicionada em um "
            "ângulo diferente ao redor do coração. A alteração observada indica como "
            "a atividade elétrica aparece daquela perspectiva."
        )

    def suggest_next_topic(self, performance: dict) -> str:
        """Suggest the next study topic based on student performance.

        Parameters
        ----------
        performance : dict
            Dict mapping topic names to scores (0-100).

        Returns
        -------
        str
            Suggested next topic with rationale.
        """
        if not performance:
            return (
                "Recomendo começar com 'Ritmo Sinusal' — entender o ECG normal "
                "é como aprender a usar a câmera no modo automático antes de "
                "tentar o modo manual."
            )

        # Find weakest topic
        weakest = min(performance, key=performance.get)
        weakest_score = performance[weakest]

        if weakest_score < 50:
            return (
                f"Recomendo revisar '{weakest}' (sua nota: {weakest_score}/100). "
                "Fortalecer a base é essencial — como aprender a focar a câmera "
                "antes de tentar efeitos avançados."
            )

        # Find topics not yet studied
        studied = set(k.lower() for k in performance)
        all_topics = list(self.EXPLANATIONS.keys())
        not_studied = [t for t in all_topics if t.lower() not in studied]

        if not_studied:
            # Suggest progressively harder topics
            beginner_topics = [
                "Onda P", "Complexo QRS", "Onda T", "Intervalo PR",
                "Ritmo Sinusal", "Intervalo QRS",
            ]
            intermediate_topics = [
                "Fibrilação Atrial", "Flutter Atrial", "Taquicardia Sinusal",
                "Bradicardia Sinusal", "Bloqueio AV 1° Grau",
            ]
            advanced_topics = [
                "Bloqueio AV 3° Grau", "Taquicardia Ventricular",
                "Wolff-Parkinson-White", "Embolia Pulmonar",
            ]

            for group_name, group in [
                ("básico", beginner_topics),
                ("intermediário", intermediate_topics),
                ("avançado", advanced_topics),
            ]:
                available = [t for t in group if t in not_studied]
                if available:
                    topic = available[0]
                    return (
                        f"Recomendo estudar '{topic}' (nível {group_name}). "
                        f"Você já estudou {len(performance)} tópicos — "
                        "é hora de expandir seu repertório de câmeras!"
                    )

        # All topics studied, suggest review of weakest
        return (
            f"Excelente progresso! Você já estudou todos os tópicos principais. "
            f"Recomendo revisar '{weakest}' (nota: {weakest_score}/100) para "
            "consolidar o conhecimento. Como um fotógrafo experiente, pratique "
            "os fundamentos regularmente."
        )


# ======================================================================
# Practice cases (used by generate_practice_case)
# ======================================================================

_PRACTICE_CASES: dict[str, list[dict]] = {
    "easy": [
        {
            "scenario": (
                "Paciente masculino, 25 anos, atleta, assintomático, "
                "apresenta-se para exame de rotina."
            ),
            "report": {
                "meta": {"src": "case_easy_1.png", "lead_used": "II"},
                "version": "0.5.0",
                "intervals_refined": {
                    "median": {
                        "PR_ms": 160.0, "QRS_ms": 88.0, "QT_ms": 400.0,
                        "QTc_B": 370.0, "QTc_F": 365.0, "RR_s": 1.15,
                    }
                },
                "axis": {"angle_deg": 60.0, "label": "Normal"},
                "flags": [],
            },
            "questions": [
                "Qual é a frequência cardíaca?",
                "Os intervalos estão normais?",
                "Qual é o diagnóstico mais provável?",
            ],
            "expected_findings": [
                "Bradicardia sinusal (~52 bpm) — fisiológica em atleta",
                "Intervalos normais",
                "Eixo normal",
            ],
        },
        {
            "scenario": (
                "Paciente feminina, 30 anos, refere palpitações durante exercício. "
                "ECG de repouso."
            ),
            "report": {
                "meta": {"src": "case_easy_2.png", "lead_used": "II"},
                "version": "0.5.0",
                "intervals_refined": {
                    "median": {
                        "PR_ms": 150.0, "QRS_ms": 80.0, "QT_ms": 350.0,
                        "QTc_B": 390.0, "QTc_F": 380.0, "RR_s": 0.55,
                    }
                },
                "axis": {"angle_deg": 50.0, "label": "Normal"},
                "flags": [],
            },
            "questions": [
                "Qual é a frequência cardíaca?",
                "Este ECG é normal?",
            ],
            "expected_findings": [
                "Taquicardia sinusal (~109 bpm)",
                "Intervalos normais",
                "Eixo normal",
            ],
        },
    ],
    "medium": [
        {
            "scenario": (
                "Paciente masculino, 65 anos, hipertenso, com dispneia aos esforços. "
                "ECG mostra alterações."
            ),
            "report": {
                "meta": {"src": "case_med_1.png", "lead_used": "II"},
                "version": "0.5.0",
                "intervals_refined": {
                    "median": {
                        "PR_ms": 220.0, "QRS_ms": 130.0, "QT_ms": 420.0,
                        "QTc_B": 470.0, "QTc_F": 460.0, "RR_s": 0.8,
                    }
                },
                "axis": {"angle_deg": -45.0, "label": "Desvio para esquerda"},
                "flags": ["Possível bloqueio de ramo"],
            },
            "questions": [
                "Quais alterações você identifica?",
                "Quais são os diagnósticos diferenciais?",
                "Que exames complementares solicitaria?",
            ],
            "expected_findings": [
                "PR prolongado — BAV 1° grau",
                "QRS alargado — bloqueio de ramo",
                "QTc prolongado",
                "Desvio do eixo para esquerda",
            ],
        },
        {
            "scenario": (
                "Paciente feminina, 70 anos, tonturas e síncope. FC baixa ao exame."
            ),
            "report": {
                "meta": {"src": "case_med_2.png", "lead_used": "II"},
                "version": "0.5.0",
                "intervals_refined": {
                    "median": {
                        "PR_ms": 240.0, "QRS_ms": 92.0, "QT_ms": 480.0,
                        "QTc_B": 410.0, "QTc_F": 400.0, "RR_s": 1.4,
                    }
                },
                "axis": {"angle_deg": 30.0, "label": "Normal"},
                "flags": [],
            },
            "questions": [
                "Qual a frequência cardíaca?",
                "O que o PR prolongado sugere?",
                "Qual a conduta recomendada?",
            ],
            "expected_findings": [
                "Bradicardia (~43 bpm)",
                "PR prolongado — BAV 1° grau",
                "Eixo normal",
            ],
        },
    ],
    "hard": [
        {
            "scenario": (
                "Paciente masculino, 45 anos, dor torácica aguda, sudorese. "
                "ECG com múltiplas alterações."
            ),
            "report": {
                "meta": {"src": "case_hard_1.png", "lead_used": "II"},
                "version": "0.5.0",
                "intervals_refined": {
                    "median": {
                        "PR_ms": 100.0, "QRS_ms": 140.0, "QT_ms": 500.0,
                        "QTc_B": 500.0, "QTc_F": 490.0, "RR_s": 0.5,
                    }
                },
                "axis": {"angle_deg": 120.0, "label": "Desvio para direita"},
                "flags": ["Supra de ST em V1-V4", "Possível bloqueio de ramo"],
            },
            "questions": [
                "Quais são todas as alterações?",
                "Qual o diagnóstico mais provável?",
                "Qual a conduta de emergência?",
            ],
            "expected_findings": [
                "PR curto — pré-excitação?",
                "QRS alargado — bloqueio de ramo",
                "QTc prolongado",
                "Taquicardia",
                "Desvio do eixo para direita",
                "Supra de ST — isquemia aguda",
            ],
        },
    ],
}

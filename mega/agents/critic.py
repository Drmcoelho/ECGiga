"""CriticAgent — agente avaliador de respostas de ECG.

Avalia respostas dos alunos quanto à correção,
identifica equívocos específicos e fornece feedback estruturado.
Possui fallback offline baseado em regras.
"""

from __future__ import annotations

import re
from typing import Any


# ======================================================================
# Base de conhecimento para avaliação offline
# ======================================================================

_ECG_KNOWLEDGE: dict[str, dict] = {
    "frequencia_cardiaca": {
        "conceito": "Frequência cardíaca calculada pelo intervalo RR",
        "formula": "FC = 60 / RR(s)  ou  FC = 300 / nº de quadradões entre RR",
        "normal": "60-100 bpm",
        "keywords": ["frequência", "fc", "bpm", "batimento", "heart rate"],
        "misconceptions": {
            "fc_fixa": (
                "Equívoco: a FC é sempre fixa. Na verdade, há variabilidade "
                "normal — como o tempo entre fotos varia mesmo no modo automático."
            ),
            "rr_invertido": (
                "Atenção: FC = 60/RR, não RR/60. O intervalo RR em segundos "
                "vai no denominador."
            ),
        },
    },
    "intervalo_pr": {
        "conceito": "Tempo de condução atrioventricular",
        "normal": "120-200 ms",
        "keywords": ["pr", "atrioventricular", "condução av"],
        "misconceptions": {
            "pr_inicio": (
                "Equívoco: o PR começa no pico da P. Na verdade, mede-se do "
                "início da onda P ao início do QRS."
            ),
            "pr_curto_normal": (
                "Atenção: PR <120 ms não é normal — pode indicar pré-excitação "
                "(WPW). É como um atalho no mecanismo da câmera."
            ),
        },
    },
    "complexo_qrs": {
        "conceito": "Despolarização ventricular",
        "normal": "<120 ms",
        "keywords": ["qrs", "complexo", "ventricular", "despolarização"],
        "misconceptions": {
            "qrs_amplitude": (
                "Equívoco: QRS largo = QRS de alta amplitude. Largura (duração) "
                "e amplitude são características diferentes."
            ),
            "qrs_negativo": (
                "Atenção: QRS predominantemente negativo em DI pode indicar "
                "desvio de eixo para direita, não necessariamente patologia."
            ),
        },
    },
    "intervalo_qt": {
        "conceito": "Sístole elétrica ventricular (despolarização + repolarização)",
        "normal": "QTc <460 ms (mulheres), <450 ms (homens)",
        "keywords": ["qt", "qtc", "repolarização", "sístole"],
        "misconceptions": {
            "qt_sem_correcao": (
                "Equívoco: usar QT sem correção pela FC. O QTc (corrigido) é "
                "essencial porque o QT varia com a frequência."
            ),
            "qtc_formula": (
                "Atenção: a fórmula de Bazett (QTc = QT/√RR) superestima "
                "em taquicardia e subestima em bradicardia. "
                "Fridericia pode ser mais precisa."
            ),
        },
    },
    "ritmo_sinusal": {
        "conceito": "Ritmo originado no nó sinusal",
        "criterios": [
            "Onda P positiva em DII, negativa em aVR",
            "Cada P seguida de QRS",
            "FC 60-100 bpm",
            "PR constante 120-200 ms",
        ],
        "keywords": ["sinusal", "ritmo", "nó sinusal", "nsa"],
        "misconceptions": {
            "sinusal_fc": (
                "Equívoco: ritmo sinusal = FC entre 60-100. Bradicardia sinusal "
                "e taquicardia sinusal ainda são ritmos sinusais!"
            ),
            "p_ausente": (
                "Atenção: se não há onda P visível, o ritmo não é sinusal. "
                "A câmera automática sempre emite flash (onda P) antes do disparo."
            ),
        },
    },
    "fibrilacao_atrial": {
        "conceito": "Atividade elétrica atrial caótica",
        "criterios": [
            "Ausência de ondas P organizadas",
            "Irregularidade RR (irregularmente irregular)",
            "Linha de base fibrilatória",
        ],
        "keywords": ["fibrilação", "atrial", "fa", "irregularmente irregular"],
        "misconceptions": {
            "fa_regular": (
                "Equívoco: FA pode ser regular. Por definição, a FA é "
                "irregularmente irregular. Se RR é regular, considere flutter."
            ),
            "fa_qrs_largo": (
                "Atenção: na FA pura, o QRS é estreito. QRS largo na FA "
                "sugere condução aberrante ou bloqueio de ramo associado."
            ),
        },
    },
    "bloqueio_av": {
        "conceito": "Atraso ou falha na condução atrioventricular",
        "keywords": ["bloqueio", "bav", "av", "atrioventricular", "wenckebach", "mobitz"],
        "tipos": {
            "1grau": "PR >200 ms constante, todas as P conduzem",
            "2grau_I": "PR progressivamente mais longo até P bloqueada (Wenckebach)",
            "2grau_II": "PR constante com P bloqueada súbita (Mobitz II)",
            "3grau": "Dissociação AV completa, P e QRS independentes",
        },
        "misconceptions": {
            "bav1_benigno": (
                "Equívoco: BAV 1° grau é sempre benigno. Pode ser sinal de "
                "doença de condução progressiva em contexto clínico."
            ),
            "mobitz_confusao": (
                "Atenção: Mobitz I (Wenckebach) tem PR que alonga — é geralmente "
                "mais benigno. Mobitz II tem PR fixo com bloqueio súbito — mais grave."
            ),
        },
    },
    "supra_st": {
        "conceito": "Elevação do segmento ST acima da linha de base",
        "keywords": ["supra", "elevação", "st", "infarto", "iamcsst"],
        "diagnosticos": [
            "IAM com supra de ST",
            "Pericardite (supra difuso côncavo)",
            "Repolarização precoce (variante normal)",
            "Aneurisma ventricular",
        ],
        "misconceptions": {
            "supra_sempre_infarto": (
                "Equívoco: supra de ST = sempre infarto. Pericardite, "
                "repolarização precoce e Brugada também causam supra."
            ),
            "localizacao": (
                "Atenção: a localização do supra indica a parede afetada. "
                "V1-V4 = anterior, DII/DIII/aVF = inferior, I/aVL/V5-V6 = lateral."
            ),
        },
    },
}


class CriticAgent:
    """Agente crítico que avalia respostas de alunos sobre ECG.

    Analisa respostas quanto à correção, identifica equívocos
    específicos e fornece feedback estruturado e construtivo.

    Parameters
    ----------
    llm_backend : Any, optional
        Backend de LLM para avaliação avançada. Se None, usa fallback offline.
    """

    def __init__(self, llm_backend: Any = None) -> None:
        self.llm_backend = llm_backend

    def evaluate(
        self,
        question: str,
        student_answer: str,
        correct_answer: str,
        skill_id: str = "",
    ) -> dict:
        """Avalia a resposta do aluno.

        Parameters
        ----------
        question : str
            A pergunta feita ao aluno.
        student_answer : str
            A resposta do aluno.
        correct_answer : str
            A resposta correta esperada.
        skill_id : str
            ID da habilidade relacionada.

        Returns
        -------
        dict
            Avaliação estruturada com chaves:
            ``is_correct``, ``score`` (0-100), ``feedback``,
            ``misconceptions``, ``missing_points``, ``correct_points``.
        """
        # Tenta LLM primeiro
        if self.llm_backend is not None:
            try:
                return self._evaluate_with_llm(
                    question, student_answer, correct_answer, skill_id
                )
            except Exception:
                pass

        # Fallback offline
        return self._evaluate_offline(
            question, student_answer, correct_answer, skill_id
        )

    def identify_misconceptions(
        self, student_answer: str, topic: str = ""
    ) -> list[dict]:
        """Identifica equívocos específicos na resposta do aluno.

        Parameters
        ----------
        student_answer : str
            Resposta do aluno.
        topic : str
            Tópico ECG relacionado.

        Returns
        -------
        list[dict]
            Lista de equívocos com ``id``, ``description`` e ``correction``.
        """
        answer_lower = student_answer.lower()
        found: list[dict] = []

        # Busca em todos os tópicos de conhecimento
        for topic_key, knowledge in _ECG_KNOWLEDGE.items():
            # Verifica se o tópico é relevante
            keywords = knowledge.get("keywords", [])
            is_relevant = (
                topic.lower() in topic_key
                or any(kw in answer_lower for kw in keywords)
                or any(kw in topic.lower() for kw in keywords)
            )

            if not is_relevant:
                continue

            misconceptions = knowledge.get("misconceptions", {})
            for mc_id, mc_desc in misconceptions.items():
                # Verifica se o equívoco se aplica à resposta
                if self._check_misconception(answer_lower, mc_id, topic_key):
                    found.append({
                        "id": f"{topic_key}::{mc_id}",
                        "description": mc_desc,
                        "correction": knowledge.get("conceito", ""),
                    })

        return found

    def provide_structured_feedback(
        self,
        score: int,
        correct_points: list[str],
        missing_points: list[str],
        misconceptions: list[dict],
    ) -> str:
        """Gera feedback textual estruturado.

        Parameters
        ----------
        score : int
            Pontuação 0-100.
        correct_points : list[str]
            Pontos corretos identificados.
        missing_points : list[str]
            Pontos que faltaram.
        misconceptions : list[dict]
            Equívocos identificados.

        Returns
        -------
        str
            Feedback formatado em português.
        """
        parts: list[str] = []

        # Cabeçalho com nota
        if score >= 90:
            parts.append(f"## Avaliação: {score}/100 — Excelente!")
        elif score >= 70:
            parts.append(f"## Avaliação: {score}/100 — Bom trabalho!")
        elif score >= 50:
            parts.append(f"## Avaliação: {score}/100 — Razoável")
        else:
            parts.append(f"## Avaliação: {score}/100 — Precisa revisar")

        # Pontos corretos
        if correct_points:
            parts.append("\n### Acertos:")
            for p in correct_points:
                parts.append(f"  - {p}")

        # Pontos faltantes
        if missing_points:
            parts.append("\n### Pontos não mencionados:")
            for p in missing_points:
                parts.append(f"  - {p}")

        # Equívocos
        if misconceptions:
            parts.append("\n### Equívocos identificados:")
            for mc in misconceptions:
                parts.append(f"  - {mc['description']}")

        # Dica final com analogia
        if score < 70:
            parts.append(
                "\n**Dica:** Lembre-se da analogia da câmera fotográfica. "
                "Cada componente do ECG tem um papel específico, assim como "
                "cada parte da câmera contribui para a foto final."
            )

        return "\n".join(parts)

    # ------------------------------------------------------------------
    # Avaliação offline
    # ------------------------------------------------------------------

    def _evaluate_offline(
        self,
        question: str,
        student_answer: str,
        correct_answer: str,
        skill_id: str,
    ) -> dict:
        """Avaliação offline baseada em correspondência de palavras-chave."""
        student_lower = student_answer.lower().strip()
        correct_lower = correct_answer.lower().strip()
        question.lower()

        # Extrai palavras-chave significativas da resposta correta
        correct_keywords = self._extract_keywords(correct_lower)
        student_keywords = self._extract_keywords(student_lower)

        # Calcula correspondência
        correct_points: list[str] = []
        missing_points: list[str] = []

        for kw in correct_keywords:
            if kw in student_lower or any(
                self._fuzzy_match(kw, skw) for skw in student_keywords
            ):
                correct_points.append(kw)
            else:
                missing_points.append(kw)

        # Calcula pontuação
        total = len(correct_keywords) if correct_keywords else 1
        matched = len(correct_points)
        score = int(100 * matched / total)

        # Verifica correspondência exata ou numérica
        if self._check_exact_or_numeric(student_lower, correct_lower):
            score = max(score, 90)
            if not correct_points:
                correct_points.append(correct_answer)

        # Identifica equívocos
        topic = skill_id.split("::")[-1] if skill_id else ""
        misconceptions = self.identify_misconceptions(student_answer, topic)
        if misconceptions:
            score = max(0, score - len(misconceptions) * 10)

        is_correct = score >= 70

        # Gera feedback
        feedback = self.provide_structured_feedback(
            score, correct_points, missing_points, misconceptions
        )

        return {
            "is_correct": is_correct,
            "score": score,
            "feedback": feedback,
            "misconceptions": [mc["description"] for mc in misconceptions],
            "missing_points": missing_points,
            "correct_points": correct_points,
        }

    def _evaluate_with_llm(
        self,
        question: str,
        student_answer: str,
        correct_answer: str,
        skill_id: str,
    ) -> dict:
        """Avaliação usando LLM."""
        system_prompt = (
            "Você é um avaliador de respostas sobre ECG. "
            "Avalie a resposta do aluno comparando com a resposta correta. "
            "Identifique equívocos e pontos corretos. "
            "Use analogias com câmera fotográfica. Responda em português. "
            "Dê uma nota de 0 a 100."
        )

        user_msg = (
            f"## Pergunta:\n{question}\n\n"
            f"## Resposta do aluno:\n{student_answer}\n\n"
            f"## Resposta correta:\n{correct_answer}\n\n"
            "Avalie e forneça: nota, acertos, erros e equívocos."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg},
        ]

        response = self.llm_backend(messages)
        text = response if isinstance(response, str) else str(response)

        # Extrai nota
        score = self._extract_score(text)

        return {
            "is_correct": score >= 70,
            "score": score,
            "feedback": text,
            "misconceptions": [],
            "missing_points": [],
            "correct_points": [],
        }

    # ------------------------------------------------------------------
    # Utilitários
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_keywords(text: str) -> list[str]:
        """Extrai palavras-chave significativas de um texto."""
        # Remove palavras muito curtas e stopwords portuguesas
        stopwords = {
            "de", "do", "da", "dos", "das", "em", "no", "na", "nos", "nas",
            "um", "uma", "uns", "umas", "o", "a", "os", "as", "e", "ou",
            "que", "se", "por", "para", "com", "não", "mais", "mas", "ao",
            "é", "são", "foi", "ser", "ter", "seu", "sua", "isso", "este",
            "esta", "esse", "essa", "como", "quando", "muito", "pode",
        }
        words = re.findall(r"\b\w+\b", text.lower())
        keywords = [
            w for w in words
            if len(w) > 2 and w not in stopwords and not w.isdigit()
        ]
        # Também extrai números com unidades
        numbers = re.findall(r"\d+(?:\.\d+)?\s*(?:ms|bpm|mv|mm|seg|s)\b", text.lower())
        keywords.extend(numbers)
        return keywords

    @staticmethod
    def _fuzzy_match(a: str, b: str) -> bool:
        """Verifica correspondência aproximada entre duas palavras."""
        if a == b:
            return True
        # Verifica se uma contém a outra
        if len(a) >= 4 and (a in b or b in a):
            return True
        # Verifica raízes comuns (simplificado)
        if len(a) >= 5 and len(b) >= 5 and a[:5] == b[:5]:
            return True
        return False

    @staticmethod
    def _check_exact_or_numeric(student: str, correct: str) -> bool:
        """Verifica correspondência exata ou numérica."""
        if student.strip() == correct.strip():
            return True
        # Extrai números e compara
        student_nums = re.findall(r"\d+(?:\.\d+)?", student)
        correct_nums = re.findall(r"\d+(?:\.\d+)?", correct)
        if student_nums and correct_nums:
            return any(sn == cn for sn in student_nums for cn in correct_nums)
        return False

    @staticmethod
    def _check_misconception(
        answer: str, mc_id: str, topic_key: str
    ) -> bool:
        """Verifica se um equívoco específico se aplica à resposta."""
        # Heurísticas simples por tipo de equívoco
        checks: dict[str, list[str]] = {
            "fc_fixa": ["fixa", "constante", "não varia", "sempre igual"],
            "rr_invertido": ["rr/60", "rr dividido"],
            "pr_inicio": ["pico da p", "máximo da p"],
            "pr_curto_normal": ["pr curto é normal", "pr curto normal"],
            "qrs_amplitude": ["qrs largo é alto", "amplitude = largura"],
            "qt_sem_correcao": ["qt sem corr", "qt absoluto"],
            "sinusal_fc": ["sinusal só entre 60", "sinusal = 60-100"],
            "fa_regular": ["fa regular", "fibrilação regular"],
            "fa_qrs_largo": ["fa sempre qrs largo", "fa = qrs largo"],
            "bav1_benigno": ["bav 1 sempre benigno", "1 grau não importa"],
            "supra_sempre_infarto": ["supra = infarto", "supra sempre infarto"],
        }

        triggers = checks.get(mc_id, [])
        return any(t in answer for t in triggers)

    @staticmethod
    def _extract_score(text: str) -> int:
        """Extrai pontuação numérica de texto."""
        match = re.search(r"(\d{1,3})\s*/?\s*100", text)
        if match:
            return min(100, int(match.group(1)))
        match = re.search(r"nota[:\s]+(\d{1,3})", text, re.IGNORECASE)
        if match:
            return min(100, int(match.group(1)))
        return 50

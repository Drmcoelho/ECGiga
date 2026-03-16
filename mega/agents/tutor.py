"""TutorAgent — agente de tutoria socrática para ECG.

Usa abordagem de questionamento socrático: fornece dicas
antes de respostas completas e acompanha o contexto da conversa.
Possui fallback offline baseado em regras.
"""

from __future__ import annotations

import random
from typing import Any


# ======================================================================
# Dicas e perguntas socráticas por tópico
# ======================================================================

_SOCRATIC_HINTS: dict[str, list[str]] = {
    "onda_p": [
        "Pense na onda P como o flash da câmera. O que acontece antes de tirar a foto?",
        "Qual estrutura cardíaca gera a onda P? Lembre-se da analogia: flash = átrios.",
        "Se a onda P é o flash, o que aconteceria se o flash falhasse?",
    ],
    "qrs": [
        "O complexo QRS é o disparo do obturador. O que ele captura?",
        "Se o obturador demora mais para abrir (QRS largo), o que isso significa?",
        "Qual é a duração normal do QRS? Pense: um clique rápido do obturador.",
    ],
    "onda_t": [
        "A onda T é o reset da câmera. O que acontece se o reset for anormal?",
        "Inversão de onda T — a câmera está tendo dificuldade em resetar. Por quê?",
        "Em quais derivações você esperaria a onda T positiva normalmente?",
    ],
    "intervalo_pr": [
        "O intervalo PR é o tempo entre flash e disparo. Qual é o normal?",
        "PR >200ms — o flash demora a acionar o obturador. Qual é o diagnóstico?",
        "PR <120ms — existe um atalho. O que poderia ser?",
    ],
    "intervalo_qt": [
        "O QT é o ciclo completo da câmera. Por que precisamos corrigi-lo?",
        "QTc prolongado — a câmera não reseta a tempo. Qual é o risco?",
        "Quais medicamentos podem prolongar o QT? Pense em antiarrítmicos.",
    ],
    "ritmo_sinusal": [
        "O que define um ritmo sinusal? Pense nos critérios da câmera automática.",
        "Como você confirma que é o nó sinusal controlando? Olhe a onda P em DII.",
        "Qual a faixa de frequência do ritmo sinusal normal?",
    ],
    "fibrilacao_atrial": [
        "Na FA, o flash dispara caoticamente. O que acontece com os intervalos RR?",
        "Como diferenciamos FA de flutter atrial na câmera?",
        "Quais são os riscos da FA? Pense no que acontece quando o flash é caótico.",
    ],
    "bloqueio_av": [
        "No BAV, a conexão entre flash e obturador está comprometida. Qual grau?",
        "Como diferenciamos Mobitz I de Mobitz II? Observe o padrão do atraso.",
        "No BAVT, flash e obturador trabalham independentemente. O que vemos no ECG?",
    ],
    "bloqueio_ramo": [
        "No bloqueio de ramo, metade do obturador está lenta. Qual lado?",
        "BRD: padrão RSR' em V1. Por que vemos duplo clique?",
        "BRE: QRS largo + R monofásico em V5-V6. O que isso indica?",
    ],
    "isquemia": [
        "Supra de ST — brilho excessivo na câmera. O que está acontecendo no miocárdio?",
        "Quais derivações afetadas apontam para qual parede? Pense nos ângulos das câmeras.",
        "Qual a diferença entre isquemia (infra ST) e lesão (supra ST)?",
    ],
}

# Mapeamento de palavras-chave para tópicos
_KEYWORD_TO_TOPIC: dict[str, str] = {
    "onda p": "onda_p",
    "p wave": "onda_p",
    "qrs": "qrs",
    "complexo qrs": "qrs",
    "onda t": "onda_t",
    "t wave": "onda_t",
    "pr": "intervalo_pr",
    "intervalo pr": "intervalo_pr",
    "qt": "intervalo_qt",
    "intervalo qt": "intervalo_qt",
    "qtc": "intervalo_qt",
    "sinusal": "ritmo_sinusal",
    "ritmo sinusal": "ritmo_sinusal",
    "fibrilação atrial": "fibrilacao_atrial",
    "fibrilacao": "fibrilacao_atrial",
    "fa ": "fibrilacao_atrial",
    "flutter": "fibrilacao_atrial",
    "bloqueio av": "bloqueio_av",
    "bav": "bloqueio_av",
    "bloqueio de ramo": "bloqueio_ramo",
    "brd": "bloqueio_ramo",
    "bre": "bloqueio_ramo",
    "isquemia": "isquemia",
    "infarto": "isquemia",
    "supra": "isquemia",
    "infra": "isquemia",
    "st": "isquemia",
}


class TutorAgent:
    """Agente tutor com abordagem socrática para ensino de ECG.

    Fornece dicas progressivas antes de revelar a resposta completa.
    Mantém contexto da conversa para tutoria personalizada.

    Parameters
    ----------
    llm_backend : Any, optional
        Backend de LLM para respostas avançadas. Se None, usa fallback offline.
    """

    def __init__(self, llm_backend: Any = None) -> None:
        self.llm_backend = llm_backend
        self._conversation: list[dict[str, str]] = []
        self._current_topic: str | None = None
        self._hint_index: dict[str, int] = {}  # tópico → próxima dica
        self._revealed: set[str] = set()  # tópicos com resposta revelada

    def reset(self) -> None:
        """Reseta o contexto da conversa."""
        self._conversation = []
        self._current_topic = None
        self._hint_index = {}
        self._revealed = set()

    def guide(self, student_answer: str, context: dict | None = None) -> dict:
        """Guia o aluno com abordagem socrática.

        Em vez de dar a resposta diretamente, fornece dicas progressivas.
        Após múltiplas tentativas, revela a explicação completa.

        Parameters
        ----------
        student_answer : str
            Resposta ou pergunta do aluno.
        context : dict, optional
            Contexto adicional (skill_id, question, correct_answer, etc).

        Returns
        -------
        dict
            Resposta com chaves: ``message``, ``hint_level``, ``topic``,
            ``should_reveal``.
        """
        self._conversation.append({"role": "student", "content": student_answer})

        # Detecta o tópico
        topic = self._detect_topic(student_answer, context)
        if topic:
            self._current_topic = topic

        # Tenta LLM primeiro
        if self.llm_backend is not None:
            try:
                return self._guide_with_llm(student_answer, context, topic)
            except Exception:
                pass

        # Fallback offline
        return self._guide_offline(student_answer, context, topic)

    def provide_hint(self, topic: str | None = None) -> str:
        """Fornece a próxima dica socrática sobre um tópico.

        Parameters
        ----------
        topic : str, optional
            Tópico para a dica. Se None, usa o tópico corrente.

        Returns
        -------
        str
            Texto da dica socrática.
        """
        t = topic or self._current_topic
        if not t:
            return (
                "Sobre qual tópico de ECG você gostaria de uma dica? "
                "Pense em qual 'parte da câmera' você quer entender melhor."
            )

        # Busca tópico normalizado
        topic_key = self._normalize_topic(t)
        hints = _SOCRATIC_HINTS.get(topic_key, [])

        if not hints:
            return (
                f"Boa pergunta sobre '{t}'! "
                "Pense em como isso se relaciona com a analogia da câmera. "
                "Cada componente do ECG tem uma função, assim como cada parte "
                "da câmera tem um papel na captura da imagem."
            )

        # Pega a próxima dica (circular)
        idx = self._hint_index.get(topic_key, 0)
        hint = hints[idx % len(hints)]
        self._hint_index[topic_key] = idx + 1

        level = min(idx + 1, len(hints))
        remaining = max(0, len(hints) - level)

        if remaining == 0:
            hint += (
                "\n\nEsta foi a última dica sobre este tópico. "
                "Se ainda tiver dúvidas, peça a explicação completa."
            )

        return hint

    def get_encouragement(self, correct: bool, streak: int = 0) -> str:
        """Gera mensagem de encorajamento baseada no desempenho.

        Parameters
        ----------
        correct : bool
            Se a resposta foi correta.
        streak : int
            Número de acertos consecutivos.

        Returns
        -------
        str
            Mensagem de encorajamento.
        """
        if correct:
            if streak >= 5:
                messages = [
                    f"Incrível! {streak} acertos seguidos! Você está dominando a câmera!",
                    f"Sequência de {streak}! Você é um fotógrafo expert de ECG!",
                    f"{streak} corretas! Maestria se constrói assim — um clique de cada vez!",
                ]
            elif streak >= 3:
                messages = [
                    f"Excelente! {streak} acertos consecutivos! Continue assim!",
                    "Muito bem! Sua leitura de ECG está ficando cada vez mais afiada!",
                    "Ótimo trabalho! A câmera está em foco perfeito!",
                ]
            else:
                messages = [
                    "Correto! Bom trabalho!",
                    "Isso mesmo! Cada acerto fortalece sua habilidade.",
                    "Perfeito! A câmera captou a imagem certa.",
                    "Muito bem! Continue praticando para consolidar.",
                ]
        else:
            messages = [
                "Não foi dessa vez, mas cada erro ensina algo novo. Vamos revisar?",
                "Quase! Pense na analogia da câmera — cada derivação é um ângulo diferente.",
                "Não desanime! Até fotógrafos profissionais precisam de muita prática.",
                "Errar faz parte do aprendizado. Que tal uma dica sobre este tópico?",
            ]

        return random.choice(messages)

    @property
    def conversation_summary(self) -> str:
        """Resumo da conversa atual."""
        if not self._conversation:
            return "Nenhuma conversa em andamento."

        n = len(self._conversation)
        topic = self._current_topic or "geral"
        return (
            f"Conversa com {n} mensagens sobre '{topic}'. "
            f"Dicas reveladas: {sum(self._hint_index.values())}."
        )

    # ------------------------------------------------------------------
    # Internos
    # ------------------------------------------------------------------

    def _detect_topic(
        self, text: str, context: dict | None = None
    ) -> str | None:
        """Detecta o tópico ECG a partir do texto ou contexto."""
        # Contexto explícito tem prioridade
        if context:
            skill = context.get("skill_id", "")
            if skill:
                parts = skill.split("::")
                return parts[-1] if parts else skill

        text_lower = text.lower()
        for keyword, topic in _KEYWORD_TO_TOPIC.items():
            if keyword in text_lower:
                return topic
        return None

    def _normalize_topic(self, topic: str) -> str:
        """Normaliza nome do tópico para chave do dicionário de dicas."""
        topic_lower = topic.lower()
        # Tenta mapeamento direto
        for keyword, key in _KEYWORD_TO_TOPIC.items():
            if keyword in topic_lower or topic_lower in keyword:
                return key
        # Tenta chave direta
        if topic_lower.replace(" ", "_") in _SOCRATIC_HINTS:
            return topic_lower.replace(" ", "_")
        return topic_lower

    def _guide_offline(
        self,
        student_answer: str,
        context: dict | None,
        topic: str | None,
    ) -> dict:
        """Guia offline usando regras e dicas pré-definidas."""
        hint_level = 0
        should_reveal = False

        if topic:
            topic_key = self._normalize_topic(topic)
            hint_level = self._hint_index.get(topic_key, 0)
            hints = _SOCRATIC_HINTS.get(topic_key, [])
            should_reveal = hint_level >= len(hints) if hints else True

        # Se tem contexto de questão, usa informações da resposta correta
        if context and context.get("correct_answer"):
            correct = context.get("correct_answer", "")
            is_correct = context.get("is_correct", False)

            if is_correct:
                message = (
                    f"Exatamente! {self.get_encouragement(True)} "
                    "Quer aprofundar mais neste tópico?"
                )
            elif should_reveal or hint_level >= 2:
                message = (
                    f"A resposta correta é: {correct}\n\n"
                    + self.provide_hint(topic)
                    + "\n\nVamos tentar outra questão para praticar?"
                )
                if topic:
                    self._revealed.add(self._normalize_topic(topic))
            else:
                message = self.provide_hint(topic)
        else:
            # Pergunta livre — dá uma dica socrática
            message = self.provide_hint(topic)

        self._conversation.append({"role": "tutor", "content": message})

        return {
            "message": message,
            "hint_level": hint_level,
            "topic": topic or self._current_topic,
            "should_reveal": should_reveal,
        }

    def _guide_with_llm(
        self,
        student_answer: str,
        context: dict | None,
        topic: str | None,
    ) -> dict:
        """Guia usando LLM (requer backend configurado)."""
        system_prompt = (
            "Você é um tutor socrático de ECG. Use analogias com câmera fotográfica. "
            "Nunca dê a resposta diretamente — faça perguntas que guiem o aluno. "
            "Forneça dicas progressivas. Responda em português."
        )

        user_msg = f"Resposta/pergunta do aluno: {student_answer}"
        if context:
            user_msg += f"\nContexto: {context}"
        if topic:
            user_msg += f"\nTópico: {topic}"

        messages = [
            {"role": "system", "content": system_prompt},
        ]
        # Inclui últimas mensagens da conversa
        for msg in self._conversation[-6:]:
            role = "user" if msg["role"] == "student" else "assistant"
            messages.append({"role": role, "content": msg["content"]})
        messages.append({"role": "user", "content": user_msg})

        response = self.llm_backend(messages)

        result_msg = response if isinstance(response, str) else str(response)
        self._conversation.append({"role": "tutor", "content": result_msg})

        return {
            "message": result_msg,
            "hint_level": self._hint_index.get(
                self._normalize_topic(topic), 0
            ) if topic else 0,
            "topic": topic,
            "should_reveal": False,
        }

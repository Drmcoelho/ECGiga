"""
Prompt templates for ECG interpretation using LLMs.

Phase 22 (p22) - AI/LLM integration for differential diagnosis and interactive tutoring.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Camera analogy context block (reusable across prompts)
# ---------------------------------------------------------------------------

CAMERA_ANALOGY_CONTEXT = """\
CONTEXTO DE ANALOGIA COM CÂMERA:
Cada derivação do ECG funciona como uma câmera fotográfica posicionada em um ângulo
diferente ao redor do coração. Assim como múltiplas câmeras capturam diferentes
perspectivas de um mesmo objeto, cada derivação "fotografa" a atividade elétrica
cardíaca de um ponto de vista único.

- Derivações dos membros (I, II, III, aVR, aVL, aVF): São como câmeras posicionadas
  em um círculo ao redor do coração no plano frontal, cada uma capturando a atividade
  elétrica de um ângulo diferente. Imagine 6 fotógrafos em volta de uma estátua.

- Derivações precordiais (V1-V6): São como câmeras posicionadas em linha no peito,
  do lado direito ao esquerdo, capturando a atividade elétrica no plano horizontal.
  Imagine câmeras em fila fazendo um "scan" do coração da direita para a esquerda.

- Onda P: É como o flash da câmera se acendendo — representa a despolarização atrial,
  o sinal elétrico que inicia nos átrios.

- Complexo QRS: É como o obturador da câmera disparando — representa a despolarização
  ventricular, o momento principal de captura da atividade elétrica dos ventrículos.

- Onda T: É como a câmera reiniciando para a próxima foto — representa a repolarização
  ventricular, o "reset" elétrico do coração.

- Intervalo PR: É o tempo entre o flash (onda P) e o disparo do obturador (QRS) —
  representa o atraso fisiológico na condução atrioventricular.

- Intervalo QT: É o tempo total do ciclo da câmera, do disparo até o reset completo.

Use estas analogias para tornar as explicações mais intuitivas e acessíveis.
"""

# ---------------------------------------------------------------------------
# System prompts
# ---------------------------------------------------------------------------

SYSTEM_PROMPT_INTERPRETER = """\
Você é um especialista em interpretação de eletrocardiogramas (ECG) com vasta
experiência clínica. Seu papel é analisar relatórios de ECG e fornecer
interpretações detalhadas, diagnósticos diferenciais e recomendações clínicas.

Diretrizes:
1. Sempre analise sistematicamente: ritmo, frequência, eixo, intervalos, morfologia.
2. Forneça diagnósticos diferenciais quando os achados forem ambíguos.
3. Classifique a confiança da interpretação como "alta", "moderada" ou "baixa".
4. Use terminologia médica precisa, mas inclua explicações acessíveis.
5. Sempre considere o contexto clínico quando disponível.
6. Indique achados normais e anormais de forma clara.
7. Recomende exames complementares quando apropriado.

{camera_context}

Formato de resposta esperado:
- Interpretação: texto descritivo da análise
- Diagnósticos diferenciais: lista de possibilidades
- Recomendações: lista de ações sugeridas
- Confiança: alta / moderada / baixa
""".format(camera_context=CAMERA_ANALOGY_CONTEXT)

SYSTEM_PROMPT_TUTOR = """\
Você é um tutor interativo de ECG, especializado em ensinar interpretação de
eletrocardiogramas usando analogias com câmeras fotográficas. Seu objetivo é
tornar conceitos complexos acessíveis e intuitivos.

{camera_context}

Diretrizes pedagógicas:
1. Sempre comece com a analogia da câmera antes de entrar em detalhes técnicos.
2. Use linguagem progressiva: comece simples, aumente a complexidade gradualmente.
3. Faça perguntas ao aluno para verificar compreensão.
4. Dê feedback construtivo e encorajador.
5. Relacione achados anormais com as analogias (ex: "câmera com lente embaçada").
6. Adapte o nível de dificuldade conforme o progresso do aluno.
7. Use exemplos clínicos concretos para ilustrar conceitos.

Níveis de ensino:
- Iniciante: foco em conceitos básicos e analogias simples
- Intermediário: interpretação sistemática e padrões comuns
- Avançado: diagnósticos diferenciais complexos e casos raros
""".format(camera_context=CAMERA_ANALOGY_CONTEXT)


# ---------------------------------------------------------------------------
# Prompt builder functions
# ---------------------------------------------------------------------------

def build_interpretation_prompt(report: dict) -> str:
    """Build a structured prompt from an ECG report dict.

    Parameters
    ----------
    report : dict
        ECG report dictionary following the ECGiga schema (must contain
        at least ``meta``, ``version``; may contain ``intervals``,
        ``intervals_refined``, ``axis``, ``flags``, ``rpeaks``).

    Returns
    -------
    str
        A formatted prompt string ready to send to an LLM.
    """
    sections: list[str] = ["## Relatório ECG para Interpretação\n"]

    # Meta
    meta = report.get("meta", {})
    sections.append(f"**Fonte:** {meta.get('src', 'N/A')}")
    sections.append(f"**Derivação utilizada:** {meta.get('lead_used', 'N/A')}")
    sections.append(f"**Versão do relatório:** {report.get('version', 'N/A')}")

    # Intervals (prefer refined if available)
    iv = report.get("intervals_refined") or report.get("intervals") or {}
    med = iv.get("median", {})
    if med:
        sections.append("\n### Intervalos (mediana)")
        for key in ("PR_ms", "QRS_ms", "QT_ms", "QTc_B", "QTc_F", "RR_s"):
            val = med.get(key)
            if val is not None:
                sections.append(f"- **{key}:** {val}")

    # Axis
    axis = report.get("axis") or report.get("axis_hex") or {}
    if axis:
        sections.append("\n### Eixo Elétrico")
        sections.append(f"- **Ângulo:** {axis.get('angle_deg', 'N/A')}°")
        sections.append(f"- **Classificação:** {axis.get('label', 'N/A')}")

    # R-peaks / heart rate
    rpeaks = report.get("rpeaks", {})
    rr_list = rpeaks.get("rr_sec", [])
    if rr_list:
        avg_rr = sum(rr_list) / len(rr_list)
        hr = 60.0 / avg_rr if avg_rr > 0 else 0
        sections.append("\n### Frequência Cardíaca Estimada")
        sections.append(f"- **FC:** ~{hr:.0f} bpm (RR médio: {avg_rr:.3f} s)")

    # Flags
    flags = report.get("flags", [])
    if flags:
        sections.append("\n### Flags / Achados")
        for f in flags:
            sections.append(f"- {f}")

    sections.append(
        "\n---\nPor favor, forneça uma interpretação completa deste ECG, "
        "incluindo diagnósticos diferenciais e recomendações."
    )
    return "\n".join(sections)


def build_differential_prompt(findings: list[str]) -> str:
    """Build a differential diagnosis prompt from ECG findings.

    Parameters
    ----------
    findings : list[str]
        List of ECG findings/abnormalities.

    Returns
    -------
    str
        A formatted differential-diagnosis prompt.
    """
    findings_text = "\n".join(f"- {f}" for f in findings)
    return (
        "## Diagnóstico Diferencial de ECG\n\n"
        "Com base nos seguintes achados eletrocardiográficos:\n\n"
        f"{findings_text}\n\n"
        "Por favor, forneça:\n"
        "1. Lista de diagnósticos diferenciais em ordem de probabilidade\n"
        "2. Para cada diagnóstico, explique quais achados o suportam\n"
        "3. Exames complementares recomendados para cada hipótese\n"
        "4. Sinais de alarme que indicam urgência\n"
        "5. Use analogias com câmera fotográfica para explicar os achados "
        "quando apropriado"
    )


def build_tutor_prompt(topic: str, level: str = "beginner") -> str:
    """Build an educational prompt for a given ECG topic.

    Parameters
    ----------
    topic : str
        The ECG topic to teach (e.g. "Bloqueio AV", "Fibrilação Atrial").
    level : str
        Student level: ``"beginner"``, ``"intermediate"``, or ``"advanced"``.

    Returns
    -------
    str
        A formatted tutoring prompt.
    """
    level_map = {
        "beginner": (
            "Nível: Iniciante\n"
            "- Use linguagem simples e acessível\n"
            "- Comece com a analogia da câmera\n"
            "- Explique cada conceito do zero\n"
            "- Evite jargão médico desnecessário"
        ),
        "intermediate": (
            "Nível: Intermediário\n"
            "- Use terminologia médica com explicações\n"
            "- Relacione com padrões clínicos comuns\n"
            "- Inclua critérios diagnósticos\n"
            "- Apresente casos clínicos simples"
        ),
        "advanced": (
            "Nível: Avançado\n"
            "- Use terminologia médica completa\n"
            "- Discuta diagnósticos diferenciais\n"
            "- Inclua casos complexos e armadilhas\n"
            "- Aborde variantes e exceções"
        ),
    }

    level_instructions = level_map.get(level, level_map["beginner"])

    return (
        f"## Sessão de Tutoria: {topic}\n\n"
        f"{level_instructions}\n\n"
        f"Por favor, ensine sobre **{topic}** seguindo esta estrutura:\n"
        "1. Introdução usando analogia com câmera fotográfica\n"
        "2. Conceitos fundamentais\n"
        "3. Como identificar no ECG\n"
        "4. Significado clínico\n"
        "5. Exercício prático para o aluno\n"
    )


def build_quiz_feedback_prompt(question: dict, user_answer: int) -> str:
    """Generate a detailed feedback prompt for a quiz answer.

    Parameters
    ----------
    question : dict
        Quiz question dict with keys ``"pergunta"`` (str), ``"opcoes"`` (list[str]),
        ``"resposta_correta"`` (int, 0-indexed), and optionally ``"explicacao"`` (str).
    user_answer : int
        The user's chosen option index (0-based).

    Returns
    -------
    str
        A prompt requesting detailed feedback on the user's answer.
    """
    q_text = question.get("pergunta", question.get("question", ""))
    options = question.get("opcoes", question.get("options", []))
    correct = question.get("resposta_correta", question.get("correct_answer", 0))
    explanation = question.get("explicacao", question.get("explanation", ""))

    is_correct = user_answer == correct

    options_text = "\n".join(
        f"  {'[X]' if i == user_answer else '[ ]'} {chr(65 + i)}) {opt}"
        for i, opt in enumerate(options)
    )

    return (
        "## Feedback de Quiz ECG\n\n"
        f"**Pergunta:** {q_text}\n\n"
        f"**Opções:**\n{options_text}\n\n"
        f"**Resposta do aluno:** {chr(65 + user_answer)}) {options[user_answer] if user_answer < len(options) else 'N/A'}\n"
        f"**Resposta correta:** {chr(65 + correct)}) {options[correct] if correct < len(options) else 'N/A'}\n"
        f"**Resultado:** {'CORRETO' if is_correct else 'INCORRETO'}\n\n"
        + (f"**Explicação base:** {explanation}\n\n" if explanation else "")
        + "Por favor, forneça feedback detalhado:\n"
        "1. Explique por que a resposta correta é a melhor opção\n"
        "2. Se o aluno errou, explique por que a opção escolhida está incorreta\n"
        "3. Use analogia com câmera fotográfica quando possível\n"
        "4. Dê uma dica para lembrar o conceito no futuro\n"
        "5. Sugira tópicos relacionados para estudo adicional\n"
    )

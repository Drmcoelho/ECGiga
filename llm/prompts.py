"""Prompt templates for ECG clinical case generation."""

CASE_GENERATION_SYSTEM = """Voc\u00ea \u00e9 um professor de cardiologia gerando casos cl\u00ednicos educacionais de ECG.
Regras:
- Conte\u00fado exclusivamente educacional
- Incluir disclaimer de que n\u00e3o substitui avalia\u00e7\u00e3o cl\u00ednica
- Usar terminologia m\u00e9dica correta em portugu\u00eas
- Explica\u00e7\u00f5es progressivas do simples ao complexo
- Incluir diagn\u00f3sticos diferenciais quando relevante"""

CASE_TEMPLATES = {
    "normal": {
        "topic": "ECG Normal",
        "context_template": "Paciente de {age} anos, {sex}, {presentation}.",
        "expected_findings": ["Ritmo sinusal", "FC normal", "Eixo normal", "Intervalos normais"],
    },
    "bav1": {
        "topic": "BAV de 1\u00ba Grau",
        "context_template": "Paciente de {age} anos, {sex}, {presentation}.",
        "expected_findings": ["PR > 200ms", "Ritmo sinusal regular", "Cada P seguida de QRS"],
    },
    "bre": {
        "topic": "Bloqueio de Ramo Esquerdo",
        "context_template": "Paciente de {age} anos, {sex}, {presentation}.",
        "expected_findings": ["QRS \u2265 120ms", "Padr\u00e3o rSR' em V5-V6", "Aus\u00eancia de q em I, aVL, V5-V6"],
    },
    "brd": {
        "topic": "Bloqueio de Ramo Direito",
        "context_template": "Paciente de {age} anos, {sex}, {presentation}.",
        "expected_findings": ["QRS \u2265 120ms", "rSR' em V1-V2", "S largo em I, V5-V6"],
    },
    "stemi_anterior": {
        "topic": "STEMI Anterior",
        "context_template": "Paciente de {age} anos, {sex}, {presentation}.",
        "expected_findings": ["Supradesn\u00edvel ST em V1-V4", "Imagem especular inferior", "Poss\u00edvel onda Q"],
    },
    "fa": {
        "topic": "Fibrila\u00e7\u00e3o Atrial",
        "context_template": "Paciente de {age} anos, {sex}, {presentation}.",
        "expected_findings": ["Aus\u00eancia de onda P", "Irregularmente irregular", "Linha de base fibrilat\u00f3ria"],
    },
    "hipercalemia": {
        "topic": "Hipercalemia",
        "context_template": "Paciente de {age} anos, {sex}, {presentation}.",
        "expected_findings": ["Ondas T apiculadas", "Poss\u00edvel alargamento QRS", "Poss\u00edvel achatamento P"],
    },
}

EXPLANATION_LEVELS = {
    "student": "Explique como para um estudante de medicina do 3\u00ba ano.",
    "resident": "Explique como para um residente de cl\u00ednica m\u00e9dica.",
    "specialist": "Explique como para um cardiologista, incluindo fisiopatologia detalhada.",
}


def build_case_prompt(template_key: str, **kwargs) -> str:
    """Build a case generation prompt from a template."""
    template = CASE_TEMPLATES.get(template_key)
    if not template:
        available = ", ".join(CASE_TEMPLATES.keys())
        raise ValueError(f"Template '{template_key}' n\u00e3o encontrado. Dispon\u00edveis: {available}")

    defaults = {"age": 55, "sex": "masculino", "presentation": "check-up de rotina"}
    params = {**defaults, **kwargs}

    context = template["context_template"].format(**params)
    findings = "\n".join(f"- {f}" for f in template["expected_findings"])

    return f"""{CASE_GENERATION_SYSTEM}

Gere um caso cl\u00ednico progressivo:
Tema: {template['topic']}
Contexto: {context}

Achados esperados:
{findings}

Formato JSON com: id, title, difficulty, context, phases[], final_interpretation, learning_points[]"""

"""
quiz/electrolyte_questions.py — Banco de questões sobre eletrólitos e ECG

Questões de múltipla escolha em português, divididas em:
- Questões sem imagem (texto puro — clínica + ECG descritivo)
- Questões com imagem (referência a patologia sintética para gerar ECG)

Cada questão segue o formato:
{
    "id": str,
    "topic": str,
    "difficulty": "easy" | "medium" | "hard" | "expert",
    "stem": str (enunciado),
    "options": list[str],
    "answer_index": int,
    "explanation": str,
    "image_pathology": str | None  (se não-None, gerar ECG sintético)
}
"""

from __future__ import annotations

# =====================================================================
# QUESTÕES SEM IMAGEM — Texto descritivo + clínica
# =====================================================================

QUESTIONS_TEXT_ONLY: list[dict] = [
    # --- HIPERCALEMIA ---
    {
        "id": "elec_hk_001",
        "topic": "Hipercalemia",
        "difficulty": "easy",
        "stem": (
            "Paciente com insuficiência renal crônica apresenta ECG com "
            "ondas T apiculadas, altas, simétricas e de base estreita em "
            "V2-V4. Qual é o distúrbio eletrolítico mais provável?"
        ),
        "options": [
            "Hipercalemia",
            "Hipocalemia",
            "Hipercalcemia",
            "Hipomagnesemia",
        ],
        "answer_index": 0,
        "explanation": (
            "T apiculadas (tent-shaped), simétricas e de base estreita são "
            "a marca registrada da hipercalemia leve (K+ 5.5-6.5 mEq/L). "
            "A câmera vê a repolarização acelerada como uma onda T mais "
            "alta e mais estreita — o ator (repolarização) que normalmente "
            "caminha, agora corre na direção da câmera."
        ),
    },
    {
        "id": "elec_hk_002",
        "topic": "Hipercalemia",
        "difficulty": "medium",
        "stem": (
            "Paciente dialítico apresenta ECG sem onda P visível, QRS de "
            "180 ms e padrão sinusoidal. O K+ sérico provavelmente está:"
        ),
        "options": [
            "> 7.5 mEq/L",
            "5.5-6.0 mEq/L",
            "3.0-3.5 mEq/L",
            "< 2.5 mEq/L",
        ],
        "answer_index": 0,
        "explanation": (
            "O padrão sine wave (QRS muito alargado fundindo com T, sem P) "
            "corresponde a hipercalemia grave (K+ > 7.5 mEq/L). Neste "
            "estágio, a câmera não distingue mais QRS de T — tudo se fundiu "
            "em uma onda senoidal. EMERGÊNCIA: gluconato de cálcio IV "
            "imediatamente!"
        ),
    },
    {
        "id": "elec_hk_003",
        "topic": "Hipercalemia",
        "difficulty": "hard",
        "stem": (
            "Qual é a sequência CORRETA da progressão eletrocardiográfica "
            "da hipercalemia?"
        ),
        "options": [
            "T apiculada → PR prolonga / P achata → QRS alarga → sine wave",
            "QRS alarga → T apiculada → PR prolonga → sine wave",
            "P some → QRS alarga → T apiculada → sine wave",
            "ST supra → T inverte → QRS alarga → sine wave",
        ],
        "answer_index": 0,
        "explanation": (
            "A hipercalemia segue uma progressão previsível: primeiro T "
            "apiculadas (fase 3 acelerada), depois prolongamento de PR e "
            "achatamento de P (condução atrial comprometida), então QRS "
            "alarga (condução ventricular lenta), e finalmente sine wave "
            "(tudo se funde). Cada estágio é como um capítulo de degradação "
            "do roteiro elétrico filmado pelas câmeras."
        ),
    },
    {
        "id": "elec_hk_004",
        "topic": "Hipercalemia",
        "difficulty": "medium",
        "stem": (
            "O primeiro tratamento a ser administrado em paciente com ECG "
            "mostrando hipercalemia grave (QRS > 160 ms) é:"
        ),
        "options": [
            "Gluconato de cálcio IV",
            "Insulina + glicose IV",
            "Resina de troca iônica (Kayexalate)",
            "Furosemida IV",
        ],
        "answer_index": 0,
        "explanation": (
            "Gluconato de cálcio IV é a PRIMEIRA medida — estabiliza a "
            "membrana cardíaca em 1-3 minutos, agindo como 'escudo'. NÃO "
            "reduz o K+, apenas protege o coração enquanto outras medidas "
            "(insulina+glicose, resinas, diálise) fazem efeito."
        ),
    },
    {
        "id": "elec_hk_005",
        "topic": "Hipercalemia",
        "difficulty": "easy",
        "stem": (
            "Um paciente com K+ de 6.2 mEq/L apresenta ECG com ondas T "
            "apiculadas. O PR e o QRS estão normais. Qual é o estágio da "
            "hipercalemia?"
        ),
        "options": [
            "Leve (K+ 5.5-6.5)",
            "Moderado (K+ 6.5-7.5)",
            "Grave (K+ 7.5-8.5)",
            "Crítico (K+ > 8.5)",
        ],
        "answer_index": 0,
        "explanation": (
            "T apiculadas com PR e QRS normais = estágio leve. No estágio "
            "moderado já haveria PR prolongado e início de alargamento de QRS."
        ),
    },

    # --- HIPOCALEMIA ---
    {
        "id": "elec_lk_001",
        "topic": "Hipocalemia",
        "difficulty": "easy",
        "stem": (
            "Paciente em uso de diuréticos apresenta ECG com onda T "
            "achatada, infradesnivelamento de ST e onda U proeminente em "
            "V2-V3. O distúrbio eletrolítico mais provável é:"
        ),
        "options": [
            "Hipocalemia",
            "Hipercalemia",
            "Hipocalcemia",
            "Hipercalcemia",
        ],
        "answer_index": 0,
        "explanation": (
            "A tríade T achatada + infra de ST + onda U proeminente é "
            "clássica de hipocalemia. A onda U é um 'ator extra' que "
            "normalmente fica nos bastidores mas que, com K+ baixo, sobe "
            "ao palco — mais visível nas câmeras V2-V3."
        ),
    },
    {
        "id": "elec_lk_002",
        "topic": "Hipocalemia",
        "difficulty": "medium",
        "stem": (
            "Na hipocalemia, o QT aparentemente prolongado no ECG se deve a:"
        ),
        "options": [
            "Fusão da onda T com a onda U proeminente",
            "Prolongamento do segmento ST por falta de cálcio",
            "Alargamento do QRS por condução lenta",
            "Aumento do intervalo PR",
        ],
        "answer_index": 0,
        "explanation": (
            "Na hipocalemia moderada a grave, a onda U cresce tanto que se "
            "funde com a T. A câmera registra uma 'onda dupla' (T+U) que "
            "parece QT longo, mas é na verdade fusão T-U. Medir o QT nesse "
            "contexto é traiçoeiro — o 'fim da T' pode ser o 'fim da U'."
        ),
    },
    {
        "id": "elec_lk_003",
        "topic": "Hipocalemia",
        "difficulty": "hard",
        "stem": (
            "Paciente com K+ de 2.8 mEq/L não responde à reposição de KCl "
            "oral e IV após 48 horas. O próximo passo mais importante é:"
        ),
        "options": [
            "Dosar e repor magnésio (Mg²+)",
            "Aumentar a dose de KCl IV",
            "Dosar cálcio iônico",
            "Suspender todos os medicamentos",
        ],
        "answer_index": 0,
        "explanation": (
            "Hipocalemia refratária quase sempre indica hipomagnesemia "
            "concomitante. O Mg²+ é essencial para a bomba Na+/K+-ATPase "
            "funcionar. Sem corrigir o Mg²+, o K+ não normaliza. Mantra "
            "clínico: 'Hipocalemia refratária? Dosa o magnésio!'"
        ),
    },
    {
        "id": "elec_lk_004",
        "topic": "Hipocalemia",
        "difficulty": "easy",
        "stem": (
            "Qual é a derivação onde a onda U da hipocalemia é mais visível?"
        ),
        "options": [
            "V2-V3 (precordiais anteriores)",
            "DII e aVF (inferiores)",
            "aVR",
            "DI e aVL (laterais altas)",
        ],
        "answer_index": 0,
        "explanation": (
            "A onda U é melhor vista em V2-V3 porque as câmeras anteriores "
            "estão mais perto do septo e das fibras de Purkinje, que são "
            "provavelmente a origem da onda U."
        ),
    },

    # --- CÁLCIO ---
    {
        "id": "elec_hca_001",
        "topic": "Hipercalcemia",
        "difficulty": "easy",
        "stem": (
            "Paciente com malignidade apresenta QTc de 310 ms. A alteração "
            "eletrolítica mais provável é:"
        ),
        "options": [
            "Hipercalcemia",
            "Hipocalcemia",
            "Hipercalemia",
            "Hipomagnesemia",
        ],
        "answer_index": 0,
        "explanation": (
            "QTc curto (< 360 ms) em contexto de malignidade é altamente "
            "sugestivo de hipercalcemia. O Ca²+ alto encurta o plateau "
            "(fase 2), e a câmera vê o QRS e a T quase grudados, sem a "
            "pausa habitual do ST."
        ),
    },
    {
        "id": "elec_lca_001",
        "topic": "Hipocalcemia",
        "difficulty": "medium",
        "stem": (
            "Como diferenciar QT longo por hipocalcemia de QT longo por "
            "hipocalemia no ECG?"
        ),
        "options": [
            "Hipocalcemia: ST longo com T normal. Hipocalemia: T alterada (achatada/fusão T-U).",
            "Hipocalcemia: T apiculada. Hipocalemia: T normal.",
            "Não é possível diferenciar pelo ECG.",
            "Hipocalcemia: QRS largo. Hipocalemia: QRS normal.",
        ],
        "answer_index": 0,
        "explanation": (
            "Na hipocalcemia, o Ca²+ baixo prolonga o plateau (fase 2), "
            "esticando o segmento ST — mas a onda T mantém sua morfologia "
            "normal. Na hipocalemia, o K+ baixo altera a repolarização "
            "diretamente: T achata, U aparece, fusão T-U. A câmera vê: "
            "hipocalcemia = pausa longa com T normal; hipocalemia = T "
            "deformada com ator extra (U) em cena."
        ),
    },
    {
        "id": "elec_lca_002",
        "topic": "Hipocalcemia",
        "difficulty": "easy",
        "stem": (
            "O prolongamento do QT na hipocalcemia ocorre principalmente "
            "às custas de:"
        ),
        "options": [
            "Prolongamento do segmento ST",
            "Alargamento do QRS",
            "Prolongamento da onda T",
            "Prolongamento do intervalo PR",
        ],
        "answer_index": 0,
        "explanation": (
            "O Ca²+ controla a duração do plateau (fase 2), que no ECG "
            "corresponde ao segmento ST. Hipocalcemia = plateau longo = "
            "ST esticado. A onda T em si não muda muito. A câmera vê uma "
            "pausa dramática longa entre QRS e T."
        ),
    },

    # --- MAGNÉSIO ---
    {
        "id": "elec_mg_001",
        "topic": "Hipomagnesemia",
        "difficulty": "medium",
        "stem": (
            "O tratamento de primeira linha para Torsades de Pointes "
            "(independente do nível sérico de Mg²+) é:"
        ),
        "options": [
            "Sulfato de magnésio IV",
            "Amiodarona IV",
            "Cardioversão elétrica",
            "Lidocaína IV",
        ],
        "answer_index": 0,
        "explanation": (
            "Sulfato de Mg²+ IV (1-2 g em 15 min) é o tratamento de "
            "primeira linha para Torsades de Pointes, MESMO se o Mg²+ "
            "sérico estiver normal. O Mg²+ estabiliza os canais iônicos "
            "e quebra o mecanismo de reentrada. Se a TdP for instável "
            "com colapso, cardioversão é indicada."
        ),
    },
    {
        "id": "elec_mg_002",
        "topic": "Hipomagnesemia",
        "difficulty": "hard",
        "stem": (
            "Por que a hipomagnesemia é difícil de distinguir da "
            "hipocalemia pelo ECG?"
        ),
        "options": [
            "Ambas produzem QT longo, T achatada e podem ter onda U — o mecanismo é interligado",
            "Ambas produzem T apiculada e QT curto",
            "Ambas produzem supra de ST",
            "O ECG é completamente normal na hipomagnesemia",
        ],
        "answer_index": 0,
        "explanation": (
            "O Mg²+ estabiliza os canais de K+. Sem Mg²+, a repolarização "
            "fica heterogênea, produzindo alterações semelhantes à "
            "hipocalemia: QT longo, T achatada, onda U. A câmera registra "
            "um filme quase idêntico. A diferença é clínica: se K+ está "
            "normal mas o ECG parece de hipocalemia → dosar Mg²+."
        ),
    },

    # --- DIAGNÓSTICO DIFERENCIAL ---
    {
        "id": "elec_dd_001",
        "topic": "Diagnóstico diferencial eletrolítico",
        "difficulty": "medium",
        "stem": (
            "A frase 'K+ mexe nas ONDAS, Ca²+ mexe no INTERVALO' significa:"
        ),
        "options": [
            "K+ altera a morfologia de P, QRS e T; Ca²+ altera a duração do QT",
            "K+ altera o QT; Ca²+ altera as ondas",
            "K+ não tem efeito no ECG; Ca²+ altera tudo",
            "K+ altera apenas a onda P; Ca²+ altera apenas a onda T",
        ],
        "answer_index": 0,
        "explanation": (
            "O K+ controla fases 3-4 (repolarização e repouso), alterando "
            "a FORMA das ondas: T apiculada/achatada, P some, QRS alarga, "
            "U aparece. O Ca²+ controla a fase 2 (plateau), alterando a "
            "DURAÇÃO do ST e, consequentemente, do QT. "
            "K+ = forma. Ca²+ = tempo."
        ),
    },
    {
        "id": "elec_dd_002",
        "topic": "Diagnóstico diferencial eletrolítico",
        "difficulty": "hard",
        "stem": (
            "Paciente grave apresenta ECG com QRS de 200 ms, T apiculadas "
            "e ausência de onda P. Gasometria: pH 7.15, K+ 8.1 mEq/L. "
            "Qual é a sequência correta de tratamento?"
        ),
        "options": [
            "Gluconato de Ca²+ IV → Insulina + Glicose → Bicarbonato → Diálise",
            "Diálise imediata → Insulina → Gluconato de Ca²+",
            "Insulina + Glicose → Kayexalate → Diálise",
            "Bicarbonato IV → Furosemida → Kayexalate",
        ],
        "answer_index": 0,
        "explanation": (
            "Com K+ 8.1 + QRS 200 ms + acidose: 1) Gluconato de Ca²+ IV "
            "PRIMEIRO (estabiliza membrana em 1-3 min); 2) Insulina + "
            "glicose (shift de K+ intracelular em 15-30 min); 3) Bicarbonato "
            "(corrige acidose + ajuda no shift); 4) Diálise (remoção "
            "definitiva). Tempo é vida."
        ),
    },
    {
        "id": "elec_dd_003",
        "topic": "Diagnóstico diferencial eletrolítico",
        "difficulty": "expert",
        "stem": (
            "Paciente apresenta QT prolongado no ECG. Qual achado "
            "morfológico mais sugere hipocalcemia como causa (em vez de "
            "hipocalemia ou drogas)?"
        ),
        "options": [
            "Segmento ST prolongado com onda T de morfologia preservada",
            "Onda T invertida e profunda",
            "Onda U proeminente fundindo com T",
            "T bífida e entalhada",
        ],
        "answer_index": 0,
        "explanation": (
            "A hipocalcemia prolonga especificamente o plateau (fase 2) = "
            "ST longo. A T mantém sua morfologia normal. Já a hipocalemia "
            "altera a T (achata, gera U), e drogas podem causar T bizarra "
            "(bífida, entalhada). A câmera diferencia: pausa longa + T "
            "normal = Ca²+; T estranha = K+/drogas."
        ),
    },
]

# =====================================================================
# QUESTÕES COM IMAGEM (referência a pathology para gerar ECG sintético)
# =====================================================================

QUESTIONS_WITH_IMAGE: list[dict] = [
    {
        "id": "elec_img_001",
        "topic": "Hipercalemia",
        "difficulty": "easy",
        "stem": (
            "Observe o ECG abaixo. Qual é o achado principal e qual "
            "distúrbio eletrolítico ele sugere?"
        ),
        "options": [
            "T apiculadas — Hipercalemia leve",
            "T achatadas — Hipocalemia",
            "QT curto — Hipercalcemia",
            "Onda U — Hipocalemia",
        ],
        "answer_index": 0,
        "explanation": (
            "O ECG mostra ondas T apiculadas, simétricas e de base estreita "
            "(tent-shaped). Esse é o primeiro sinal da hipercalemia — a "
            "repolarização acelerada (fase 3) faz a câmera registrar T mais "
            "alta e pontuda. Dosar K+ é urgente."
        ),
        "image_pathology": "hyperkalemia",
    },
    {
        "id": "elec_img_002",
        "topic": "Hipercalemia grave",
        "difficulty": "medium",
        "stem": (
            "Observe o ECG abaixo de um paciente com insuficiência renal. "
            "Qual é o padrão e a conduta imediata?"
        ),
        "options": [
            "Sine wave — Gluconato de cálcio IV imediato",
            "Fibrilação atrial — Anticoagulação",
            "STEMI anterior — Cateterismo de emergência",
            "BRE — Avaliar critérios de Sgarbossa",
        ],
        "answer_index": 0,
        "explanation": (
            "O padrão sine wave (QRS muito largo fundindo com T, sem P) é "
            "hipercalemia grave/crítica. A câmera não distingue mais as "
            "ondas individuais — tudo se fundiu. EMERGÊNCIA: gluconato de "
            "Ca²+ IV imediato para estabilizar a membrana, seguido de "
            "insulina+glicose e diálise."
        ),
        "image_pathology": "hyperkalemia_severe",
    },
    {
        "id": "elec_img_003",
        "topic": "Hipocalemia",
        "difficulty": "easy",
        "stem": (
            "Observe o ECG de um paciente em uso de furosemida. Qual é "
            "o achado mais específico de hipocalemia neste traçado?"
        ),
        "options": [
            "Onda U proeminente após a onda T",
            "Onda T apiculada e simétrica",
            "Supra de ST em V1-V4",
            "QRS alargado > 120 ms",
        ],
        "answer_index": 0,
        "explanation": (
            "A onda U proeminente (deflexão positiva APÓS a T) é a marca "
            "registrada da hipocalemia. Além disso, note T achatada e "
            "infra de ST sutil. A onda U é um 'ator extra' que sobe ao "
            "palco quando o K+ cai — mais visível em V2-V3."
        ),
        "image_pathology": "hypokalemia",
    },
    {
        "id": "elec_img_004",
        "topic": "Hipercalcemia",
        "difficulty": "medium",
        "stem": (
            "Observe o ECG abaixo. O achado principal é QT curto. Qual é "
            "a causa eletrolítica mais provável?"
        ),
        "options": [
            "Hipercalcemia — Ca²+ alto encurta o plateau",
            "Hipocalemia — K+ baixo encurta a repolarização",
            "Hipermagnesemia — Mg²+ alto reduz o QT",
            "Hipocalcemia — Ca²+ baixo acelera a condução",
        ],
        "answer_index": 0,
        "explanation": (
            "QT curto (QTc < 360 ms) com ST quase ausente — a onda T "
            "parece 'grudada' no QRS. O Ca²+ alto encurta o plateau "
            "(fase 2), fazendo o ST praticamente desaparecer. A câmera vê "
            "QRS → T sem pausa."
        ),
        "image_pathology": "hypercalcemia",
    },
    {
        "id": "elec_img_005",
        "topic": "Hipocalcemia",
        "difficulty": "medium",
        "stem": (
            "Observe o ECG abaixo. O QT está prolongado. O segmento ST "
            "está visivelmente alongado mas a onda T mantém morfologia "
            "normal. Qual é a causa mais provável?"
        ),
        "options": [
            "Hipocalcemia — Ca²+ baixo prolonga o plateau/ST",
            "Hipocalemia — K+ baixo prolonga a repolarização",
            "Síndrome do QT longo congênito",
            "Efeito de amiodarona",
        ],
        "answer_index": 0,
        "explanation": (
            "A pista-chave é ST prolongado com T NORMAL. A hipocalcemia "
            "prolonga especificamente o plateau (fase 2 = ST), sem alterar "
            "a forma da T. Na hipocalemia, a T seria achatada ou haveria "
            "onda U. Em drogas/congênito, a T seria alterada (bífida, "
            "entalhada). A câmera registra uma pausa dramática longa entre "
            "QRS e T, mas quando T aparece, está perfeita."
        ),
        "image_pathology": "hypocalcemia",
    },
    {
        "id": "elec_img_006",
        "topic": "Diagnóstico diferencial eletrolítico",
        "difficulty": "hard",
        "stem": (
            "Observe este ECG com T apiculadas. Como diferenciar "
            "hipercalemia de repolarização precoce benigna em jovem?"
        ),
        "options": [
            "Hipercalemia: T simétrica, base estreita. Benigna: T assimétrica, base larga.",
            "Não é possível diferenciar pelo ECG.",
            "Hipercalemia: T com entalhe. Benigna: T lisa.",
            "Hipercalemia: T apenas em V1. Benigna: T em todas derivações.",
        ],
        "answer_index": 0,
        "explanation": (
            "A T da hipercalemia é SIMÉTRICA (subida = descida) e de BASE "
            "ESTREITA — como uma barraca de camping. A T benigna de jovem "
            "vagotônico é ASSIMÉTRICA (subida lenta, descida rápida) e de "
            "base mais larga. Clinicamente, se o paciente tem fator de risco "
            "(IRC, diuréticos poupadores de K+), dosar K+ é obrigatório."
        ),
        "image_pathology": "hyperkalemia",
    },
]

# =====================================================================
# Funções auxiliares
# =====================================================================

ALL_QUESTIONS: list[dict] = QUESTIONS_TEXT_ONLY + QUESTIONS_WITH_IMAGE


def get_questions_by_topic(topic: str) -> list[dict]:
    """Retorna questões filtradas por tópico."""
    return [q for q in ALL_QUESTIONS if q["topic"].lower() == topic.lower()]


def get_questions_by_difficulty(difficulty: str) -> list[dict]:
    """Retorna questões filtradas por dificuldade."""
    return [q for q in ALL_QUESTIONS if q["difficulty"] == difficulty]


def get_image_questions() -> list[dict]:
    """Retorna apenas questões que possuem ECG sintético associado."""
    return [q for q in ALL_QUESTIONS if q.get("image_pathology")]


def get_text_questions() -> list[dict]:
    """Retorna apenas questões sem imagem."""
    return [q for q in ALL_QUESTIONS if not q.get("image_pathology")]

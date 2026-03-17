"""
quiz/electrophysiology_questions.py — Questões de eletrofisiologia cardíaca

Questões sobre:
- Potencial de ação (fases 0-4)
- Correntes iônicas de cada fase
- Automatismo do nó sinusal
- Períodos refratários absoluto e relativo
- Correlação com ECG
- Questões com e sem figura (image_figure indica tipo de figura a gerar)
"""

from __future__ import annotations

# =====================================================================
# QUESTÕES SEM IMAGEM
# =====================================================================

QUESTIONS_TEXT_ONLY: list[dict] = [
    # --- FASE 0 ---
    {
        "id": "ephys_f0_001",
        "topic": "Fase 0 — Despolarização",
        "difficulty": "easy",
        "stem": (
            "A fase 0 do potencial de ação do cardiomiócito ventricular "
            "depende principalmente de qual corrente iônica?"
        ),
        "options": [
            "INa — corrente rápida de sódio (Nav1.5)",
            "ICa,L — corrente de cálcio tipo L",
            "IK1 — corrente retificadora inward de potássio",
            "If — funny current (HCN4)",
        ],
        "answer_index": 0,
        "explanation": (
            "A fase 0 do cardiomiócito é mediada pela INa (canais Nav1.5). "
            "A abertura massiva e rápida desses canais produz o upstroke "
            "ultra-rápido (~200-400 V/s) que no ECG gera o complexo QRS. "
            "A ICa,L é responsável pela fase 0 do NÓ SINUSAL (upstroke lento)."
        ),
    },
    {
        "id": "ephys_f0_002",
        "topic": "Fase 0 — Despolarização",
        "difficulty": "medium",
        "stem": (
            "O QRS alargado na hipercalemia se deve a qual mecanismo "
            "eletrofisiológico?"
        ),
        "options": [
            "Inativação parcial dos canais de Na+ pelo potencial de repouso menos negativo",
            "Bloqueio direto dos canais de Ca²+ tipo L",
            "Abertura excessiva dos canais IK1",
            "Hiperpolarização das fibras de Purkinje",
        ],
        "answer_index": 0,
        "explanation": (
            "Na hipercalemia, o K+ alto torna o potencial de repouso menos "
            "negativo (~-75 mV em vez de -90 mV). Nesta voltagem, muitos canais "
            "de Na+ já estão no estado INATIVADO (porta h fechada). Resultado: "
            "menos canais disponíveis para a fase 0 → upstroke mais lento → "
            "QRS alargado. É como ter menos atores disponíveis para entrar em cena."
        ),
    },
    {
        "id": "ephys_f0_003",
        "topic": "Fase 0 — Despolarização",
        "difficulty": "hard",
        "stem": (
            "A velocidade do upstroke (dV/dt) da fase 0 das fibras de Purkinje "
            "é aproximadamente:"
        ),
        "options": [
            "200-400 V/s (a mais rápida do coração)",
            "1-10 V/s (muito lenta, dependente de Ca²+)",
            "50-100 V/s (intermediária)",
            "0 V/s (as fibras de Purkinje não têm upstroke)",
        ],
        "answer_index": 0,
        "explanation": (
            "As fibras de Purkinje têm o upstroke MAIS RÁPIDO do coração "
            "(~200-400 V/s) graças à alta densidade de canais Nav1.5. Isso "
            "garante condução ultra-rápida (2-4 m/s) pelo sistema His-Purkinje, "
            "essencial para ativação ventricular coordenada. Em contraste, o "
            "nó sinusal tem upstroke lento (~1-10 V/s) dependente de ICa,L."
        ),
    },

    # --- FASE 1 ---
    {
        "id": "ephys_f1_001",
        "topic": "Fase 1 — Repolarização precoce",
        "difficulty": "medium",
        "stem": (
            "A corrente Ito (transient outward) é mais proeminente em qual "
            "camada do ventrículo, e qual a consequência clínica?"
        ),
        "options": [
            "Epicárdio — responsável pelo padrão de Brugada quando exagerada",
            "Endocárdio — responsável pela onda U proeminente",
            "Septo — causa bloqueio de ramo quando alterada",
            "Igualmente distribuída — sem consequência clínica",
        ],
        "answer_index": 0,
        "explanation": (
            "A Ito é muito mais proeminente no EPICÁRDIO que no endocárdio. "
            "Isso cria o entalhe (notch) da fase 1, que no ECG aparece como "
            "o ponto J. Se a Ito é exagerada (genética, febre), o platô "
            "epicárdico pode colapsar → padrão de Brugada → risco de FV."
        ),
    },

    # --- FASE 2 ---
    {
        "id": "ephys_f2_001",
        "topic": "Fase 2 — Platô",
        "difficulty": "easy",
        "stem": (
            "O platô (fase 2) do potencial de ação é mantido pelo equilíbrio "
            "entre quais correntes?"
        ),
        "options": [
            "Entrada de Ca²+ (ICa,L) vs saída de K+ (IKr/IKs)",
            "Entrada de Na+ (INa) vs saída de Cl- (ICl)",
            "Saída de Ca²+ vs entrada de K+",
            "Apenas pela bomba Na+/K+-ATPase",
        ],
        "answer_index": 0,
        "explanation": (
            "O platô é um equilíbrio: a ICa,L (Ca²+ entrando) mantém a voltagem "
            "positiva, enquanto IKr e IKs (K+ saindo) tentam repolarizar. Quando "
            "a ICa,L inativa e as correntes de K+ predominam, o platô termina e "
            "a fase 3 começa. No ECG, o platô corresponde ao segmento ST."
        ),
    },
    {
        "id": "ephys_f2_002",
        "topic": "Fase 2 — Platô",
        "difficulty": "medium",
        "stem": (
            "Por que o coração não entra em tetania como o músculo "
            "esquelético, apesar de contrair-se ritmicamente?"
        ),
        "options": [
            "O platô longo (~200 ms) mantém a célula refratária durante toda a contração",
            "O coração não tem receptores de acetilcolina",
            "As células cardíacas não têm sarcômeros",
            "A contração cardíaca não depende de Ca²+",
        ],
        "answer_index": 0,
        "explanation": (
            "O platô (fase 2) dura ~200 ms — praticamente toda a duração da "
            "contração mecânica. Durante este tempo, a célula está em período "
            "refratário absoluto (canais de Na+ inativados) → impossível "
            "re-excitação → impossível tetania. É a proteção mais elegante "
            "da natureza contra contração sustentada do coração."
        ),
    },
    {
        "id": "ephys_f2_003",
        "topic": "Fase 2 — Platô",
        "difficulty": "hard",
        "stem": (
            "O gene CACNA1C codifica qual canal, e mutações neste gene "
            "causam qual síndrome?"
        ),
        "options": [
            "Canal Ca²+ tipo L (Cav1.2) — Síndrome de Timothy",
            "Canal Na+ (Nav1.5) — Síndrome de Brugada",
            "Canal K+ (hERG) — QT longo tipo 2",
            "Canal HCN4 — Doença do nó sinusal",
        ],
        "answer_index": 0,
        "explanation": (
            "CACNA1C codifica a subunidade α1C do canal de Ca²+ tipo L (Cav1.2), "
            "responsável pelo platô. Mutações gain-of-function causam a Síndrome "
            "de Timothy: QT muito longo, arritmias letais, sindactilia, autismo. "
            "O canal fica aberto demais → platô excessivo → QT prolongado."
        ),
    },

    # --- FASE 3 ---
    {
        "id": "ephys_f3_001",
        "topic": "Fase 3 — Repolarização",
        "difficulty": "easy",
        "stem": (
            "A onda T no ECG é normalmente positiva na maioria das derivações "
            "apesar de representar repolarização. Qual é a explicação?"
        ),
        "options": [
            "O epicárdio repolariza antes do endocárdio, e o vetor de repolarização é concordante com o de despolarização",
            "A onda T é gerada pela despolarização, não pela repolarização",
            "O endocárdio repolariza antes do epicárdio",
            "A onda T é um artefato do filtro do eletrocardiógrafo",
        ],
        "answer_index": 0,
        "explanation": (
            "Apesar de a despolarização ir de endocárdio → epicárdio, a "
            "REPOLARIZAÇÃO vai de epicárdio → endocárdio (porque o PA "
            "epicárdico é mais curto, graças à Ito). Repolarização é "
            "o oposto de despolarização, mas na direção oposta → os dois "
            "'opostos' se cancelam → vetor T concorda com QRS → T positiva."
        ),
    },
    {
        "id": "ephys_f3_002",
        "topic": "Fase 3 — Repolarização",
        "difficulty": "medium",
        "stem": (
            "O canal hERG (IKr) é o principal alvo de drogas que prolongam "
            "o QT. Qual classe de antiarrítmicos bloqueia diretamente este canal?"
        ),
        "options": [
            "Classe III (sotalol, dofetilida, amiodarona)",
            "Classe I (lidocaína, flecainida)",
            "Classe II (betabloqueadores)",
            "Classe IV (verapamil, diltiazem)",
        ],
        "answer_index": 0,
        "explanation": (
            "Os antiarrítmicos classe III bloqueiam canais de K+, "
            "principalmente o IKr (hERG/Kv11.1). Isso retarda a fase 3 → "
            "PA mais longo → QT prolonga → PRE aumenta. O efeito é "
            "antiarrítmico (dificulta reentrada) mas o risco é QT longo "
            "excessivo → Torsades de Pointes."
        ),
    },

    # --- FASE 4 ---
    {
        "id": "ephys_f4_001",
        "topic": "Fase 4 — Repouso",
        "difficulty": "easy",
        "stem": (
            "A fase 4 do cardiomiócito contrátil (ventricular) é:"
        ),
        "options": [
            "Estável em -90 mV, mantida pela IK1",
            "Instável, com despolarização diastólica lenta (If)",
            "Estável em -60 mV, mantida pela ICa,L",
            "Alternando entre -90 mV e -60 mV",
        ],
        "answer_index": 0,
        "explanation": (
            "No cardiomiócito contrátil, a fase 4 é ESTÁVEL em -90 mV. "
            "A IK1 (Kir2.1) é a guardiã: mantém o repouso permitindo saída "
            "de K+ suficiente. A célula NÃO se despolariza sozinha — precisa "
            "de estímulo externo. Apenas as células pacemaker (nó SA, AV) "
            "têm fase 4 instável com automatismo."
        ),
    },
    {
        "id": "ephys_f4_002",
        "topic": "Fase 4 — Repouso",
        "difficulty": "medium",
        "stem": (
            "A bomba Na+/K+-ATPase é eletrogênica porque:"
        ),
        "options": [
            "Bombeia 3 Na+ para fora e 2 K+ para dentro, gerando -1 carga/ciclo",
            "Bombeia 2 Na+ e 2 K+ em direções opostas, sem carga líquida",
            "Funciona apenas durante a fase 0",
            "É ativada pela despolarização",
        ],
        "answer_index": 0,
        "explanation": (
            "A bomba Na+/K+-ATPase troca 3 Na+ (para fora) por 2 K+ (para dentro), "
            "resultando em perda líquida de 1 carga positiva por ciclo → contribui "
            "~-5 a -10 mV ao potencial de repouso. Os digitálicos (digoxina) inibem "
            "parcialmente esta bomba → acúmulo de Na+ → troca Na+/Ca²+ reversa → "
            "mais Ca²+ → inotropismo positivo."
        ),
    },

    # --- NÓ SINUSAL ---
    {
        "id": "ephys_sa_001",
        "topic": "Nó Sinusal — Automatismo",
        "difficulty": "easy",
        "stem": (
            "A fase 0 (upstroke) do potencial de ação do nó sinusal é "
            "mediada por qual corrente?"
        ),
        "options": [
            "ICa,L — corrente de cálcio tipo L (upstroke lento)",
            "INa — corrente rápida de sódio (upstroke rápido)",
            "If — funny current",
            "IK1 — corrente retificadora inward",
        ],
        "answer_index": 0,
        "explanation": (
            "No nó sinusal, o potencial de repouso é ~-60 mV — voltagem na "
            "qual os canais de Na+ já estão inativados. A fase 0 depende da "
            "ICa,L (Ca²+ tipo L), que produz um upstroke LENTO (1-10 V/s) "
            "comparado ao INa do cardiomiócito (200-400 V/s). Por isso o nó "
            "sinusal conduz lentamente e não é visto diretamente no ECG."
        ),
    },
    {
        "id": "ephys_sa_002",
        "topic": "Nó Sinusal — Automatismo",
        "difficulty": "medium",
        "stem": (
            "A ivabradina reduz a frequência cardíaca bloqueando qual corrente?"
        ),
        "options": [
            "If (funny current / HCN4) — retarda a despolarização diastólica",
            "ICa,L — reduz a contratilidade e a condução AV",
            "INa — retarda a condução His-Purkinje",
            "IKr — prolonga o potencial de ação",
        ],
        "answer_index": 0,
        "explanation": (
            "A ivabradina bloqueia seletivamente a If (canais HCN4) no nó "
            "sinusal. A If inicia a despolarização diastólica da fase 4. "
            "Com menos If → fase 4 mais lenta → FC cai. Vantagem sobre "
            "betabloqueadores: reduz FC SEM afetar contratilidade ou PA."
        ),
    },
    {
        "id": "ephys_sa_003",
        "topic": "Nó Sinusal — Automatismo",
        "difficulty": "hard",
        "stem": (
            "Se o nó sinusal falha completamente, qual é a frequência "
            "de escape esperada de um ritmo juncional (nó AV)?"
        ),
        "options": [
            "40-60 bpm",
            "60-100 bpm",
            "20-40 bpm",
            "100-150 bpm",
        ],
        "answer_index": 0,
        "explanation": (
            "A hierarquia dos marcapassos: nó SA (60-100 bpm) > nó AV "
            "(40-60 bpm) > His-Purkinje (20-40 bpm). O nó AV assume "
            "como backup de 1º nível se o SA falha, gerando ritmo "
            "juncional a 40-60 bpm (QRS estreito, P retrógrada ou ausente)."
        ),
    },

    # --- PERÍODOS REFRATÁRIOS ---
    {
        "id": "ephys_pra_001",
        "topic": "Período Refratário Absoluto",
        "difficulty": "easy",
        "stem": (
            "O período refratário absoluto (PRA) do ventrículo corresponde "
            "a qual intervalo no ECG?"
        ),
        "options": [
            "Do início do QRS até aproximadamente o pico da onda T",
            "Apenas o segmento ST",
            "Apenas a onda T descendente",
            "O intervalo T-P (entre T e próxima P)",
        ],
        "answer_index": 0,
        "explanation": (
            "O PRA abrange fases 0, 1, 2 e início da fase 3 = do início do "
            "QRS até ~metade da T (ascendente). Durante este período, os canais "
            "de Na+ estão INATIVADOS (porta h fechada) → NENHUM estímulo gera "
            "novo PA, por mais forte que seja."
        ),
    },
    {
        "id": "ephys_prr_001",
        "topic": "Período Refratário Relativo",
        "difficulty": "medium",
        "stem": (
            "O fenômeno 'R sobre T' (R-on-T) pode desencadear fibrilação "
            "ventricular porque a extrassístole cai no:"
        ),
        "options": [
            "Período refratário relativo (parte descendente da onda T) — janela vulnerável",
            "Período refratário absoluto (segmento ST)",
            "Fase 4 (intervalo T-P)",
            "Onda P do próximo batimento",
        ],
        "answer_index": 0,
        "explanation": (
            "O período refratário relativo (PRR) corresponde à parte "
            "descendente da onda T (final da fase 3). Neste momento, PARTE dos "
            "canais de Na+ já recuperou. Um estímulo forte gera PA anormal: "
            "condução lenta, bloqueio unidirecional → substrato para reentrada → "
            "pode deflagrar TV/FV. É a 'janela vulnerável' do coração."
        ),
    },
    {
        "id": "ephys_prr_002",
        "topic": "Período Refratário",
        "difficulty": "hard",
        "stem": (
            "Qual é a diferença entre o período refratário absoluto (PRA) "
            "e o período refratário efetivo (PRE)?"
        ),
        "options": [
            "O PRE = PRA + parte do PRR onde o PA gerado é fraco demais para se propagar",
            "São sinônimos — não há diferença",
            "O PRA é maior que o PRE",
            "O PRE só existe no nó sinusal",
        ],
        "answer_index": 0,
        "explanation": (
            "O PRA é quando nenhum PA pode ser gerado. O PRE vai além: inclui "
            "o PRA + a parte do PRR na qual, mesmo que um PA seja gerado, ele é "
            "fraco demais para se propagar às células vizinhas. Clinicamente, o "
            "PRE é o que importa: drogas que aumentam o PRE (classe III) são "
            "antiarrítmicas porque dificultam a propagação de reentrada."
        ),
    },
    {
        "id": "ephys_prr_003",
        "topic": "Período Refratário",
        "difficulty": "expert",
        "stem": (
            "A dispersão de refratariedade é um substrato para arritmias "
            "por reentrada. Qual condição exemplifica melhor este conceito?"
        ),
        "options": [
            "Zona de borda de cicatriz pós-infarto com PREs heterogêneos",
            "Bradicardia sinusal isolada sem doença estrutural",
            "Bloqueio AV de 1º grau isolado",
            "Extrassístole atrial isolada em coração normal",
        ],
        "answer_index": 0,
        "explanation": (
            "A dispersão de refratariedade ocorre quando regiões vizinhas têm "
            "PREs muito diferentes. Na borda de uma cicatriz pós-infarto, o "
            "tecido normal tem PRE normal, mas o tecido fibrosado/isquêmico "
            "tem PRE alterado. Um impulso pode encontrar uma via bloqueada "
            "(ainda refratária) e outra desbloqueada → condução unidirecional → "
            "reentrada clássica."
        ),
    },

    # --- CORRELAÇÃO GERAL ---
    {
        "id": "ephys_corr_001",
        "topic": "Correlação PA-ECG",
        "difficulty": "easy",
        "stem": (
            "Qual fase do potencial de ação corresponde ao segmento ST "
            "no ECG?"
        ),
        "options": [
            "Fase 2 — Platô",
            "Fase 0 — Despolarização rápida",
            "Fase 3 — Repolarização",
            "Fase 4 — Repouso",
        ],
        "answer_index": 0,
        "explanation": (
            "O segmento ST corresponde à fase 2 (platô). Durante o platô, "
            "todas as células ventriculares estão no mesmo potencial (~0 mV) → "
            "sem diferença elétrica → ST isoelétrico. Quando há isquemia, "
            "parte do miocárdio tem platô diferente → diferença de potencial → "
            "supra ou infra de ST."
        ),
    },
    {
        "id": "ephys_corr_002",
        "topic": "Correlação PA-ECG",
        "difficulty": "medium",
        "stem": (
            "O intervalo QT no ECG corresponde, em termos de potencial "
            "de ação, a:"
        ),
        "options": [
            "Toda a duração do PA ventricular (fases 0 + 1 + 2 + 3)",
            "Apenas a fase 2 (platô)",
            "Apenas a fase 3 (repolarização)",
            "A fase 4 (repouso elétrico)",
        ],
        "answer_index": 0,
        "explanation": (
            "O intervalo QT vai do início do QRS (fase 0) ao final da T "
            "(final da fase 3). Portanto, QT = fases 0+1+2+3 = toda a "
            "duração do potencial de ação ventricular. Quando o QT prolonga, "
            "significa que o PA está mais longo (geralmente por fase 2 ou "
            "fase 3 prolongadas)."
        ),
    },
]

# =====================================================================
# QUESTÕES COM FIGURA (geram Plotly interativo)
# =====================================================================

QUESTIONS_WITH_FIGURE: list[dict] = [
    {
        "id": "ephys_fig_001",
        "topic": "Potencial de Ação",
        "difficulty": "easy",
        "stem": (
            "Observe o potencial de ação do cardiomiócito contrátil. "
            "Qual fase é responsável pelo platô e corresponde ao "
            "segmento ST no ECG?"
        ),
        "options": [
            "Fase 2 (região verde) — ICa,L vs IKr/IKs",
            "Fase 0 (região vermelha) — INa",
            "Fase 3 (região azul) — IKr + IKs",
            "Fase 4 (região roxa) — IK1",
        ],
        "answer_index": 0,
        "explanation": (
            "A fase 2 (destacada em verde) é o platô mantido pelo equilíbrio "
            "entre ICa,L (entrada de Ca²+) e IKr/IKs (saída de K+). No ECG "
            "abaixo, corresponde ao segmento ST isoelétrico. Note como o "
            "período refratário absoluto (barra vermelha) cobre toda esta fase."
        ),
        "image_figure": "contractile",
    },
    {
        "id": "ephys_fig_002",
        "topic": "Nó Sinusal",
        "difficulty": "medium",
        "stem": (
            "Observe o potencial de ação do nó sinusal. Qual é a "
            "característica que confere automatismo a esta célula?"
        ),
        "options": [
            "Fase 4 instável — despolarização diastólica espontânea (If + ICaT)",
            "Upstroke muito rápido dependente de INa",
            "Platô prolongado pela ICa,L",
            "Potencial de repouso muito negativo (-90 mV)",
        ],
        "answer_index": 0,
        "explanation": (
            "O nó sinusal tem fase 4 INSTÁVEL (destacada em roxo): a voltagem "
            "sobe espontaneamente de -60 mV até o limiar (-40 mV) graças a "
            "If (funny current) e ICa,T. Quando o limiar é atingido, ICa,L "
            "produz a fase 0 LENTA. Note: sem platô visível e sem INa!"
        ),
        "image_figure": "pacemaker",
    },
    {
        "id": "ephys_fig_003",
        "topic": "Períodos Refratários",
        "difficulty": "medium",
        "stem": (
            "Observe a correlação PA-ECG. O período refratário relativo "
            "(PRR, barra azul tracejada) corresponde a qual parte do ECG?"
        ),
        "options": [
            "Parte descendente da onda T — janela vulnerável",
            "Segmento ST",
            "Onda P",
            "Intervalo T-P",
        ],
        "answer_index": 0,
        "explanation": (
            "O PRR (barra azul tracejada) corresponde ao final da fase 3 = "
            "parte descendente da T. Neste período, parte dos canais de Na+ "
            "já recuperou. Um estímulo forte gera PA anormal → risco de "
            "reentrada. É a 'janela vulnerável' — o temido fenômeno R sobre T."
        ),
        "image_figure": "contractile",
    },
    {
        "id": "ephys_fig_004",
        "topic": "Comparação PA",
        "difficulty": "hard",
        "stem": (
            "Observe a sobreposição dos dois potenciais de ação. Qual "
            "característica do PA contrátil está AUSENTE no pacemaker?"
        ),
        "options": [
            "Platô (fase 2) — ausente no pacemaker por falta de Ito/ICa,L sustentada",
            "Fase 0 — ausente no pacemaker",
            "Repolarização (fase 3) — ausente no pacemaker",
            "Ambos são idênticos, sem diferença",
        ],
        "answer_index": 0,
        "explanation": (
            "O PA contrátil (preto) tem platô proeminente (fase 2) mantido "
            "pelo equilíbrio ICa,L/IK. O pacemaker (vermelho tracejado) não "
            "tem platô visível — passa direto da fase 0 lenta para a fase 3. "
            "Outras diferenças: repouso mais negativo (-90 vs -60 mV) e "
            "fase 0 rápida (INa) vs lenta (ICa,L)."
        ),
        "image_figure": "comparison",
    },
]

# =====================================================================
# Funções auxiliares
# =====================================================================

ALL_QUESTIONS: list[dict] = QUESTIONS_TEXT_ONLY + QUESTIONS_WITH_FIGURE


def get_questions_by_topic(topic: str) -> list[dict]:
    return [q for q in ALL_QUESTIONS if topic.lower() in q["topic"].lower()]


def get_figure_questions() -> list[dict]:
    return [q for q in ALL_QUESTIONS if q.get("image_figure")]


def get_text_questions() -> list[dict]:
    return [q for q in ALL_QUESTIONS if not q.get("image_figure")]

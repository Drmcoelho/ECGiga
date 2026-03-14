"""
education/didactic_text.py — Conteúdo didático estruturado em português

Todo o material usa a analogia de "Câmeras Cardíacas" para explicar o ECG
de forma intuitiva e memorável.
"""

from __future__ import annotations

# =====================================================================
# INTRO_ECG_CAMERAS  — Introdução ao ECG usando analogia de câmeras
# =====================================================================

INTRO_ECG_CAMERAS: str = """\
ELETROCARDIOGRAMA: O CORAÇÃO FILMADO POR 12 CÂMERAS

Imagine que você é um diretor de cinema e precisa registrar, com a maior
fidelidade possível, um evento que acontece dentro de uma sala fechada — a
despolarização e repolarização do coração. Você não pode abrir a sala. Você
não pode colocar uma câmera dentro dela. Tudo o que você pode fazer é
posicionar câmeras do lado de fora, em ângulos diferentes, e tentar
reconstruir o que aconteceu lá dentro a partir das imagens capturadas.

É exatamente isso que o eletrocardiograma faz.

O ECG de 12 derivações usa 10 eletrodos colados no corpo do paciente para
criar 12 "câmeras" que filmam a atividade elétrica do coração de 12 ângulos
diferentes. Seis câmeras estão no plano frontal (olhando o coração de
frente, como um retrato) e seis estão no plano horizontal (olhando o
coração em corte transversal, como uma fatia de tomografia).

REGRA FUNDAMENTAL: O MNEMÔNICO CAFÉ

Antes de qualquer coisa, grave esta regra de ouro:

C — Câmera = polo positivo da derivação
A — Aproximando = quando o vetor elétrico se aproxima da câmera, a
    deflexão é POSITIVA (onda para cima no traçado)
F — Fugindo = quando o vetor elétrico se afasta da câmera, a deflexão
    é NEGATIVA (onda para baixo)
É — Esquece quando perpendicular = se o vetor cruza perpendicular à
    câmera, o registro é BIFÁSICO ou isoelétrico (a câmera não consegue
    resolver se está vindo ou indo)

Esta regra explica TUDO no ECG. Cada onda, cada segmento, cada desvio de
eixo. Se você entender o CAFÉ, entende o ECG.

O VETOR ELÉTRICO: O ATOR PRINCIPAL

O "ator" que as câmeras filmam é o vetor elétrico cardíaco. Esse vetor
representa a soma de todas as forças elétricas geradas pelas células
cardíacas em um dado instante. Ele muda de direção e magnitude a cada
milissegundo durante o ciclo cardíaco.

Quando o nó sinusal dispara, uma onda de despolarização se espalha pelos
átrios de cima para baixo e da direita para a esquerda. O vetor atrial
resultante aponta para baixo e para a esquerda — e as câmeras posicionadas
nessa direção (DII, DIII, aVF) registram uma onda P positiva. A câmera
aVR, que está no lado oposto, vê o vetor se afastando e registra P
negativa.

Depois dos átrios, a despolarização chega ao nó AV, que age como um
"porteiro" — segura o sinal por ~120-200 ms (intervalo PR). Esse atraso é
essencial: permite que os átrios terminem de contrair antes que os
ventrículos comecem.

A despolarização ventricular começa pelo septo (da esquerda para a
direita), depois envolve as paredes livres de ambos os ventrículos. Como o
ventrículo esquerdo é muito mais espesso, domina o vetor resultante, que
aponta para baixo e para a esquerda (~60° no plano frontal). É por isso
que o QRS é positivo em DII — a câmera DII está a 60°, exatamente alinhada
com o vetor principal!

A repolarização (onda T) normalmente segue a mesma direção geral do QRS
principal. Parece estranho — a repolarização vai na mesma direção da
despolarização? Sim, porque a repolarização começa pelo epicárdio (de fora
para dentro), invertendo a direção célula a célula, mas mantendo o vetor
resultante na mesma direção geral.

POR QUE 12 CÂMERAS?

Uma única câmera não é suficiente. Se você filmasse o coração apenas de DII,
veria que o QRS é positivo, mas não saberia se o vetor aponta para 30°, 60°
ou 80° — todos produziriam QRS positivo em DII. Mas se você olhar DI e aVF
ao mesmo tempo, pode triangular: se DI é positivo e aVF é positivo, o vetor
está entre 0° e 90°. Se aVL é bifásico, o vetor é perpendicular a aVL
(-30°), ou seja, a ~60°. Quanto mais câmeras, melhor a resolução.

As seis câmeras precordiais (V1-V6) fazem o mesmo no plano horizontal. V1,
perto do VD, vê o septo vindo em sua direção (r pequeno) e depois o VE se
afastando (S grande). V6, do outro lado, vê o VE vindo em sua direção
(R grande). A progressão de rS em V1 para qRs em V6 é chamada de "progressão
do R" e reflete o vetor girando no plano horizontal.

COMO LER UM ECG COM CÂMERAS

1. Olhe o ritmo pela câmera DII (melhor visão do nó sinusal)
2. Calcule o eixo vendo qual câmera tem o maior QRS e qual tem QRS bifásico
3. Para cada câmera, pergunte: o vetor está se aproximando ou se afastando?
4. Alterações focais (ex: supra de ST) → indicam lesão na região que aquela
   câmera está filmando

Com esta abordagem, o ECG deixa de ser um conjunto de rabiscos misteriosos
e se torna um mapa tridimensional da atividade elétrica do coração, visto
por 12 ângulos diferentes. Cada câmera conta uma parte da história. Juntas,
contam a história completa.
"""

# =====================================================================
# FRONTAL_PLANE_CAMERAS
# =====================================================================

FRONTAL_PLANE_CAMERAS: str = """\
AS 6 CÂMERAS DO PLANO FRONTAL

O plano frontal é como olhar o paciente de frente. Seis câmeras estão
distribuídas em um círculo ao redor do coração, como os números de um relógio:

DI (0°) — Câmera no ombro esquerdo
  Olha horizontalmente da direita para a esquerda. Qualquer vetor que
  aponta para a esquerda aparece positivo. É a referência do eixo
  horizontal. Se o QRS é positivo em DI, o eixo está no hemisfério esquerdo.

DII (60°) — Câmera na perna esquerda (ângulo inferior-esquerdo)
  A derivação mais alinhada com o eixo cardíaco normal. Por isso, costuma
  ter o maior QRS positivo e a onda P mais bonita. É a derivação padrão
  para monitorização de ritmo. Se o ritmo é sinusal, a onda P é positiva
  em DII.

DIII (120°) — Câmera na perna esquerda (ângulo inferior-direito)
  Complementa DII para a parede inferior. Quando o eixo se desvia para a
  direita, DIII mostra QRS mais positivo que DII.

aVR (-150°) — Câmera no ombro direito
  A "câmera do contra"! Olha o coração de um ângulo quase oposto ao vetor
  normal. Resultado: quase tudo é negativo (P negativa, QRS negativo, T
  negativa). Se aVR ficar positiva, algo muito incomum está acontecendo
  (dextrocardia, troca de eletrodos, ou taquicardia atrial ectópica).

aVL (-30°) — Câmera no ombro esquerdo (ligeiramente superior)
  Filma a parede lateral alta. Quando o eixo é exatamente 60° (normal),
  aVL está a 90° do vetor → QRS bifásico. Um aVL com QRS bifásico
  confirma eixo ~60°, perfeito!

aVF (90°) — Câmera embaixo do coração
  A câmera da parede inferior. Olha diretamente para cima. Se o QRS é
  positivo em aVF, o vetor tem componente inferior (para baixo). Se o QRS
  é negativo, o vetor aponta para cima → desvio do eixo para a esquerda.

TRIÂNGULO DE EINTHOVEN:
DI, DII e DIII formam o triângulo de Einthoven. A lei é simples:
DII = DI + DIII. Se DI mostra +5mm e DIII mostra +3mm, DII deve mostrar
~+8mm. Isso é matemática pura — é geometria de vetores.

COMO CALCULAR O EIXO COM AS CÂMERAS FRONTAIS:
1. Olhe DI: positivo → eixo vai para a esquerda (0° a ±90°)
2. Olhe aVF: positivo → eixo vai para baixo (0° a 180°)
3. Se DI+ e aVF+ → eixo normal (entre 0° e 90°)
4. Encontre a derivação com QRS bifásico → eixo é perpendicular a ela
5. Encontre a derivação com maior QRS → eixo aponta nessa direção
"""

# =====================================================================
# HORIZONTAL_PLANE_CAMERAS
# =====================================================================

HORIZONTAL_PLANE_CAMERAS: str = """\
AS 6 CÂMERAS DO PLANO HORIZONTAL (PRECORDIAIS)

As derivações precordiais (V1-V6) são câmeras coladas no peito do paciente,
formando um arco que vai do lado direito do esterno até a linha axilar
média esquerda. Elas filmam o coração em "fatia", como uma tomografia.

V1 — Câmera na borda esternal direita
  Está quase em cima do ventrículo direito e do septo. Vê:
  - Primeiro: septo se despolarizando da esquerda para a direita → onda r
    pequena (vetor vem em sua direção)
  - Depois: VE se despolarizando para a esquerda → onda S profunda (vetor
    foge da câmera)
  Padrão normal: rS (r pequeno, S grande)
  Se R > S em V1 → algo anormal (HVD, IAM posterior, WPW, BRD)

V2 — Câmera na borda esternal esquerda
  Similar a V1, mas levemente mais à esquerda. Padrão rS também.
  V1 e V2 juntas são as "câmeras septais" ou "câmeras do VD".

V3 — Câmera de transição
  Posicionada entre V2 e V4. Aqui ocorre a "zona de transição" — o ponto
  em que R e S têm amplitude semelhante. A câmera V3 vê o vetor passando
  "de lado" — nem vindo nem indo claramente.

V4 — Câmera no ápice
  No 5º espaço intercostal, linha hemiclavicular. O vetor já aponta mais
  na sua direção. R começa a dominar. Padrão: RS ou Rs.

V5 — Câmera na linha axilar anterior
  O vetor do VE já está claramente vindo em sua direção. R alto.
  Padrão: Rs ou qRs.

V6 — Câmera na linha axilar média
  A câmera mais lateral. Vê o VE de lado. R dominante.
  Padrão: qRs (q de despolarização septal que se afasta, R de VE
  que se aproxima, s terminal de despolarização basal).

PROGRESSÃO DO R:
De V1 a V6, o R vai crescendo e o S vai diminuindo. É como uma câmera
fazendo um "pan" (movimento panorâmico) da direita para a esquerda.
Primeiro o vetor foge da câmera (V1 = S grande), depois cruza de lado
(V3 = transição), e finalmente vem na direção da câmera (V6 = R grande).

Transição precoce: R > S antes de V3 (pode ser normal, HVD, IAM posterior)
Transição tardia: R > S depois de V4 (pode indicar HVE, DPOC, IAM anterior)

CÂMERAS E TERRITÓRIOS CORONARIANOS:
  V1-V2: Septal (descendente anterior)
  V3-V4: Anterior (descendente anterior)
  V5-V6: Lateral (circunflexa ou diagonal)
  Se supra de ST em V1-V4 → A câmera está filmando lesão na parede
  anterior → oclusão da artéria descendente anterior!
"""

# =====================================================================
# WAVE_EXPLANATIONS
# =====================================================================

WAVE_EXPLANATIONS: dict = {
    "P": {
        "nome": "Onda P — A filmagem dos átrios",
        "descricao": (
            "A onda P é o registro da despolarização atrial. O vetor atrial "
            "aponta para baixo e para a esquerda (cerca de +60° no plano "
            "frontal), porque o nó sinusal fica no topo do átrio direito "
            "e a despolarização desce em direção ao nó AV."
        ),
        "camera_analogy": (
            "As câmeras DII, DIII e aVF (posicionadas embaixo) veem o "
            "vetor atrial se aproximando → onda P positiva. A câmera aVR "
            "(no alto à direita) vê o vetor se afastando → P negativa. "
            "A câmera V1 está tão perto do átrio que registra um P "
            "bifásico: primeiro positivo (átrio direito se aproxima) "
            "depois negativo (átrio esquerdo se afasta, para trás)."
        ),
        "dica_clinica": (
            "P positiva em DII e negativa em aVR = ritmo sinusal confirmado. "
            "P ausente? O 'ator atrial' não entrou em cena → ritmo juncional "
            "ou fibrilação atrial (câmera não capta nada organizado)."
        ),
    },
    "QRS": {
        "nome": "Complexo QRS — O filme dos ventrículos",
        "descricao": (
            "O QRS é a despolarização ventricular. É o evento elétrico mais "
            "potente do coração — os ventrículos são atores principais. "
            "O vetor muda rapidamente: primeiro vai da esquerda para a "
            "direita (septo), depois para baixo e para a esquerda (paredes "
            "ventriculares), e termina subindo (base)."
        ),
        "camera_analogy": (
            "Câmera V1: vê o septo vindo → r pequeno. Depois vê o VE "
            "fugindo → S profundo. Câmera V6: vê o septo fugindo → q "
            "pequeno. Depois vê o VE vindo → R alto. Câmera DII: vê o "
            "vetor principal (~60°) vindo direto → R alto e positivo. "
            "Câmera aVR: vê tudo fugindo → QS ou rS (quase tudo negativo)."
        ),
        "dica_clinica": (
            "QRS largo (>120 ms)? A despolarização está demorando demais — "
            "como uma cena em câmera lenta. Pode ser bloqueio de ramo: "
            "BRD → V1 vê um R' tardio (o VD despolariza atrasado). "
            "BRE → V6 vê um R largo e entalhado (VE despolariza devagar)."
        ),
    },
    "T": {
        "nome": "Onda T — A repolarização filmada",
        "descricao": (
            "A onda T registra a repolarização ventricular. Normalmente, "
            "o vetor T aponta na mesma direção geral que o QRS principal."
        ),
        "camera_analogy": (
            "Se o QRS é positivo em DII, a onda T também deveria ser "
            "positiva em DII — a câmera vê a repolarização vindo na "
            "mesma direção. Inversão de T (T negativa onde QRS é positivo) "
            "significa que a repolarização mudou de direção — a câmera "
            "agora vê a repolarização fugindo. Isso pode indicar "
            "isquemia, sobrecarga ou outros problemas."
        ),
        "dica_clinica": (
            "T invertida em derivações onde QRS é positivo → isquemia? "
            "Sobrecarga? Sempre correlacionar com a clínica. "
            "T apiculada e simétrica → hipercalemia (a câmera vê uma "
            "repolarização absurdamente rápida e intensa)."
        ),
    },
}

# =====================================================================
# AXIS_EXPLAINED
# =====================================================================

AXIS_EXPLAINED: str = """\
EIXO CARDÍACO: PARA ONDE O VETOR APONTA — E QUAIS CÂMERAS VÊM MELHOR

O eixo elétrico do QRS representa a direção média do vetor de
despolarização ventricular no plano frontal. Normalmente fica entre
-30° e +90°.

MÉTODO DAS CÂMERAS PARA CALCULAR O EIXO:

PASSO 1: Qual câmera mostra QRS bifásico?
  Se encontrar uma derivação com R = S (bifásico), o eixo é PERPENDICULAR
  a essa câmera. Por exemplo:
  - aVL bifásico → eixo perpendicular a -30° → eixo a ~60° (normal!)
  - DI bifásico → eixo perpendicular a 0° → eixo a ~90°
  - aVF bifásico → eixo perpendicular a 90° → eixo a ~0°

PASSO 2: Qual câmera mostra o maior QRS positivo?
  O eixo aponta na direção dessa câmera. Se DII tem o QRS mais positivo,
  o eixo está perto de 60°.

MÉTODO RÁPIDO (DI + aVF):
  DI (+) e aVF (+) → Eixo normal (0° a 90°)
  DI (+) e aVF (-) → Desvio para a esquerda (-90° a 0°)
  DI (-) e aVF (+) → Desvio para a direita (90° a 180°)
  DI (-) e aVF (-) → Desvio extremo ("terra de ninguém")

DESVIOS E SUAS CAUSAS (visão pelas câmeras):

Eixo para a esquerda (ex: -45°):
  → As câmeras DI e aVL veem o vetor vindo na direção delas (QRS positivo)
  → As câmeras DIII e aVF veem o vetor fugindo (QRS negativo)
  → Causas: BDAS, HVE, IAM inferior

Eixo para a direita (ex: +120°):
  → As câmeras DIII e aVF veem o vetor se aproximando
  → A câmera DI vê o vetor fugindo (QRS negativo em DI!)
  → Causas: HVD, BDPI, TEP, DPOC, coração pediátrico

Eixo extremo (ex: -150°):
  → A câmera aVR é a única que vê o vetor de frente!
  → Todas as outras câmeras veem o vetor fugindo
  → Causas: ritmo ventricular, hipercalemia grave
"""

# =====================================================================
# COMMON_PATTERNS_CAMERAS
# =====================================================================

COMMON_PATTERNS_CAMERAS: dict = {
    "STEMI": {
        "titulo": "Infarto com Supra de ST — A câmera filma a lesão!",
        "explicacao": (
            "Quando uma artéria coronária é ocluída, a região do "
            "miocárdio irrigada por ela sofre lesão. As câmeras "
            "posicionadas diretamente sobre essa região registram "
            "supradesnivelamento do segmento ST — é como se a câmera "
            "estivesse filmando um 'incêndio' na parede cardíaca.\n\n"
            "As câmeras do lado oposto (derivações recíprocas) veem "
            "o oposto: infradesnivelamento de ST — o 'reflexo' do "
            "incêndio no espelho.\n\n"
            "Exemplos por território:\n"
            "• IAM anterior: Supra em V1-V4 (câmeras anteriores filmam "
            "a lesão) + Infra em DII, DIII, aVF (câmeras inferiores "
            "veem o reflexo)\n"
            "• IAM inferior: Supra em DII, DIII, aVF (câmeras "
            "inferiores) + Infra em DI, aVL (câmeras laterais altas)\n"
            "• IAM lateral: Supra em DI, aVL, V5, V6 (câmeras laterais)"
        ),
    },
    "BRD": {
        "titulo": "Bloqueio de Ramo Direito — Uma câmera vê o VD atrasado",
        "explicacao": (
            "No BRD, o ramo direito está bloqueado. O VE despolariza "
            "normalmente, mas o VD despolariza com atraso, usando fibras "
            "musculares em vez do sistema de condução.\n\n"
            "Câmera V1 (perto do VD): vê primeiro o septo (r), depois "
            "o VE fugindo (S), e depois o VD despolarizando tardiamente "
            "em sua direção → R' (segunda onda R). Padrão: rsR' — o "
            "famoso 'orelha de coelho'.\n\n"
            "Câmera V6 (longe do VD): vê o QRS normal do VE, seguido de "
            "um S largo e empastado — o VD despolarizando tardiamente "
            "para longe dela.\n\n"
            "QRS alargado (>120 ms) porque a cena está em câmera lenta "
            "no VD."
        ),
    },
    "BRE": {
        "titulo": "Bloqueio de Ramo Esquerdo — O VE em câmera lenta",
        "explicacao": (
            "No BRE, o ramo esquerdo está bloqueado. O septo se "
            "despolariza da direita para a esquerda (invertido!) e o VE "
            "despolariza lentamente.\n\n"
            "Câmera V1: perde o r inicial (septo agora foge dela) e vê "
            "um QS largo ou rS largo — tudo fugindo.\n\n"
            "Câmera V6: vê tudo vindo em sua direção o tempo todo — "
            "R largo, entalhado, sem q inicial. O 'plateau' na onda R "
            "reflete a condução lenta.\n\n"
            "Câmera DI: R largo e positivo (VE vem na direção dela).\n\n"
            "QRS > 120 ms. O BRE distorce tanto o registro que dificulta "
            "a interpretação de isquemia e HVE."
        ),
    },
    "HVE": {
        "titulo": "Hipertrofia Ventricular Esquerda — O VE grita para as câmeras",
        "explicacao": (
            "Com o VE hipertrofiado, a massa muscular aumentada gera "
            "vetores maiores apontando para a esquerda e para trás.\n\n"
            "Câmera V1: vê um S ainda mais profundo (vetor foge com "
            "mais intensidade).\n"
            "Câmera V5/V6: vê um R ainda mais alto (vetor se aproxima "
            "com mais força).\n\n"
            "Critério de Sokolow-Lyon: S(V1) + R(V5 ou V6) ≥ 35mm.\n"
            "Traduzindo: 'o quanto a câmera V1 vê fugindo + o quanto "
            "a câmera V5/V6 vê se aproximando = hipertrofia'.\n\n"
            "Pode haver strain pattern (infradesnivelamento de ST + T "
            "invertida) em V5-V6: as câmeras laterais veem a "
            "repolarização alterada pela hipertrofia."
        ),
    },
    "HVD": {
        "titulo": "Hipertrofia Ventricular Direita — O VD compete com o VE",
        "explicacao": (
            "Normalmente o VE domina o vetor. Na HVD, o VD cresceu tanto "
            "que começa a competir.\n\n"
            "Câmera V1: agora vê o VD gerando vetores tão fortes que o R "
            "fica dominante (R > S em V1). A câmera que normalmente via "
            "tudo fugindo agora vê parte vindo!\n"
            "Câmera V6: S mais profundo que o normal (mais vetor fugindo "
            "para a direita).\n\n"
            "O eixo se desvia para a direita (>+90°): as câmeras "
            "inferiores-direitas veem melhor."
        ),
    },
    "FA": {
        "titulo": "Fibrilação Atrial — A câmera perde o ator atrial",
        "explicacao": (
            "Na fibrilação atrial, os átrios não se despolarizam de forma "
            "organizada. Em vez de um vetor atrial limpo, há centenas de "
            "micro-vetores caóticos.\n\n"
            "Resultado para as câmeras: nenhuma registra onda P definida. "
            "Em vez disso, a linha de base fica irregular com ondas 'f' "
            "(fibrilatórias) — é como estática na TV.\n\n"
            "A câmera V1, por estar mais perto dos átrios, costuma mostrar "
            "as ondas f com mais clareza.\n\n"
            "O QRS continua normal (o VE funciona normalmente), mas o "
            "ritmo é irregularmente irregular — cada QRS aparece em "
            "momentos imprevisíveis."
        ),
    },
}

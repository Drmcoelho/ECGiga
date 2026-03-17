"""
education/electrophysiology.py — Eletrofisiologia cardíaca completa

Conteúdo educacional detalhado em português:
- Potencial de ação do cardiomiócito contrátil (fases 0-4)
- Correntes iônicas de cada fase
- Automatismo do nó sinusal (potencial pacemaker)
- Períodos refratários absoluto e relativo
- Correlação exata de cada fase com o ECG (P, QRS, ST, T, U)
- Visualizações interativas com Plotly

Referências:
- Katz AM, "Physiology of the Heart", 6th ed
- Antzelevitch & Bhurga, "Brugada Syndrome", JACC 2007
- Nerbonne & Kass, "Molecular Physiology of Cardiac Repolarization",
  Physiological Reviews, 2005
"""

from __future__ import annotations

import numpy as np

try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    HAS_PLOTLY = True
except ImportError:  # pragma: no cover
    HAS_PLOTLY = False

# =====================================================================
# 1. O POTENCIAL DE AÇÃO DO CARDIOMIÓCITO CONTRÁTIL — Fases 0-4
# =====================================================================

ACTION_POTENTIAL_INTRO: str = """\
ELETROFISIOLOGIA CARDÍACA: O POTENCIAL DE AÇÃO DO CARDIOMIÓCITO

═══════════════════════════════════════════════════════════════════════
O QUE É O POTENCIAL DE AÇÃO?
═══════════════════════════════════════════════════════════════════════

O potencial de ação (PA) é a sequência de mudanças elétricas que cada
célula cardíaca executa a cada batimento. É o "roteiro" que cada ator
(célula) segue no palco do coração.

Diferença fundamental entre o PA CARDÍACO e o NEURONAL:
- PA neuronal: dura ~1-2 ms (sprint rápido)
- PA cardíaco: dura ~250-350 ms (peça teatral completa com 5 atos)

Essa duração longa é ESSENCIAL: garante que o coração não entre em
tetania (contração sustentada) como um músculo esquelético. O platô
(fase 2) mantém a célula "ocupada" tempo suficiente para que a
contração mecânica ocorra de forma coordenada.

O PA é dividido em 5 FASES (0-4), cada uma com correntes iônicas
específicas e uma correspondência direta no ECG:

  Fase 0 → Despolarização rápida       → QRS no ECG
  Fase 1 → Repolarização precoce       → Ponto J (junção QRS-ST)
  Fase 2 → Platô (plateau)             → Segmento ST
  Fase 3 → Repolarização               → Onda T
  Fase 4 → Repouso (diástole elétrica) → Linha isoelétrica (T-P)
"""

# =====================================================================
# FASE 0 — Despolarização rápida
# =====================================================================

PHASE_0_TEXT: str = """\
═══════════════════════════════════════════════════════════════════════
FASE 0 — DESPOLARIZAÇÃO RÁPIDA (A EXPLOSÃO ELÉTRICA)
═══════════════════════════════════════════════════════════════════════

Voltagem: de -90 mV → +20 mV (em ~1-2 ms)
Corrente principal: INa (corrente de sódio — canais Nav1.5)

O QUE ACONTECE:
Quando o estímulo chega à célula (via gap junctions do vizinho), o
potencial de membrana sobe de -90 mV até o limiar (~-70 mV). Nesse
momento, milhares de canais de Na+ voltagem-dependentes ABREM
simultaneamente.

O Na+ extracelular (145 mEq/L) despenca para dentro da célula (12 mEq/L
intracelular) — a favor do gradiente eletroquímico. É como uma represa
que se rompe: MASSIVA entrada de carga positiva.

Em ~1-2 ms, a voltagem salta de -90 mV para +20 mV. É o upstroke
mais rápido de todas as células do corpo: dV/dt ≈ 200-400 V/s.

VELOCIDADE DE CONDUÇÃO:
A velocidade do upstroke determina a velocidade de condução:
  → Fibras de Purkinje: upstroke ultra-rápido → condução 2-4 m/s
  → Miócitos ventriculares: rápido → 0.3-1.0 m/s
  → Nó AV: upstroke LENTO (dependente de Ca²+) → 0.02-0.05 m/s

CORRELAÇÃO COM ECG:
  → A ONDA QRS é o registro das câmeras (derivações) da fase 0
    ocorrendo em milhões de cardiomiócitos ventriculares.
  → A velocidade do upstroke (INa) determina a largura do QRS:
    • Normal: INa rápida → QRS < 120 ms
    • Bloqueio de ramo: condução atrasada → QRS > 120 ms
    • Hipercalemia: INa parcialmente inativada → QRS alargado
    • Classe I antiarrítmicos (lidocaína, flecainida): bloqueiam
      INa → QRS alarga

ANALOGIA:
A fase 0 é como a ENTRADA em cena de todos os atores simultaneamente
— a "explosão" de atividade que as câmeras registram como o complexo
QRS. Quanto mais rápido os atores entram, mais "compacta" é a cena
filmada (QRS estreito). Se entram em câmera lenta, a cena se arrasta
(QRS largo).

O Na+ é o COMBUSTÍVEL da explosão. Se falta Na+ (hiponatremia grave)
ou os canais estão bloqueados (drogas, hipercalemia), a explosão é
fraca e lenta → QRS largo.

CANAIS ENVOLVIDOS:
  INa (Nav1.5) — ativação ultra-rápida → abre em -70 mV
                — inativação rápida → fecha em ~2 ms
                → Gene: SCN5A (mutações → Brugada, QT longo tipo 3)
"""

# =====================================================================
# FASE 1 — Repolarização precoce
# =====================================================================

PHASE_1_TEXT: str = """\
═══════════════════════════════════════════════════════════════════════
FASE 1 — REPOLARIZAÇÃO PRECOCE (O ENTALHE)
═══════════════════════════════════════════════════════════════════════

Voltagem: de +20 mV → +5 a 0 mV (breve descida)
Correntes principais: Ito (transient outward K+) e ICl(Ca)

O QUE ACONTECE:
Assim que os canais de Na+ inativam (fase 0 termina), canais de K+
transientes (Ito) abrem brevemente. O K+ SAI da célula, causando uma
repolarização parcial rápida — o "entalhe" (notch) entre o pico do PA
e o início do platô.

A corrente Ito é particularmente proeminente no EPICÁRDIO (camada
externa) do ventrículo, mas fraca no ENDOCÁRDIO (camada interna).
Essa diferença epicárdio-endocárdio é fundamental:

  → Epicárdio: Ito forte → entalhe profundo → "spike-and-dome"
  → Endocárdio: Ito fraca → entalhe mínimo → transição suave

CORRELAÇÃO COM ECG:
  → A fase 1 corresponde ao PONTO J (junção entre QRS e ST)
  → O ENTALHE Ito epicárdico é responsável pela elevação do
    ponto J em condições normais → "repolarização precoce benigna"
  → Se Ito é excessivo no epicárdio (por predisposição genética
    ou febre): o platô pode "colapsar" → PADRÃO DE BRUGADA
  → A onda J (Osborn) da hipotermia também envolve Ito exagerada

ANALOGIA:
A fase 1 é como o INTERVALO RÁPIDO entre a entrada em cena (fase 0)
e o grande ato principal (platô/fase 2). Os atores entram correndo
(despolarização), respiram por um instante (entalhe Ito), e então
começam a cena longa do platô.

Se o intervalo é exagerado (Ito muito forte), o ritmo da peça se
desequilibra — isso é a Síndrome de Brugada, onde o "intervalo"
epicárdico é tão grande que a cena pode desmoronar.

CANAIS ENVOLVIDOS:
  Ito1 (Kv4.3) — corrente K+ transitória → rápida ativação/inativação
                → Gene: KCND3
  Ito2 (ICl(Ca)) — corrente Cl- ativada por Ca²+
                → contribui para o entalhe
"""

# =====================================================================
# FASE 2 — Platô (Plateau)
# =====================================================================

PHASE_2_TEXT: str = """\
═══════════════════════════════════════════════════════════════════════
FASE 2 — PLATÔ (O GRANDE ATO DO CÁLCIO)
═══════════════════════════════════════════════════════════════════════

Voltagem: ~0 a +5 mV (mantida por ~200 ms)
Correntes: ICa,L (entrada de Ca²+) vs IKr/IKs (saída de K+)

O QUE ACONTECE:
O platô é a fase mais LONGA e mais EXCLUSIVA do coração. Nenhum outro
tecido do corpo tem um platô assim. Ele existe porque duas forças
opostas se equilibram:

  → ENTRADA de Ca²+ (ICa,L — corrente de cálcio tipo L)
    Os canais de Ca²+ tipo L (Cav1.2) abrem lentamente e mantêm a
    voltagem "suspensa" em ~0 mV. O Ca²+ entra e desencadeia a
    liberação de Ca²+ do retículo sarcoplasmático (CICR — calcium-
    induced calcium release) → CONTRAÇÃO MECÂNICA.

  → SAÍDA de K+ (IKr, IKs — correntes retificadoras tardias)
    Canais de K+ começam a abrir gradualmente, tentando repolarizar.
    Mas a entrada de Ca²+ contrabalança.

O platô dura até que a ICa,L comece a inativar (os canais de Ca²+
fecham lentamente) e as correntes de K+ predominem → início da fase 3.

POR QUE O PLATÔ É ESSENCIAL:
1. CONTRAÇÃO MECÂNICA: o Ca²+ que entra durante o platô é o gatilho
   para a contração. Sem platô → sem contração coordenada.
2. PERÍODO REFRATÁRIO: enquanto o platô dura, a célula NÃO PODE ser
   re-excitada → impede tetania e reentrada.
3. COORDENAÇÃO: o platô longo garante que toda a massa ventricular
   se despolarize antes de qualquer célula repolarizar.

CORRELAÇÃO COM ECG:
  → O SEGMENTO ST corresponde ao platô.
  → Normalmente, o ST é ISOELÉTRICO porque todas as células
    ventriculares estão no mesmo potencial (~0 mV) → sem diferença
    de voltagem → sem deflexão → linha reta.
  → SUPRA de ST: parte do miocárdio tem platô diferente do resto
    (ex.: isquemia aguda — células lesadas têm PA encurtado)
  → INFRA de ST: diferença oposta de potenciais
  → QT CURTO (hipercalcemia): Ca²+ alto → ICa,L inativa mais rápido
    → platô encurta → ST encurta
  → QT LONGO (hipocalcemia): Ca²+ baixo → ICa,L demora a inativar
    → platô estica → ST prolonga

ANALOGIA:
O platô é o GRANDE ATO da peça — o ato central, longo e dramático.
O Ca²+ é o ator principal que mantém a tensão em cena. O K+ é o
contra-regra que tenta encerrar o ato. Enquanto o ator principal
(Ca²+) domina, o ato continua. Quando ele se cansa (ICa,L inativa),
o contra-regra (K+) prevalece e o ato termina.

O segmento ST no ECG é como a câmera filmando esse ato: se todos os
atores estão na mesma intensidade, a câmera registra uma cena "plana"
(ST isoelétrico). Se um grupo de atores para mais cedo (isquemia),
a câmera capta a diferença (supra/infra de ST).

CANAIS ENVOLVIDOS:
  ICa,L (Cav1.2) — canal de Ca²+ tipo L ("L" = Long-lasting)
                  → ativação lenta, inativação lenta
                  → Gene: CACNA1C (mutações → Timothy syndrome,
                    Brugada tipo 3)
  IKr (hERG/Kv11.1) — retificador tardio rápido
                     → Gene: KCNH2 (mutações → QT longo tipo 2)
  IKs (Kv7.1/KvLQT1) — retificador tardio lento
                      → Gene: KCNQ1 (mutações → QT longo tipo 1)
"""

# =====================================================================
# FASE 3 — Repolarização
# =====================================================================

PHASE_3_TEXT: str = """\
═══════════════════════════════════════════════════════════════════════
FASE 3 — REPOLARIZAÇÃO (A VOLTA AO REPOUSO)
═══════════════════════════════════════════════════════════════════════

Voltagem: de ~0 mV → -90 mV (em ~100-150 ms)
Correntes: IKr + IKs + IK1 (saída massiva de K+)

O QUE ACONTECE:
Quando a ICa,L finalmente inativa, as correntes de K+ (que vinham
crescendo durante o platô) passam a dominar. Há três protagonistas:

  → IKr (rapid delayed rectifier) — o primeiro a agir fortemente
    É o canal hERG. Abre durante o platô mas atinge pico na fase 3.
    É o alvo principal de drogas que prolongam o QT!

  → IKs (slow delayed rectifier) — o reforço lento
    Abre lentamente durante o platô e contribui na repolarização.
    É a "reserva de segurança" — se IKr é bloqueada, IKs compensa
    (parcialmente). Quando ambas falham → QT muito longo.

  → IK1 (inward rectifier) — o finalizador
    Muito ativa em potenciais negativos. Não contribui no platô
    (retificação inward), mas "puxa" forte a voltagem de volta
    para -90 mV na parte final da fase 3 e mantém o repouso.

A fase 3 é uma CORRIDA de saída de K+: quanto mais canais abertos,
mais rápida a repolarização. Se IKr/IKs são bloqueados (drogas,
mutações), a repolarização é LENTA → PA longo → QT longo no ECG.

CORRELAÇÃO COM ECG:
  → A ONDA T corresponde à fase 3 dos cardiomiócitos.
  → A T é positiva (na maioria das derivações) apesar de representar
    REPOLARIZAÇÃO (processo oposto à despolarização). Por quê?
    → O epicárdio repolariza ANTES do endocárdio (PA mais curto no
      epicárdio por causa da Ito proeminente + platô mais curto)
    → O vetor de repolarização vai de epicárdio → endocárdio
    → Esse vetor TEM A MESMA DIREÇÃO que o vetor de despolarização
      (que vai de endocárdio → epicárdio)
    → Por isso T e QRS normalmente têm a mesma polaridade!

  → T APICULADA (hipercalemia): fase 3 acelerada → repolarização
    rápida e intensa → T alta, estreita, simétrica
  → T ACHATADA (hipocalemia): fase 3 lenta e espalhada →
    repolarização arrastada → T baixa e plana
  → T INVERTIDA: pode significar inversão da sequência de
    repolarização (isquemia, hipertrofia, sobrecarga)

ANALOGIA:
A fase 3 é o ENCERRAMENTO do ato — os atores saem do palco (K+ sai da
célula). Normalmente, os atores do andar de cima (epicárdio) saem
PRIMEIRO, e os do andar de baixo (endocárdio) saem DEPOIS. A câmera,
olhando de fora, vê os atores saindo na mesma direção em que entraram
→ T positiva, concordante com QRS.

Se todos os atores saem correndo (hipercalemia), a câmera registra
uma saída explosiva (T apiculada). Se saem arrastados (hipocalemia),
a câmera mal percebe (T achatada).

CANAIS ENVOLVIDOS:
  IKr (hERG/Kv11.1) — retificador tardio rápido → fase 3 inicial
     → BLOQUEADO por: sotalol, dofetilida, amiodarona, eritromicina,
       haloperidol, metadona → QT longo adquirido
     → Gene: KCNH2 (LQT2)
  IKs (KvLQT1/minK) — retificador tardio lento → fase 3 tardia
     → Gene: KCNQ1 (LQT1)
  IK1 (Kir2.1) — retificador inward → estabiliza repouso
     → Gene: KCNJ2 (Andersen-Tawil syndrome)
"""

# =====================================================================
# FASE 4 — Repouso (diástole elétrica)
# =====================================================================

PHASE_4_TEXT: str = """\
═══════════════════════════════════════════════════════════════════════
FASE 4 — REPOUSO / DIÁSTOLE ELÉTRICA
═══════════════════════════════════════════════════════════════════════

Voltagem: -90 mV (estável nos cardiomiócitos contráteis)
Corrente: IK1 (mantém o repouso)

O QUE ACONTECE:
Nos cardiomiócitos CONTRÁTEIS (átrios e ventrículos), a fase 4 é
estável — a voltagem fica fixa em -90 mV. A IK1 é a guardiã: permite
a saída de K+ suficiente para manter o potencial de repouso negativo,
equilibrando qualquer vazamento de cátions.

A célula fica polarizada, pronta para receber o próximo estímulo. Ela
NÃO se despolariza sozinha — precisa que o vizinho (ou o sistema de
condução) envie o estímulo via gap junctions.

A fase 4 dura até o próximo estímulo chegar. Seu tempo é determinado
pela frequência cardíaca:
  → FC 60 bpm: fase 4 dura ~600 ms (repouso longo)
  → FC 120 bpm: fase 4 dura ~150 ms (repouso curto)
  → FC muito alta: o repouso encurta tanto que pode invadir a fase 3
    → problema para repolarização → arritmias

CORRELAÇÃO COM ECG:
  → A LINHA ISOELÉTRICA entre a onda T e a próxima onda P
    (intervalo T-P) corresponde à fase 4 ventricular.
  → A linha isoelétrica entre P e QRS (segmento PR) corresponde em
    parte à fase 4 atrial (já repolarizado) + condução pelo nó AV.
  → Em repouso, todas as células estão no mesmo potencial →
    nenhuma diferença de voltagem → linha reta no ECG.
  → Na bradicardia: intervalo T-P longo (fase 4 esticada)
  → Na taquicardia: T-P encurta → pode desaparecer → T funde com P

ANALOGIA:
A fase 4 é o INTERVALO entre as cenas. O palco está vazio, os atores
descansam nos bastidores, as câmeras filmam um palco imóvel (linha
isoelétrica). A bomba Na+/K+-ATPase trabalha silenciosamente nos
bastidores, restaurando os figurinos (gradientes iônicos) para a
próxima cena.

Se a frequência cardíaca aumenta, o intervalo encurta — os atores
mal descansam antes de entrar novamente. Se o intervalo some (FC
muito alta), não há tempo para recuperação → risco de "esgotamento"
(arritmias).

BOMBA Na+/K+-ATPase:
  → 3 Na+ para FORA, 2 K+ para DENTRO (eletrogênica: -1 carga/ciclo)
  → Mantém os gradientes de Na+ e K+ durante a fase 4
  → Consome ATP → por isso isquemia (falta de ATP) desestabiliza
    os potenciais → arritmias isquêmicas
  → DIGITÁLICOS (digoxina) inibem parcialmente a bomba → acúmulo
    de Na+ intracelular → troca Na+/Ca²+ reversa → mais Ca²+ →
    inotropismo positivo (mas risco de intoxicação → arritmias)
"""

# =====================================================================
# AUTOMATISMO DO NÓ SINUSAL — O marcapasso natural
# =====================================================================

SINUS_NODE_TEXT: str = """\
═══════════════════════════════════════════════════════════════════════
AUTOMATISMO DO NÓ SINUSAL: O MARCAPASSO NATURAL
═══════════════════════════════════════════════════════════════════════

O nó sinusal (SA) é fundamentalmente DIFERENTE dos cardiomiócitos
contráteis. Sua principal característica: a fase 4 NÃO É ESTÁVEL —
ela se despolariza SOZINHA, sem precisar de estímulo externo.

Isso é AUTOMATISMO (ou cronotropismo intrínseco).

DIFERENÇAS-CHAVE: NÓ SINUSAL vs CARDIOMIÓCITO CONTRÁTIL

│ Característica     │ Nó Sinusal (SA)    │ Cardiomiócito       │
│────────────────────│────────────────────│─────────────────────│
│ Potencial repouso  │ -55 a -60 mV      │ -90 mV              │
│ Fase 4             │ INSTÁVEL (sobe)    │ ESTÁVEL (plana)     │
│ Fase 0 (upstroke)  │ LENTO (Ca²+, ICaL) │ RÁPIDO (Na+, INa)  │
│ Amplitude do PA    │ ~70 mV             │ ~110 mV             │
│ dV/dt fase 0       │ 1-10 V/s           │ 200-400 V/s         │
│ Canais fase 0      │ ICa,L              │ INa                 │
│ Fase 1             │ Ausente            │ Ito (entalhe)       │
│ Fase 2 (platô)     │ Mínimo/ausente     │ Proeminente         │
│ Automatismo        │ SIM                │ NÃO                 │

═══════════════════════════════════════════════════════════════════════
AS 3 CORRENTES DO AUTOMATISMO SINUSAL (Fase 4 instável)
═══════════════════════════════════════════════════════════════════════

A fase 4 do nó sinusal se despolariza lentamente graças a 3 correntes
que trabalham em sequência — o "relógio de membrana":

1. If (funny current / HCN)
   → Canal ativado por HIPERPOLARIZAÇÃO (peculiar! Ativa quando a
     voltagem cai, não quando sobe)
   → Permite entrada de Na+ e K+ quando a voltagem está em ~-60 mV
   → Inicia a despolarização diastólica lenta
   → Alvo da IVABRADINA: bloqueia If → reduz FC sem afetar contração
   → Gene: HCN4

2. ICa,T (corrente de cálcio tipo T)
   → Canais de Ca²+ tipo T ("T" = Transient) abrem em voltagens baixas
     (~-50 mV) — antes dos tipo L
   → Dá o "empurrão" intermediário na fase 4
   → Amplifica a despolarização iniciada pela If

3. ICa,L (corrente de cálcio tipo L)
   → Quando a voltagem atinge ~-40 mV (limiar do nó sinusal), os
     canais tipo L abrem → fase 0 LENTA do nó sinusal
   → É uma fase 0 DEPENDENTE DE Ca²+ (não de Na+ como no miócito!)
   → Por isso o upstroke é lento (1-10 V/s vs 200-400 V/s)

Além do relógio de membrana, há o "relógio de cálcio":
  → Liberação espontânea de Ca²+ do retículo sarcoplasmático (RyR2)
  → Ca²+ ativa o trocador Na+/Ca²+ (NCX) → entrada de Na+ (3:1)
  → Corrente despolarizante → contribui para a fase 4

═══════════════════════════════════════════════════════════════════════
CONTROLE AUTONÔMICO DA FC
═══════════════════════════════════════════════════════════════════════

O sistema nervoso autônomo modula a velocidade da fase 4:

SIMPÁTICO (↑ FC):
  → Noradrenalina → receptores β1 → ↑ AMPc
  → AMPc abre mais canais If → fase 4 sobe mais rápido
  → AMPc aumenta ICa,L → limiar atingido mais cedo
  → Resultado: fase 4 mais rápida → FC aumenta

PARASSIMPÁTICO (↓ FC):
  → Acetilcolina → receptores M2 → ↓ AMPc + ativa IKACh
  → ↓ AMPc → menos If → fase 4 sobe mais devagar
  → IKACh (corrente de K+) → HIPERPOLARIZA o nó → parte de ponto
    mais negativo (-65 mV em vez de -60 mV)
  → Resultado: fase 4 mais lenta E partindo de mais negativo → FC cai

CORRELAÇÃO COM ECG:
  → A fase 4 do nó sinusal determina o INTERVALO P-P (e portanto a FC)
  → Taquicardia sinusal: fase 4 rápida → P-P curto → FC > 100
  → Bradicardia sinusal: fase 4 lenta → P-P longo → FC < 60
  → A onda P é o registro da despolarização ATRIAL (que é desencadeada
    pelo nó sinusal quando seu PA dispara)
  → O nó sinusal em si é pequeno demais para gerar deflexão visível
    no ECG — a câmera NÃO vê o disparo do nó SA diretamente

ANALOGIA:
O nó sinusal é o DIRETOR-GERAL do filme. Ele decide quando dizer
"AÇÃO!" (disparar o PA). A fase 4 é ele contando mentalmente até o
próximo "AÇÃO!". If é a contagem (1... 2... 3...), ICa,T é o dedo
se levantando, e ICa,L é o grito de "AÇÃO!" que desencadeia tudo.

O simpático é como café — o diretor conta mais rápido.
O parassimpático é como calmante — conta mais devagar e de mais longe.

═══════════════════════════════════════════════════════════════════════
HIERARQUIA DOS MARCAPASSOS
═══════════════════════════════════════════════════════════════════════

Todas as células do sistema de condução têm automatismo, mas com
velocidades diferentes:

  Nó sinusal:  60-100 bpm (mais rápido → COMANDA)
  Nó AV:       40-60 bpm  (backup de primeiro nível)
  His-Purkinje: 20-40 bpm (backup de último recurso)

O nó sinusal "ganha a corrida" porque sua fase 4 é a mais rápida.
Quando dispara, despolariza todos os outros ANTES que eles atinjam
seu próprio limiar (supressão por overdrive).

Se o nó sinusal falha:
  → O nó AV assume a 40-60 bpm → ritmo juncional (QRS estreito, P
    retrógrada ou ausente)
Se o nó AV também falha:
  → Purkinje assume a 20-40 bpm → ritmo de escape ventricular (QRS
    largo, potencialmente instável)
"""

# =====================================================================
# PERÍODOS REFRATÁRIOS — A defesa contra arritmias
# =====================================================================

REFRACTORY_PERIODS_TEXT: str = """\
═══════════════════════════════════════════════════════════════════════
PERÍODOS REFRATÁRIOS: A DEFESA DO CORAÇÃO CONTRA O CAOS
═══════════════════════════════════════════════════════════════════════

O período refratário é o tempo durante o qual a célula NÃO PODE (ou
DIFICILMENTE consegue) ser re-excitada. É a principal defesa contra
reentrada e arritmias.

Por que o coração precisa de período refratário?
  → Impede que um estímulo retrógrado re-excite uma célula que acabou
    de se despolarizar → bloqueia circuitos de reentrada
  → Garante que a contração mecânica termine antes de uma nova
    excitação → previne tetania
  → Coordena a propagação unidirecional do impulso

═══════════════════════════════════════════════════════════════════════
PERÍODO REFRATÁRIO ABSOLUTO (PRA)
═══════════════════════════════════════════════════════════════════════

Duração: ~250 ms (compreende fases 0, 1, 2 e início da fase 3)

Definição: período durante o qual NENHUM estímulo, por mais forte que
seja, consegue gerar um novo potencial de ação.

Por que é absoluto?
  → Durante as fases 0-2, os canais de Na+ (Nav1.5) estão no estado
    INATIVADO (porta h fechada). Eles NÃO PODEM ser reabertos
    diretamente — precisam primeiro RECUPERAR (voltar ao estado de
    repouso), o que só acontece quando a voltagem fica suficientemente
    negativa (< -60 mV).
  → Enquanto a voltagem está em +20 mV (fase 0), 0 mV (fase 2) ou
    ainda pouco negativa (início da fase 3), os canais de Na+ estão
    travados no estado inativado → IMPOSSÍVEL nova fase 0.

Representação nos estados do canal de Na+:
  Repouso (-90 mV): porta m fechada, porta h ABERTA → pode ativar
  Aberto (fase 0): portas m e h ABERTAS → Na+ flui
  Inativado (+20 → -40 mV): porta m aberta, porta h FECHADA → travado
  ↓ (voltagem precisa cair para < -60 mV para h reabrir)
  Recuperação (-70 a -90 mV): porta h REABRE → canal volta ao repouso

CORRELAÇÃO COM ECG:
  → O PRA se estende do INÍCIO DO QRS até ~metade da onda T.
  → Ou seja: durante QRS + ST + início de T, a célula ventricular
    é ABSOLUTAMENTE refratária.
  → Um estímulo extra (extrassístole) que caia neste período
    simplesmente NÃO gera resposta → é "engolido" sem efeito.

ANALOGIA:
O PRA é como um ator que acabou de atuar e está FISICAMENTE
incapaz de subir ao palco novamente — está nos bastidores trocando
de figurino (canais inativados). Mesmo que o diretor grite "AÇÃO!",
ele não consegue responder. Precisa terminar de se trocar primeiro.

═══════════════════════════════════════════════════════════════════════
PERÍODO REFRATÁRIO RELATIVO (PRR)
═══════════════════════════════════════════════════════════════════════

Duração: ~50 ms (final da fase 3, parte descendente da onda T)

Definição: período durante o qual um estímulo MAIS FORTE que o normal
PODE gerar um novo potencial de ação — mas ele será ANORMAL:
  → Amplitude menor (menos canais de Na+ recuperaram)
  → Upstroke mais lento (dV/dt reduzido)
  → Condução mais lenta (maior risco de bloqueio unidirecional)
  → Duração mais curta (menos canais de K+ disponíveis)

Por que é relativo?
  → A voltagem já caiu para -60 a -75 mV durante a parte final da
    fase 3. PARTE dos canais de Na+ já recuperou (porta h reabriu),
    mas NÃO TODOS. Um estímulo forte consegue ativar os que já
    recuperaram → PA de baixa qualidade.

O PERIGO DO PRR — FENÔMENO R-sobre-T:
  → Se uma extrassístole ventricular (EV) cai EXATAMENTE no PRR
    (sobre a onda T descendente), ela pode gerar um PA anormal que:
    • Conduz lentamente em algumas direções
    • Bloqueia em outras (bloqueio unidirecional)
    • Cria o substrato perfeito para REENTRADA
    → Pode deflagrar TV/FV!
  → Isso é o temido fenômeno "R sobre T" — o QRS da EV caindo sobre
    a onda T do batimento anterior.

CORRELAÇÃO COM ECG:
  → O PRR corresponde à PARTE DESCENDENTE DA ONDA T
    (aproximadamente do pico da T até o final da T).
  → A "janela vulnerável" é exatamente este período.
  → Se uma extrassístole cai aqui → "R sobre T" → risco de FV.
  → Um estímulo na fase 4 (após T) gera PA normal → sem risco.

ANALOGIA:
O PRR é o ator que ESTÁ se trocando — metade do figurino está pronto,
metade não. Se o diretor gritar "AÇÃO!" agora, ele PODE subir ao palco,
mas vai atuar mal (PA anormal). E o pior: como está descoordenado,
pode tropeçar nos outros atores (bloqueio unidirecional) e causar
caos no palco (reentrada → arritmia).

═══════════════════════════════════════════════════════════════════════
PERÍODO REFRATÁRIO EFETIVO (PRE)
═══════════════════════════════════════════════════════════════════════

É um conceito funcional que inclui o PRA + a parte do PRR na qual,
mesmo que um PA seja gerado, ele é fraco demais para se PROPAGAR
para as células vizinhas. Em termos práticos:

  PRE ≈ PRA + parte inicial do PRR

O PRE é o que realmente importa clinicamente:
  → Drogas que AUMENTAM o PRE (amiodarona, sotalol) são antiarrítmicas
    porque tornam mais difícil a reentrada.
  → Drogas que DIMINUEM o PRE podem ser pró-arrítmicas.

═══════════════════════════════════════════════════════════════════════
RESUMO: ONDE ESTÃO OS PERÍODOS REFRATÁRIOS NO ECG
═══════════════════════════════════════════════════════════════════════

  QRS .......... PRA (canais Na+ inativados — fase 0/1)
  Segmento ST .. PRA (platô — fase 2, canais Na+ inativados)
  Onda T (↑) ... PRA (início da fase 3, maioria dos Na+ ainda inativos)
  Onda T (↓) ... PRR (final da fase 3, Na+ parcialmente recuperados)
                  ← JANELA VULNERÁVEL ("R sobre T")
  Após onda T .. CÉLULA RESPONSIVA (fase 4, Na+ todos recuperados)

  ┌─────────────────────────────────────────────────────────────┐
  │ ECG:  P   QRS    ST-seg     T↑     T↓    │ T-P (repouso)  │
  │       │   ├──── PRA ──────────┤ PRR │     │ Responsiva     │
  │       │   │ canais Na+ INATIVADOS   │     │                │
  │       │   │ NENHUM estímulo gera PA │semi │ Estímulo normal│
  │       │   │                         │     │ → PA normal    │
  └─────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════
O QUE ALTERA OS PERÍODOS REFRATÁRIOS?
═══════════════════════════════════════════════════════════════════════

AUMENTAM o PRE (antiarrítmico):
  → Amiodarona (classe III): bloqueia IKr → repolarização lenta →
    PA mais longo → PRE mais longo
  → Sotalol: idem
  → Hipocalemia: repolarização lenta → PRE aumentado (mas heterogêneo
    → paradoxalmente, pode ser pró-arrítmico por dispersão!)
  → FC mais baixa → PA mais longo → PRE mais longo

DIMINUEM o PRE (potencialmente pró-arrítmico):
  → Hipercalemia: repolarização acelerada → PA mais curto → PRE
    mais curto → risco de reentrada
  → Catecolaminas (adrenalina): encurtam o PA
  → FC muito alta → PA encurta → PRE diminui
  → Isquemia: encurta o PA nas zonas afetadas → heterogeneidade →
    substrato para reentrada

DISPERSÃO DE REFRATARIEDADE:
O problema não é apenas um PRE curto ou longo, mas sim quando
diferentes regiões do coração têm PREs DIFERENTES. Isso cria zonas
que já recuperaram ao lado de zonas que ainda estão refratárias →
substrato perfeito para reentrada.

  → Isquemia: zona isquêmica tem PRE diferente da saudável
  → Cicatriz de infarto: bordas com PREs heterogêneos
  → QT longo: dispersão transmural de repolarização
  → Brugada: dispersão epicárdio-endocárdio no VD
"""

# =====================================================================
# CORRELAÇÃO COMPLETA FASES × ECG — Tabela-resumo
# =====================================================================

PHASE_ECG_CORRELATION: str = """\
═══════════════════════════════════════════════════════════════════════
TABELA: CORRELAÇÃO COMPLETA — FASES DO PA × ECG × CORRENTES
═══════════════════════════════════════════════════════════════════════

┌────────┬────────────────────────┬──────────────────┬──────────────────────┐
│ FASE   │ EVENTO CELULAR         │ CORRENTE         │ ECG                  │
│        │                        │ PRINCIPAL        │                      │
├────────┼────────────────────────┼──────────────────┼──────────────────────┤
│ Fase 4 │ Repouso (-90 mV)       │ IK1              │ Linha isoelétrica    │
│ (sin.) │ Despol. diastólica     │ If, ICaT, ICaL   │ (T-P / pré-P)       │
├────────┼────────────────────────┼──────────────────┼──────────────────────┤
│ Fase 0 │ Despolarização rápida  │ INa (Nav1.5)     │ Complexo QRS         │
│ (átrio)│ (+Na+ entra)           │                  │ (ou onda P nos       │
│        │ -90→+20 mV em 1-2 ms   │                  │ átrios)              │
├────────┼────────────────────────┼──────────────────┼──────────────────────┤
│ Fase 1 │ Repol. precoce (notch) │ Ito              │ Ponto J              │
│        │ +20→+5 mV              │                  │ (junção QRS-ST)      │
├────────┼────────────────────────┼──────────────────┼──────────────────────┤
│ Fase 2 │ Platô (~0 mV, 200 ms) │ ICa,L ↔ IKr/IKs │ Segmento ST          │
│        │ Ca²+ entra = contração │                  │ (isoelétrico se      │
│        │                        │                  │ homogêneo)           │
├────────┼────────────────────────┼──────────────────┼──────────────────────┤
│ Fase 3 │ Repolarização          │ IKr + IKs + IK1  │ Onda T               │
│        │ 0→-90 mV em 100-150ms  │                  │ (positiva = epicárdio│
│        │                        │                  │ repolariza primeiro) │
├────────┼────────────────────────┼──────────────────┼──────────────────────┤
│ Fase 4 │ Repouso restaurado     │ IK1 + Na/K-ATPase│ Intervalo T-P        │
│        │ -90 mV estável         │                  │ (linha isoelétrica)  │
└────────┴────────────────────────┴──────────────────┴──────────────────────┘

PERÍODOS REFRATÁRIOS NO ECG:

  QRS ──── ST ──── T(ascend.) ──── T(descend.) ──── T-P
  │←──── PERÍODO REFRATÁRIO ABSOLUTO ────→│← PRR →│← resp. →│
  │ canais Na+ INATIVADOS (h gate closed) │parcial│ pronto  │
  │ NENHUM estímulo gera PA               │PA abn.│PA normal│
  │                                       │R/T!   │         │
"""

# =====================================================================
# Geração de figuras Plotly
# =====================================================================

def create_action_potential_figure(
    cell_type: str = "contractile",
    highlight_phase: int | None = None,
) -> "go.Figure":
    """Cria figura interativa do potencial de ação cardíaco.

    Parâmetros
    ----------
    cell_type : str
        "contractile" (cardiomiócito) ou "pacemaker" (nó sinusal).
    highlight_phase : int, opcional
        Fase (0-4) para destacar com cor.

    Retorna
    -------
    go.Figure
    """
    if not HAS_PLOTLY:
        raise ImportError("Plotly necessário para figuras interativas")

    if cell_type == "pacemaker":
        return _create_pacemaker_ap_figure(highlight_phase)
    return _create_contractile_ap_figure(highlight_phase)


def _create_contractile_ap_figure(highlight_phase: int | None = None) -> "go.Figure":
    """PA do cardiomiócito contrátil com fases 0-4 e correlação ECG."""
    # --- Gerar PA do cardiomiócito ---
    t = np.linspace(0, 400, 2000)  # ms
    pa = np.full_like(t, -90.0)

    # Fase 4 pré-estímulo (0-50 ms)
    # Fase 0 (50-52 ms) — upstroke rápido
    m0 = (t >= 50) & (t < 52)
    pa[m0] = -90 + (110) * (t[m0] - 50) / 2  # -90 → +20
    # Fase 1 (52-60 ms) — notch
    m1 = (t >= 52) & (t < 60)
    pa[m1] = 20 - 15 * (1 - np.exp(-(t[m1] - 52) / 3))
    # Fase 2 (60-250 ms) — platô
    m2 = (t >= 60) & (t < 250)
    pa[m2] = 5 - 0.02 * (t[m2] - 60)  # leve descida lenta
    # Fase 3 (250-350 ms) — repolarização
    m3 = (t >= 250) & (t < 350)
    start_v = pa[m2][-1] if np.any(m2) else 0
    pa[m3] = start_v - (start_v + 90) * (1 - np.exp(-(t[m3] - 250) / 30))
    # Fase 4 (350-400 ms)
    m4 = t >= 350
    pa[m4] = -90.0

    # --- Gerar ECG simplificado (DII) abaixo ---
    ecg_t = np.linspace(0, 400, 2000)
    ecg = np.zeros_like(ecg_t)
    # Onda P (20-50 ms)
    mp = (ecg_t >= 20) & (ecg_t < 50)
    ecg[mp] = 0.15 * np.sin(np.pi * (ecg_t[mp] - 20) / 30)
    # QRS (50-80 ms)
    mq = (ecg_t >= 50) & (ecg_t < 58)
    ecg[mq] = -0.1 * np.sin(np.pi * (ecg_t[mq] - 50) / 8)
    mr = (ecg_t >= 58) & (ecg_t < 72)
    ecg[mr] = 1.0 * np.sin(np.pi * (ecg_t[mr] - 58) / 14)
    ms = (ecg_t >= 72) & (ecg_t < 80)
    ecg[ms] = -0.2 * np.sin(np.pi * (ecg_t[ms] - 72) / 8)
    # ST (80-200 ms) — isoelétrico
    # T wave (200-310 ms)
    mt = (ecg_t >= 200) & (ecg_t < 310)
    ecg[mt] = 0.35 * np.sin(np.pi * (ecg_t[mt] - 200) / 110)

    # --- Criar subplot ---
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=[
            "Potencial de Ação — Cardiomiócito Contrátil",
            "ECG (DII) — Correlação Temporal",
        ],
        vertical_spacing=0.15,
        row_heights=[0.6, 0.4],
    )

    # Cores das fases
    phase_colors = {
        0: "rgba(231,76,60,0.25)",    # vermelho
        1: "rgba(243,156,18,0.25)",    # laranja
        2: "rgba(46,204,113,0.25)",    # verde
        3: "rgba(52,152,219,0.25)",    # azul
        4: "rgba(155,89,182,0.25)",    # roxo
    }
    phase_names = {
        0: "Fase 0: Despol. rápida (INa)",
        1: "Fase 1: Repol. precoce (Ito)",
        2: "Fase 2: Platô (ICaL vs IKr/IKs)",
        3: "Fase 3: Repolarização (IKr+IKs+IK1)",
        4: "Fase 4: Repouso (IK1)",
    }
    phase_ranges = [
        (50, 52), (52, 60), (60, 250), (250, 350), (0, 50),
    ]
    # Fase 4 pós também
    phase_ranges_post = {4: (350, 400)}

    # Adicionar faixas de fase (em ambos subplots)
    for ph, (t0, t1) in enumerate(phase_ranges):
        color = phase_colors[ph]
        opacity = 0.5 if highlight_phase == ph else 0.2
        if highlight_phase is not None and highlight_phase != ph:
            opacity = 0.08
        for row in [1, 2]:
            fig.add_vrect(
                x0=t0, x1=t1, fillcolor=color.replace("0.25", str(opacity)),
                layer="below", line_width=0, row=row, col=1,
            )
    # Fase 4 pós-repolarização
    fig.add_vrect(
        x0=350, x1=400,
        fillcolor=phase_colors[4].replace("0.25", "0.2" if highlight_phase != 4 else "0.5"),
        layer="below", line_width=0, row=1, col=1,
    )
    fig.add_vrect(
        x0=350, x1=400,
        fillcolor=phase_colors[4].replace("0.25", "0.2" if highlight_phase != 4 else "0.5"),
        layer="below", line_width=0, row=2, col=1,
    )

    # PA trace
    fig.add_trace(
        go.Scatter(x=t.tolist(), y=pa.tolist(), mode="lines",
                   line=dict(color="black", width=2.5), name="PA (mV)",
                   showlegend=False),
        row=1, col=1,
    )

    # ECG trace
    fig.add_trace(
        go.Scatter(x=ecg_t.tolist(), y=ecg.tolist(), mode="lines",
                   line=dict(color="black", width=2), name="ECG DII",
                   showlegend=False),
        row=2, col=1,
    )

    # Anotações das fases no PA
    annotations_data = [
        (51, 15, "0", "Fase 0\nINa", "red"),
        (56, 10, "1", "Fase 1\nIto", "orange"),
        (155, 8, "2", "Fase 2\nICaL↔IK", "#2ecc71"),
        (300, -45, "3", "Fase 3\nIKr+IKs", "#3498db"),
        (25, -85, "4", "Fase 4\nIK1", "#9b59b6"),
        (375, -85, "4", "Fase 4", "#9b59b6"),
    ]
    for x, y, phase, text, color in annotations_data:
        fig.add_annotation(
            x=x, y=y, text=f"<b>{text}</b>", showarrow=False,
            font=dict(size=10, color=color), row=1, col=1,
        )

    # Anotações no ECG
    ecg_labels = [
        (35, 0.22, "P"),
        (65, 1.1, "QRS"),
        (140, 0.05, "ST"),
        (255, 0.42, "T"),
        (380, 0.0, "T-P"),
    ]
    for x, y, text in ecg_labels:
        fig.add_annotation(
            x=x, y=y, text=f"<b>{text}</b>", showarrow=False,
            font=dict(size=11, color="#2c3e50"), row=2, col=1,
        )

    # Período refratário absoluto e relativo no ECG subplot
    fig.add_shape(
        type="line", x0=50, x1=270, y0=-0.35, y1=-0.35,
        line=dict(color="red", width=3), row=2, col=1,
    )
    fig.add_annotation(
        x=160, y=-0.45, text="<b>PRA (Período Refratário Absoluto)</b>",
        showarrow=False, font=dict(size=9, color="red"), row=2, col=1,
    )
    fig.add_shape(
        type="line", x0=270, x1=310, y0=-0.35, y1=-0.35,
        line=dict(color="blue", width=3, dash="dash"), row=2, col=1,
    )
    fig.add_annotation(
        x=290, y=-0.45, text="<b>PRR</b>",
        showarrow=False, font=dict(size=9, color="blue"), row=2, col=1,
    )

    fig.update_layout(
        height=650, width=850,
        paper_bgcolor="white", plot_bgcolor="#FAFAFA",
        margin=dict(l=60, r=30, t=50, b=30),
    )
    fig.update_xaxes(title_text="Tempo (ms)", row=2, col=1)
    fig.update_yaxes(title_text="mV", range=[-100, 40], row=1, col=1)
    fig.update_yaxes(title_text="mV", range=[-0.6, 1.3], row=2, col=1)

    return fig


def _create_pacemaker_ap_figure(highlight_phase: int | None = None) -> "go.Figure":
    """PA do nó sinusal (pacemaker) com fase 4 instável."""
    t = np.linspace(0, 600, 3000)  # ms, 2 ciclos
    pa = np.full_like(t, -60.0)

    def one_cycle(t_arr, t_start):
        """Gera um ciclo do PA do nó sinusal."""
        out = np.full_like(t_arr, np.nan)
        # Fase 4 — despolarização diastólica lenta (0-200 ms)
        m4 = (t_arr >= t_start) & (t_arr < t_start + 200)
        out[m4] = -60 + 20 * (1 - np.exp(-(t_arr[m4] - t_start) / 120))
        # Fase 0 — upstroke lento (200-230 ms, dependente de Ca²+)
        m0 = (t_arr >= t_start + 200) & (t_arr < t_start + 230)
        v_start = -60 + 20 * (1 - np.exp(-200 / 120))
        out[m0] = v_start + (10 - v_start) * (t_arr[m0] - (t_start + 200)) / 30
        # Fase 3 — repolarização (230-340 ms)
        m3 = (t_arr >= t_start + 230) & (t_arr < t_start + 340)
        out[m3] = 10 - 70 * (1 - np.exp(-(t_arr[m3] - (t_start + 230)) / 40))
        return out

    cycle1 = one_cycle(t, 0)
    cycle2 = one_cycle(t, 340)
    for i in range(len(t)):
        if not np.isnan(cycle1[i]):
            pa[i] = cycle1[i]
        if not np.isnan(cycle2[i]):
            pa[i] = cycle2[i]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=t.tolist(), y=pa.tolist(), mode="lines",
        line=dict(color="black", width=2.5), name="PA nó sinusal",
    ))

    # Fases do primeiro ciclo
    phase_info = [
        (0, 200, "Fase 4\n(If + ICaT)\nDesp. diastólica", "#9b59b6", -70),
        (200, 230, "Fase 0\n(ICaL)\nUpstroke lento", "red", -25),
        (230, 340, "Fase 3\n(IKr+IKs)\nRepolarização", "#3498db", -25),
    ]
    for t0, t1, label, color, y_pos in phase_info:
        fig.add_vrect(x0=t0, x1=t1, fillcolor=color, opacity=0.15,
                      layer="below", line_width=0)
        fig.add_annotation(
            x=(t0 + t1) / 2, y=y_pos, text=f"<b>{label}</b>",
            showarrow=False, font=dict(size=9, color=color),
        )

    # Correntes
    fig.add_annotation(
        x=100, y=-55, text="If: 'funny current'\nHCN4 (Na+/K+ in)",
        showarrow=True, arrowhead=2, ax=0, ay=-40,
        font=dict(size=8, color="#8e44ad"),
    )
    fig.add_annotation(
        x=215, y=-30, text="ICa,L: Ca²+\ntipo L entra",
        showarrow=True, arrowhead=2, ax=40, ay=-30,
        font=dict(size=8, color="#c0392b"),
    )

    # Limiar
    fig.add_hline(y=-40, line_dash="dash", line_color="gray",
                  annotation_text="Limiar (~-40 mV)", annotation_position="top left")

    fig.update_layout(
        title="Potencial de Ação — Nó Sinusal (Pacemaker)",
        xaxis_title="Tempo (ms)",
        yaxis_title="mV",
        yaxis_range=[-75, 20],
        height=450, width=750,
        paper_bgcolor="white", plot_bgcolor="#FAFAFA",
    )
    return fig


def create_refractory_period_figure() -> "go.Figure":
    """Cria figura mostrando PRA e PRR sobre o PA e ECG."""
    return _create_contractile_ap_figure(highlight_phase=None)


def create_phase_comparison_figure() -> "go.Figure":
    """Sobreposição de PA contrátil vs pacemaker para comparação."""
    if not HAS_PLOTLY:
        raise ImportError("Plotly necessário")

    t_c = np.linspace(0, 400, 2000)
    pa_c = np.full_like(t_c, -90.0)
    # Contractile PA (simplified)
    m0 = (t_c >= 50) & (t_c < 52)
    pa_c[m0] = -90 + 110 * (t_c[m0] - 50) / 2
    m1 = (t_c >= 52) & (t_c < 60)
    pa_c[m1] = 20 - 15 * (1 - np.exp(-(t_c[m1] - 52) / 3))
    m2 = (t_c >= 60) & (t_c < 250)
    pa_c[m2] = 5 - 0.02 * (t_c[m2] - 60)
    m3 = (t_c >= 250) & (t_c < 350)
    sv = pa_c[m2][-1] if np.any(m2) else 0
    pa_c[m3] = sv - (sv + 90) * (1 - np.exp(-(t_c[m3] - 250) / 30))
    m4 = t_c >= 350
    pa_c[m4] = -90.0

    # Pacemaker PA (simplified)
    t_p = np.linspace(0, 400, 2000)
    pa_p = np.full_like(t_p, -60.0)
    m4p = (t_p >= 0) & (t_p < 200)
    pa_p[m4p] = -60 + 20 * (1 - np.exp(-(t_p[m4p]) / 120))
    m0p = (t_p >= 200) & (t_p < 230)
    vs = -60 + 20 * (1 - np.exp(-200 / 120))
    pa_p[m0p] = vs + (10 - vs) * (t_p[m0p] - 200) / 30
    m3p = (t_p >= 230) & (t_p < 340)
    pa_p[m3p] = 10 - 70 * (1 - np.exp(-(t_p[m3p] - 230) / 40))
    m4p2 = t_p >= 340
    pa_p[m4p2] = -60 + 20 * (1 - np.exp(-(t_p[m4p2] - 340) / 120))

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=t_c.tolist(), y=pa_c.tolist(), mode="lines",
        line=dict(color="#2c3e50", width=2.5),
        name="Cardiomiócito contrátil",
    ))
    fig.add_trace(go.Scatter(
        x=t_p.tolist(), y=pa_p.tolist(), mode="lines",
        line=dict(color="#e74c3c", width=2.5, dash="dash"),
        name="Nó sinusal (pacemaker)",
    ))

    # Anotações
    fig.add_annotation(x=155, y=5, text="Platô (fase 2)\nExclusivo do contrátil",
                       showarrow=True, ax=60, ay=-40, font=dict(size=9))
    fig.add_annotation(x=100, y=-52, text="Fase 4 instável\n(automatismo)",
                       showarrow=True, ax=-50, ay=30, font=dict(size=9, color="#e74c3c"))

    fig.update_layout(
        title="Comparação: PA Contrátil vs Pacemaker (Nó Sinusal)",
        xaxis_title="Tempo (ms)", yaxis_title="mV",
        yaxis_range=[-100, 30],
        height=450, width=750,
        paper_bgcolor="white", plot_bgcolor="#FAFAFA",
        legend=dict(x=0.6, y=0.95),
    )
    return fig

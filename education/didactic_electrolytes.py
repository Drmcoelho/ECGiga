"""
education/didactic_electrolytes.py — Mega-analogia clínico-eletrolítica-eletrocardiográfica

Conteúdo educacional completo em português usando a analogia das câmeras
para explicar como distúrbios eletrolíticos alteram o ECG. Inclui:
- Hipercalemia (K+ alto): 4 estágios progressivos
- Hipocalemia (K+ baixo): achatamento de T, onda U, fusão T-U
- Hipercalcemia (Ca²+ alto): QT curto
- Hipocalcemia (Ca²+ baixo): QT longo (ST prolongado)
- Hipomagnesemia (Mg²+ baixo): QT longo, Torsades
- Tabela comparativa e fluxograma diagnóstico
"""

from __future__ import annotations

# =====================================================================
# INTRO — Por que eletrólitos mudam o ECG?
# =====================================================================

ELECTROLYTE_INTRO: str = """\
ELETRÓLITOS E ECG: POR QUE ÍONS MUDAM O FILME DO CORAÇÃO

═══════════════════════════════════════════════════════════════════════
O POTENCIAL DE AÇÃO COMO "ROTEIRO" DO FILME CARDÍACO
═══════════════════════════════════════════════════════════════════════

Cada célula cardíaca segue um "roteiro" elétrico chamado potencial de
ação. Esse roteiro tem 5 fases:

  Fase 0 — Despolarização rápida (entrada de Na+)
  Fase 1 — Repolarização precoce breve (saída de K+)
  Fase 2 — Plateau (entrada de Ca²+ equilibra saída de K+)
  Fase 3 — Repolarização (saída massiva de K+)
  Fase 4 — Repouso (bomba Na+/K+ restaura o equilíbrio)

O ECG é o "filme" que as câmeras (derivações) fazem desse roteiro
elétrico. Quando os íons mudam de concentração no sangue, eles alteram
diretamente as fases do potencial de ação — e as câmeras registram
essa alteração como mudanças nas ondas, segmentos e intervalos.

Pense assim: se o potencial de ação é o ROTEIRO, os eletrólitos são os
DIRETORES. Cada íon controla uma fase diferente do roteiro. Se o diretor
muda as instruções, os atores (ondas P, QRS, T) mudam a performance.

═══════════════════════════════════════════════════════════════════════
QUEM CONTROLA O QUÊ?
═══════════════════════════════════════════════════════════════════════

POTÁSSIO (K+) — O DIRETOR DA REPOLARIZAÇÃO
  → Controla a fase 3 (repolarização) e o potencial de repouso (fase 4)
  → K+ alto → repolarização acelerada → T apiculada, QRS alargado
  → K+ baixo → repolarização lenta → T achatada, onda U proeminente
  → É o eletrólito que MAIS muda o ECG. O "diretor principal".

CÁLCIO (Ca²+) — O DIRETOR DO PLATEAU
  → Controla a fase 2 (plateau — segmento ST)
  → Ca²+ alto → plateau mais curto → QT curto (ST encurtado)
  → Ca²+ baixo → plateau mais longo → QT longo (ST prolongado)
  → Só mexe no QT. Não mexe na morfologia das ondas.

MAGNÉSIO (Mg²+) — O CODIRETOR SILENCIOSO
  → Estabiliza canais de K+ e Ca²+
  → Mg²+ baixo → instabilidade elétrica → QT longo, Torsades de Pointes
  → Quase sempre acompanha hipocalemia (codiretores trabalham juntos)
  → Tratar Mg²+ é essencial para corrigir K+ refratário

SÓDIO (Na+) — O DIRETOR DA ENTRADA EM CENA
  → Controla a fase 0 (despolarização rápida — upstroke do QRS)
  → Na+ muito baixo → QRS levemente alargado
  → Efeito no ECG é geralmente sutil comparado a K+ e Ca²+
  → Raramente o "vilão" principal das alterações eletrocardiográficas

═══════════════════════════════════════════════════════════════════════
REGRA DE OURO PARA MEMORIZAR
═══════════════════════════════════════════════════════════════════════

"K+ mexe nas ONDAS. Ca²+ mexe no INTERVALO. Mg²+ mexe na ESTABILIDADE."

K+ alto = T pontuda, QRS largo (ondas mudam de forma)
K+ baixo = T achatada, U aparece (ondas somem/surgem)
Ca²+ alto = QT curto (intervalo encurta)
Ca²+ baixo = QT longo (intervalo estica)
Mg²+ baixo = QT longo + arritmias (o sistema fica instável)
"""

# =====================================================================
# HIPERCALEMIA — Os 4 estágios filmados pelas câmeras
# =====================================================================

HYPERKALEMIA_EXPLAINED: str = """\
HIPERCALEMIA: O POTÁSSIO SOBE E O ECG GRITA — 4 ESTÁGIOS DE ALARME

A hipercalemia é a emergência eletrolítica mais perigosa. O ECG é muitas
vezes mais rápido que o laboratório para detectá-la. As câmeras filmam
uma deterioração progressiva que, se não tratada, termina em parada.

═══════════════════════════════════════════════════════════════════════
POR QUE K+ ALTO MUDA O ECG?
═══════════════════════════════════════════════════════════════════════

O potencial de repouso da célula cardíaca depende do gradiente de K+
entre dentro e fora da célula. Normalmente, K+ é ~150 mEq/L dentro e
~4 mEq/L fora. Esse gradiente mantém o potencial de repouso em ~-90 mV.

Quando o K+ sérico sobe:
→ O gradiente diminui
→ O potencial de repouso fica menos negativo (ex.: -80 mV, -70 mV)
→ A célula fica "mais perto de disparar" (hiperexcitável no início)
→ Mas rapidamente os canais de Na+ inativam (fase 0 fica lenta)
→ A repolarização (fase 3) acelera porque a condutância de K+ aumenta

É como se o volume do roteiro fosse aumentando progressivamente até
distorcer o som e, no final, estourar os alto-falantes.

═══════════════════════════════════════════════════════════════════════
ESTÁGIO 1 — LEVE (K+ 5.5–6.5 mEq/L): T APICULADAS
═══════════════════════════════════════════════════════════════════════

O que acontece na célula:
  → A fase 3 (repolarização) acelera
  → O gradiente de K+ ainda permite despolarização relativamente normal
  → A repolarização é mais rápida e mais intensa

O que a câmera vê:
  → A onda T fica ALTA, ESTREITA e SIMÉTRICA — "apiculada"
  → Em forma de barraca de camping (tent-shaped T)
  → O QTc pode encurtar ligeiramente
  → QRS e PR ainda normais

Analogia: o ator da repolarização (onda T), que normalmente caminha
devagar pela cena, agora CORRE na direção da câmera — a câmera registra
uma imagem mais alta e mais estreita (T apiculada). É como um sprint
em vez de uma caminhada tranquila.

Derivações mais afetadas: V2-V4 (precordiais anteriores) e DII
→ As câmeras mais perto do VE veem a repolarização acelerada primeiro

⚠ ARMADILHA: T apiculada pode ser normal em jovens vagotônicos!
Diferenciar: T da hipercalemia é SIMÉTRICA e de BASE ESTREITA.
T normal de jovem é assimétrica e de base mais larga.

═══════════════════════════════════════════════════════════════════════
ESTÁGIO 2 — MODERADO (K+ 6.5–7.5 mEq/L): PR ↑, P SOME, QRS ALARGA
═══════════════════════════════════════════════════════════════════════

O que acontece na célula:
  → O potencial de repouso está agora ~-75 mV
  → Os canais de Na+ começam a inativar → fase 0 fica mais lenta
  → A condução pelo nó AV e pelos feixes diminui
  → Os átrios, com menos massa, são mais sensíveis ao K+

O que a câmera vê:
  → PR prolonga (> 200 ms) — o "porteiro" AV demora mais
  → A onda P fica achatada e depois DESAPARECE — os átrios "silenciam"
  → O QRS começa a alargar (> 120 ms) — a despolarização ventricular
    fica em "câmera lenta"
  → T continua apiculada

Analogia: o diretor (K+) está gritando cada vez mais alto. O porteiro
(nó AV) fica confuso e demora a abrir a porta (PR longo). Os atores
atriais (onda P) ficam tão atordoados que param de atuar (P desaparece).
Os atores ventriculares (QRS) ainda funcionam mas estão em câmera lenta
(QRS alarga).

A câmera que filmava a onda P (ex.: DII, V1) agora registra uma linha
quase reta onde antes havia P — o ator atrial saiu de cena.

═══════════════════════════════════════════════════════════════════════
ESTÁGIO 3 — GRAVE (K+ 7.5–8.5 mEq/L): ONDA SENOIDAL
═══════════════════════════════════════════════════════════════════════

O que acontece na célula:
  → Potencial de repouso ~-65 mV — a maioria dos canais de Na+ inativou
  → A despolarização agora é tão lenta que o QRS "funde" com o ST e a T
  → A distinção entre despolarização e repolarização se perde

O que a câmera vê:
  → QRS > 160 ms (muito largo e bizarro)
  → Sem onda P
  → O QRS largo se funde com a T apiculada → padrão sinusoidal
  → O traçado parece uma onda senoidal suave → SINE WAVE
  → A câmera não consegue mais distinguir "quem é quem" — QRS, ST e T
    viraram uma massa única

Analogia: o diretor enlouquecido (K+ altíssimo) bagunçou tanto o
roteiro que os atores (ondas) se confundem e se fundem em um único
movimento ondulante. A câmera registra uma "onda do mar" — subindo e
descendo sem distinção clara entre personagens. É o padrão sine wave.

EMERGÊNCIA: este padrão precede FV ou assistolia por minutos!
→ Gluconato de cálcio IV IMEDIATAMENTE (estabiliza membranas)
→ Insulina + glicose (shift de K+ para dentro da célula)
→ Bicarbonato se acidose
→ Diálise de emergência

═══════════════════════════════════════════════════════════════════════
ESTÁGIO 4 — CRÍTICO (K+ > 8.5 mEq/L): PARADA IMINENTE
═══════════════════════════════════════════════════════════════════════

O que acontece na célula:
  → O gradiente de K+ é tão pequeno que as células não conseguem
    gerar potencial de ação adequado
  → O coração perde a capacidade de conduzir de forma organizada

O que a câmera vê:
  → Bradicardia extrema → ritmo idioventricular
  → Sine wave desacelerando
  → Pode degenerar para FV (fibrilação ventricular)
  → Ou simplesmente parar → ASSISTOLIA

Analogia: o diretor destruiu o set de filmagem. Os atores param.
As câmeras registram... nada. Silêncio. Linha reta. Parada.

═══════════════════════════════════════════════════════════════════════
RESUMO VISUAL DA PROGRESSÃO
═══════════════════════════════════════════════════════════════════════

K+ normal → ECG normal
  ↓ K+ sobe
K+ 5.5-6.5 → T apiculadas (repolarização acelerada)
  ↓
K+ 6.5-7.5 → PR ↑ + P some + QRS alarga (condução lenta)
  ↓
K+ 7.5-8.5 → Sine wave (tudo se funde)
  ↓
K+ > 8.5 → FV ou assistolia (parada!)

Cada estágio é a câmera filmando uma degradação progressiva do
"roteiro" elétrico — do sprint inicial da T até o colapso total.
"""

# =====================================================================
# HIPOCALEMIA — Quando o K+ cai e a onda U entra em cena
# =====================================================================

HYPOKALEMIA_EXPLAINED: str = """\
HIPOCALEMIA: O POTÁSSIO CAI E UM NOVO ATOR APARECE — A ONDA U

═══════════════════════════════════════════════════════════════════════
POR QUE K+ BAIXO MUDA O ECG?
═══════════════════════════════════════════════════════════════════════

Quando o K+ sérico cai:
→ O gradiente de K+ entre dentro e fora da célula AUMENTA
→ O potencial de repouso fica MAIS negativo (hiperpolarizado: ~-95 mV)
→ A fase 3 (repolarização) fica mais LENTA — a condutância de K+ diminui
→ A repolarização demora mais → o potencial de ação se prolonga
→ Correntes tardias (IKs, IKr) são mais afetadas → heterogeneidade

É o oposto da hipercalemia: em vez de a repolarização correr, ela
ARRASTA. E aparecem novos "atores" no palco — como a onda U.

═══════════════════════════════════════════════════════════════════════
AS 5 ALTERAÇÕES DA HIPOCALEMIA (em ordem de aparecimento)
═══════════════════════════════════════════════════════════════════════

1. ACHATAMENTO DA ONDA T
   → A repolarização fica lenta e espalhada
   → A câmera vê a onda T diminuir de amplitude — como um ator que
     caminha cada vez mais devagar e com menos energia
   → T pode ficar quase plana

2. INFRADESNIVELAMENTO DE ST
   → A repolarização alterada distorce o segmento ST
   → A câmera registra o ST descendo suavemente abaixo da linha de base
   → Parece strain, mas é metabólico

3. APARECIMENTO DA ONDA U
   → A marca registrada da hipocalemia!
   → A onda U é uma deflexão positiva que aparece DEPOIS da onda T
   → Mecanismo provável: repolarização tardia das fibras de Purkinje
     ou pós-potenciais mecanoelétricos das paredes ventriculares
   → A câmera registra um "ator extra" entrando em cena — a onda U é
     um personagem que normalmente fica nos bastidores mas que, com
     K+ baixo, ganha destaque e sobe ao palco
   → Mais visível em V2-V3 (câmeras anteriores)

4. FUSÃO T-U (PROLONGAMENTO APARENTE DO QT)
   → Quando o K+ cai mais, a onda U cresce tanto que se FUNDE com a T
   → A câmera registra uma "onda dupla" — parece que o QT prolongou,
     mas na verdade é a fusão de T+U
   → ARMADILHA: medir o QT nesse contexto é traiçoeiro — o "fim da T"
     é na verdade o "fim da U". O QT aparente pode ser > 500 ms
   → Risco de Torsades de Pointes!

5. ALTERAÇÕES TARDIAS (K+ < 2.5 mEq/L)
   → QRS pode alargar levemente
   → Onda P pode ficar proeminente (hiperexcitabilidade atrial)
   → Arritmias: extrassístoles, TV, Torsades de Pointes
   → O "elenco" está em caos — atores entrando fora de hora

═══════════════════════════════════════════════════════════════════════
COMO DIFERENCIAR ONDA U DE T BIFÁSICA
═══════════════════════════════════════════════════════════════════════

  → Onda U: aparece DEPOIS de a T terminar. Há um vale (isoelétrico)
    entre T e U. É um ator diferente entrando em cena.
  → T bifásica: a própria T tem dois componentes (positivo-negativo ou
    vice-versa). É o MESMO ator fazendo dois movimentos seguidos.

Na hipocalemia, se você vê "T-vale-U", é onda U. Se vê "T fundindo
suavemente com U" (K+ muito baixo), a distinção se perde — é fusão T-U.

═══════════════════════════════════════════════════════════════════════
RESUMO VISUAL
═══════════════════════════════════════════════════════════════════════

K+ normal: T normal, sem U visível
  ↓ K+ cai
K+ 3.0-3.5: T achatada, ST leve infra
  ↓
K+ 2.5-3.0: T achatada + onda U proeminente em V2-V3
  ↓
K+ < 2.5: Fusão T-U (QT aparente longo), risco de Torsades
  ↓
K+ < 2.0: QRS alarga, arritmias, risco de parada

Hipocalemia = o potássio sai de cena e a onda U assume o protagonismo.
"""

# =====================================================================
# CÁLCIO — O diretor do plateau (QT)
# =====================================================================

CALCIUM_EXPLAINED: str = """\
CÁLCIO: O DIRETOR DO PLATEAU — QT CURTO OU QT LONGO

═══════════════════════════════════════════════════════════════════════
POR QUE Ca²+ MUDA O QT?
═══════════════════════════════════════════════════════════════════════

O cálcio controla a DURAÇÃO da fase 2 (plateau) do potencial de ação.
Durante o plateau, o Ca²+ entra na célula pelos canais tipo L e mantém
o potencial "suspenso" em ~0 mV. O equilíbrio entre a entrada de Ca²+
e a saída de K+ define quanto tempo o plateau dura.

No ECG, a duração do plateau corresponde principalmente ao SEGMENTO ST
(o trecho entre o QRS e a onda T). Alterar o Ca²+ muda o ST:

  Ca²+ alto → plateau mais curto → ST encurta → QT curto
  Ca²+ baixo → plateau mais longo → ST estica → QT longo

É como se o diretor (Ca²+) controlasse um dimmer de luz. Mais Ca²+
= luz intensa que queima rápido (plateau curto). Menos Ca²+ = luz
fraca que demora a apagar (plateau longo).

═══════════════════════════════════════════════════════════════════════
HIPERCALCEMIA (Ca²+ > 10.5 mg/dL) — QT CURTO
═══════════════════════════════════════════════════════════════════════

O que acontece:
  → A fase 2 (plateau) encurta porque o excesso de Ca²+ inativa os
    canais tipo L mais rapidamente
  → A repolarização (fase 3) começa mais cedo
  → O QT diminui — principalmente às custas do segmento ST

O que a câmera vê:
  → QTc < 360 ms (ou até < 300 ms nos casos graves)
  → O segmento ST é curtíssimo — quase desaparece
  → A onda T começa "grudada" no QRS
  → A câmera vê: QRS → imediatamente T, quase sem intervalo
  → Analogia: a pausa dramática entre os atos (plateau/ST) foi
    eliminada. Os atores saem de um ato e entram no próximo sem
    intervalo. A cena fica acelerada.

Causa mais comum: hiperparatireoidismo, malignidade, intoxicação
por vitamina D.

Na hipercalcemia grave:
  → Pode haver alargamento de QRS
  → Ondas J (Osborn) — semelhantes às da hipotermia
  → Arritmias (raro, mas possível)

═══════════════════════════════════════════════════════════════════════
HIPOCALCEMIA (Ca²+ < 8.5 mg/dL) — QT LONGO
═══════════════════════════════════════════════════════════════════════

O que acontece:
  → A fase 2 (plateau) prolonga porque a falta de Ca²+ não consegue
    inativar os canais tipo L no tempo normal
  → A repolarização (fase 3) atrasa
  → O QT aumenta — principalmente às custas do segmento ST

O que a câmera vê:
  → QTc > 480 ms (pode chegar a > 600 ms!)
  → O segmento ST fica alongado — há uma pausa longa entre QRS e T
  → A onda T em si mantém a morfologia relativamente normal
  → Isso é DIFERENTE do QT longo por K+ (que altera a T) ou por
    medicamentos (que alteram a T e podem causar T bizarra)

Analogia: o diretor (Ca²+) pediu uma pausa dramática longa entre os
atos. O ST se estica — a câmera filma um "silêncio" prolongado entre
o QRS e a T. Os atores (ondas) estão normais, mas a pausa é enorme.

Diferenciação crucial:
  → QT longo por HIPOCALCEMIA: ST longo + T normal
  → QT longo por HIPOCALEMIA: ST pode ter infra + T achatada + U
  → QT longo por MEDICAMENTOS: T pode ser bizarra, bífida, entalhada
  → QT longo CONGÊNITO: T pode ser tardia, bífida ou de base larga

═══════════════════════════════════════════════════════════════════════
RESUMO DO CÁLCIO
═══════════════════════════════════════════════════════════════════════

Ca²+ ALTO → Plateau curto → ST quase ausente → QT curto
  A câmera vê QRS e T quase grudados, sem pausa.

Ca²+ BAIXO → Plateau longo → ST prolongado → QT longo
  A câmera vê uma pausa longa entre QRS e T. T é normal.

PISTA: se o QT é longo mas a ONDA T parece normal (só o ST é longo),
pense em hipocalcemia. Se a T está alterada, pense em K+ ou drogas.
"""

# =====================================================================
# MAGNÉSIO — O codiretor silencioso
# =====================================================================

MAGNESIUM_EXPLAINED: str = """\
MAGNÉSIO: O CODIRETOR SILENCIOSO QUE PODE MATAR

═══════════════════════════════════════════════════════════════════════
POR QUE O Mg²+ IMPORTA?
═══════════════════════════════════════════════════════════════════════

O magnésio não tem um "papel principal" no ECG como o K+ ou o Ca²+.
Ele é mais um codiretor: estabiliza os canais iônicos, especialmente
os canais de K+ (HERG/IKr) e os canais de Ca²+ tipo L.

Quando o Mg²+ cai:
→ Os canais de K+ ficam instáveis → repolarização heterogênea
→ Há prolongamento do QT → risco de Torsades de Pointes
→ A bomba Na+/K+-ATPase funciona mal → difícil corrigir K+
→ Liberação excessiva de Ca²+ pelo retículo → pós-potenciais

É por isso que o mantra clínico é:
"HIPOCALEMIA REFRATÁRIA? DOSA O MAGNÉSIO!"
Sem corrigir o Mg²+, o K+ não normaliza.

═══════════════════════════════════════════════════════════════════════
ALTERAÇÕES NO ECG
═══════════════════════════════════════════════════════════════════════

As alterações do Mg²+ baixo são muito parecidas com as do K+ baixo:
→ QT prolongado
→ Achatamento de onda T
→ Onda U pode aparecer
→ Infradesnivelamento de ST
→ Arritmias: extrassístoles, TV polimórfica, Torsades

A câmera não consegue distinguir diretamente entre hipocalemia e
hipomagnesemia — o filme é quase idêntico. A diferença é clínica:
  → Se o K+ está normal mas o ECG parece de hipocalemia → dosar Mg²+
  → Se a hipocalemia não corrige com reposição de K+ → corrigir Mg²+
  → Se há Torsades de Pointes → sulfato de Mg²+ IV é o tratamento
    de primeira linha, INDEPENDENTE do nível sérico

Analogia: o Mg²+ é como o técnico de som nos bastidores. Quando ele
falta, a acústica do estúdio deteriora — ecos, distorções, feedback
(arritmias). Os atores (ondas) podem até estar em cena, mas o
resultado final é caótico. E o pior: mesmo reposicionando os atores
(K+), sem o técnico de som (Mg²+) o problema persiste.

═══════════════════════════════════════════════════════════════════════
TORSADES DE POINTES — O CAOS FINAL
═══════════════════════════════════════════════════════════════════════

Torsades de Pointes (TdP) é uma taquicardia ventricular polimórfica
que ocorre no contexto de QT longo. O nome ("torção das pontas") descreve
o que a câmera vê: o eixo do QRS gira progressivamente, fazendo os
complexos parecerem "torcer" ao redor da linha de base.

Mecanismo: a repolarização prolongada e heterogênea cria "janelas"
em que partes do miocárdio já repolarizaram enquanto outras ainda estão
em plateau. Isso permite reentrada funcional.

A câmera registra:
→ QRS que vai crescendo de amplitude → pico → vai diminuindo → cresce
  de novo (padrão "fuso" ou spindle)
→ A cada ciclo, o eixo gira — como se a câmera estivesse em um
  carrossel olhando o coração girar
→ Frequência: 150-300 bpm
→ Pode terminar espontaneamente ou degenerar em FV

Causas principais de TdP:
1. Hipocalemia + Hipomagnesemia (a dupla mais perigosa)
2. Medicamentos que prolongam QT (antiarrítmicos, antibióticos,
   antipsicóticos, antidepressivos)
3. QT longo congênito
4. Hipocalcemia grave
"""

# =====================================================================
# TABELA COMPARATIVA — Resumo prático
# =====================================================================

ELECTROLYTE_COMPARISON_TABLE: str = """\
═══════════════════════════════════════════════════════════════════════
TABELA COMPARATIVA: ELETRÓLITOS × ECG
═══════════════════════════════════════════════════════════════════════

┌───────────────┬───────────────────┬──────────────────────────────────┐
│ DISTÚRBIO     │ FASE AFETADA      │ O QUE A CÂMERA VÊ               │
├───────────────┼───────────────────┼──────────────────────────────────┤
│ K+ ALTO       │ Fase 3 (repol.)   │ T apiculada → P some →           │
│ (Hipercalemia)│ + Fase 4 (repouso)│ QRS alarga → sine wave → parada │
├───────────────┼───────────────────┼──────────────────────────────────┤
│ K+ BAIXO      │ Fase 3 (repol.)   │ T achata → ST infra →            │
│ (Hipocalemia) │                   │ onda U → fusão T-U → arritmias   │
├───────────────┼───────────────────┼──────────────────────────────────┤
│ Ca²+ ALTO     │ Fase 2 (plateau)  │ ST encurta → QT curto            │
│ (Hipercalcemia)│                  │ (T "gruda" no QRS)               │
├───────────────┼───────────────────┼──────────────────────────────────┤
│ Ca²+ BAIXO    │ Fase 2 (plateau)  │ ST prolonga → QT longo           │
│ (Hipocalcemia)│                   │ (T mantém morfologia normal)     │
├───────────────┼───────────────────┼──────────────────────────────────┤
│ Mg²+ BAIXO    │ Canais K+/Ca²+    │ Similar a K+ baixo + QT longo    │
│ (Hipomagnese.)│ (estabilidade)    │ + risco alto de Torsades         │
└───────────────┴───────────────────┴──────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════
FLUXOGRAMA DIAGNÓSTICO RÁPIDO
═══════════════════════════════════════════════════════════════════════

ECG alterado → suspeita eletrolítica?

  ┌─ T apiculada + simétrica?
  │    SIM → Dosar K+ (provável hipercalemia)
  │          Se QRS largo → EMERGÊNCIA! Gluconato de Ca²+ IV
  │
  ├─ T achatada + onda U?
  │    SIM → Dosar K+ e Mg²+ (provável hipocalemia ± hipoMg)
  │          Se fusão T-U → risco de Torsades
  │
  ├─ QT curto (QTc < 360 ms)?
  │    SIM → Dosar Ca²+ (provável hipercalcemia)
  │
  ├─ QT longo com ST prolongado + T normal?
  │    SIM → Dosar Ca²+ (provável hipocalcemia)
  │
  └─ QT longo com T alterada?
       → Verificar medicamentos, K+, Mg²+, Ca²+
       → Se K+ e Ca²+ normais → dosar Mg²+
"""

# =====================================================================
# DICAS CLÍNICAS INTEGRADAS
# =====================================================================

CLINICAL_PEARLS: str = """\
═══════════════════════════════════════════════════════════════════════
PÉROLAS CLÍNICAS: ELETRÓLITOS E ECG
═══════════════════════════════════════════════════════════════════════

1. "O ECG é o EXAME DE POTÁSSIO mais rápido que existe."
   → Em emergência, o ECG mostra hipercalemia ANTES do laboratório.
   → Se vê T apiculada + QRS largo → trate ANTES do resultado do K+.

2. "Hipocalemia + Hipomagnesemia = a dupla mais arritmogênica."
   → Quase sempre coexistem (diuréticos, diarreia, vômitos).
   → Tratar AMBOS simultaneamente. Mg²+ primeiro se possível.

3. "QT longo com T normal = pense em Ca²+. QT longo com T estranha
   = pense em K+, Mg²+ ou drogas."
   → Hipocalcemia prolonga o ST mas preserva a T.
   → Hipocalemia/drogas alteram a morfologia da T.

4. "Na dúvida, peça o 'painel eletrolítico + ECG'."
   → K+, Ca²+ iônico, Mg²+, Na+, fosfato.
   → O ECG complementa o laboratório e vice-versa.

5. "Gluconato de cálcio é o antídoto da hipercalemia no ECG."
   → Não corrige o K+! Apenas estabiliza a membrana cardíaca.
   → Funciona em 1-3 minutos. Dura 30-60 minutos.
   → O Ca²+ IV age como um "escudo" na membrana enquanto você
     trata a causa (insulina+glicose, resinas, diálise).

6. "Sulfato de Mg²+ IV é o tratamento de Torsades de Pointes."
   → Mesmo se o Mg²+ sérico estiver normal!
   → 1-2 g IV em 15 min → estabiliza os canais e quebra o circuito.

7. "Na hipocalemia, corrigir K+ oral é lento. IV é perigoso."
   → Máximo 10-20 mEq/h IV em veia periférica.
   → Sempre monitorar ECG durante reposição IV.
   → Se K+ < 2.5 → reposição IV + monitorização contínua.

8. "Acidose metabólica + hipercalemia = combinação letal."
   → A acidose joga K+ para fora da célula (shift transcelular).
   → Corrigir a acidose ajuda a baixar o K+.
   → Bicarbonato IV: trata acidose + ajuda no shift de K+.
"""

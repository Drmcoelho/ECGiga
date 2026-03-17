# Intervalos e Segmentos — PR, QRS, QT

## Introdução

Os intervalos e segmentos do ECG fornecem informações cruciais sobre a **velocidade de condução** elétrica e o **estado funcional** do miocárdio. Alterações nesses parâmetros podem indicar bloqueios, distúrbios eletrolíticos, efeitos de drogas e risco de arritmias fatais.

> **Diferença fundamental:**
> - **Intervalo** = inclui ondas + segmentos (ex.: intervalo PR = onda P + segmento PR)
> - **Segmento** = linha entre duas ondas, sem incluí-las (ex.: segmento ST = do final do QRS ao início da onda T)

---

## Intervalo PR

### Definição

O intervalo PR é medido do **início da onda P** até o **início do complexo QRS**. Representa o tempo total de condução do impulso desde a despolarização atrial até o início da despolarização ventricular.

### Valores normais

- **Normal:** 120–200 ms (3 a 5 quadradinhos)
- Medido preferencialmente em **DII** (onde a onda P geralmente é mais visível)

### PR Prolongado (> 200 ms)

Indica **retardo na condução AV** — bloqueio atrioventricular de 1° grau.

**Causas:**
- Aumento do tônus vagal (atletas, sono)
- Medicamentos: betabloqueadores, bloqueadores de canal de cálcio, digoxina, amiodarona
- Miocardite, febre reumática
- Cardiopatia isquêmica
- Doença degenerativa do sistema de condução (fibrose)
- Hipercalemia

> **Pérola clínica:** BAV de 1° grau isolado geralmente é benigno. Torna-se clinicamente significativo quando associado a sintomas ou evolui para graus mais avançados de bloqueio.

### PR Curto (< 120 ms)

**Causas:**
- **Pré-excitação (Wolff-Parkinson-White):** PR curto + onda delta + QRS alargado
- Ritmo juncional (onda P retrógrada próxima ou dentro do QRS)
- Síndrome de Lown-Ganong-Levine (PR curto sem onda delta — conceito controverso)
- Variante normal em crianças

> **Atenção:** PR curto com onda delta indica via acessória (WPW) e risco de arritmias, incluindo fibrilação atrial com condução rápida — potencialmente fatal.

---

## Complexo QRS

### Definição

O complexo QRS representa a **despolarização ventricular**. Sua duração é medida do início da primeira deflexão (Q ou R) até o final da última deflexão (R ou S).

### Valores normais

- **Normal:** < 120 ms (< 3 quadrados grandes)
- **Limítrofe:** 100–120 ms
- **Alargado:** >= 120 ms

### QRS Estreito (< 120 ms)

Indica condução ventricular **normal** através do sistema His-Purkinje. O impulso é conduzido rapidamente por fibras especializadas, ativando ambos os ventrículos de forma quase simultânea.

### QRS Alargado (>= 120 ms)

O alargamento do QRS indica que a despolarização ventricular está **anormalmente lenta**. Causas principais:

| Duração do QRS | Possíveis causas |
|:--------------|:----------------|
| **120–149 ms** | Bloqueio de ramo incompleto, distúrbio inespecífico de condução |
| **>= 120 ms com morfologia típica** | Bloqueio de ramo direito (BRD) ou esquerdo (BRE) |
| **>= 140 ms** | BRE, ritmo de marca-passo, pré-excitação, ritmo ventricular |
| **> 160 ms** | Hipercalemia grave, intoxicação por antidepressivo tricíclico |

### Bloqueio de Ramo Direito (BRD)

- QRS >= 120 ms
- Padrão **rsR'** (orelhas de coelho) em **V1**
- Onda S empastada em **DI** e **V6**

> **Mnemônico — "MaRRoW":** Em V1 vemos M (rsR'), em V6 vemos W (qRS com S larga). **M**arrom = M em V1 (Ramo direito).

### Bloqueio de Ramo Esquerdo (BRE)

- QRS >= 120 ms
- Onda R alargada e entalhada em **DI**, **aVL** e **V5-V6**
- Padrão QS ou rS em **V1**
- Ausência de onda Q septal em V5-V6

> **Mnemônico — "WiLLiaM":** Em V1 vemos W (QS), em V6 vemos M (R entalhado). **W**illiam = W em V1 (ramo Esquerdo / Left).

---

## Segmento ST

### Definição

O segmento ST vai do **final do complexo QRS (ponto J)** até o **início da onda T**. Representa o período em que os ventrículos estão uniformemente despolarizados (platô do potencial de ação).

### Avaliação

- Normalmente **isoelétrico** (na linha de base)
- Referência: segmento **TP** ou **PR** como linha de base
- Desvios >= 1 mm são potencialmente significativos

### Supradesnivelamento de ST

- **Infarto agudo com supra de ST (IAMCSST):** convexo, "lombo de golfinho"
- Pericardite aguda: côncavo, difuso
- Repolarização precoce: variante normal em jovens
- Aneurisma ventricular: persistente, crônico

### Infradesnivelamento de ST

- Isquemia subendocárdica
- Efeito digitálico (concavidade invertida, "colher")
- Hipertrofia ventricular com strain
- Alteração recíproca em contexto de IAMCSST

> **Pérola clínica:** Supra de ST em pelo menos **2 derivações contíguas** com amplitude >= 1 mm (>= 2 mm em V1-V3 em homens) define o IAMCSST e exige reperfusão de urgência.

---

## Intervalo QT

### Definição

O intervalo QT é medido do **início do QRS** até o **final da onda T**. Representa a duração total da despolarização + repolarização ventricular.

### O problema: dependência da frequência cardíaca

O QT **encurta** quando a FC aumenta e **alonga** quando a FC diminui. Por isso, é necessário corrigi-lo para a FC, gerando o **QTc (QT corrigido)**.

### Fórmula de Bazett

A mais utilizada na prática clínica:

**QTc = QT / raiz quadrada(RR)**

Onde RR é medido em **segundos**.

Exemplo: QT = 360 ms, RR = 800 ms (0,8 s)
QTc = 360 / raiz(0,8) = 360 / 0,894 = **403 ms**

> **Limitação:** Bazett **superestima** o QTc em frequências altas (taquicardia) e **subestima** em frequências baixas (bradicardia).

### Fórmula de Fridericia

Mais precisa em frequências extremas:

**QTc = QT / raiz cúbica(RR)**

Exemplo: QT = 360 ms, RR = 0,8 s
QTc = 360 / (0,8)^(1/3) = 360 / 0,928 = **388 ms**

> **Na prática:** Fridericia é preferida em estudos clínicos e quando a FC é < 60 ou > 100 bpm. Bazett permanece aceitável para FC entre 60–100 bpm.

### Outras fórmulas

| Fórmula | Cálculo | Uso |
|:--------|:--------|:----|
| **Hodges** | QTc = QT + 1,75 x (FC - 60) | Linear, boa para FC extremas |
| **Framingham** | QTc = QT + 0,154 x (1 - RR) | Baseada no estudo de Framingham |

### Valores normais do QTc

| | Normal | Limítrofe | Prolongado |
|:---|:------|:----------|:-----------|
| **Homens** | < 430 ms | 430–450 ms | > 450 ms |
| **Mulheres** | < 450 ms | 450–470 ms | > 470 ms |

**QTc > 500 ms** em qualquer sexo é considerado de **alto risco** para arritmias ventriculares (Torsades de Pointes).

### QT Prolongado — Causas

- **Congênitas:** Síndrome do QT longo (Romano-Ward, Jervell-Lange-Nielsen)
- **Medicamentos:** antiarrítmicos (sotalol, amiodarona), antipsicóticos, antibióticos (macrolídeos, fluoroquinolonas), antidepressivos
- **Eletrolíticas:** hipocalemia, hipomagnesemia, hipocalcemia
- **Outras:** bradicardia, hipotermia, isquemia miocárdica, AVC

> **Pérola clínica:** Sempre calcule o QTc ao prescrever medicamentos que prolongam o QT. A lista de drogas que afetam o QT pode ser consultada em crediblemeds.org.

### QT Curto (QTc < 340 ms)

Achado raro. Pode indicar:
- Síndrome do QT curto congênito (risco de morte súbita)
- Hipercalcemia
- Efeito digitálico
- Acidose

---

## Dicas Práticas para Medição

1. **Meça o QT na derivação com o maior intervalo** (geralmente V2 ou V3)
2. **Use o final real da onda T** — ignore a onda U se presente (separe T e U mentalmente)
3. **Se a onda T e U se fundirem**, meça até o nadir entre T e U
4. **Confirme a medida em pelo menos 3 ciclos** e faça a média
5. **Em fibrilação atrial**, meça vários intervalos e use a média dos RR para calcular o QTc

> **Regra rápida do QT:** O QT deve ser **menor que a metade** do intervalo RR precedente. Se o QT parecer "mais da metade" do RR, provavelmente está prolongado.

---

## Resumo dos Intervalos

| Intervalo | Normal | O que representa | Alargado indica |
|:----------|:-------|:----------------|:---------------|
| **PR** | 120–200 ms | Condução AV | Bloqueio AV |
| **QRS** | < 120 ms | Despolarização ventricular | Bloqueio de ramo, ritmo ventricular |
| **QT/QTc** | Variável/< 440-460 ms | Despolarização + repolarização | Risco de arritmia ventricular |
| **Seg. ST** | Isoelétrico | Platô ventricular | Isquemia, infarto, pericardite |

---

## Próximos Passos

Parabéns! Com esta lição, você completou o módulo de **ECG Básico**. Agora aplique todos os conceitos no **Caso Clínico 01 — ECG Normal**, onde fará uma análise sistemática completa.

Revise seus conhecimentos no **Quiz de Fundamentos** para garantir que domina os conceitos essenciais antes de avançar para módulos mais avançados.

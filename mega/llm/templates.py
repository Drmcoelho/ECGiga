"""
Modelos de casos clínicos de ECG em Português.

Cada template contém: história clínica, achados eletrocardiográficos,
perguntas para o aluno e explicações detalhadas.

Refs: GitHub issue #20
"""

from __future__ import annotations

import random
from typing import Any


# ---------------------------------------------------------------------------
# Template dataclass-like dicts
# ---------------------------------------------------------------------------

TEMPLATES: list[dict[str, Any]] = [
    # 1 — STEMI anterior
    {
        "id": "stemi_anterior",
        "titulo": "Infarto Agudo do Miocárdio com Supra de ST — Parede Anterior",
        "topico": "STEMI",
        "dificuldade": "hard",
        "historia": (
            "Paciente masculino, 58 anos, tabagista, hipertenso e diabético, "
            "apresenta-se ao pronto-socorro com dor torácica retroesternal em "
            "aperto, irradiada para o membro superior esquerdo, iniciada há 2 horas. "
            "Sudorese profusa e náuseas. PA 90/60 mmHg, FC 110 bpm."
        ),
        "achados_ecg": {
            "ritmo": "Taquicardia sinusal",
            "fc_bpm": 110,
            "eixo": "Normal (60°)",
            "pr_ms": 160,
            "qrs_ms": 90,
            "qtc_ms": 440,
            "st_segment": "Supradesnivelamento de ST >= 2 mm em V1-V4",
            "ondas_t": "Ondas T hiperagudas em V1-V4",
            "reciprocidade": "Infradesnivelamento de ST em DII, DIII, aVF",
            "outras": "Sem ondas Q patológicas ainda",
        },
        "diagnostico": "IAMCSST anterior — oclusão da artéria descendente anterior (DA)",
        "perguntas": [
            "Quais derivações mostram supradesnivelamento de ST e qual território coronariano corresponde?",
            "Qual a conduta imediata para este paciente?",
            "O que as alterações recíprocas indicam?",
        ],
        "explicacao": (
            "O supradesnivelamento de ST em V1-V4 indica lesão transmural aguda na "
            "parede anterior do ventrículo esquerdo, irrigada pela artéria descendente "
            "anterior (DA). A presença de reciprocidade em derivações inferiores reforça "
            "o diagnóstico de IAMCSST. Conduta: ativar hemodinâmica para angioplastia "
            "primária (ICP) em até 90 minutos. Administrar AAS, heparina, clopidogrel e "
            "considerar nitroglicerina IV se PA permitir."
        ),
    },
    # 2 — STEMI inferior
    {
        "id": "stemi_inferior",
        "titulo": "Infarto Agudo do Miocárdio com Supra de ST — Parede Inferior",
        "topico": "STEMI",
        "dificuldade": "hard",
        "historia": (
            "Paciente masculino, 67 anos, ex-tabagista, com dislipidemia, apresenta "
            "dor epigástrica intensa com irradiação para dorso há 3 horas. Bradicardia "
            "sinusal ao exame. PA 100/70 mmHg, FC 48 bpm. Sudorese fria."
        ),
        "achados_ecg": {
            "ritmo": "Bradicardia sinusal",
            "fc_bpm": 48,
            "eixo": "Normal (45°)",
            "pr_ms": 200,
            "qrs_ms": 88,
            "qtc_ms": 420,
            "st_segment": "Supradesnivelamento de ST >= 2 mm em DII, DIII e aVF",
            "ondas_t": "Ondas T hiperagudas em derivações inferiores",
            "reciprocidade": "Infradesnivelamento de ST em DI e aVL",
            "outras": "Solicitar V3R e V4R para avaliar extensão para VD",
        },
        "diagnostico": "IAMCSST inferior — oclusão da coronária direita (CD)",
        "perguntas": [
            "Por que este paciente apresenta bradicardia?",
            "Por que é importante fazer V3R e V4R?",
            "Qual a diferença entre oclusão da CD e da circunflexa no IAM inferior?",
        ],
        "explicacao": (
            "O IAM inferior por oclusão da CD frequentemente cursa com bradicardia "
            "sinusal porque a CD irriga o nó sinusal em 60% dos pacientes e o nó AV "
            "em 85%. A extensão para ventrículo direito (VD) é avaliada com V3R-V4R "
            "e contraindica nitratos e diuréticos. A bradicardia reflexa (Bezold-Jarisch) "
            "também é comum. Conduta: ICP primária, evitar nitratos se envolvimento de VD, "
            "atropina se bradicardia sintomática."
        ),
    },
    # 3 — Fibrilação Atrial
    {
        "id": "fibrilacao_atrial",
        "titulo": "Fibrilação Atrial com Resposta Ventricular Rápida",
        "topico": "Fibrilação Atrial",
        "dificuldade": "medium",
        "historia": (
            "Paciente feminina, 72 anos, hipertensa, com insuficiência cardíaca "
            "compensada (FEVE 40%), apresenta palpitações e dispneia aos esforços "
            "há 2 dias. Pulso irregular ao exame. PA 130/80 mmHg."
        ),
        "achados_ecg": {
            "ritmo": "Fibrilação atrial — ritmo irregularmente irregular",
            "fc_bpm": 132,
            "eixo": "Normal (30°)",
            "pr_ms": None,
            "qrs_ms": 92,
            "qtc_ms": 410,
            "st_segment": "Sem alterações significativas de ST",
            "ondas_t": "Ondas T normais",
            "reciprocidade": None,
            "outras": "Ausência de ondas P, linha de base fibrilatória (ondas f)",
        },
        "diagnostico": "Fibrilação atrial com resposta ventricular rápida",
        "perguntas": [
            "Quais são os critérios diagnósticos da fibrilação atrial no ECG?",
            "Qual o risco principal da FA e como se calcula?",
            "Qual a estratégia terapêutica: controle de frequência ou ritmo?",
        ],
        "explicacao": (
            "A fibrilação atrial é caracterizada por: (1) ausência de ondas P organizadas, "
            "substituídas por atividade fibrilatória (ondas f), (2) intervalos RR irregulares "
            "(irregularmente irregular), (3) QRS geralmente estreito. O principal risco é "
            "tromboembolismo — calcular CHA2DS2-VASc para decidir anticoagulação. Nesta "
            "paciente (72 anos, HAS, IC): CHA2DS2-VASc >= 3 — anticoagulação indicada. "
            "Controle de frequência com betabloqueador ou digoxina (IC presente)."
        ),
    },
    # 4 — Bradicardia / BAV 3° grau
    {
        "id": "bav_terceiro_grau",
        "titulo": "Bloqueio Atrioventricular de 3.° Grau (Bloqueio Total)",
        "topico": "Bradicardia",
        "dificuldade": "hard",
        "historia": (
            "Paciente masculino, 78 anos, com antecedente de cirurgia cardíaca, "
            "apresenta síncope recorrente e tontura. FC 35 bpm ao exame. "
            "PA 90/60 mmHg. Palidez cutânea."
        ),
        "achados_ecg": {
            "ritmo": "Dissociação AV completa — ondas P e QRS independentes",
            "fc_bpm": 35,
            "eixo": "Normal (40°)",
            "pr_ms": None,
            "qrs_ms": 140,
            "qtc_ms": 480,
            "st_segment": "Sem alterações agudas de ST",
            "ondas_t": "Alterações secundárias da repolarização pelo QRS alargado",
            "reciprocidade": None,
            "outras": "Frequência atrial ~80 bpm, frequência ventricular ~35 bpm, QRS alargado (escape ventricular)",
        },
        "diagnostico": "Bloqueio AV de 3.° grau (BAVT) com ritmo de escape ventricular",
        "perguntas": [
            "Como diferenciar BAV 3° grau de BAV 2° grau Mobitz II?",
            "Por que o QRS é alargado neste caso?",
            "Qual a conduta definitiva?",
        ],
        "explicacao": (
            "No BAVT, há dissociação completa entre átrios e ventrículos: as ondas P "
            "ocorrem em ritmo próprio (80 bpm) e os QRS em outro ritmo mais lento (35 bpm), "
            "sem relação entre si. O QRS é alargado porque o escape é ventricular "
            "(abaixo do feixe de His). Se o escape fosse juncional, o QRS seria estreito. "
            "Conduta: marca-passo provisório (transcutâneo) de emergência, seguido de "
            "implante de marca-passo definitivo (DDDR)."
        ),
    },
    # 5 — Flutter Atrial
    {
        "id": "flutter_atrial",
        "titulo": "Flutter Atrial com Condução 2:1",
        "topico": "Flutter Atrial",
        "dificuldade": "medium",
        "historia": (
            "Paciente masculino, 55 anos, com DPOC, apresenta dispneia progressiva "
            "e palpitações regulares há 1 semana. FC 150 bpm, regular. PA 120/80 mmHg."
        ),
        "achados_ecg": {
            "ritmo": "Flutter atrial com condução 2:1",
            "fc_bpm": 150,
            "eixo": "Desvio para direita (110°)",
            "pr_ms": None,
            "qrs_ms": 86,
            "qtc_ms": 400,
            "st_segment": "Ondas F (dente de serra) visíveis em DII, DIII, aVF e V1",
            "ondas_t": "Difícil avaliação por sobreposição com ondas F",
            "reciprocidade": None,
            "outras": "Frequência atrial ~300 bpm, ventricular ~150 bpm (condução 2:1)",
        },
        "diagnostico": "Flutter atrial típico com condução AV 2:1",
        "perguntas": [
            "Qual a frequência atrial típica do flutter e por que a FC ventricular é ~150 bpm?",
            "Como diferenciar flutter 2:1 de taquicardia sinusal?",
            "Quais manobras podem auxiliar no diagnóstico?",
        ],
        "explicacao": (
            "O flutter atrial típico tem frequência atrial de ~300 bpm com ondas F "
            "em dente de serra (melhor vistas em DII, DIII, aVF e V1). Na condução 2:1, "
            "apenas metade dos impulsos é conduzida, resultando em FC ventricular de ~150 bpm. "
            "Dica: FC de 150 bpm regular deve sempre levantar suspeita de flutter 2:1. "
            "A manobra vagal (massagem do seio carotídeo) ou adenosina pode aumentar "
            "transitoriamente o bloqueio AV e revelar as ondas F."
        ),
    },
    # 6 — Bloqueio de Ramo Esquerdo
    {
        "id": "bre",
        "titulo": "Bloqueio de Ramo Esquerdo (BRE)",
        "topico": "Bloqueio de Ramo",
        "dificuldade": "medium",
        "historia": (
            "Paciente feminina, 65 anos, hipertensa e diabética, com dispneia "
            "aos médios esforços. Ecocardiograma prévio mostra FEVE 35%. "
            "ECG de rotina em consulta ambulatorial."
        ),
        "achados_ecg": {
            "ritmo": "Ritmo sinusal",
            "fc_bpm": 72,
            "eixo": "Desvio para esquerda (-30°)",
            "pr_ms": 180,
            "qrs_ms": 160,
            "qtc_ms": 460,
            "st_segment": "Alterações secundárias de ST-T (discordantes do QRS)",
            "ondas_t": "T invertida em DI, aVL, V5-V6 (padrão strain secundário)",
            "reciprocidade": None,
            "outras": "QS ou rS em V1, R monofásico largo em V5-V6, ausência de onda q septal em V5-V6",
        },
        "diagnostico": "Bloqueio de ramo esquerdo completo",
        "perguntas": [
            "Quais são os critérios diagnósticos do BRE?",
            "O BRE dificulta o diagnóstico de IAM — por quê?",
            "Quando considerar terapia de ressincronização cardíaca (TRC)?",
        ],
        "explicacao": (
            "Critérios do BRE: (1) QRS >= 120 ms, (2) QS ou rS em V1, (3) R monofásico "
            "largo em DI e V5-V6, (4) ausência de onda q septal em derivações esquerdas. "
            "O BRE mascara alterações de ST do IAM — usar critérios de Sgarbossa para "
            "detectar IAMCSST em presença de BRE. Em pacientes com IC e FEVE <= 35% + "
            "BRE com QRS >= 150 ms, considerar TRC (classe I de recomendação)."
        ),
    },
    # 7 — Bloqueio de Ramo Direito
    {
        "id": "brd",
        "titulo": "Bloqueio de Ramo Direito (BRD)",
        "topico": "Bloqueio de Ramo",
        "dificuldade": "easy",
        "historia": (
            "Paciente masculino, 45 anos, assintomático, realiza ECG pré-operatório "
            "para cirurgia de hérnia inguinal. Sem antecedentes cardíacos."
        ),
        "achados_ecg": {
            "ritmo": "Ritmo sinusal",
            "fc_bpm": 68,
            "eixo": "Normal (80°)",
            "pr_ms": 160,
            "qrs_ms": 130,
            "qtc_ms": 420,
            "st_segment": "Infradesnivelamento de ST e T invertida em V1-V3 (secundário ao BRD)",
            "ondas_t": "T invertida em V1-V3",
            "reciprocidade": None,
            "outras": "Padrão RSR' (M) em V1-V2, S empastado em DI e V6",
        },
        "diagnostico": "Bloqueio de ramo direito completo isolado",
        "perguntas": [
            "Quais são os critérios eletrocardiográficos do BRD?",
            "O BRD isolado em paciente assintomático tem significado clínico?",
            "Como diferenciar BRD de outras causas de QRS alargado?",
        ],
        "explicacao": (
            "Critérios do BRD: (1) QRS >= 120 ms, (2) RSR' (morfologia em M) em V1-V2, "
            "(3) S empastado e largo em DI e V6, (4) T invertida em V1-V3 (alteração "
            "secundária). O BRD isolado em paciente jovem e assintomático é geralmente "
            "benigno e não requer tratamento. Pode ser variante normal ou achado "
            "incidental. Investigar se houver: síncope, história familiar de morte "
            "súbita, ou padrão de Brugada associado."
        ),
    },
    # 8 — Wolff-Parkinson-White
    {
        "id": "wpw",
        "titulo": "Síndrome de Wolff-Parkinson-White (WPW)",
        "topico": "Pré-excitação",
        "dificuldade": "hard",
        "historia": (
            "Paciente masculino, 22 anos, atleta, com episódios recorrentes de "
            "palpitações de início e término súbitos desde os 16 anos. ECG de "
            "repouso entre episódios. PA 120/70 mmHg, FC 78 bpm."
        ),
        "achados_ecg": {
            "ritmo": "Ritmo sinusal",
            "fc_bpm": 78,
            "eixo": "Normal (50°)",
            "pr_ms": 100,
            "qrs_ms": 140,
            "qtc_ms": 430,
            "st_segment": "Alterações secundárias de ST",
            "ondas_t": "T invertida em derivações com onda delta proeminente",
            "reciprocidade": None,
            "outras": "Intervalo PR curto (<120 ms), onda delta (empastamento inicial do QRS), QRS alargado",
        },
        "diagnostico": "Padrão de Wolff-Parkinson-White (pré-excitação ventricular)",
        "perguntas": [
            "Quais são os três achados clássicos do WPW no ECG?",
            "Qual arritmia é mais perigosa em pacientes com WPW?",
            "Qual o tratamento definitivo?",
        ],
        "explicacao": (
            "A tríade clássica do WPW: (1) intervalo PR curto (<120 ms), (2) onda delta "
            "(empastamento do início do QRS), (3) QRS alargado (>120 ms). A via acessória "
            "permite condução anterógrada precoce, gerando pré-excitação ventricular. "
            "A arritmia mais perigosa é FA pré-excitada (condução anterógrada rápida pela "
            "via acessória), que pode degenerar em FV. NUNCA usar bloqueadores do nó AV "
            "(verapamil, digoxina, adenosina) na FA pré-excitada. Tratamento definitivo: "
            "ablação por cateter da via acessória."
        ),
    },
    # 9 — Hipercalemia
    {
        "id": "hipercalemia",
        "titulo": "Alterações Eletrocardiográficas da Hipercalemia",
        "topico": "Distúrbios Eletrolíticos",
        "dificuldade": "medium",
        "historia": (
            "Paciente masculino, 60 anos, com doença renal crônica estágio 5 em "
            "hemodiálise, faltou à última sessão. Apresenta fraqueza muscular "
            "generalizada e parestesias. K+ sérico: 7.8 mEq/L."
        ),
        "achados_ecg": {
            "ritmo": "Ritmo sinusal com condução lenta",
            "fc_bpm": 55,
            "eixo": "Indeterminado",
            "pr_ms": 240,
            "qrs_ms": 160,
            "qtc_ms": 400,
            "st_segment": "Supradesnivelamento de ST difuso (pseudo-STEMI)",
            "ondas_t": "Ondas T apiculadas (em tenda) simétricas e estreitas, difusas",
            "reciprocidade": None,
            "outras": "Achatamento de ondas P, PR prolongado, QRS alargado — padrão progressivo de hipercalemia grave",
        },
        "diagnostico": "Alterações eletrocardiográficas da hipercalemia grave",
        "perguntas": [
            "Qual é a sequência de alterações no ECG conforme o potássio aumenta?",
            "O que fazer como primeira medida de emergência?",
            "Como diferenciar ondas T apiculadas da hipercalemia de ondas T hiperagudas do IAM?",
        ],
        "explicacao": (
            "Sequência de alterações com hipercalemia progressiva: (1) K+ 5.5-6.5: ondas T "
            "apiculadas (simétricas, estreitas, em tenda); (2) K+ 6.5-7.5: achatamento de "
            "P, prolongamento de PR; (3) K+ 7.5-8.5: alargamento de QRS; (4) K+ >8.5: "
            "padrão sinusoidal, FV, assistolia. Primeira medida: gluconato de cálcio IV "
            "(estabilização de membrana). Diferença do IAM: ondas T da hipercalemia são "
            "simétricas, estreitas e difusas; as do IAM são assimétricas, mais largas e "
            "territoriais."
        ),
    },
    # 10 — QT Longo
    {
        "id": "qt_longo",
        "titulo": "Síndrome do QT Longo",
        "topico": "QT Longo",
        "dificuldade": "medium",
        "historia": (
            "Paciente feminina, 18 anos, com história de síncope durante exercício "
            "físico. Tia faleceu por morte súbita aos 30 anos. PA 110/70 mmHg, "
            "FC 65 bpm. Exame físico normal."
        ),
        "achados_ecg": {
            "ritmo": "Ritmo sinusal",
            "fc_bpm": 65,
            "eixo": "Normal (50°)",
            "pr_ms": 160,
            "qrs_ms": 88,
            "qtc_ms": 520,
            "st_segment": "Sem alterações significativas de ST",
            "ondas_t": "Ondas T de base ampla em DII (padrão sugestivo de LQT1)",
            "reciprocidade": None,
            "outras": "QTc marcadamente prolongado (520 ms, Bazett). Considerar LQTS congênito.",
        },
        "diagnostico": "Síndrome do QT longo congênito (suspeita de LQT1)",
        "perguntas": [
            "Como se calcula o QTc e qual o limite superior da normalidade?",
            "Quais são os subtipos de LQTS e seus padrões de onda T?",
            "Qual é o tratamento e quais medicamentos devem ser evitados?",
        ],
        "explicacao": (
            "O QTc é calculado pela fórmula de Bazett: QTc = QT / sqrt(RR em s). "
            "Limite superior: 460 ms (mulheres), 450 ms (homens). Subtipos: LQT1 "
            "(T de base ampla, gatilho: exercício), LQT2 (T bífida/entalhada, gatilho: "
            "estímulo auditivo/emocional), LQT3 (T pontiaguda tardia, gatilho: repouso/sono). "
            "Tratamento: betabloqueador (especialmente nadolol), evitar drogas que prolongam "
            "o QT (antiarrítmicos classe IA/III, macrolídeos, fluoroquinolonas, "
            "antipsicóticos). CDI se síncope recorrente apesar de betabloqueador."
        ),
    },
    # 11 — Embolia Pulmonar
    {
        "id": "embolia_pulmonar",
        "titulo": "Tromboembolismo Pulmonar Agudo",
        "topico": "Embolia Pulmonar",
        "dificuldade": "hard",
        "historia": (
            "Paciente feminina, 45 anos, pós-operatório tardio de cirurgia ortopédica "
            "(fratura de fêmur), apresenta dispneia súbita, dor pleurítica e taquicardia. "
            "SpO2 88%, FC 120 bpm, PA 100/60 mmHg. TVP em membro inferior direito."
        ),
        "achados_ecg": {
            "ritmo": "Taquicardia sinusal",
            "fc_bpm": 120,
            "eixo": "Desvio para direita (110°)",
            "pr_ms": 150,
            "qrs_ms": 100,
            "qtc_ms": 450,
            "st_segment": "Infradesnivelamento de ST em DI, supradesnivelamento de ST em DIII",
            "ondas_t": "T invertida em V1-V4 e DIII (padrão de sobrecarga VD aguda)",
            "reciprocidade": None,
            "outras": "Padrão S1Q3T3 (S profundo em DI, Q em DIII, T invertida em DIII). BRD incompleto novo.",
        },
        "diagnostico": "Achados sugestivos de tromboembolismo pulmonar agudo (cor pulmonale agudo)",
        "perguntas": [
            "O que significa o padrão S1Q3T3?",
            "O ECG é sensível para diagnóstico de TEP?",
            "Quais outros exames são necessários?",
        ],
        "explicacao": (
            "O padrão S1Q3T3 (onda S em DI + onda Q e T invertida em DIII) é classicamente "
            "descrito no TEP, mas tem sensibilidade de apenas ~20%. Outros achados: taquicardia "
            "sinusal (achado mais frequente), desvio de eixo para direita, BRD novo, T invertida "
            "em V1-V4, P pulmonale. O ECG é pouco sensível mas achados sugestivos em contexto "
            "clínico apropriado reforçam a hipótese. Confirmar com angiotomografia de tórax ou "
            "cintilografia V/Q. D-dímero útil para exclusão se probabilidade pré-teste baixa."
        ),
    },
    # 12 — Pericardite
    {
        "id": "pericardite",
        "titulo": "Pericardite Aguda",
        "topico": "Pericardite",
        "dificuldade": "medium",
        "historia": (
            "Paciente masculino, 28 anos, previamente hígido, com dor torácica "
            "pleurítica que piora ao deitar e melhora sentado inclinado para frente. "
            "Febre (38.2°C) há 3 dias após quadro gripal. Atrito pericárdico à ausculta."
        ),
        "achados_ecg": {
            "ritmo": "Taquicardia sinusal leve",
            "fc_bpm": 100,
            "eixo": "Normal (60°)",
            "pr_ms": 140,
            "qrs_ms": 86,
            "qtc_ms": 410,
            "st_segment": "Supradesnivelamento difuso de ST (côncavo para cima) em múltiplas derivações",
            "ondas_t": "Ondas T normais preservadas nesta fase",
            "reciprocidade": "Depressão de PR difusa, supra de ST em aVR (Espelho invertido)",
            "outras": "Infra de PR em DII (achado precoce de pericardite). Sem reciprocidade territorial clássica de IAM.",
        },
        "diagnostico": "Pericardite aguda (provável etiologia viral)",
        "perguntas": [
            "Como diferenciar o supra de ST da pericardite do IAM?",
            "Quais são os estágios evolutivos do ECG na pericardite?",
            "Qual o tratamento de primeira linha?",
        ],
        "explicacao": (
            "Diferenças do IAM: (1) supra difuso e não territorial, (2) supra côncavo "
            "(em sela, concavidade para cima), (3) depressão de PR (patognomônico), "
            "(4) sem ondas Q, (5) sem reciprocidade territorial. Estágios: I — supra "
            "difuso + infra de PR, II — normalização de ST com achatamento de T, "
            "III — inversão difusa de T, IV — normalização completa. Tratamento: "
            "AINEs (ibuprofeno 600mg 8/8h) + colchicina (0.5mg 12/12h) por 3 meses."
        ),
    },
    # 13 — Taquicardia Ventricular
    {
        "id": "taquicardia_ventricular",
        "titulo": "Taquicardia Ventricular Monomórfica Sustentada",
        "topico": "Taquicardia Ventricular",
        "dificuldade": "hard",
        "historia": (
            "Paciente masculino, 62 anos, com IAM prévio há 5 anos e FEVE 30%, "
            "apresenta palpitações e tontura há 20 minutos. Hemodinamicamente instável, "
            "PA 80/50 mmHg. Pele fria e úmida."
        ),
        "achados_ecg": {
            "ritmo": "Taquicardia de complexos largos, regular",
            "fc_bpm": 180,
            "eixo": "Desvio extremo para esquerda (eixo noroeste)",
            "pr_ms": None,
            "qrs_ms": 180,
            "qtc_ms": None,
            "st_segment": "Não avaliável durante taquicardia",
            "ondas_t": "Não avaliáveis — fundidas nos complexos QRS",
            "reciprocidade": None,
            "outras": "QRS alargado (180 ms), dissociação AV, batimentos de captura e fusão (critérios de Brugada para TV)",
        },
        "diagnostico": "Taquicardia ventricular monomórfica sustentada",
        "perguntas": [
            "Quais critérios diferenciam TV de TSV com aberrância?",
            "Qual a conduta imediata neste caso?",
            "Qual o tratamento a longo prazo?",
        ],
        "explicacao": (
            "Critérios que favorecem TV: (1) dissociação AV (ondas P independentes do QRS), "
            "(2) batimentos de captura e fusão, (3) concordância precordial (todos os QRS na "
            "mesma direção em V1-V6), (4) ausência de padrão típico de BRD ou BRE, "
            "(5) critérios de Brugada. Regra prática: taquicardia de complexo largo em "
            "paciente com cardiopatia estrutural é TV até prova em contrário. Conduta imediata "
            "com instabilidade: cardioversão elétrica sincronizada. Longo prazo: CDI + "
            "amiodarona + otimização de IC."
        ),
    },
    # 14 — Hipertrofia Ventricular Esquerda
    {
        "id": "hve",
        "titulo": "Hipertrofia Ventricular Esquerda (HVE)",
        "topico": "Hipertrofia",
        "dificuldade": "easy",
        "historia": (
            "Paciente masculino, 55 anos, hipertenso há 20 anos, com tratamento "
            "irregular. Assintomático cardiovascular. PA 170/100 mmHg. ECG de rotina."
        ),
        "achados_ecg": {
            "ritmo": "Ritmo sinusal",
            "fc_bpm": 76,
            "eixo": "Desvio leve para esquerda (-10°)",
            "pr_ms": 170,
            "qrs_ms": 100,
            "qtc_ms": 440,
            "st_segment": "Infra de ST com T invertida assimétrica em V5-V6 (strain pattern)",
            "ondas_t": "T invertida assimétrica em DI, aVL, V5-V6",
            "reciprocidade": None,
            "outras": "SV1 + RV5 = 42 mm (Sokolow-Lyon positivo >= 35 mm). RaVL = 14 mm (Cornell).",
        },
        "diagnostico": "Hipertrofia ventricular esquerda com padrão strain",
        "perguntas": [
            "Quais são os critérios de voltagem para HVE?",
            "O que é o padrão strain e qual seu significado?",
            "Quais as limitações dos critérios eletrocardiográficos de HVE?",
        ],
        "explicacao": (
            "Critérios de voltagem: Sokolow-Lyon (SV1 + RV5 ou RV6 >= 35 mm), "
            "Cornell (RaVL + SV3 > 28 mm em homens, > 20 mm em mulheres). O padrão "
            "strain (infra de ST com T invertida assimétrica nas derivações laterais) "
            "indica sobrecarga sistólica crônica e está associado a pior prognóstico. "
            "Limitações: baixa sensibilidade (~20-50%), especialmente em obesos e jovens. "
            "A sensibilidade melhora com critérios combinados (Romhilt-Estes >= 5 pontos)."
        ),
    },
    # 15 — BAV 2° grau Mobitz I (Wenckebach)
    {
        "id": "bav_segundo_wenckebach",
        "titulo": "Bloqueio AV de 2.° Grau — Mobitz Tipo I (Wenckebach)",
        "topico": "Bloqueio AV",
        "dificuldade": "medium",
        "historia": (
            "Paciente masculino, 30 anos, atleta de maratona, realiza ECG em "
            "check-up desportivo. Assintomático. FC de repouso 52 bpm. "
            "Sem medicações."
        ),
        "achados_ecg": {
            "ritmo": "Ritmo sinusal com fenômeno de Wenckebach",
            "fc_bpm": 52,
            "eixo": "Normal (60°)",
            "pr_ms": None,
            "qrs_ms": 86,
            "qtc_ms": 410,
            "st_segment": "Sem alterações de ST",
            "ondas_t": "Ondas T normais",
            "reciprocidade": None,
            "outras": (
                "PR progressivamente mais longo a cada batimento (160, 200, 240 ms) "
                "até uma onda P não conduzida (QRS ausente). Ciclo se repete."
            ),
        },
        "diagnostico": "BAV 2° grau Mobitz I (Wenckebach) — provável fisiológico em atleta",
        "perguntas": [
            "Qual o mecanismo do fenômeno de Wenckebach?",
            "Quando o Mobitz I é benigno e quando é patológico?",
            "Como diferenciar Mobitz I de Mobitz II?",
        ],
        "explicacao": (
            "No Wenckebach, há prolongamento progressivo do PR até que um impulso "
            "atrial não é conduzido. O bloqueio geralmente ocorre no nó AV (supra-hisiano). "
            "É benigno em atletas e durante o sono (tônus vagal alto). É patológico se: "
            "sintomático (síncope, tontura), em vigília com FC muito baixa, ou com QRS "
            "alargado (sugere nível infra-hisiano). Mobitz II: PR constante com falha "
            "súbita de condução — mais grave, frequentemente infra-hisiano, pode progredir "
            "para BAVT. Mobitz II com QRS alargado é indicação de marca-passo."
        ),
    },
]


# ---------------------------------------------------------------------------
# Mapeamento por tópico e dificuldade
# ---------------------------------------------------------------------------

_INDEX_BY_TOPIC: dict[str, list[int]] = {}
_INDEX_BY_DIFFICULTY: dict[str, list[int]] = {}

for _i, _t in enumerate(TEMPLATES):
    _topic = _t["topico"].lower()
    _INDEX_BY_TOPIC.setdefault(_topic, []).append(_i)
    _diff = _t["dificuldade"].lower()
    _INDEX_BY_DIFFICULTY.setdefault(_diff, []).append(_i)


def get_template(
    topic: str | None = None,
    difficulty: str | None = None,
) -> dict[str, Any]:
    """Retorna um template de caso clínico, opcionalmente filtrado.

    Parameters
    ----------
    topic : str | None
        Filtrar por tópico (ex. "STEMI", "Bradicardia"). Busca parcial.
    difficulty : str | None
        Filtrar por dificuldade ("easy", "medium", "hard").

    Returns
    -------
    dict
        Um template de caso clínico selecionado aleatoriamente.
    """
    candidates = list(range(len(TEMPLATES)))

    if topic:
        topic_lower = topic.lower()
        topic_matches = []
        for idx in candidates:
            t = TEMPLATES[idx]
            if (
                topic_lower in t["topico"].lower()
                or topic_lower in t["titulo"].lower()
                or topic_lower in t["id"].lower()
            ):
                topic_matches.append(idx)
        if topic_matches:
            candidates = topic_matches

    if difficulty:
        diff_lower = difficulty.lower()
        diff_matches = [i for i in candidates if TEMPLATES[i]["dificuldade"].lower() == diff_lower]
        if diff_matches:
            candidates = diff_matches

    idx = random.choice(candidates)
    return TEMPLATES[idx]


def list_topics() -> list[str]:
    """Retorna lista de tópicos disponíveis sem duplicatas."""
    seen: set[str] = set()
    result: list[str] = []
    for t in TEMPLATES:
        if t["topico"] not in seen:
            seen.add(t["topico"])
            result.append(t["topico"])
    return result


def list_difficulties() -> list[str]:
    """Retorna dificuldades disponíveis."""
    return sorted(set(t["dificuldade"] for t in TEMPLATES))

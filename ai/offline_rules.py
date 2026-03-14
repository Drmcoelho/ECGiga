"""
Rule-based ECG interpretation that works without any API.

Phase 22 (p22) - Offline fallback for AI/LLM integration.
All output is in Portuguese with camera analogies where appropriate.
"""

from __future__ import annotations

from typing import Any


# ---------------------------------------------------------------------------
# Interpretation rules: each rule has a condition function and a conclusion
# ---------------------------------------------------------------------------

INTERPRETATION_RULES: list[dict[str, Any]] = [
    # --- PR interval ---
    {
        "id": "pr_prolonged",
        "category": "intervals",
        "condition": lambda med: med.get("PR_ms", 0) and med["PR_ms"] > 200,
        "conclusion": "Intervalo PR prolongado (>{val:.0f} ms) — sugere bloqueio AV de 1.° grau.",
        "severity": "moderate",
        "camera": (
            "O atraso entre o flash (onda P) e o disparo do obturador (QRS) está "
            "maior que o normal — a câmera demora mais para disparar após o flash."
        ),
        "val_key": "PR_ms",
    },
    {
        "id": "pr_markedly_prolonged",
        "category": "intervals",
        "condition": lambda med: med.get("PR_ms", 0) and med["PR_ms"] > 300,
        "conclusion": "PR marcadamente prolongado ({val:.0f} ms) — BAV avançado, risco de progressão.",
        "severity": "high",
        "camera": (
            "O atraso entre flash e obturador é extremo — a câmera quase perde o evento."
        ),
        "val_key": "PR_ms",
    },
    {
        "id": "pr_short",
        "category": "intervals",
        "condition": lambda med: med.get("PR_ms", 999) < 120 and med.get("PR_ms", 0) > 0,
        "conclusion": "Intervalo PR curto (<120 ms) — considerar pré-excitação (ex: Wolff-Parkinson-White).",
        "severity": "moderate",
        "camera": (
            "O flash e o obturador disparam quase simultaneamente — como se houvesse "
            "um atalho no mecanismo da câmera."
        ),
        "val_key": "PR_ms",
    },
    # --- QRS duration ---
    {
        "id": "qrs_wide",
        "category": "intervals",
        "condition": lambda med: med.get("QRS_ms", 0) and med["QRS_ms"] > 120,
        "conclusion": "QRS alargado (>{val:.0f} ms) — possível bloqueio de ramo ou ritmo ventricular.",
        "severity": "moderate",
        "camera": (
            "O obturador da câmera está demorando mais para abrir e fechar — a captura "
            "da imagem fica borrada e mais larga que o normal."
        ),
        "val_key": "QRS_ms",
    },
    {
        "id": "qrs_very_wide",
        "category": "intervals",
        "condition": lambda med: med.get("QRS_ms", 0) and med["QRS_ms"] > 160,
        "conclusion": "QRS muito alargado ({val:.0f} ms) — considerar hipercalemia, toxicidade por antiarrítmico, ou ritmo ventricular.",
        "severity": "high",
        "camera": (
            "O obturador está tão lento que a imagem sai completamente borrada — "
            "a câmera está em modo de emergência."
        ),
        "val_key": "QRS_ms",
    },
    {
        "id": "qrs_borderline",
        "category": "intervals",
        "condition": lambda med: 110 <= med.get("QRS_ms", 0) <= 120,
        "conclusion": "QRS limítrofe (110-120 ms) — bloqueio de ramo incompleto possível.",
        "severity": "low",
        "camera": (
            "O obturador está ligeiramente mais lento que o ideal — a câmera ainda "
            "funciona, mas a imagem pode ficar levemente desfocada."
        ),
        "val_key": "QRS_ms",
    },
    # --- QTc ---
    {
        "id": "qtc_prolonged",
        "category": "intervals",
        "condition": lambda med: med.get("QTc_B", 0) and 460 < med["QTc_B"] <= 500,
        "conclusion": "QTc prolongado ({val:.0f} ms, Bazett) — risco moderado de arritmias ventriculares.",
        "severity": "moderate",
        "camera": (
            "O ciclo completo da câmera (do disparo ao reset) está mais longo que o normal — "
            "a câmera pode não estar pronta para a próxima foto a tempo."
        ),
        "val_key": "QTc_B",
    },
    {
        "id": "qtc_markedly_prolonged",
        "category": "intervals",
        "condition": lambda med: med.get("QTc_B", 0) and med["QTc_B"] > 500,
        "conclusion": "QTc muito prolongado ({val:.0f} ms) — ALTO RISCO de torsade de pointes!",
        "severity": "critical",
        "camera": (
            "O ciclo da câmera está perigosamente longo — a câmera pode travar "
            "e entrar em modo caótico (Torsade de Pointes)."
        ),
        "val_key": "QTc_B",
    },
    {
        "id": "qtc_short",
        "category": "intervals",
        "condition": lambda med: med.get("QTc_B", 999) < 340 and med.get("QTc_B", 0) > 0,
        "conclusion": "QTc curto (<340 ms) — síndrome do QT curto, risco arritmogênico.",
        "severity": "moderate",
        "camera": (
            "O ciclo da câmera está rápido demais — o reset ocorre antes que a "
            "captura esteja completa."
        ),
        "val_key": "QTc_B",
    },
    # --- Heart rate (from RR) ---
    {
        "id": "tachycardia",
        "category": "rhythm",
        "condition": lambda med: med.get("RR_s", 0) and med["RR_s"] > 0 and 100 < (60.0 / med["RR_s"]) <= 150,
        "conclusion": "Taquicardia sinusal (FC ~{val:.0f} bpm).",
        "severity": "low",
        "camera": (
            "A câmera está disparando mais rápido — como um fotógrafo em modo burst."
        ),
        "val_key": "RR_s",
        "val_transform": lambda rr: 60.0 / rr if rr > 0 else 0,
    },
    {
        "id": "marked_tachycardia",
        "category": "rhythm",
        "condition": lambda med: med.get("RR_s", 0) and med["RR_s"] > 0 and (60.0 / med["RR_s"]) > 150,
        "conclusion": "Taquicardia significativa (FC ~{val:.0f} bpm) — considerar TSV, flutter ou TV.",
        "severity": "high",
        "camera": (
            "A câmera está em modo burst extremo — tirando tantas fotos que as imagens "
            "se sobrepõem. Pode ser TSV, flutter ou taquicardia ventricular."
        ),
        "val_key": "RR_s",
        "val_transform": lambda rr: 60.0 / rr if rr > 0 else 0,
    },
    {
        "id": "bradycardia",
        "category": "rhythm",
        "condition": lambda med: med.get("RR_s", 0) and med["RR_s"] > 0 and 40 <= (60.0 / med["RR_s"]) < 60,
        "conclusion": "Bradicardia sinusal (FC ~{val:.0f} bpm).",
        "severity": "low",
        "camera": (
            "A câmera está disparando devagar — o fotógrafo está em modo contemplativo."
        ),
        "val_key": "RR_s",
        "val_transform": lambda rr: 60.0 / rr if rr > 0 else 0,
    },
    {
        "id": "severe_bradycardia",
        "category": "rhythm",
        "condition": lambda med: med.get("RR_s", 0) and med["RR_s"] > 0 and (60.0 / med["RR_s"]) < 40,
        "conclusion": "Bradicardia grave (FC ~{val:.0f} bpm) — risco de síncope ou assistolia!",
        "severity": "critical",
        "camera": (
            "A câmera quase parou — está tirando tão poucas fotos que corre o risco "
            "de perder eventos inteiros. Situação de emergência!"
        ),
        "val_key": "RR_s",
        "val_transform": lambda rr: 60.0 / rr if rr > 0 else 0,
    },
    # --- Axis ---
    {
        "id": "axis_left_deviation",
        "category": "axis",
        "condition": lambda med: False,  # handled separately via axis dict
        "conclusion": "Desvio do eixo para a esquerda.",
        "severity": "moderate",
        "camera": (
            "As câmeras frontais mostram que a atividade elétrica principal está "
            "apontando mais para a esquerda do que o esperado — como se o cenário "
            "tivesse se deslocado para a esquerda da cena."
        ),
    },
    {
        "id": "axis_right_deviation",
        "category": "axis",
        "condition": lambda med: False,
        "conclusion": "Desvio do eixo para a direita.",
        "severity": "moderate",
        "camera": (
            "As câmeras frontais mostram que a atividade elétrica principal está "
            "apontando mais para a direita do que o esperado — como se o cenário "
            "tivesse se deslocado para a direita."
        ),
    },
    {
        "id": "axis_extreme",
        "category": "axis",
        "condition": lambda med: False,
        "conclusion": "Eixo extremo (terra de ninguém).",
        "severity": "high",
        "camera": (
            "Nenhuma câmera frontal consegue capturar bem a atividade elétrica — "
            "como se o coração estivesse de costas para todas as câmeras. "
            "Considerar ritmo ventricular ou hipercalemia grave."
        ),
    },
    # --- Combined findings ---
    {
        "id": "pr_short_qrs_wide",
        "category": "intervals",
        "condition": lambda med: (
            med.get("PR_ms", 999) < 120
            and med.get("PR_ms", 0) > 0
            and med.get("QRS_ms", 0) > 120
        ),
        "conclusion": "PR curto + QRS alargado — padrão clássico de pré-excitação (WPW)!",
        "severity": "high",
        "camera": (
            "O flash e o obturador disparam quase juntos via atalho, e a exposição fica "
            "mais longa que o normal — padrão clássico de via acessória (WPW)."
        ),
        "val_key": "PR_ms",
    },
    {
        "id": "wide_qrs_prolonged_qt",
        "category": "intervals",
        "condition": lambda med: (
            med.get("QRS_ms", 0) > 120
            and med.get("QTc_B", 0) > 500
        ),
        "conclusion": "QRS alargado + QTc muito prolongado — risco alto de arritmia ventricular maligna!",
        "severity": "critical",
        "camera": (
            "O obturador está lento E o ciclo da câmera está muito longo — a combinação "
            "pode fazer a câmera entrar em modo caótico. Emergência potencial!"
        ),
        "val_key": "QRS_ms",
    },
]

# Mapping from flag text patterns to differential diagnoses
_FLAG_DIFFERENTIAL_MAP: dict[str, list[dict[str, str]]] = {
    "bloqueio": [
        {"diagnosis": "Bloqueio de ramo direito", "support": "QRS alargado com padrão RSR' em V1"},
        {"diagnosis": "Bloqueio de ramo esquerdo", "support": "QRS alargado com ausência de R em V1"},
        {"diagnosis": "Bloqueio AV", "support": "PR prolongado ou dissociação AV"},
        {"diagnosis": "Bloqueio divisional anterossuperior (BDAS)", "support": "Desvio de eixo para esquerda + S em DII/DIII > R"},
    ],
    "taquicardia": [
        {"diagnosis": "Taquicardia sinusal", "support": "FC >100 bpm com ondas P normais"},
        {"diagnosis": "Taquicardia supraventricular", "support": "FC >150 bpm com QRS estreito"},
        {"diagnosis": "Taquicardia ventricular", "support": "FC >100 bpm com QRS alargado"},
        {"diagnosis": "Flutter atrial com condução 2:1", "support": "FC ~150 bpm, ondas F em dente de serra"},
        {"diagnosis": "Taquicardia por reentrada nodal (TRN)", "support": "FC 150-250 bpm, pseudo-r' em V1"},
    ],
    "bradicardia": [
        {"diagnosis": "Bradicardia sinusal", "support": "FC <60 bpm com ondas P normais"},
        {"diagnosis": "Bloqueio AV de 2.° grau Mobitz I (Wenckebach)", "support": "PR progressivamente mais longo antes de falha"},
        {"diagnosis": "Bloqueio AV de 2.° grau Mobitz II", "support": "PR constante com falhas intermitentes de QRS"},
        {"diagnosis": "Bloqueio AV de 3.° grau (total)", "support": "Dissociação P-QRS completa, ritmo de escape"},
        {"diagnosis": "Disfunção do nó sinusal", "support": "Pausas sinusais prolongadas"},
        {"diagnosis": "Hipotireoidismo", "support": "Bradicardia + baixa voltagem + QT prolongado"},
    ],
    "qt prolongado": [
        {"diagnosis": "Síndrome do QT longo congênito (LQTS)", "support": "QTc >460 ms sem causa secundária"},
        {"diagnosis": "LQTS tipo 1 (LQT1)", "support": "Ondas T largas e de base ampla"},
        {"diagnosis": "LQTS tipo 2 (LQT2)", "support": "Ondas T bífidas ou com entalhe"},
        {"diagnosis": "LQTS tipo 3 (LQT3)", "support": "Ondas T pontiagudas com início tardio"},
        {"diagnosis": "QT longo induzido por drogas", "support": "Antiarrítmicos, antipsicóticos, antibióticos (fluoroquinolonas, macrolídeos)"},
        {"diagnosis": "Distúrbio eletrolítico", "support": "Hipocalemia (onda U), hipocalcemia, hipomagnesemia"},
    ],
    "hipertrofia": [
        {"diagnosis": "Hipertrofia ventricular esquerda (HVE)", "support": "Sokolow-Lyon: SV1+RV5≥35mm; Cornell: RaVL+SV3>28mm(H)/20mm(M)"},
        {"diagnosis": "Hipertrofia ventricular direita (HVD)", "support": "Desvio de eixo para direita, R/S >1 em V1, strain pattern VD"},
        {"diagnosis": "Hipertrofia atrial esquerda (HAE)", "support": "Onda P bífida em DII >120ms, componente negativo em V1 >40ms"},
        {"diagnosis": "Hipertrofia atrial direita (HAD)", "support": "Onda P pontiaguda em DII >2.5mm (P pulmonale)"},
        {"diagnosis": "Cardiomiopatia hipertrófica", "support": "HVE com ondas Q septais profundas + padrão strain"},
    ],
    "isquemia": [
        {"diagnosis": "Síndrome coronariana aguda (SCA)", "support": "Alterações de ST-T agudas"},
        {"diagnosis": "Angina instável / IAMSSST", "support": "Infradesnivelamento de ST + T invertida dinâmica"},
        {"diagnosis": "Infarto prévio (necrose)", "support": "Ondas Q patológicas (>40ms ou >25% do R) em derivações contíguas"},
        {"diagnosis": "Angina de Prinzmetal (vasoespástica)", "support": "Supradesnivelamento transitório de ST durante dor"},
        {"diagnosis": "Padrão de Wellens", "support": "T invertida profunda ou bifásica em V2-V3 (estenose de DA proximal)"},
        {"diagnosis": "Padrão de de Winter", "support": "Infra ST ascendente com T hiperaguda em precordiais (equivalente STEMI)"},
    ],
    "fibrilação": [
        {"diagnosis": "Fibrilação atrial", "support": "Ritmo irregularmente irregular, ausência de ondas P"},
        {"diagnosis": "Flutter atrial", "support": "Ondas F em dente de serra (300/min), condução variável"},
        {"diagnosis": "Fibrilação atrial paroxística", "support": "Episódios intermitentes de RR irregular"},
        {"diagnosis": "Taquicardia atrial multifocal", "support": "≥3 morfologias de P diferentes, RR irregular"},
    ],
    "supra": [
        {"diagnosis": "IAMCSST (infarto com supra de ST)", "support": "Supra >1mm em 2+ derivações contíguas com reciprocidade"},
        {"diagnosis": "Pericardite aguda", "support": "Supra difuso e côncavo, depressão PR, sem reciprocidade territorial"},
        {"diagnosis": "Repolarização precoce benigna", "support": "Supra côncavo com J point em jovens, sem reciprocidade"},
        {"diagnosis": "Síndrome de Brugada tipo 1", "support": "Supra coved ≥2mm em V1-V2 com T invertida"},
        {"diagnosis": "Aneurisma ventricular", "support": "Supra persistente com ondas Q em território prévio de IAM"},
        {"diagnosis": "Hipercalemia grave", "support": "Supra de ST + QRS alargado + T apiculada"},
    ],
    "infra": [
        {"diagnosis": "Isquemia subendocárdica", "support": "Infra ST horizontal ou descendente ≥1mm"},
        {"diagnosis": "Efeito digitálico (digoxina)", "support": "ST em colher (concavidade superior) com T achatada"},
        {"diagnosis": "Sobrecarga ventricular (strain pattern)", "support": "Infra ST assimétrico com HVE/HVD"},
        {"diagnosis": "Imagem recíproca de STEMI", "support": "Infra em derivações opostas ao supra de ST territorial"},
        {"diagnosis": "Hipocalemia", "support": "Infra ST + achatamento de T + onda U proeminente"},
    ],
    "onda t invertida": [
        {"diagnosis": "Isquemia miocárdica", "support": "Inversão de T simétrica e profunda em território coronariano"},
        {"diagnosis": "Sobrecarga ventricular (strain)", "support": "T invertida assimétrica com HVE/HVD"},
        {"diagnosis": "Embolia pulmonar (TEP)", "support": "T invertida em V1-V4 com S1Q3T3 e taquicardia"},
        {"diagnosis": "Miocardite", "support": "T invertida difusa com elevação de troponina sem lesão coronariana"},
        {"diagnosis": "Cardiomiopatia de Takotsubo", "support": "T invertida profunda difusa com QTc prolongado pós-estresse emocional"},
        {"diagnosis": "Síndrome de Wellens", "support": "T invertida profunda ou bifásica em V2-V3 (estenose de DA)"},
        {"diagnosis": "Hemorragia subaracnoide", "support": "T invertida gigante com QTc muito prolongado (cerebral T waves)"},
    ],
    "onda u": [
        {"diagnosis": "Hipocalemia", "support": "Onda U proeminente com T achatada e infra de ST"},
        {"diagnosis": "Variante normal", "support": "Onda U pequena em V2-V3 (principalmente em bradicardia)"},
        {"diagnosis": "Efeito medicamentoso", "support": "Digoxina, antiarrítmicos, fenotiazinas"},
    ],
    "baixa voltagem": [
        {"diagnosis": "Derrame pericárdico", "support": "Baixa voltagem difusa com alternância elétrica"},
        {"diagnosis": "DPOC / Enfisema", "support": "Baixa voltagem com eixo indeterminado e P pulmonale"},
        {"diagnosis": "Hipotireoidismo", "support": "Baixa voltagem com bradicardia sinusal"},
        {"diagnosis": "Obesidade", "support": "Baixa voltagem com critérios de HVE por voltagem reduzida"},
        {"diagnosis": "Infiltração miocárdica (amiloidose)", "support": "Baixa voltagem + pseudo-padrão de infarto"},
    ],
    "delta": [
        {"diagnosis": "Síndrome de Wolff-Parkinson-White (WPW)", "support": "PR curto + onda delta + QRS alargado"},
        {"diagnosis": "Via acessória oculta", "support": "Sem delta em repouso mas episódios de TSV"},
    ],
    "alternância": [
        {"diagnosis": "Derrame pericárdico volumoso", "support": "Alternância elétrica com baixa voltagem"},
        {"diagnosis": "TV polimórfica (torsade de pointes)", "support": "Alternância de amplitude do QRS com QT longo"},
    ],
}


# ---------------------------------------------------------------------------
# Core interpretation function
# ---------------------------------------------------------------------------

def interpret_report(report: dict) -> dict:
    """Full rule-based interpretation of an ECG report.

    Analyzes intervals (PR, QRS, QT/QTc), axis, rhythm, and pathology flags.
    Generates structured interpretation text in Portuguese using camera analogies.

    Parameters
    ----------
    report : dict
        ECG report dictionary (ECGiga schema).

    Returns
    -------
    dict
        ``{"interpretation": str, "differentials": list, "recommendations": list, "confidence": str}``
    """
    findings: list[str] = []
    camera_notes: list[str] = []
    differentials: list[str] = []
    recommendations: list[str] = []

    # --- Extract intervals ---
    iv = report.get("intervals_refined") or report.get("intervals") or {}
    med = iv.get("median", {})

    # Apply interval / rhythm rules
    for rule in INTERPRETATION_RULES:
        if rule["category"] in ("intervals", "rhythm"):
            try:
                if rule["condition"](med):
                    val_key = rule.get("val_key", "")
                    val = med.get(val_key, 0)
                    transform = rule.get("val_transform")
                    if transform:
                        val = transform(val)
                    conclusion = rule["conclusion"].format(val=val)
                    findings.append(conclusion)
                    camera_notes.append(rule["camera"])
            except (TypeError, ZeroDivisionError, KeyError):
                continue

    # --- Axis analysis ---
    axis = report.get("axis") or report.get("axis_hex") or {}
    angle = axis.get("angle_deg")
    label = axis.get("label", "")

    if angle is not None:
        if -30 <= angle <= 90:
            findings.append(f"Eixo elétrico normal ({angle:.0f}°).")
        elif -90 <= angle < -30:
            findings.append(f"Desvio do eixo para a esquerda ({angle:.0f}°).")
            camera_notes.append(
                "As câmeras frontais mostram que a atividade elétrica principal "
                "está apontando mais para a esquerda do que o esperado."
            )
            differentials.append("Considerar: bloqueio divisional anterossuperior esquerdo, HVE")
        elif 90 < angle <= 180:
            findings.append(f"Desvio do eixo para a direita ({angle:.0f}°).")
            camera_notes.append(
                "As câmeras frontais mostram que a atividade elétrica principal "
                "está apontando mais para a direita do que o esperado."
            )
            differentials.append("Considerar: HVD, bloqueio divisional posteroinferior, TEP")
        else:
            findings.append(f"Eixo extremo ({angle:.0f}°) — eixo indeterminado.")
            camera_notes.append(
                "Nenhuma câmera frontal consegue capturar bem a atividade elétrica — "
                "como se o coração estivesse de costas para todas as câmeras."
            )
            differentials.append("Eixo extremo: considerar ritmo ventricular, hipercalemia grave")

    # --- Heart rate ---
    rr_s = med.get("RR_s", 0)
    if rr_s and rr_s > 0:
        hr = 60.0 / rr_s
        findings.append(f"Frequência cardíaca estimada: ~{hr:.0f} bpm.")
        if hr > 100:
            recommendations.append("Investigar causa da taquicardia (febre, dor, ansiedade, hipertireoidismo, etc.).")
        elif hr < 60:
            recommendations.append("Avaliar se bradicardia é fisiológica (atleta) ou patológica.")
    else:
        # Try rpeaks
        rpeaks = report.get("rpeaks", {})
        rr_list = rpeaks.get("rr_sec", [])
        if rr_list:
            avg_rr = sum(rr_list) / len(rr_list)
            if avg_rr > 0:
                hr = 60.0 / avg_rr
                findings.append(f"Frequência cardíaca estimada: ~{hr:.0f} bpm.")

    # --- Flags ---
    flags = report.get("flags", [])
    for flag in flags:
        fl = flag.lower()
        if fl in ("sem flags relevantes", "nenhum", "normal"):
            continue
        findings.append(f"Flag: {flag}")
        # Match flag to differentials
        for pattern, diffs in _FLAG_DIFFERENTIAL_MAP.items():
            if pattern in fl:
                for d in diffs:
                    differentials.append(f"{d['diagnosis']} — {d['support']}")

    # --- ST territory analysis (if st_changes present) ---
    st_changes = report.get("st_changes", {})
    if st_changes:
        territory_findings = _analyze_st_territories(st_changes)
        findings.extend(territory_findings.get("findings", []))
        camera_notes.extend(territory_findings.get("camera_notes", []))
        differentials.extend(territory_findings.get("differentials", []))
        recommendations.extend(territory_findings.get("recommendations", []))

    # --- Severity assessment ---
    max_severity = "normal"
    severity_order = {"normal": 0, "low": 1, "moderate": 2, "high": 3, "critical": 4}

    for rule in INTERPRETATION_RULES:
        if rule["category"] in ("intervals", "rhythm"):
            try:
                if rule["condition"](med):
                    sev = rule.get("severity", "moderate")
                    if severity_order.get(sev, 0) > severity_order.get(max_severity, 0):
                        max_severity = sev
            except (TypeError, ZeroDivisionError, KeyError):
                continue

    # --- Normal ECG check ---
    has_abnormal = any(
        kw in f.lower()
        for f in findings
        for kw in (
            "prolongado", "curto", "alargado", "limítrofe", "desvio",
            "taquicardia", "bradicardia", "extremo", "flag", "risco",
            "grave", "stemi", "iamcsst", "pré-excitação", "wpw",
        )
    )

    if not has_abnormal:
        findings.append("ECG dentro dos limites da normalidade.")
        camera_notes.append(
            "Todas as câmeras estão funcionando corretamente — cada uma captura "
            "a atividade elétrica exatamente como esperado."
        )

    # --- Build interpretation text ---
    interpretation_parts = ["## Interpretação do ECG\n"]

    # Urgency banner
    if max_severity == "critical":
        interpretation_parts.append("⚠️ **URGENTE** — Achados que requerem avaliação imediata!\n")
    elif max_severity == "high":
        interpretation_parts.append("⚡ **ATENÇÃO** — Achados significativos identificados.\n")

    interpretation_parts.append("### Achados")
    for f in findings:
        interpretation_parts.append(f"- {f}")

    if camera_notes:
        interpretation_parts.append("\n### Analogias com Câmera")
        for c in camera_notes:
            interpretation_parts.append(f"- {c}")

    if not differentials:
        differentials.append("Sem diagnósticos diferenciais relevantes — ECG compatível com normalidade.")

    if not recommendations:
        recommendations.append("Correlacionar com quadro clínico.")
        recommendations.append("Repetir ECG se houver alteração clínica.")

    # Standard recommendations based on severity
    if max_severity == "critical":
        recommendations.insert(0, "AVALIAÇÃO MÉDICA IMEDIATA recomendada.")
        recommendations.append("Considerar monitorização contínua.")
    elif max_severity == "high":
        recommendations.append("Avaliação cardiológica recomendada em breve.")

    # Confidence
    if has_abnormal and len(differentials) > 3:
        confidence = "moderada"
    elif not has_abnormal:
        confidence = "alta"
    elif max_severity in ("critical", "high"):
        confidence = "alta"
    else:
        confidence = "moderada"

    interpretation_text = "\n".join(interpretation_parts)

    return {
        "interpretation": interpretation_text,
        "differentials": differentials,
        "recommendations": recommendations,
        "confidence": confidence,
        "severity": max_severity,
    }


# ---------------------------------------------------------------------------
# ST territory analysis
# ---------------------------------------------------------------------------

_TERRITORY_LEADS: dict[str, list[str]] = {
    "inferior": ["II", "III", "aVF"],
    "anterior": ["V1", "V2", "V3", "V4"],
    "lateral": ["I", "aVL", "V5", "V6"],
    "septal": ["V1", "V2"],
    "lateral_alto": ["I", "aVL"],
    "apical": ["V3", "V4", "V5"],
}

_RECIPROCAL_MAP: dict[str, list[str]] = {
    "inferior": ["I", "aVL"],
    "anterior": ["II", "III", "aVF"],
    "lateral": ["III", "aVF", "V1"],
}

_CORONARY_MAP: dict[str, str] = {
    "inferior": "Coronária direita (CD) ou circunflexa (Cx)",
    "anterior": "Descendente anterior (DA)",
    "lateral": "Circunflexa (Cx) ou ramo diagonal da DA",
    "septal": "Descendente anterior (DA) proximal",
    "lateral_alto": "Circunflexa (Cx) ou diagonal da DA",
}


def _analyze_st_territories(st_changes: dict[str, str]) -> dict:
    """Analyze ST changes for territorial patterns (STEMI detection)."""
    findings: list[str] = []
    camera_notes: list[str] = []
    differentials: list[str] = []
    recommendations: list[str] = []

    supra_leads = {lead for lead, change in st_changes.items() if change.lower() == "supra"}
    infra_leads = {lead for lead, change in st_changes.items() if change.lower() == "infra"}

    # Detect STEMI territory
    stemi_territories: list[str] = []
    for territory, leads in _TERRITORY_LEADS.items():
        territory_supra = supra_leads & set(leads)
        if len(territory_supra) >= 2:
            stemi_territories.append(territory)

            # Check reciprocal changes
            reciprocal = _RECIPROCAL_MAP.get(territory, [])
            reciprocal_present = infra_leads & set(reciprocal)

            coronary = _CORONARY_MAP.get(territory, "artéria coronária não determinada")

            findings.append(
                f"Padrão de IAMCSST {territory}: supra de ST em "
                f"{', '.join(sorted(territory_supra))}"
                + (f" com reciprocidade em {', '.join(sorted(reciprocal_present))}"
                   if reciprocal_present else "")
                + f". Território coronariano: {coronary}."
            )

            camera_notes.append(
                f"As câmeras {', '.join(sorted(territory_supra))} estão vendo LESÃO AGUDA "
                f"na parede {territory} do coração — como se essa região estivesse "
                f"brilhando intensamente."
                + (f" As câmeras do lado oposto ({', '.join(sorted(reciprocal_present))}) "
                   "veem o reflexo invertido (imagem espelhada), confirmando que a lesão é real."
                   if reciprocal_present else "")
            )

            differentials.append(f"IAMCSST {territory} — oclusão de {coronary}")
            recommendations.append(f"EMERGÊNCIA: Ativar protocolo de cateterismo para IAMCSST {territory}!")

    # Pericarditis pattern: diffuse supra without territorial reciprocity
    if len(supra_leads) >= 5 and not stemi_territories:
        # Diffuse supra across multiple territories
        frontal_supra = supra_leads & {"I", "II", "III", "aVL", "aVF"}
        precordial_supra = supra_leads & {"V1", "V2", "V3", "V4", "V5", "V6"}
        if frontal_supra and precordial_supra:
            findings.append(
                f"Supradesnivelamento difuso de ST em {len(supra_leads)} derivações — "
                "padrão sugestivo de pericardite aguda (não territorial)."
            )
            differentials.append("Pericardite aguda — supra difuso sem reciprocidade territorial")
            camera_notes.append(
                "TODAS as câmeras estão vendo brilho aumentado — não é uma área específica, "
                "mas toda a superfície do coração parece inflamada."
            )

    # Isolated infra
    if infra_leads and not supra_leads:
        findings.append(
            f"Infradesnivelamento de ST em {', '.join(sorted(infra_leads))} sem supra correspondente — "
            "considerar isquemia subendocárdica ou efeito medicamentoso."
        )

    return {
        "findings": findings,
        "camera_notes": camera_notes,
        "differentials": differentials,
        "recommendations": recommendations,
    }


# ---------------------------------------------------------------------------
# Rule-based differential diagnosis
# ---------------------------------------------------------------------------

def generate_differential(findings: list[str]) -> list[dict]:
    """Generate rule-based differential diagnoses from a list of ECG findings.

    Parameters
    ----------
    findings : list[str]
        List of ECG findings/abnormalities as free-text strings.

    Returns
    -------
    list[dict]
        Each dict has ``{"diagnosis": str, "support": str, "camera_analogy": str}``.
    """
    results: list[dict] = []
    seen: set[str] = set()

    for finding in findings:
        fl = finding.lower()

        # PR interval
        if "pr" in fl and ("prolongado" in fl or "longo" in fl or "> 200" in fl or ">200" in fl):
            _add_differential(results, seen, {
                "diagnosis": "Bloqueio AV de 1.° grau",
                "support": "Intervalo PR prolongado (>200 ms)",
                "camera_analogy": "O atraso entre o flash e o obturador está maior que o normal.",
            })
            _add_differential(results, seen, {
                "diagnosis": "Efeito medicamentoso (betabloqueador, digital)",
                "support": "PR prolongado pode ser efeito de drogas cronotrópicas negativas",
                "camera_analogy": "Alguém ajustou o timer da câmera para demorar mais entre o flash e a foto.",
            })

        if "pr" in fl and ("curto" in fl or "< 120" in fl or "<120" in fl):
            _add_differential(results, seen, {
                "diagnosis": "Síndrome de Wolff-Parkinson-White",
                "support": "PR curto com possível onda delta",
                "camera_analogy": "Existe um atalho no mecanismo — o obturador dispara quase junto com o flash.",
            })
            _add_differential(results, seen, {
                "diagnosis": "Síndrome de Lown-Ganong-Levine",
                "support": "PR curto sem onda delta",
                "camera_analogy": "O timer da câmera foi encurtado, mas o obturador funciona normalmente.",
            })

        # QRS
        if "qrs" in fl and ("alargado" in fl or "largo" in fl or "> 120" in fl or ">120" in fl):
            _add_differential(results, seen, {
                "diagnosis": "Bloqueio de ramo direito",
                "support": "QRS alargado com morfologia RSR' em V1",
                "camera_analogy": "O obturador está abrindo em duas etapas — primeiro rápido, depois lento.",
            })
            _add_differential(results, seen, {
                "diagnosis": "Bloqueio de ramo esquerdo",
                "support": "QRS alargado com QS ou rS em V1",
                "camera_analogy": "O obturador está preso e demora mais para completar o ciclo.",
            })
            _add_differential(results, seen, {
                "diagnosis": "Ritmo ventricular / Marca-passo",
                "support": "QRS alargado com morfologia bizarra",
                "camera_analogy": "A câmera está sendo acionada manualmente em vez do mecanismo automático.",
            })

        # QTc
        if "qtc" in fl and ("prolongado" in fl or "longo" in fl or "> 460" in fl or ">460" in fl):
            _add_differential(results, seen, {
                "diagnosis": "Síndrome do QT longo congênito",
                "support": "QTc prolongado sem causa secundária identificável",
                "camera_analogy": "O ciclo completo da câmera é geneticamente mais longo.",
            })
            _add_differential(results, seen, {
                "diagnosis": "QT longo adquirido (medicamentoso/eletrolítico)",
                "support": "QTc prolongado com uso de fármacos ou distúrbio iônico",
                "camera_analogy": "Algo externo está fazendo a câmera demorar mais para resetar.",
            })

        # Tachycardia
        if "taquicardia" in fl:
            _add_differential(results, seen, {
                "diagnosis": "Taquicardia sinusal",
                "support": "FC >100 bpm com ondas P normais precedendo cada QRS",
                "camera_analogy": "O fotógrafo está disparando mais rápido, mas cada foto é normal.",
            })
            _add_differential(results, seen, {
                "diagnosis": "Taquicardia supraventricular paroxística",
                "support": "FC 150-250 bpm, QRS estreito, início/fim súbitos",
                "camera_analogy": "A câmera entrou em modo burst — disparo automático ultrarrápido.",
            })

        # Bradycardia
        if "bradicardia" in fl:
            _add_differential(results, seen, {
                "diagnosis": "Bradicardia sinusal fisiológica",
                "support": "FC <60 bpm em atleta ou durante sono, ondas P normais",
                "camera_analogy": "O fotógrafo profissional tira menos fotos — cada uma com mais qualidade.",
            })
            _add_differential(results, seen, {
                "diagnosis": "Bloqueio AV de alto grau",
                "support": "Dissociação entre ondas P e complexos QRS",
                "camera_analogy": "O flash dispara mas o obturador nem sempre responde.",
            })

        # Axis deviation
        if "eixo" in fl and "esquerda" in fl:
            _add_differential(results, seen, {
                "diagnosis": "Bloqueio divisional anterossuperior esquerdo (BDAS)",
                "support": "Desvio do eixo para esquerda (-30° a -90°)",
                "camera_analogy": "As câmeras do lado esquerdo capturam sinais mais fortes.",
            })
            _add_differential(results, seen, {
                "diagnosis": "Hipertrofia ventricular esquerda",
                "support": "Eixo desviado com critérios de voltagem aumentada",
                "camera_analogy": "O lado esquerdo do cenário está tão grande que domina todas as fotos das câmeras esquerdas.",
            })

        if "eixo" in fl and "direita" in fl:
            _add_differential(results, seen, {
                "diagnosis": "Hipertrofia ventricular direita",
                "support": "Desvio do eixo para direita (>90°) com R alto em V1",
                "camera_analogy": "As câmeras do lado direito estão captando sinais desproporcionalmente fortes.",
            })
            _add_differential(results, seen, {
                "diagnosis": "Tromboembolismo pulmonar",
                "support": "Desvio de eixo agudo com padrão S1Q3T3",
                "camera_analogy": "Uma obstrução súbita fez o lado direito inchar e dominar as câmeras.",
            })

        # ST changes
        if "supra" in fl or "st" in fl and "elev" in fl:
            _add_differential(results, seen, {
                "diagnosis": "Infarto agudo do miocárdio com supra de ST",
                "support": "Supradesnivelamento >1mm em derivações contíguas",
                "camera_analogy": "Algumas câmeras mostram uma área brilhante demais — sinal de lesão aguda.",
            })
            _add_differential(results, seen, {
                "diagnosis": "Pericardite aguda",
                "support": "Supradesnivelamento difuso e côncavo",
                "camera_analogy": "Todas as câmeras mostram brilho difuso — inflamação ao redor do coração.",
            })

        # Fibrilação
        if "fibrilação" in fl or "fa" == fl.strip() or "irregular" in fl:
            _add_differential(results, seen, {
                "diagnosis": "Fibrilação atrial",
                "support": "Ritmo irregularmente irregular, sem ondas P definidas",
                "camera_analogy": "O flash está disparando caoticamente — sem ritmo ou padrão definido.",
            })

    # Fallback if no matches
    if not results:
        results.append({
            "diagnosis": "Sem diagnóstico diferencial específico identificado",
            "support": "Os achados não correspondem a padrões patológicos conhecidos nas regras offline",
            "camera_analogy": "Todas as câmeras parecem estar funcionando dentro do esperado.",
        })

    return results


def _add_differential(
    results: list[dict], seen: set[str], entry: dict
) -> None:
    """Add a differential if not already present."""
    if entry["diagnosis"] not in seen:
        seen.add(entry["diagnosis"])
        results.append(entry)

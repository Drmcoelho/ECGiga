"""Detecção de distúrbios eletrolíticos a partir de padrões de ECG.

Detecta manifestações eletrocardiográficas de:
- Hipercalemia: ondas T apiculadas, prolongamento de PR, alargamento de QRS, onda senoidal
- Hipocalemia: infradesnivelamento de ST, achatamento de T, ondas U, prolongamento de QT
- Hipercalcemia: QT encurtado, ondas de Osborn (sobreposição com hipotermia)
- Hipocalcemia: QT prolongado (principalmente segmento ST), alterações de onda T

Referências:
- Diercks et al., "Electrocardiographic manifestations: electrolyte abnormalities",
  J Emerg Med, 2004.
- Slovis & Jenkins, "ABC of clinical electrocardiography: Conditions not
  primarily affecting the heart", BMJ, 2002.
"""

from __future__ import annotations

from typing import Any


# Estágios de progressão eletrocardiográfica da hipercalemia
_HYPERKALEMIA_STAGES = {
    "mild": {
        "k_range": "5.5-6.5 mEq/L",
        "findings": ["T apiculadas (peaked T waves)", "QTc possivelmente encurtado"],
        "severity": "low",
    },
    "moderate": {
        "k_range": "6.5-7.5 mEq/L",
        "findings": [
            "T apiculadas altas e estreitas",
            "PR prolongado",
            "Achatamento de onda P",
            "QRS início de alargamento",
        ],
        "severity": "high",
    },
    "severe": {
        "k_range": "7.5-8.5 mEq/L",
        "findings": [
            "Ausência de onda P",
            "QRS muito alargado",
            "Padrão de onda senoidal",
            "Possível ritmo idioventricular",
        ],
        "severity": "critical",
    },
    "critical": {
        "k_range": ">8.5 mEq/L",
        "findings": [
            "Padrão sine wave",
            "QRS extremamente largo fundindo com T",
            "Risco iminente de FV/assistolia",
        ],
        "severity": "critical",
    },
}


def detect_hyperkalemia_pattern(
    report: dict,
    t_wave_amplitude: dict[str, float] | None = None,
    t_wave_peaked: list[str] | None = None,
) -> dict[str, Any]:
    """Detecta padrão eletrocardiográfico de hipercalemia.

    Utiliza medições de intervalos e características morfológicas para estimar
    o estágio da hipercalemia com base na progressão eletrocardiográfica.

    Parâmetros
    ----------
    report : dict
        Laudo de ECG com intervalos, eixo, flags.
    t_wave_amplitude : dict, opcional
        Amplitude da onda T por derivação em mV (ex.: {"V2": 1.2, "V3": 1.4}).
    t_wave_peaked : list[str], opcional
        Lista de derivações com ondas T apiculadas.

    Retorna
    -------
    dict
        - detected: bool
        - stage: str ('mild', 'moderate', 'severe', 'critical', 'none')
        - confidence: float (0-1)
        - findings: list[str]
        - recommendations: list[str]
        - details: str
    """
    iv = (report.get("intervals_refined") or report.get("intervals") or {}).get("median", {})
    flags = [f.lower() for f in report.get("flags", [])]

    findings: list[str] = []
    score = 0.0

    pr_ms = iv.get("PR_ms")
    qrs_ms = iv.get("QRS_ms")
    qtc = iv.get("QTc_B")
    rr_s = iv.get("RR_s")
    hr = 60.0 / rr_s if rr_s and rr_s > 0 else None

    # Estágio 1: Ondas T apiculadas (hipercalemia leve)
    peaked_count = 0
    if t_wave_peaked:
        peaked_count = len(t_wave_peaked)
        if peaked_count >= 2:
            findings.append(f"T apiculadas em {', '.join(t_wave_peaked)}")
            score += 0.3
    if t_wave_amplitude:
        tall_t_leads = [lead for lead, amp in t_wave_amplitude.items() if amp > 0.8]
        if tall_t_leads:
            findings.append(f"T de alta amplitude em {', '.join(tall_t_leads)}")
            score += 0.2

    # Verifica flags de T apiculada
    if any("t apiculada" in f or "peaked t" in f or "t pontia" in f for f in flags):
        findings.append("Flag: T apiculadas detectadas")
        score += 0.2

    # Estágio 2: Prolongamento de PR + alargamento de QRS (moderado)
    if pr_ms and pr_ms > 200:
        findings.append(f"PR prolongado ({pr_ms:.0f} ms)")
        score += 0.15

    if qrs_ms and qrs_ms > 120:
        findings.append(f"QRS alargado ({qrs_ms:.0f} ms)")
        score += 0.2
        if qrs_ms > 160:
            findings.append(f"QRS muito alargado ({qrs_ms:.0f} ms) — padrão de hipercalemia grave")
            score += 0.3

    # Estágio 3: Ausência de onda P + QRS muito largo (grave)
    if any("ausência de p" in f or "sem onda p" in f for f in flags):
        findings.append("Ausência de onda P")
        score += 0.3

    # QTc curto (hipercalemia precoce pode encurtar QT)
    if qtc and qtc < 340:
        findings.append(f"QTc curto ({qtc:.0f} ms) — possível hipercalemia precoce")
        score += 0.1

    # Padrão de onda senoidal nas flags
    if any("onda senoidal" in f or "sine wave" in f for f in flags):
        findings.append("Padrão de onda senoidal — hipercalemia crítica!")
        score += 0.5

    # Combinado: PR + QRS + T apiculada = sinal mais forte
    if pr_ms and pr_ms > 200 and qrs_ms and qrs_ms > 120 and peaked_count >= 1:
        score += 0.2
        findings.append("Tríade: PR↑ + QRS↑ + T apiculadas — altamente sugestivo")

    # Determina estágio
    score = min(1.0, score)
    if score > 0.7:
        stage = "severe" if qrs_ms and qrs_ms > 160 else "moderate"
    elif score > 0.4:
        stage = "moderate" if pr_ms and pr_ms > 200 else "mild"
    elif score > 0.15:
        stage = "mild"
    else:
        stage = "none"

    detected = stage != "none"

    recommendations = []
    if detected:
        stage_info = _HYPERKALEMIA_STAGES.get(stage, {})
        recommendations.append(f"Dosagem sérica de potássio URGENTE (padrão sugere K+ ~ {stage_info.get('k_range', '?')})")
        if stage in ("severe", "critical"):
            recommendations.extend([
                "Gluconato de cálcio IV imediato (estabilização de membrana)",
                "Insulina + glicose IV (shift de K+ para intracelular)",
                "Monitorização cardíaca contínua",
                "Considerar diálise de emergência",
            ])
        elif stage == "moderate":
            recommendations.extend([
                "Gluconato de cálcio IV se ECG progressivo",
                "Poliestirenossulfonato (Kayexalate) ou patiromer",
                "Monitorização ECG",
            ])
        else:
            recommendations.append("Correção com resinas ou diuréticos conforme nível sérico")

    details = (
        f"{'Padrão de hipercalemia detectado' if detected else 'Sem padrão claro de hipercalemia'}. "
        f"Estágio estimado: {stage}. Confiança: {score:.0%}."
    )

    return {
        "detected": detected,
        "stage": stage,
        "confidence": round(score, 3),
        "findings": findings,
        "recommendations": recommendations,
        "details": details,
    }


def detect_hypokalemia_pattern(
    report: dict,
    u_wave_present: list[str] | None = None,
    t_wave_flat: list[str] | None = None,
    st_depression_leads: list[str] | None = None,
) -> dict[str, Any]:
    """Detecta padrão eletrocardiográfico de hipocalemia.

    Progressão eletrocardiográfica da hipocalemia:
    1. Achatamento de onda T
    2. Infradesnivelamento de ST
    3. Proeminência de onda U
    4. Fusão T-U (aparente prolongamento de QT)
    5. Grave: proeminência de onda P, alargamento de QRS

    Parâmetros
    ----------
    report : dict
        Laudo de ECG.
    u_wave_present : list[str], opcional
        Derivações com ondas U.
    t_wave_flat : list[str], opcional
        Derivações com ondas T achatadas.
    st_depression_leads : list[str], opcional
        Derivações com infradesnivelamento de ST.

    Retorna
    -------
    dict
        - detected: bool
        - severity: str ('mild', 'moderate', 'severe', 'none')
        - confidence: float (0-1)
        - findings: list[str]
        - estimated_k_range: str
        - details: str
    """
    iv = (report.get("intervals_refined") or report.get("intervals") or {}).get("median", {})
    flags = [f.lower() for f in report.get("flags", [])]

    findings: list[str] = []
    score = 0.0

    qtc = iv.get("QTc_B")

    # Ondas U (marca registrada da hipocalemia)
    if u_wave_present:
        findings.append(f"Onda U presente em {', '.join(u_wave_present)}")
        score += 0.35
    if any("onda u" in f for f in flags):
        findings.append("Flag: onda U detectada")
        score += 0.2

    # Achatamento de onda T
    if t_wave_flat:
        findings.append(f"T achatada em {', '.join(t_wave_flat)}")
        score += 0.2

    # Infradesnivelamento de ST
    if st_depression_leads:
        findings.append(f"Infra de ST em {', '.join(st_depression_leads)}")
        score += 0.15

    # Prolongamento de QTc (por fusão T-U)
    if qtc and qtc > 480:
        findings.append(f"QTc prolongado ({qtc:.0f} ms) — possível fusão T-U")
        score += 0.15
    elif qtc and qtc > 460:
        findings.append(f"QTc limítrofe ({qtc:.0f} ms)")
        score += 0.05

    # Detecção baseada em flags
    if any("hipocalemia" in f or "hypokalemia" in f for f in flags):
        score += 0.3
    if any("t achatada" in f or "flat t" in f for f in flags):
        findings.append("Flag: T achatada")
        score += 0.15
    if any("infra" in f and "st" in f for f in flags):
        score += 0.1

    score = min(1.0, score)

    # Estimativa de severidade
    if score > 0.6:
        severity = "severe"
        k_range = "< 2.5 mEq/L"
    elif score > 0.35:
        severity = "moderate"
        k_range = "2.5-3.0 mEq/L"
    elif score > 0.15:
        severity = "mild"
        k_range = "3.0-3.5 mEq/L"
    else:
        severity = "none"
        k_range = "> 3.5 mEq/L (normal)"

    detected = severity != "none"

    details = (
        f"{'Padrão de hipocalemia detectado' if detected else 'Sem padrão de hipocalemia'}. "
        f"Severidade estimada: {severity}. K+ estimado: {k_range}."
    )

    return {
        "detected": detected,
        "severity": severity,
        "confidence": round(score, 3),
        "findings": findings,
        "estimated_k_range": k_range,
        "details": details,
    }


def detect_calcium_abnormality(
    report: dict,
    osborn_waves: bool = False,
) -> dict[str, Any]:
    """Detecta padrões eletrocardiográficos de alterações de cálcio.

    - Hipercalcemia: QTc encurtado (principalmente segmento ST curto)
    - Hipocalcemia: QTc prolongado (principalmente segmento ST prolongado)
    - Ondas de Osborn (J) sugerem hipotermia mas sobrepõem-se à hipercalcemia

    Parâmetros
    ----------
    report : dict
        Laudo de ECG.
    osborn_waves : bool
        Se ondas de Osborn (J) estão presentes.

    Retorna
    -------
    dict
        - detected: bool
        - abnormality: str ('hypercalcemia', 'hypocalcemia', 'none')
        - confidence: float (0-1)
        - findings: list[str]
        - details: str
    """
    iv = (report.get("intervals_refined") or report.get("intervals") or {}).get("median", {})
    flags = [f.lower() for f in report.get("flags", [])]

    findings: list[str] = []

    qtc = iv.get("QTc_B")
    qt_ms = iv.get("QT_ms")

    # Hipercalcemia: QTc curto
    if qtc and qtc < 340:
        findings.append(f"QTc encurtado ({qtc:.0f} ms) — sugere hipercalcemia")
        if osborn_waves:
            findings.append("Ondas J (Osborn) presentes — considerar hipotermia/hipercalcemia")
        return {
            "detected": True,
            "abnormality": "hypercalcemia",
            "confidence": 0.6 if qtc < 320 else 0.4,
            "findings": findings,
            "details": f"QTc curto ({qtc:.0f} ms) sugestivo de hipercalcemia. Dosar cálcio sérico.",
        }

    # Hipocalcemia: QTc prolongado (principalmente por prolongamento do ST)
    if qtc and qtc > 480:
        # Tenta distinguir de outras causas de QT longo
        qrs_ms = iv.get("QRS_ms", 0)
        # Hipocalcemia prolonga o segmento ST, não a onda T
        # Se QRS normal mas QT muito longo, mais provável hipocalcemia
        if qrs_ms and qrs_ms < 120:
            findings.append(f"QTc prolongado ({qtc:.0f} ms) com QRS normal — possível hipocalcemia")
            return {
                "detected": True,
                "abnormality": "hypocalcemia",
                "confidence": 0.4,
                "findings": findings,
                "details": (
                    f"QTc prolongado ({qtc:.0f} ms) com QRS normal sugere "
                    "prolongamento do segmento ST (hipocalcemia). Dosar cálcio sérico."
                ),
            }

    if any("hipercalcemia" in f for f in flags):
        return {
            "detected": True,
            "abnormality": "hypercalcemia",
            "confidence": 0.5,
            "findings": ["Flag de hipercalcemia detectada"],
            "details": "Flag de hipercalcemia presente. Confirmar com dosagem sérica.",
        }

    if any("hipocalcemia" in f for f in flags):
        return {
            "detected": True,
            "abnormality": "hypocalcemia",
            "confidence": 0.5,
            "findings": ["Flag de hipocalcemia detectada"],
            "details": "Flag de hipocalcemia presente. Confirmar com dosagem sérica.",
        }

    return {
        "detected": False,
        "abnormality": "none",
        "confidence": 0.0,
        "findings": [],
        "details": "Sem padrão sugestivo de distúrbio de cálcio.",
    }

"""Electrolyte disturbance detection from ECG patterns.

Detects ECG manifestations of:
- Hyperkalemia: peaked T waves, PR prolongation, QRS widening, sine wave
- Hypokalemia: ST depression, T flattening, U waves, QT prolongation
- Hypercalcemia: shortened QT, Osborn waves (hypothermia overlap)
- Hypocalcemia: prolonged QT (primarily ST segment), T wave changes

References:
- Diercks et al., "Electrocardiographic manifestations: electrolyte abnormalities",
  J Emerg Med, 2004.
- Slovis & Jenkins, "ABC of clinical electrocardiography: Conditions not
  primarily affecting the heart", BMJ, 2002.
"""

from __future__ import annotations

from typing import Any


# Hyperkalemia ECG progression stages
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
    """Detect ECG pattern of hyperkalemia.

    Uses interval measurements and morphological features to estimate
    the stage of hyperkalemia based on ECG progression.

    Parameters
    ----------
    report : dict
        ECG report with intervals, axis, flags.
    t_wave_amplitude : dict, optional
        T-wave amplitude per lead in mV (e.g., {"V2": 1.2, "V3": 1.4}).
    t_wave_peaked : list[str], optional
        List of leads showing peaked T waves.

    Returns
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

    # Stage 1: Peaked T waves (mild hyperkalemia)
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

    # Check flags for peaked T
    if any("t apiculada" in f or "peaked t" in f or "t pontia" in f for f in flags):
        findings.append("Flag: T apiculadas detectadas")
        score += 0.2

    # Stage 2: PR prolongation + QRS widening (moderate)
    if pr_ms and pr_ms > 200:
        findings.append(f"PR prolongado ({pr_ms:.0f} ms)")
        score += 0.15

    if qrs_ms and qrs_ms > 120:
        findings.append(f"QRS alargado ({qrs_ms:.0f} ms)")
        score += 0.2
        if qrs_ms > 160:
            findings.append(f"QRS muito alargado ({qrs_ms:.0f} ms) — padrão de hipercalemia grave")
            score += 0.3

    # Stage 3: P wave absence + very wide QRS (severe)
    if any("ausência de p" in f or "sem onda p" in f for f in flags):
        findings.append("Ausência de onda P")
        score += 0.3

    # Short QTc (early hyperkalemia can shorten QT)
    if qtc and qtc < 340:
        findings.append(f"QTc curto ({qtc:.0f} ms) — possível hipercalemia precoce")
        score += 0.1

    # Sine wave pattern in flags
    if any("onda senoidal" in f or "sine wave" in f for f in flags):
        findings.append("Padrão de onda senoidal — hipercalemia crítica!")
        score += 0.5

    # Combined: PR + QRS + peaked T = stronger signal
    if pr_ms and pr_ms > 200 and qrs_ms and qrs_ms > 120 and peaked_count >= 1:
        score += 0.2
        findings.append("Tríade: PR↑ + QRS↑ + T apiculadas — altamente sugestivo")

    # Determine stage
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
    """Detect ECG pattern of hypokalemia.

    Hypokalemia ECG progression:
    1. T wave flattening
    2. ST depression
    3. U wave prominence
    4. T-U fusion (apparent QT prolongation)
    5. Severe: P wave prominence, QRS widening

    Parameters
    ----------
    report : dict
        ECG report.
    u_wave_present : list[str], optional
        Leads showing U waves.
    t_wave_flat : list[str], optional
        Leads with flattened T waves.
    st_depression_leads : list[str], optional
        Leads with ST depression.

    Returns
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

    # U waves (hallmark of hypokalemia)
    if u_wave_present:
        findings.append(f"Onda U presente em {', '.join(u_wave_present)}")
        score += 0.35
    if any("onda u" in f for f in flags):
        findings.append("Flag: onda U detectada")
        score += 0.2

    # T wave flattening
    if t_wave_flat:
        findings.append(f"T achatada em {', '.join(t_wave_flat)}")
        score += 0.2

    # ST depression
    if st_depression_leads:
        findings.append(f"Infra de ST em {', '.join(st_depression_leads)}")
        score += 0.15

    # QTc prolongation (from T-U fusion)
    if qtc and qtc > 480:
        findings.append(f"QTc prolongado ({qtc:.0f} ms) — possível fusão T-U")
        score += 0.15
    elif qtc and qtc > 460:
        findings.append(f"QTc limítrofe ({qtc:.0f} ms)")
        score += 0.05

    # Flag-based detection
    if any("hipocalemia" in f or "hypokalemia" in f for f in flags):
        score += 0.3
    if any("t achatada" in f or "flat t" in f for f in flags):
        findings.append("Flag: T achatada")
        score += 0.15
    if any("infra" in f and "st" in f for f in flags):
        score += 0.1

    score = min(1.0, score)

    # Severity estimation
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
    """Detect ECG patterns of calcium abnormalities.

    - Hypercalcemia: shortened QTc (primarily short ST segment)
    - Hypocalcemia: prolonged QTc (primarily prolonged ST segment)
    - Osborn (J) waves suggest hypothermia but overlap with hypercalcemia

    Parameters
    ----------
    report : dict
        ECG report.
    osborn_waves : bool
        Whether Osborn (J) waves are present.

    Returns
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

    # Hypercalcemia: short QTc
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

    # Hypocalcemia: prolonged QTc (primarily from prolonged ST)
    if qtc and qtc > 480:
        # Try to distinguish from other causes of long QT
        qrs_ms = iv.get("QRS_ms", 0)
        # Hypocalcemia prolongs ST segment, not T wave
        # If QRS is normal but QT very long, more likely hypocalcemia
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

"""Ischemia pattern detection and differentiation.

Detects and differentiates:
- NSTEMI patterns (ST depression, T inversion in contiguous leads)
- STEMI vs early repolarization (using Smith criteria, convexity, reciprocity)
- Wellens syndrome (Type A and B)
- de Winter pattern (STEMI equivalent)

References:
- Smith et al., "Electrocardiographic differentiation of early repolarization
  from subtle anterior STEMI", Ann Emerg Med, 2012.
- Rhinehardt et al., "Electrocardiographic manifestations of Wellens' syndrome",
  Am J Emerg Med, 2002.
- de Winter et al., "A new ECG sign of proximal LAD occlusion", NEJM, 2008.
"""

from __future__ import annotations

from typing import Any


# Contiguous lead groups for NSTEMI pattern recognition
_CONTIGUOUS_LEADS = {
    "anterior": ["V1", "V2", "V3", "V4"],
    "inferior": ["II", "III", "aVF"],
    "lateral": ["I", "aVL", "V5", "V6"],
    "septal": ["V1", "V2"],
    "anteroseptal": ["V1", "V2", "V3"],
    "anterolateral": ["V3", "V4", "V5", "V6"],
    "inferolateral": ["II", "III", "aVF", "V5", "V6"],
    "high_lateral": ["I", "aVL"],
}


def detect_nstemi_pattern(
    st_changes: dict[str, str],
    t_inversions: list[str] | None = None,
    troponin_positive: bool | None = None,
) -> dict[str, Any]:
    """Detect NSTEMI pattern from ST-T changes.

    NSTEMI criteria:
    - New ST depression >=0.5mm in >=2 contiguous leads
    - New T-wave inversion >=1mm in >=2 contiguous leads
    - Dynamic changes increase specificity

    Parameters
    ----------
    st_changes : dict
        Lead -> change type ('infra', 'supra', 'normal').
    t_inversions : list[str], optional
        Leads with T-wave inversions.
    troponin_positive : bool, optional
        Whether troponin is elevated.

    Returns
    -------
    dict
        - detected: bool
        - territory: str
        - confidence: float (0-1)
        - criteria_met: list[str]
        - risk_assessment: str ('low', 'intermediate', 'high')
        - details: str
    """
    infra_leads = {lead for lead, change in st_changes.items() if change.lower() == "infra"}
    supra_leads = {lead for lead, change in st_changes.items() if change.lower() == "supra"}
    t_inv_set = set(t_inversions or [])

    criteria_met: list[str] = []
    score = 0.0
    territory = "indeterminado"

    # Check for contiguous ST depression
    for terr_name, leads in _CONTIGUOUS_LEADS.items():
        lead_set = set(leads)
        infra_in_territory = infra_leads & lead_set
        if len(infra_in_territory) >= 2:
            territory = terr_name
            criteria_met.append(
                f"Infra de ST em {', '.join(sorted(infra_in_territory))} "
                f"(território {terr_name})"
            )
            score += 0.4

    # Check for contiguous T inversions
    for terr_name, leads in _CONTIGUOUS_LEADS.items():
        lead_set = set(leads)
        t_inv_in_territory = t_inv_set & lead_set
        if len(t_inv_in_territory) >= 2:
            if territory == "indeterminado":
                territory = terr_name
            criteria_met.append(
                f"T invertida em {', '.join(sorted(t_inv_in_territory))} "
                f"(território {terr_name})"
            )
            score += 0.3

    # Combined ST depression + T inversion = stronger
    if infra_leads and t_inv_set:
        overlap = infra_leads & t_inv_set
        if overlap:
            criteria_met.append("Infra ST + T invertida nas mesmas derivações")
            score += 0.15

    # Widespread ST depression with supra in aVR = left main / 3-vessel disease
    if len(infra_leads) >= 6 and "aVR" in supra_leads:
        criteria_met.append(
            "Infra difuso + supra em aVR — PADRÃO DE LESÃO MULTIARTERIAL / TRONCO!"
        )
        score += 0.3
        territory = "difuso (TCE/3V)"

    # Troponin if available
    if troponin_positive is True:
        criteria_met.append("Troponina positiva")
        score += 0.2
    elif troponin_positive is False:
        criteria_met.append("Troponina negativa (angina instável se padrão presente)")
        score -= 0.1

    score = min(1.0, max(0.0, score))
    detected = score > 0.3

    # Risk assessment
    if score > 0.7 or "TCE" in territory:
        risk = "high"
    elif score > 0.4:
        risk = "intermediate"
    else:
        risk = "low"

    details = (
        f"{'IAMSSST/NSTEMI detectado' if detected else 'Sem padrão claro de NSTEMI'}. "
        f"Território: {territory}. "
        f"Risco: {risk}. Confiança: {score:.0%}."
    )

    return {
        "detected": detected,
        "territory": territory,
        "confidence": round(score, 3),
        "criteria_met": criteria_met,
        "risk_assessment": risk,
        "details": details,
    }


def differentiate_stemi_vs_early_repol(
    st_elevation_mv: dict[str, float],
    t_wave_amplitude: dict[str, float] | None = None,
    patient_age: int | None = None,
    patient_sex: str | None = None,
    reciprocal_changes: bool = False,
    st_morphology: str | None = None,
    qrs_distortion: bool = False,
) -> dict[str, Any]:
    """Differentiate STEMI from benign early repolarization.

    Applies Smith criteria and other differentiating features:
    - ST/T ratio (>0.25 in V1-V4 favors STEMI)
    - ST morphology (convex favors STEMI, concave favors BER)
    - Reciprocal ST depression (favors STEMI)
    - QRS terminal distortion (favors STEMI)
    - Age/sex demographics

    Parameters
    ----------
    st_elevation_mv : dict
        Lead -> ST elevation in millivolts.
    t_wave_amplitude : dict, optional
        Lead -> T wave amplitude in millivolts.
    patient_age : int, optional
        Patient age in years.
    patient_sex : str, optional
        'M' or 'F'.
    reciprocal_changes : bool
        Whether reciprocal ST depression is present.
    st_morphology : str, optional
        'convex' (tombstone), 'concave' (scooped), or 'straight'.
    qrs_distortion : bool
        Whether terminal QRS distortion is present.

    Returns
    -------
    dict
        - classification: str ('STEMI', 'early_repolarization', 'uncertain')
        - stemi_probability: float (0-1)
        - smith_score: float (if applicable)
        - criteria: list[str]
        - details: str
    """
    stemi_points = 0.0
    ber_points = 0.0
    criteria: list[str] = []

    # 1. ST/T amplitude ratio (Smith criterion)
    if t_wave_amplitude:
        st_t_ratios = {}
        precordial = ["V1", "V2", "V3", "V4"]
        for lead in precordial:
            st = st_elevation_mv.get(lead)
            t = t_wave_amplitude.get(lead)
            if st and t and t > 0:
                st_t_ratios[lead] = st / t

        high_ratio_leads = {lead: r for lead, r in st_t_ratios.items() if r > 0.25}
        if high_ratio_leads:
            stemi_points += 0.3
            criteria.append(
                f"ST/T ratio > 0.25 em {', '.join(high_ratio_leads.keys())} "
                f"(favorece STEMI)"
            )
        else:
            ber_points += 0.2
            criteria.append("ST/T ratio < 0.25 (favorece repolarização precoce)")

    # 2. ST morphology
    if st_morphology == "convex":
        stemi_points += 0.25
        criteria.append("Morfologia convexa (tombstone) do ST — forte indicador de STEMI")
    elif st_morphology == "concave":
        ber_points += 0.25
        criteria.append("Morfologia côncava do ST — favorece repolarização precoce")
    elif st_morphology == "straight":
        stemi_points += 0.1
        criteria.append("Morfologia retilínea do ST — possível STEMI precoce")

    # 3. Reciprocal changes
    if reciprocal_changes:
        stemi_points += 0.3
        criteria.append("Alterações recíprocas presentes — forte indicador de STEMI")
    else:
        ber_points += 0.15
        criteria.append("Sem alterações recíprocas (favorece repolarização precoce)")

    # 4. QRS terminal distortion
    if qrs_distortion:
        stemi_points += 0.25
        criteria.append("Distorção terminal do QRS — altamente sugestivo de STEMI")

    # 5. Magnitude of ST elevation
    max_st = max(st_elevation_mv.values()) if st_elevation_mv else 0
    if max_st > 0.5:  # > 5mm
        stemi_points += 0.2
        criteria.append(f"Supra de ST muito elevado ({max_st:.1f} mV)")
    elif max_st < 0.1:
        ber_points += 0.1

    # 6. Demographics
    if patient_age is not None:
        if patient_age > 50:
            stemi_points += 0.1
            criteria.append(f"Idade {patient_age} — STEMI mais provável que BER")
        elif patient_age < 35:
            ber_points += 0.1
            criteria.append(f"Idade {patient_age} — BER mais comum nesta faixa")

    if patient_sex == "M" and patient_age and patient_age < 40:
        ber_points += 0.05
        criteria.append("Homem jovem — BER mais prevalente")

    # Calculate probability
    total = stemi_points + ber_points
    stemi_prob = stemi_points / total if total > 0 else 0.5

    if stemi_prob > 0.6:
        classification = "STEMI"
    elif stemi_prob < 0.4:
        classification = "early_repolarization"
    else:
        classification = "uncertain"

    details = (
        f"{'STEMI' if classification == 'STEMI' else 'Repolarização precoce' if classification == 'early_repolarization' else 'Diferenciação incerta'}. "
        f"Probabilidade de STEMI: {stemi_prob:.0%}. "
        f"{'TRATAR COMO STEMI SE DÚVIDA!' if classification == 'uncertain' else ''}"
    )

    return {
        "classification": classification,
        "stemi_probability": round(stemi_prob, 3),
        "smith_score": round(stemi_points, 3),
        "criteria": criteria,
        "details": details,
    }


def detect_wellens_pattern(
    t_wave_morphology: dict[str, str],
    history_chest_pain: bool = False,
    troponin_normal: bool = True,
    st_normal: bool = True,
) -> dict[str, Any]:
    """Detect Wellens syndrome pattern.

    Wellens syndrome indicates critical LAD stenosis:
    - Type A (25%): Biphasic T in V2-V3 (initially positive, then negative)
    - Type B (75%): Deep symmetric T inversion in V2-V3

    Key: occurs in PAIN-FREE period (normal ST during pain-free interval)

    Parameters
    ----------
    t_wave_morphology : dict
        Lead -> T wave description ('biphasic', 'deep_inversion', 'normal', etc.)
    history_chest_pain : bool
        Whether patient has history of chest pain.
    troponin_normal : bool
        Whether troponin is normal or minimally elevated.
    st_normal : bool
        Whether ST segments are normal (important: Wellens is pain-free pattern).

    Returns
    -------
    dict
        - detected: bool
        - wellens_type: str ('A', 'B', 'none')
        - confidence: float (0-1)
        - details: str
    """
    v2_morph = t_wave_morphology.get("V2", "").lower()
    v3_morph = t_wave_morphology.get("V3", "").lower()
    v1_morph = t_wave_morphology.get("V1", "").lower()
    v4_morph = t_wave_morphology.get("V4", "").lower()

    score = 0.0
    wellens_type = "none"
    findings: list[str] = []

    # Type A: Biphasic T in V2-V3
    if "biphasic" in v2_morph or "biphasic" in v3_morph:
        wellens_type = "A"
        score += 0.4
        findings.append("T bifásica em V2-V3 (Wellens tipo A)")

    # Type B: Deep symmetric T inversion in V2-V3
    if "deep_inversion" in v2_morph or "deep_inversion" in v3_morph:
        wellens_type = "B"
        score += 0.4
        findings.append("T invertida profunda e simétrica em V2-V3 (Wellens tipo B)")

    # Spread to V1-V4
    if "deep_inversion" in v1_morph or "deep_inversion" in v4_morph:
        score += 0.1
        findings.append("T invertida estende-se a V1 e/ou V4")

    # Context: pain-free period with normal ST
    if st_normal:
        score += 0.15
        findings.append("ST normal (padrão de período livre de dor)")

    if history_chest_pain:
        score += 0.15
        findings.append("História de dor torácica")

    if troponin_normal:
        score += 0.1
        findings.append("Troponina normal ou minimamente elevada")

    score = min(1.0, score)
    detected = score > 0.4 and wellens_type != "none"

    details = (
        f"{'Síndrome de Wellens detectada' if detected else 'Sem padrão de Wellens'}. "
        f"Tipo: {wellens_type}. "
        f"{'ATENÇÃO: NÃO realizar teste ergométrico! Risco de IAM. Cineangiocoronariografia indicada.' if detected else ''}"
    )

    return {
        "detected": detected,
        "wellens_type": wellens_type,
        "confidence": round(score, 3),
        "findings": findings,
        "details": details,
    }


def detect_de_winter_pattern(
    st_changes: dict[str, str],
    t_wave_morphology: dict[str, str] | None = None,
    t_wave_amplitude: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Detect de Winter pattern (STEMI equivalent).

    de Winter pattern characteristics:
    - Upsloping ST depression at J-point in V1-V6 (1-3mm)
    - Tall, symmetric, peaked T waves in precordial leads
    - Absence of ST elevation in precordials
    - May have slight ST elevation in aVR

    Indicates acute LAD occlusion. Treat as STEMI equivalent.

    Parameters
    ----------
    st_changes : dict
        Lead -> ST change type.
    t_wave_morphology : dict, optional
        Lead -> T wave description.
    t_wave_amplitude : dict, optional
        Lead -> T amplitude in mV.

    Returns
    -------
    dict
        - detected: bool
        - confidence: float (0-1)
        - criteria_met: list[str]
        - details: str
    """
    precordial = ["V1", "V2", "V3", "V4", "V5", "V6"]
    criteria_met: list[str] = []
    score = 0.0

    # Criterion 1: Upsloping ST depression in precordials
    infra_precordial = [
        lead for lead in precordial
        if st_changes.get(lead, "").lower() == "infra"
    ]
    if len(infra_precordial) >= 3:
        criteria_met.append(f"Infra ST em precordiais: {', '.join(infra_precordial)}")
        score += 0.3

    # Criterion 2: Tall/peaked T waves in precordials
    if t_wave_morphology:
        tall_t = [
            lead for lead in precordial
            if "tall" in t_wave_morphology.get(lead, "").lower()
            or "peaked" in t_wave_morphology.get(lead, "").lower()
            or "hiperaguda" in t_wave_morphology.get(lead, "").lower()
        ]
        if tall_t:
            criteria_met.append(f"T hiperagudas em {', '.join(tall_t)}")
            score += 0.3

    if t_wave_amplitude:
        very_tall = [
            lead for lead in precordial
            if (t_wave_amplitude.get(lead, 0) or 0) > 1.0
        ]
        if very_tall:
            criteria_met.append(f"T > 1.0 mV em {', '.join(very_tall)}")
            score += 0.2

    # Criterion 3: No ST elevation in precordials
    supra_precordial = [
        lead for lead in precordial
        if st_changes.get(lead, "").lower() == "supra"
    ]
    if not supra_precordial and infra_precordial:
        criteria_met.append("Ausência de supra de ST precordial (critério de de Winter)")
        score += 0.1

    # Criterion 4: ST elevation in aVR
    if st_changes.get("aVR", "").lower() == "supra":
        criteria_met.append("Supra em aVR")
        score += 0.1

    score = min(1.0, score)
    detected = score > 0.5

    details = (
        f"{'Padrão de de Winter detectado' if detected else 'Sem padrão de de Winter'}. "
        f"{'EQUIVALENTE DE STEMI — ativar protocolo de cateterismo!' if detected else ''} "
        f"Confiança: {score:.0%}."
    )

    return {
        "detected": detected,
        "confidence": round(score, 3),
        "criteria_met": criteria_met,
        "details": details,
    }

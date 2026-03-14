"""Detecção e diferenciação de padrões isquêmicos.

Detecta e diferencia:
- Padrões de NSTEMI (infradesnivelamento de ST, inversão de T em derivações contíguas)
- STEMI vs repolarização precoce (usando critérios de Smith, convexidade, reciprocidade)
- Síndrome de Wellens (Tipo A e B)
- Padrão de de Winter (equivalente de STEMI)

Referências:
- Smith et al., "Electrocardiographic differentiation of early repolarization
  from subtle anterior STEMI", Ann Emerg Med, 2012.
- Rhinehardt et al., "Electrocardiographic manifestations of Wellens' syndrome",
  Am J Emerg Med, 2002.
- de Winter et al., "A new ECG sign of proximal LAD occlusion", NEJM, 2008.
"""

from __future__ import annotations

from typing import Any


# Grupos de derivações contíguas para reconhecimento de padrão de NSTEMI
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
    """Detecta padrão de NSTEMI a partir de alterações ST-T.

    Critérios de NSTEMI:
    - Infradesnivelamento de ST novo >= 0,5mm em >= 2 derivações contíguas
    - Inversão de onda T nova >= 1mm em >= 2 derivações contíguas
    - Alterações dinâmicas aumentam a especificidade

    Parâmetros
    ----------
    st_changes : dict
        Derivação -> tipo de alteração ('infra', 'supra', 'normal').
    t_inversions : list[str], opcional
        Derivações com inversão de onda T.
    troponin_positive : bool, opcional
        Se troponina está elevada.

    Retorna
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

    # Verifica infradesnivelamento de ST contíguo
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

    # Verifica inversões de T contíguas
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

    # Combinado: infradesnivelamento de ST + inversão de T = mais forte
    if infra_leads and t_inv_set:
        overlap = infra_leads & t_inv_set
        if overlap:
            criteria_met.append("Infra ST + T invertida nas mesmas derivações")
            score += 0.15

    # Infra difuso com supra em aVR = doença de tronco / triarterial
    if len(infra_leads) >= 6 and "aVR" in supra_leads:
        criteria_met.append(
            "Infra difuso + supra em aVR — PADRÃO DE LESÃO MULTIARTERIAL / TRONCO!"
        )
        score += 0.3
        territory = "difuso (TCE/3V)"

    # Troponina se disponível
    if troponin_positive is True:
        criteria_met.append("Troponina positiva")
        score += 0.2
    elif troponin_positive is False:
        criteria_met.append("Troponina negativa (angina instável se padrão presente)")
        score -= 0.1

    score = min(1.0, max(0.0, score))
    detected = score > 0.3

    # Avaliação de risco
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
    """Diferencia STEMI de repolarização precoce benigna.

    Aplica critérios de Smith e outras características diferenciadores:
    - Razão ST/T (> 0,25 em V1-V4 favorece STEMI)
    - Morfologia do ST (convexa favorece STEMI, côncava favorece BER)
    - Infradesnivelamento recíproco de ST (favorece STEMI)
    - Distorção terminal do QRS (favorece STEMI)
    - Dados demográficos idade/sexo

    Parâmetros
    ----------
    st_elevation_mv : dict
        Derivação -> supradesnivelamento de ST em milivolts.
    t_wave_amplitude : dict, opcional
        Derivação -> amplitude da onda T em milivolts.
    patient_age : int, opcional
        Idade do paciente em anos.
    patient_sex : str, opcional
        'M' ou 'F'.
    reciprocal_changes : bool
        Se infradesnivelamento recíproco de ST está presente.
    st_morphology : str, opcional
        'convex' (tombstone), 'concave' (côncavo), ou 'straight'.
    qrs_distortion : bool
        Se distorção terminal do QRS está presente.

    Retorna
    -------
    dict
        - classification: str ('STEMI', 'early_repolarization', 'uncertain')
        - stemi_probability: float (0-1)
        - smith_score: float (se aplicável)
        - criteria: list[str]
        - details: str
    """
    stemi_points = 0.0
    ber_points = 0.0
    criteria: list[str] = []

    # 1. Razão de amplitude ST/T (critério de Smith)
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

    # 2. Morfologia do ST
    if st_morphology == "convex":
        stemi_points += 0.25
        criteria.append("Morfologia convexa (tombstone) do ST — forte indicador de STEMI")
    elif st_morphology == "concave":
        ber_points += 0.25
        criteria.append("Morfologia côncava do ST — favorece repolarização precoce")
    elif st_morphology == "straight":
        stemi_points += 0.1
        criteria.append("Morfologia retilínea do ST — possível STEMI precoce")

    # 3. Alterações recíprocas
    if reciprocal_changes:
        stemi_points += 0.3
        criteria.append("Alterações recíprocas presentes — forte indicador de STEMI")
    else:
        ber_points += 0.15
        criteria.append("Sem alterações recíprocas (favorece repolarização precoce)")

    # 4. Distorção terminal do QRS
    if qrs_distortion:
        stemi_points += 0.25
        criteria.append("Distorção terminal do QRS — altamente sugestivo de STEMI")

    # 5. Magnitude do supradesnivelamento de ST
    max_st = max(st_elevation_mv.values()) if st_elevation_mv else 0
    if max_st > 0.5:  # > 5mm
        stemi_points += 0.2
        criteria.append(f"Supra de ST muito elevado ({max_st:.1f} mV)")
    elif max_st < 0.1:
        ber_points += 0.1

    # 6. Dados demográficos
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

    # Calcula probabilidade
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
    """Detecta padrão da síndrome de Wellens.

    Síndrome de Wellens indica estenose crítica da DA (artéria descendente anterior):
    - Tipo A (25%): T bifásica em V2-V3 (inicialmente positiva, depois negativa)
    - Tipo B (75%): Inversão profunda e simétrica de T em V2-V3

    Importante: ocorre no período LIVRE DE DOR (ST normal durante intervalo sem dor)

    Parâmetros
    ----------
    t_wave_morphology : dict
        Derivação -> descrição da onda T ('biphasic', 'deep_inversion', 'normal', etc.)
    history_chest_pain : bool
        Se o paciente tem história de dor torácica.
    troponin_normal : bool
        Se a troponina está normal ou minimamente elevada.
    st_normal : bool
        Se os segmentos ST estão normais (importante: Wellens é padrão do período sem dor).

    Retorna
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

    # Tipo A: T bifásica em V2-V3
    if "biphasic" in v2_morph or "biphasic" in v3_morph:
        wellens_type = "A"
        score += 0.4
        findings.append("T bifásica em V2-V3 (Wellens tipo A)")

    # Tipo B: Inversão profunda e simétrica de T em V2-V3
    if "deep_inversion" in v2_morph or "deep_inversion" in v3_morph:
        wellens_type = "B"
        score += 0.4
        findings.append("T invertida profunda e simétrica em V2-V3 (Wellens tipo B)")

    # Extensão para V1-V4
    if "deep_inversion" in v1_morph or "deep_inversion" in v4_morph:
        score += 0.1
        findings.append("T invertida estende-se a V1 e/ou V4")

    # Contexto: período livre de dor com ST normal
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
    """Detecta padrão de de Winter (equivalente de STEMI).

    Características do padrão de de Winter:
    - Infradesnivelamento ascendente de ST no ponto J em V1-V6 (1-3mm)
    - Ondas T altas, simétricas e apiculadas nas derivações precordiais
    - Ausência de supradesnivelamento de ST nas precordiais
    - Pode ter discreto supra de ST em aVR

    Indica oclusão aguda da DA. Tratar como equivalente de STEMI.

    Parâmetros
    ----------
    st_changes : dict
        Derivação -> tipo de alteração de ST.
    t_wave_morphology : dict, opcional
        Derivação -> descrição da onda T.
    t_wave_amplitude : dict, opcional
        Derivação -> amplitude da onda T em mV.

    Retorna
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

    # Critério 1: Infradesnivelamento ascendente de ST nas precordiais
    infra_precordial = [
        lead for lead in precordial
        if st_changes.get(lead, "").lower() == "infra"
    ]
    if len(infra_precordial) >= 3:
        criteria_met.append(f"Infra ST em precordiais: {', '.join(infra_precordial)}")
        score += 0.3

    # Critério 2: Ondas T altas/apiculadas nas precordiais
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

    # Critério 3: Ausência de supra de ST nas precordiais
    supra_precordial = [
        lead for lead in precordial
        if st_changes.get(lead, "").lower() == "supra"
    ]
    if not supra_precordial and infra_precordial:
        criteria_met.append("Ausência de supra de ST precordial (critério de de Winter)")
        score += 0.1

    # Critério 4: Supra de ST em aVR
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

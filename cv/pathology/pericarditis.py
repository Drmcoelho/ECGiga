"""
Phase 20 – Pericarditis Detection
===================================
Detection of ECG patterns consistent with acute pericarditis:
diffuse ST elevation, PR depression, Spodick sign, and stage classification.

Camera analogy:
    Pericarditis inflames the *entire* pericardial sac around the heart.
    Unlike STEMI (where only cameras aimed at one wall see the problem),
    in pericarditis **almost all cameras** see ST elevation simultaneously
    — the inflammation is diffuse, like fog surrounding the entire heart.
"""

from __future__ import annotations

from typing import Dict, List

import numpy as np

# ---------------------------------------------------------------------------
# Lead groups used for diffuse-pattern analysis
# ---------------------------------------------------------------------------

_LIMB_LEADS = ["I", "II", "III", "aVL", "aVF"]
_PRECORDIAL_LEADS = ["V1", "V2", "V3", "V4", "V5", "V6"]
_ALL_STANDARD_LEADS = _LIMB_LEADS + ["aVR"] + _PRECORDIAL_LEADS

# Pericarditis typically spares aVR (which shows reciprocal depression)
# and V1 (which may be isoelectric or slightly depressed).

# Stage definitions (Spodick's stages)
_STAGES = {
    "I": {
        "name": "Estágio I — Agudo",
        "description": (
            "Elevação difusa e côncava do ST com depressão do segmento PR. "
            "Depressão recíproca de ST em aVR (e por vezes V1)."
        ),
        "features": ["diffuse_st_elevation", "pr_depression"],
    },
    "II": {
        "name": "Estágio II — Normalização",
        "description": (
            "Normalização do ST e PR. O ECG pode parecer transitoriamente normal."
        ),
        "features": ["st_normalizing"],
    },
    "III": {
        "name": "Estágio III — Inversão de T",
        "description": (
            "Inversão difusa de onda T, sem ondas Q patológicas (diferencial com IAM)."
        ),
        "features": ["diffuse_t_inversion"],
    },
    "IV": {
        "name": "Estágio IV — Normalização completa",
        "description": "Retorno ao ECG basal. Pode levar semanas a meses.",
        "features": [],
    },
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def detect_diffuse_st_elevation(
    st_by_lead: Dict[str, float],
    threshold: float = 0.5,
) -> Dict:
    """Detect diffuse (widespread) ST elevation consistent with pericarditis.

    Pericarditis criteria:
    * ST elevation in ≥ 5 leads (limb + precordial), typically concave-up.
    * aVR shows reciprocal ST depression.
    * Elevation is usually modest (0.5–2 mm), unlike STEMI (often > 2 mm).

    Parameters
    ----------
    st_by_lead : dict[str, float]
        Mean ST deviation in mm for each lead.
    threshold : float
        Minimum ST elevation (mm) to count a lead as "elevated" (default 0.5).

    Returns
    -------
    dict
        ``detected`` (bool), ``elevated_leads``, ``avr_depression`` (bool),
        ``num_elevated``, ``confidence``.
    """
    elevated_leads: List[str] = []
    for lead in _LIMB_LEADS + _PRECORDIAL_LEADS:
        val = st_by_lead.get(lead, 0.0)
        if val >= threshold:
            elevated_leads.append(lead)

    avr_val = st_by_lead.get("aVR", 0.0)
    avr_depression = avr_val <= -0.5

    num_elevated = len(elevated_leads)

    # Pericarditis: typically ≥ 5 leads, not confined to one territory
    # Check that leads span both limb and precordial groups
    has_limb = any(l in _LIMB_LEADS for l in elevated_leads)
    has_precordial = any(l in _PRECORDIAL_LEADS for l in elevated_leads)
    spans_multiple = has_limb and has_precordial

    detected = num_elevated >= 5 and spans_multiple

    # Confidence scoring
    confidence = 0.0
    if detected:
        confidence = 0.5
        if avr_depression:
            confidence += 0.2
        # More leads → higher confidence
        confidence += min(0.3, 0.05 * (num_elevated - 5))
        confidence = round(min(1.0, confidence), 2)

    return {
        "detected": detected,
        "elevated_leads": elevated_leads,
        "avr_depression": avr_depression,
        "num_elevated": num_elevated,
        "confidence": confidence,
    }


def detect_pr_depression(pr_segments: Dict[str, float]) -> bool:
    """Detect PR-segment depression, pathognomonic of acute pericarditis.

    PR depression ≥ 0.5 mm in ≥ 2 leads (excluding aVR where PR is elevated)
    is considered significant.

    Parameters
    ----------
    pr_segments : dict[str, float]
        PR segment deviation in mm per lead.  Negative = depression.

    Returns
    -------
    bool
        ``True`` if PR depression is detected.
    """
    depressed_count = 0

    for lead, val in pr_segments.items():
        if lead == "aVR":
            if val >= 0.5:
                pass
            continue
        if val <= -0.5:
            depressed_count += 1

    # Classic: PR depression in inferior and lateral leads + PR elevation in aVR
    return depressed_count >= 2


def detect_spodick_sign(
    trace: np.ndarray,
    r_peaks: List[int],
    fs: float,
) -> bool:
    """Detect Spodick sign: downsloping TP segment.

    The TP segment connects the end of the T wave to the start of the next
    P wave.  In pericarditis Stage I, this segment slopes downward, producing
    the Spodick sign.

    We estimate this by measuring the slope of the signal between 60 % and
    90 % of each R-R interval (approximating the TP segment).

    Parameters
    ----------
    trace : 1-D ndarray
        Single-lead ECG in mV.
    r_peaks : list[int]
        R-peak sample indices.
    fs : float
        Sampling frequency (Hz).

    Returns
    -------
    bool
        ``True`` if a consistent downsloping TP segment is detected.
    """
    trace = np.asarray(trace, dtype=float)

    if len(r_peaks) < 3:
        return False

    downslope_count = 0
    total_intervals = 0

    for i in range(len(r_peaks) - 1):
        rr = r_peaks[i + 1] - r_peaks[i]
        if rr <= 0:
            continue

        # TP segment approximation: 60–90 % of R-R interval after current R
        tp_start = r_peaks[i] + int(0.60 * rr)
        tp_end = r_peaks[i] + int(0.90 * rr)

        if tp_end >= len(trace):
            continue

        segment = trace[tp_start:tp_end + 1]
        if len(segment) < 3:
            continue

        total_intervals += 1

        # Linear fit to assess slope
        x = np.arange(len(segment))
        coeffs = np.polyfit(x, segment, 1)
        slope_mv_per_sample = coeffs[0]

        # Convert to mV/s to assess clinical significance
        slope_mv_per_s = slope_mv_per_sample * fs

        # Downslope threshold: more negative than −0.05 mV/s
        if slope_mv_per_s < -0.05:
            downslope_count += 1

    if total_intervals == 0:
        return False

    # Spodick sign present if majority of beats show downsloping TP
    return (downslope_count / total_intervals) >= 0.6


def classify_pericarditis_stage(features: Dict) -> Dict:
    """Classify pericarditis into Spodick stages I–IV.

    Parameters
    ----------
    features : dict
        Must contain boolean/float keys:
        - ``diffuse_st_elevation``: bool
        - ``pr_depression``: bool
        - ``st_normalizing``: bool — ST returning to baseline
        - ``diffuse_t_inversion``: bool
        - ``ecg_normalized``: bool — all segments back to normal

    Returns
    -------
    dict
        ``stage`` (str "I"-"IV"), ``name``, ``description``, ``confidence``.
    """
    st_elev = features.get("diffuse_st_elevation", False)
    pr_dep = features.get("pr_depression", False)
    st_norm = features.get("st_normalizing", False)
    t_inv = features.get("diffuse_t_inversion", False)
    ecg_norm = features.get("ecg_normalized", False)

    if ecg_norm and not st_elev and not t_inv:
        stage = "IV"
        confidence = 0.7
    elif t_inv and not st_elev:
        stage = "III"
        confidence = 0.7
    elif st_norm and not st_elev and not t_inv:
        stage = "II"
        confidence = 0.5
    elif st_elev:
        stage = "I"
        confidence = 0.6
        if pr_dep:
            confidence += 0.2
        confidence = min(1.0, confidence)
    else:
        # Indeterminate — default to stage I if PR depression present
        if pr_dep:
            stage = "I"
            confidence = 0.4
        else:
            stage = "I"
            confidence = 0.2

    info = _STAGES[stage]
    return {
        "stage": stage,
        "name": info["name"],
        "description": info["description"],
        "confidence": round(confidence, 2),
    }


def explain_pericarditis_cameras() -> str:
    """Camera-analogy educational explanation of pericarditis ECG findings.

    Returns
    -------
    str
        Multi-paragraph explanation in Portuguese.
    """
    return (
        "Analogia das Câmeras — Pericardite\n"
        "=" * 40 + "\n\n"
        "Imagine que o coração está envolto por uma capa inflamada (o pericárdio). "
        "Diferente do infarto, onde apenas as câmeras de uma parede mostram o "
        "problema, na pericardite QUASE TODAS as câmeras veem a inflamação "
        "simultaneamente.\n\n"
        "Por isso, o ECG mostra elevação de ST difusa — em derivações dos membros "
        "E precordiais ao mesmo tempo. É como se houvesse nevoeiro em volta de "
        "todo o coração: todas as câmeras ficam embaçadas.\n\n"
        "A câmera aVR, que olha para o interior das cavidades, vê o oposto: "
        "depressão de ST (e elevação do PR). Isso acontece porque aVR é o "
        "'espelho' do restante.\n\n"
        "Depressão do segmento PR é o achado patognomônico: a inflamação "
        "pericárdica afeta os átrios (que têm parede fina), deslocando o "
        "segmento PR para baixo.\n\n"
        "Sinal de Spodick: o segmento TP (entre a onda T e a onda P seguinte) "
        "apresenta uma inclinação descendente. É um achado sutil mas muito "
        "específico — como se a câmera registrasse uma queda contínua do "
        "sinal entre os batimentos.\n\n"
        "Estágios de Spodick:\n"
        "  I  — Elevação difusa de ST + depressão de PR (fase aguda)\n"
        "  II — Normalização do ST (ECG pseudonormal)\n"
        "  III — Inversão difusa de T\n"
        "  IV — Normalização completa"
    )

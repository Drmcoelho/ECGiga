"""
Phase 19 – STEMI / NSTEMI Detection
====================================
ST-segment elevation and depression measurement, territory mapping,
and reciprocal change identification based on standard clinical criteria.

Camera analogy:
    Each ECG lead is a "camera" pointing at the heart from a specific angle.
    ST elevation in a group of contiguous leads tells us which wall of the
    heart is injured – exactly like several cameras all showing smoke in
    the same direction point to the fire.
"""

from __future__ import annotations

import math
from typing import Dict, List, Optional

import numpy as np

# ---------------------------------------------------------------------------
# Territory map: lead groups → coronary territory
# ---------------------------------------------------------------------------

TERRITORY_MAP: Dict[str, Dict] = {
    "anterior": {
        "leads": ["V1", "V2", "V3", "V4"],
        "artery": "LAD",
        "description": "Parede anterior – artéria descendente anterior esquerda (DA/LAD)",
    },
    "inferior": {
        "leads": ["II", "III", "aVF"],
        "artery": "RCA/Cx",
        "description": "Parede inferior – artéria coronária direita (CD/RCA) ou circunflexa (Cx)",
    },
    "lateral": {
        "leads": ["I", "aVL", "V5", "V6"],
        "artery": "Cx",
        "description": "Parede lateral – artéria circunflexa (Cx)",
    },
    "posterior": {
        "leads": ["V7", "V8", "V9"],
        "artery": "Cx/RCA",
        "description": (
            "Parede posterior – Cx ou CD. "
            "Na ausência de V7-V9, depressão recíproca em V1-V3 sugere infarto posterior."
        ),
    },
    "right_ventricle": {
        "leads": ["V3R", "V4R"],
        "artery": "RCA",
        "description": "Ventrículo direito – artéria coronária direita (CD/RCA)",
    },
}

# Reciprocal lead pairs: territory → leads where reciprocal depression is expected
_RECIPROCAL_MAP: Dict[str, List[str]] = {
    "anterior": ["II", "III", "aVF"],
    "inferior": ["I", "aVL"],
    "lateral": ["III", "aVF"],
    "posterior": ["V1", "V2", "V3"],  # depression in ant → reciprocal of posterior elev
    "right_ventricle": ["I", "aVL"],
}


# ---------------------------------------------------------------------------
# Core measurement helpers
# ---------------------------------------------------------------------------

def _baseline_level(trace: np.ndarray, r_peak: int, fs: float) -> float:
    """Estimate isoelectric baseline as the mean of the TP segment preceding the beat.

    We look 40 ms before the P-wave onset (≈200 ms before QRS) to find a
    quiet segment.  If unavailable we fall back to the PR segment (60-20 ms
    before the R-peak).
    """
    # Try TP segment: 320-280 ms before R peak
    tp_start = r_peak - int(0.32 * fs)
    tp_end = r_peak - int(0.28 * fs)
    if tp_start >= 0 and tp_end > tp_start:
        return float(np.mean(trace[tp_start:tp_end]))

    # Fallback: PR segment 60-20 ms before R peak
    pr_start = r_peak - int(0.06 * fs)
    pr_end = r_peak - int(0.02 * fs)
    if pr_start >= 0 and pr_end > pr_start:
        return float(np.mean(trace[pr_start:pr_end]))

    # Last resort: local mean in 10-sample window before R
    start = max(0, r_peak - 10)
    return float(np.mean(trace[start:r_peak]))


def _j_point_index(trace: np.ndarray, r_peak: int, fs: float) -> int:
    """Estimate J-point as the end of the QRS complex.

    Simplified approach: from the R-peak, walk forward through the S-wave
    trough (minimum within 80 ms) then find where the gradient settles
    (absolute derivative drops below 15 % of peak gradient).
    """
    qrs_window = int(0.08 * fs)  # 80 ms max QRS width after R
    end_idx = min(len(trace) - 1, r_peak + qrs_window)

    segment = trace[r_peak:end_idx + 1]
    if len(segment) < 3:
        return r_peak + int(0.04 * fs)

    # Find S-wave trough (minimum after R)
    s_offset = int(np.argmin(segment))
    search_start = r_peak + s_offset

    # Walk forward until gradient is small
    grad = np.abs(np.diff(trace[search_start:end_idx + 1].astype(float)))
    if len(grad) == 0:
        return search_start

    grad_threshold = 0.15 * np.max(grad) if np.max(grad) > 0 else 0
    for i, g in enumerate(grad):
        if g < grad_threshold:
            return search_start + i

    return search_start + len(grad) - 1


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def measure_st_deviation(
    trace: np.ndarray,
    r_peaks: List[int],
    fs: float,
    st_offset_ms: float = 80,
) -> List[float]:
    """Measure ST deviation (in mm, assuming 1 mm = 0.1 mV) at J + *st_offset_ms*
    for every beat defined by *r_peaks*.

    Parameters
    ----------
    trace : 1-D array
        Single-lead ECG signal in **millivolts** (mV).
    r_peaks : list[int]
        Sample indices of detected R-peaks.
    fs : float
        Sampling frequency in Hz.
    st_offset_ms : float
        Milliseconds after J-point at which to measure ST level (default 80 ms).

    Returns
    -------
    list[float]
        ST deviation in mm for each beat.  Positive = elevation, negative = depression.
    """
    trace = np.asarray(trace, dtype=float)
    st_offset_samples = int(st_offset_ms * fs / 1000.0)
    deviations: List[float] = []

    for rp in r_peaks:
        baseline = _baseline_level(trace, rp, fs)
        j_idx = _j_point_index(trace, rp, fs)
        measure_idx = j_idx + st_offset_samples

        if measure_idx >= len(trace):
            measure_idx = len(trace) - 1

        st_voltage_mv = trace[measure_idx] - baseline
        # Convert mV → mm  (standard calibration: 1 mm = 0.1 mV)
        st_mm = st_voltage_mv / 0.1
        deviations.append(round(st_mm, 3))

    return deviations


def classify_st_deviation(
    st_mm: float,
    threshold_elev: float = 1.0,
    threshold_dep: float = -1.0,
) -> str:
    """Classify a single ST measurement as elevation, depression, or normal.

    Parameters
    ----------
    st_mm : float
        ST deviation in mm.
    threshold_elev : float
        Minimum mm for ST elevation (default 1.0 mm).
    threshold_dep : float
        Maximum (most negative) mm for ST depression (default −1.0 mm).

    Returns
    -------
    str
        ``"elevation"``, ``"depression"``, or ``"normal"``.
    """
    if st_mm >= threshold_elev:
        return "elevation"
    if st_mm <= threshold_dep:
        return "depression"
    return "normal"


def detect_stemi_pattern(st_by_lead: Dict[str, float]) -> Dict:
    """Identify STEMI territory from per-lead ST measurements.

    Parameters
    ----------
    st_by_lead : dict[str, float]
        Mean ST deviation (mm) for each lead name, e.g. ``{"V1": 2.1, "V2": 1.8, ...}``.

    Returns
    -------
    dict
        Keys: ``territory``, ``affected_leads``, ``reciprocal_leads``, ``confidence``.
        If no STEMI pattern is found, ``territory`` is ``"none"``.
    """
    best_territory: Optional[str] = None
    best_score: float = 0.0
    best_affected: List[str] = []
    best_reciprocal: List[str] = []

    for territory, info in TERRITORY_MAP.items():
        territory_leads = info["leads"]
        elevated: List[str] = []
        total_elev: float = 0.0

        for lead in territory_leads:
            val = st_by_lead.get(lead, 0.0)
            if val >= 1.0:  # ≥1 mm elevation
                elevated.append(lead)
                total_elev += val

        # Need at least 2 contiguous leads with elevation for STEMI criteria
        if len(elevated) < 2:
            continue

        # Check reciprocal depression
        reciprocal_leads_expected = _RECIPROCAL_MAP.get(territory, [])
        reciprocal_found: List[str] = []
        for lead in reciprocal_leads_expected:
            val = st_by_lead.get(lead, 0.0)
            if val <= -0.5:  # reciprocal depression ≥0.5 mm
                reciprocal_found.append(lead)

        # Score: weighted by amount of elevation + reciprocal bonus
        score = total_elev + 0.5 * len(reciprocal_found)

        if score > best_score:
            best_score = score
            best_territory = territory
            best_affected = elevated
            best_reciprocal = reciprocal_found

    # Special case: posterior MI detected by reciprocal V1-V3 depression
    if best_territory is None:
        v1v3_depression = []
        for lead in ["V1", "V2", "V3"]:
            val = st_by_lead.get(lead, 0.0)
            if val <= -1.0:
                v1v3_depression.append(lead)
        if len(v1v3_depression) >= 2:
            best_territory = "posterior"
            best_affected = v1v3_depression
            best_reciprocal = []
            best_score = sum(abs(st_by_lead.get(l, 0.0)) for l in v1v3_depression)

    if best_territory is None:
        return {
            "territory": "none",
            "affected_leads": [],
            "reciprocal_leads": [],
            "confidence": 0.0,
        }

    # Confidence heuristic: 2 leads ≥1 mm = 0.6 base, +0.1 per extra lead,
    # +0.1 per reciprocal lead, capped at 1.0
    confidence = min(
        1.0,
        0.6 + 0.1 * max(0, len(best_affected) - 2) + 0.1 * len(best_reciprocal),
    )

    return {
        "territory": best_territory,
        "affected_leads": best_affected,
        "reciprocal_leads": best_reciprocal,
        "confidence": round(confidence, 2),
    }


def explain_stemi_cameras(territory: str) -> str:
    """Educational explanation of STEMI using the camera analogy.

    Parameters
    ----------
    territory : str
        One of the keys of :data:`TERRITORY_MAP` (e.g. ``"anterior"``).

    Returns
    -------
    str
        Multi-paragraph explanation in Portuguese.
    """
    info = TERRITORY_MAP.get(territory)
    if info is None:
        return (
            "Território não reconhecido. Os territórios válidos são: "
            + ", ".join(TERRITORY_MAP.keys())
            + "."
        )

    leads = ", ".join(info["leads"])
    artery = info["artery"]
    desc = info["description"]

    return (
        f"Analogia das Câmeras — Território {territory.title()}\n"
        f"{'=' * 50}\n\n"
        f"Imagine que cada derivação do ECG é uma câmera de segurança "
        f"apontada para uma parede do coração.\n\n"
        f"As câmeras {leads} estão todas olhando para a parede "
        f"{territory} do coração. Quando vemos elevação de ST nessas "
        f"derivações simultaneamente, é como se várias câmeras "
        f"mostrassem fumaça vindo da mesma direção — indicando que "
        f"o 'incêndio' (isquemia/infarto) está naquela parede.\n\n"
        f"Artéria responsável: {artery}\n"
        f"{desc}\n\n"
        f"As câmeras do lado oposto (derivações recíprocas) veem o "
        f"mesmo evento de trás — por isso mostram depressão de ST "
        f"(imagem invertida do mesmo incêndio). A presença de "
        f"alterações recíprocas aumenta muito a especificidade do "
        f"diagnóstico de STEMI.\n\n"
        f"Critério: elevação de ST ≥ 1 mm em pelo menos 2 derivações "
        f"contíguas do mesmo território."
    )

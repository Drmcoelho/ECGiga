"""
Phase 20 – Brugada Syndrome Detection
=======================================
Detection of Brugada ECG patterns (Type 1 coved, Type 2 saddleback)
in leads V1 and V2, with morphology analysis.

Camera analogy:
    V1 and V2 are the cameras closest to the right ventricular outflow
    tract (RVOT).  In Brugada syndrome, a channelopathy in the RVOT
    creates an abnormal "dome" on the ST segment — visible only to these
    two nearby cameras.  Type 1 shows a smooth coved dome; Type 2 shows
    a two-humped saddleback.
"""

from __future__ import annotations

from typing import Dict, List, Optional

import numpy as np


# ---------------------------------------------------------------------------
# Diagnostic criteria constants
# ---------------------------------------------------------------------------

BRUGADA_CRITERIA: Dict[str, Dict] = {
    "type_1": {
        "name": "Tipo 1 (Coved / em tenda)",
        "st_elevation_mm": 2.0,  # ≥ 2 mm coved ST elevation
        "morphology": "coved",
        "leads": ["V1", "V2"],
        "t_wave": "negative",
        "description": (
            "Elevação do ponto J ≥ 2 mm com ST em forma de abóbada (coved) "
            "e onda T negativa em V1 e/ou V2. É o único padrão diagnóstico."
        ),
    },
    "type_2": {
        "name": "Tipo 2 (Saddleback / em sela)",
        "st_elevation_mm": 2.0,  # ≥ 2 mm saddleback
        "morphology": "saddleback",
        "leads": ["V1", "V2"],
        "t_wave": "positive_or_biphasic",
        "description": (
            "Elevação do ponto J ≥ 2 mm com ST em forma de sela (saddleback) "
            "e onda T positiva ou bifásica em V1 e/ou V2. Padrão sugestivo "
            "mas NÃO diagnóstico isoladamente."
        ),
    },
}


# ---------------------------------------------------------------------------
# Morphology analysis helpers
# ---------------------------------------------------------------------------

def _find_j_point(trace: np.ndarray, r_peak: int, fs: float) -> int:
    """Locate J-point (end of QRS) after R peak."""
    max_qrs = int(0.08 * fs)  # 80 ms window
    end = min(len(trace) - 1, r_peak + max_qrs)
    segment = trace[r_peak:end + 1]
    if len(segment) < 3:
        return r_peak + int(0.04 * fs)

    s_trough = int(np.argmin(segment))
    search_start = r_peak + s_trough
    grad = np.abs(np.diff(trace[search_start:end + 1].astype(float)))
    if len(grad) == 0:
        return search_start

    threshold = 0.15 * (np.max(grad) if np.max(grad) > 0 else 1)
    for i, g in enumerate(grad):
        if g < threshold:
            return search_start + i
    return search_start + len(grad) - 1


def _st_segment_features(
    trace: np.ndarray,
    j_point: int,
    fs: float,
    window_ms: float = 200,
) -> Dict:
    """Extract features from the ST segment after the J-point.

    Analyses the first *window_ms* ms after J-point to distinguish
    coved vs saddleback morphology.
    """
    window = int(window_ms * fs / 1000)
    end = min(len(trace), j_point + window)
    seg = trace[j_point:end].astype(float)

    if len(seg) < 5:
        return {"j_amplitude_mv": 0.0, "morphology": "indeterminate", "peak_count": 0}

    # Baseline: mean of 40 ms before the J-point's QRS onset (rough)
    bl_start = max(0, j_point - int(0.30 * fs))
    bl_end = max(0, j_point - int(0.28 * fs))
    if bl_end > bl_start:
        baseline = float(np.mean(trace[bl_start:bl_end]))
    else:
        baseline = float(trace[max(0, j_point - 5)])

    j_amp = float(seg[0]) - baseline

    # Smooth the segment for peak finding
    if len(seg) >= 7:
        kernel = np.ones(7) / 7
        smooth = np.convolve(seg - baseline, kernel, mode="same")
    else:
        smooth = seg - baseline

    # Count local maxima
    peaks: List[int] = []
    for i in range(1, len(smooth) - 1):
        if smooth[i] > smooth[i - 1] and smooth[i] > smooth[i + 1]:
            if smooth[i] > 0.02:  # above noise floor
                peaks.append(i)

    # Morphology classification
    if len(peaks) == 0:
        # Monotonically descending after J → coved
        morphology = "coved"
    elif len(peaks) == 1:
        # Single peak then descent → coved (dome shape)
        morphology = "coved"
    elif len(peaks) >= 2:
        # Two peaks → saddleback
        morphology = "saddleback"
    else:
        morphology = "indeterminate"

    # Check T-wave direction (last third of the window)
    t_seg = seg[int(0.6 * len(seg)):]
    if len(t_seg) > 2:
        t_mean = float(np.mean(t_seg)) - baseline
        if t_mean < -0.03:
            t_polarity = "negative"
        elif t_mean > 0.03:
            t_polarity = "positive"
        else:
            t_polarity = "isoelectric"
    else:
        t_polarity = "indeterminate"

    # Coved: single dome + negative T.  Saddleback: two humps + positive T.
    # Refine: if morphology is coved but T is positive, could be saddleback variant
    if morphology == "coved" and t_polarity == "positive":
        morphology = "saddleback"
    if morphology == "saddleback" and t_polarity == "negative":
        # Could still be saddleback with negative T, but more coved-like
        morphology = "coved"

    return {
        "j_amplitude_mv": round(j_amp, 4),
        "morphology": morphology,
        "t_polarity": t_polarity,
        "peak_count": len(peaks),
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def measure_st_morphology(
    trace: np.ndarray,
    r_peak: int,
    fs: float,
) -> Dict:
    """Classify ST-segment morphology for a single beat.

    Parameters
    ----------
    trace : 1-D ndarray
        Single-lead ECG in mV.
    r_peak : int
        Sample index of the R-peak.
    fs : float
        Sampling frequency (Hz).

    Returns
    -------
    dict
        ``j_amplitude_mv``, ``morphology`` ("coved" / "saddleback" / "indeterminate"),
        ``t_polarity`` ("positive" / "negative" / "isoelectric"),
        ``j_amplitude_mm`` (using 0.1 mV/mm standard).
    """
    j_point = _find_j_point(trace, r_peak, fs)
    features = _st_segment_features(trace, j_point, fs)
    features["j_amplitude_mm"] = round(features["j_amplitude_mv"] / 0.1, 2)
    return features


def detect_brugada_pattern(
    v1_trace: np.ndarray,
    v2_trace: np.ndarray,
    r_peaks: List[int],
    fs: float,
) -> Dict:
    """Detect Brugada pattern in V1 and V2.

    Parameters
    ----------
    v1_trace, v2_trace : 1-D ndarray
        ECG traces for leads V1 and V2 in mV.
    r_peaks : list[int]
        R-peak sample indices (same for both leads).
    fs : float
        Sampling frequency (Hz).

    Returns
    -------
    dict
        ``detected`` (bool), ``brugada_type`` (str or None),
        ``v1_features``, ``v2_features``, ``confidence`` (float),
        ``criteria_met`` (str).
    """
    v1_trace = np.asarray(v1_trace, dtype=float)
    v2_trace = np.asarray(v2_trace, dtype=float)

    if len(r_peaks) == 0:
        return {
            "detected": False,
            "brugada_type": None,
            "v1_features": {},
            "v2_features": {},
            "confidence": 0.0,
            "criteria_met": "Sem batimentos detectados",
        }

    # Analyse each beat and take majority vote
    v1_morphologies: List[str] = []
    v2_morphologies: List[str] = []
    v1_amps: List[float] = []
    v2_amps: List[float] = []

    for rp in r_peaks:
        if rp < len(v1_trace):
            f1 = measure_st_morphology(v1_trace, rp, fs)
            v1_morphologies.append(f1["morphology"])
            v1_amps.append(f1["j_amplitude_mm"])

        if rp < len(v2_trace):
            f2 = measure_st_morphology(v2_trace, rp, fs)
            v2_morphologies.append(f2["morphology"])
            v2_amps.append(f2["j_amplitude_mm"])

    # Majority morphology per lead
    def _majority(lst: List[str]) -> str:
        if not lst:
            return "indeterminate"
        from collections import Counter
        return Counter(lst).most_common(1)[0][0]

    v1_morph = _majority(v1_morphologies)
    v2_morph = _majority(v2_morphologies)

    v1_mean_amp = float(np.mean(v1_amps)) if v1_amps else 0.0
    v2_mean_amp = float(np.mean(v2_amps)) if v2_amps else 0.0

    # Get last-beat detailed features for output
    v1_feat = measure_st_morphology(v1_trace, r_peaks[-1], fs) if r_peaks[-1] < len(v1_trace) else {}
    v2_feat = measure_st_morphology(v2_trace, r_peaks[-1], fs) if r_peaks[-1] < len(v2_trace) else {}

    # Apply Brugada criteria
    # Type 1: coved, ≥ 2mm, in at least one of V1/V2
    type1_v1 = v1_morph == "coved" and v1_mean_amp >= 2.0
    type1_v2 = v2_morph == "coved" and v2_mean_amp >= 2.0

    # Type 2: saddleback, ≥ 2mm, in at least one of V1/V2
    type2_v1 = v1_morph == "saddleback" and v1_mean_amp >= 2.0
    type2_v2 = v2_morph == "saddleback" and v2_mean_amp >= 2.0

    if type1_v1 or type1_v2:
        detected = True
        brugada_type = "type_1"
        confidence = 0.85
        affected = []
        if type1_v1:
            affected.append("V1")
        if type1_v2:
            affected.append("V2")
        criteria_met = (
            f"Tipo 1 (coved) com elevação ≥ 2 mm em {', '.join(affected)}. "
            "Padrão DIAGNÓSTICO de Brugada."
        )
    elif type2_v1 or type2_v2:
        detected = True
        brugada_type = "type_2"
        confidence = 0.55
        affected = []
        if type2_v1:
            affected.append("V1")
        if type2_v2:
            affected.append("V2")
        criteria_met = (
            f"Tipo 2 (saddleback) com elevação ≥ 2 mm em {', '.join(affected)}. "
            "Padrão SUGESTIVO — considerar teste provocativo com ajmalina/flecainida."
        )
    else:
        detected = False
        brugada_type = None
        confidence = 0.0
        criteria_met = "Critérios de Brugada não preenchidos."

    return {
        "detected": detected,
        "brugada_type": brugada_type,
        "v1_features": v1_feat,
        "v2_features": v2_feat,
        "confidence": round(confidence, 2),
        "criteria_met": criteria_met,
    }


def explain_brugada_cameras() -> str:
    """Camera-analogy educational explanation of Brugada syndrome.

    Returns
    -------
    str
        Multi-paragraph explanation in Portuguese.
    """
    return (
        "Analogia das Câmeras — Síndrome de Brugada\n"
        "=" * 45 + "\n\n"
        "As câmeras V1 e V2 estão posicionadas logo na frente da via de "
        "saída do ventrículo direito (VSVD). Na síndrome de Brugada, há "
        "um defeito nos canais de sódio exatamente nessa região.\n\n"
        "Tipo 1 (Coved / Tenda):\n"
        "  A câmera V1/V2 registra uma 'cúpula' única no segmento ST "
        "que desce suavemente até uma onda T negativa. Parece o telhado "
        "de uma tenda — uma elevação côncava para baixo seguida de queda.\n"
        "  Este é o ÚNICO padrão diagnóstico.\n\n"
        "Tipo 2 (Saddleback / Sela):\n"
        "  A câmera vê duas corcundas — como uma sela de cavalo. O ponto J "
        "sobe, depois desce brevemente, depois sobe de novo antes de cair "
        "para uma onda T positiva. É sugestivo mas requer teste provocativo.\n\n"
        "Por que só V1 e V2?\n"
        "  Porque são as únicas câmeras apontadas diretamente para a VSVD. "
        "As outras câmeras estão longe demais para captar essa anomalia "
        "localizada — assim como uma câmera no fundo de um estádio não "
        "consegue ver um defeito no telhado do lado oposto.\n\n"
        "Importância: Brugada pode causar fibrilação ventricular e morte "
        "súbita, especialmente em homens jovens e durante o sono ou febre. "
        "O diagnóstico precoce salva vidas."
    )

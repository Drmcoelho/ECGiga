"""
Phase 21 – Channelopathy Detection (Long QT, Short QT, WPW)
=============================================================
Detection of ion-channel and accessory-pathway disorders:
* Long QT syndrome (LQTS)
* Short QT syndrome (SQTS)
* Wolff-Parkinson-White (WPW) pre-excitation with delta-wave detection.

Camera analogy:
    Channel disorders alter the *electrical timing* of the heart.  Every
    camera records the same prolongation or shortening of the QT interval.
    In WPW an extra electrical "shortcut" (accessory pathway) lets the
    impulse reach part of the ventricle early — producing a delta wave
    visible as a slurred upstroke at the start of the QRS.
"""

from __future__ import annotations

from typing import Dict, List, Optional

import numpy as np


# ---------------------------------------------------------------------------
# Long QT
# ---------------------------------------------------------------------------

# Schwartz score thresholds (simplified, based on QTc alone)
_LONG_QT_THRESHOLDS = {
    "male":   {"borderline": 450, "prolonged": 470, "high_risk": 500},
    "female": {"borderline": 460, "prolonged": 480, "high_risk": 500},
    "unknown": {"borderline": 460, "prolonged": 480, "high_risk": 500},
}


def detect_long_qt(qtc_ms: float, sex: str = "unknown") -> Dict:
    """Classify QTc as normal, borderline, prolonged, or high-risk.

    Thresholds (Bazett-corrected QTc):
    * **Male**: borderline 450-469 ms, prolonged 470-499 ms, high-risk >= 500 ms
    * **Female** / unknown: borderline 460-479 ms, prolonged 480-499 ms,
      high-risk >= 500 ms

    Parameters
    ----------
    qtc_ms : float
        Corrected QT interval in milliseconds (Bazett or Fridericia).
    sex : str
        ``"male"``, ``"female"``, or ``"unknown"``.

    Returns
    -------
    dict
        ``classification`` (str), ``qtc_ms``, ``thresholds`` (dict),
        ``risk_note`` (str).
    """
    sex = sex.lower() if sex else "unknown"
    if sex not in _LONG_QT_THRESHOLDS:
        sex = "unknown"

    thr = _LONG_QT_THRESHOLDS[sex]

    if qtc_ms >= thr["high_risk"]:
        classification = "high_risk"
        risk_note = (
            "QTc ≥ 500 ms — alto risco de Torsades de Pointes e morte súbita. "
            "Investigação urgente e retirada de fármacos que prolongam QT."
        )
    elif qtc_ms >= thr["prolonged"]:
        classification = "prolonged"
        risk_note = (
            "QTc prolongado — risco aumentado de arritmias ventriculares. "
            "Investigar causas (fármacos, eletrólitos, SQTL congênito)."
        )
    elif qtc_ms >= thr["borderline"]:
        classification = "borderline"
        risk_note = (
            "QTc borderline — monitorizar. Evitar drogas que prolongam QT. "
            "Considerar repetição do ECG e história familiar."
        )
    else:
        classification = "normal"
        risk_note = "QTc dentro dos limites da normalidade."

    return {
        "classification": classification,
        "qtc_ms": qtc_ms,
        "sex": sex,
        "thresholds": thr,
        "risk_note": risk_note,
    }


# ---------------------------------------------------------------------------
# Short QT
# ---------------------------------------------------------------------------

def detect_short_qt(qtc_ms: float) -> Dict:
    """Detect short QT syndrome.

    Diagnostic threshold: QTc ≤ 340 ms (Gollob criteria).
    Suggestive: QTc 340-360 ms with family history / symptoms.

    Parameters
    ----------
    qtc_ms : float
        Corrected QT interval in ms.

    Returns
    -------
    dict
        ``classification`` (str), ``qtc_ms``, ``risk_note`` (str).
    """
    if qtc_ms <= 340:
        classification = "short_qt"
        risk_note = (
            "QTc ≤ 340 ms — critério diagnóstico para Síndrome do QT Curto. "
            "Alto risco de fibrilação ventricular e morte súbita. "
            "Encaminhar para eletrofisiologia."
        )
    elif qtc_ms <= 360:
        classification = "borderline_short"
        risk_note = (
            "QTc 340-360 ms — borderline curto. "
            "Investigar história familiar de morte súbita e síncope."
        )
    else:
        classification = "normal"
        risk_note = "QTc não sugestivo de QT curto."

    return {
        "classification": classification,
        "qtc_ms": qtc_ms,
        "risk_note": risk_note,
    }


# ---------------------------------------------------------------------------
# WPW / Pre-excitation
# ---------------------------------------------------------------------------

def detect_wpw(
    pr_ms: float,
    qrs_ms: float,
    delta_wave_present: bool = False,
) -> Dict:
    """Detect Wolff-Parkinson-White pre-excitation pattern.

    Classic triad:
    1. Short PR interval (< 120 ms)
    2. Wide QRS (> 120 ms) due to delta wave
    3. Delta wave (slurred upstroke of QRS)

    Parameters
    ----------
    pr_ms : float
        PR interval in milliseconds.
    qrs_ms : float
        QRS duration in milliseconds.
    delta_wave_present : bool
        Whether a delta wave has been detected (by :func:`detect_delta_wave`
        or clinical assessment).

    Returns
    -------
    dict
        ``detected`` (bool), ``criteria_met`` (list[str]),
        ``confidence`` (float), ``interpretation`` (str).
    """
    criteria: List[str] = []

    short_pr = pr_ms < 120
    wide_qrs = qrs_ms > 120

    if short_pr:
        criteria.append("PR curto (< 120 ms)")
    if wide_qrs:
        criteria.append("QRS alargado (> 120 ms)")
    if delta_wave_present:
        criteria.append("Onda delta presente")

    n_criteria = len(criteria)

    if n_criteria == 3:
        detected = True
        confidence = 0.95
        interpretation = (
            "Tríade completa de WPW: PR curto + QRS largo + onda delta. "
            "Pré-excitação ventricular por via acessória."
        )
    elif n_criteria == 2 and delta_wave_present:
        detected = True
        confidence = 0.75
        interpretation = (
            "Dois critérios presentes incluindo onda delta — "
            "fortemente sugestivo de WPW."
        )
    elif n_criteria == 2:
        detected = False
        confidence = 0.40
        interpretation = (
            "Dois critérios presentes mas sem onda delta confirmada. "
            "Considerar LGL (Lown-Ganong-Levine) ou variante normal."
        )
    elif n_criteria == 1:
        detected = False
        confidence = 0.15
        interpretation = "Achado isolado — insuficiente para diagnóstico de WPW."
    else:
        detected = False
        confidence = 0.0
        interpretation = "Sem critérios de pré-excitação."

    return {
        "detected": detected,
        "pr_ms": pr_ms,
        "qrs_ms": qrs_ms,
        "delta_wave_present": delta_wave_present,
        "criteria_met": criteria,
        "confidence": round(confidence, 2),
        "interpretation": interpretation,
    }


def detect_delta_wave(
    trace: np.ndarray,
    qrs_onset: int,
    fs: float,
) -> Dict:
    """Detect delta-wave morphology at the onset of the QRS complex.

    A delta wave is a slurred, gradual upstroke at the very beginning of
    the QRS — the impulse arrives via the slow accessory pathway before
    the fast His-Purkinje system catches up.

    Detection method:
    * Measure the slope of the first 40 ms of the QRS.
    * Compare with the slope of the next 40 ms (normal rapid upstroke).
    * Delta wave: initial slope is significantly lower (< 50 %) than the
      subsequent rapid phase.

    Parameters
    ----------
    trace : 1-D ndarray
        ECG signal in mV.
    qrs_onset : int
        Sample index of QRS onset.
    fs : float
        Sampling frequency (Hz).

    Returns
    -------
    dict
        ``detected`` (bool), ``initial_slope`` (float mV/ms),
        ``rapid_slope`` (float mV/ms), ``slope_ratio`` (float),
        ``delta_duration_ms`` (float), ``confidence`` (float).
    """
    trace = np.asarray(trace, dtype=float)

    # Two windows: initial (delta) and rapid (normal His-Purkinje)
    delta_window_ms = 40
    rapid_window_ms = 40

    delta_samples = int(delta_window_ms * fs / 1000)
    rapid_samples = int(rapid_window_ms * fs / 1000)

    delta_end = qrs_onset + delta_samples
    rapid_end = delta_end + rapid_samples

    if rapid_end >= len(trace) or qrs_onset < 0:
        return {
            "detected": False,
            "initial_slope": 0.0,
            "rapid_slope": 0.0,
            "slope_ratio": 0.0,
            "delta_duration_ms": 0.0,
            "confidence": 0.0,
        }

    # Initial segment (potential delta wave)
    seg_delta = trace[qrs_onset:delta_end]
    # Rapid upstroke segment
    seg_rapid = trace[delta_end:rapid_end]

    if len(seg_delta) < 2 or len(seg_rapid) < 2:
        return {
            "detected": False,
            "initial_slope": 0.0,
            "rapid_slope": 0.0,
            "slope_ratio": 0.0,
            "delta_duration_ms": 0.0,
            "confidence": 0.0,
        }

    # Compute slopes (mV per ms)
    ms_per_sample = 1000.0 / fs

    # Linear regression for each segment
    x_delta = np.arange(len(seg_delta)) * ms_per_sample
    x_rapid = np.arange(len(seg_rapid)) * ms_per_sample

    coeff_delta = np.polyfit(x_delta, seg_delta, 1)
    coeff_rapid = np.polyfit(x_rapid, seg_rapid, 1)

    initial_slope = abs(coeff_delta[0])  # mV/ms (absolute value)
    rapid_slope = abs(coeff_rapid[0])

    # Slope ratio: delta wave → low initial slope relative to rapid phase
    if rapid_slope > 1e-6:
        slope_ratio = initial_slope / rapid_slope
    else:
        slope_ratio = 1.0  # both flat → no delta

    # Delta wave: initial slope < 50% of rapid slope, and rapid slope
    # must be meaningful (> 0.005 mV/ms = some real QRS)
    detected = slope_ratio < 0.50 and rapid_slope > 0.005

    # Estimate delta duration: from onset until slope exceeds 70 % of rapid slope
    delta_duration_ms = 0.0
    if detected:
        cumulative_slope = np.abs(np.diff(trace[qrs_onset:rapid_end].astype(float)))
        threshold_slope = 0.7 * rapid_slope * ms_per_sample
        for i, s in enumerate(cumulative_slope):
            if s > threshold_slope:
                delta_duration_ms = i * ms_per_sample
                break
        else:
            delta_duration_ms = delta_window_ms

    confidence = 0.0
    if detected:
        confidence = 0.6
        if slope_ratio < 0.30:
            confidence += 0.2
        if delta_duration_ms > 20:
            confidence += 0.1
        confidence = min(1.0, confidence)

    return {
        "detected": detected,
        "initial_slope": round(initial_slope, 6),
        "rapid_slope": round(rapid_slope, 6),
        "slope_ratio": round(slope_ratio, 3),
        "delta_duration_ms": round(delta_duration_ms, 1),
        "confidence": round(confidence, 2),
    }


# ---------------------------------------------------------------------------
# Educational
# ---------------------------------------------------------------------------

def explain_channelopathy_cameras() -> str:
    """Camera-analogy explanation of channelopathies.

    Returns
    -------
    str
        Multi-paragraph explanation in Portuguese.
    """
    return (
        "Analogia das Câmeras — Canalopatias e WPW\n"
        "=" * 44 + "\n\n"
        "QT LONGO (LQTS):\n"
        "  Todas as câmeras registram uma 'exposição prolongada' — a "
        "onda T demora mais para terminar. Imagine que cada câmera "
        "precisa esperar mais tempo até o coração 'recarregar' para "
        "o próximo batimento. Se esse tempo é excessivo (QTc ≥ 500 ms), "
        "o risco de uma arritmia perigosa (Torsades de Pointes) aumenta "
        "dramaticamente.\n\n"
        "QT CURTO (SQTS):\n"
        "  O oposto: o coração recarrega rápido demais. As câmeras "
        "mostram um intervalo QT encurtado (QTc ≤ 340 ms). A recarga "
        "prematura torna o miocárdio vulnerável a reentradas e fibrilação "
        "ventricular. É raro mas potencialmente letal.\n\n"
        "WPW (Wolff-Parkinson-White):\n"
        "  Existe uma 'passagem secreta' (via acessória) entre átrio "
        "e ventrículo que contorna o nó AV. O impulso chega ao ventrículo "
        "por dois caminhos:\n"
        "  1. Via acessória (rápida, mas sem freio do nó AV)\n"
        "  2. Via normal pelo nó AV (com atraso fisiológico)\n\n"
        "  A câmera vê o resultado: o início do QRS é 'borrado' porque "
        "a via acessória ativa uma pequena parte do ventrículo antes do "
        "resto — essa rampa lenta é a ONDA DELTA.\n\n"
        "  Consequências no ECG:\n"
        "  • PR curto (< 120 ms) — o atalho encurta o tempo AV\n"
        "  • QRS largo (> 120 ms) — a onda delta 'alarga' o início\n"
        "  • Onda delta — a rampa lenta no início do QRS\n\n"
        "  Perigo: se o paciente desenvolve fibrilação atrial, a via "
        "acessória pode conduzir a frequências ventriculares mortais. "
        "Por isso, WPW + FA é uma emergência."
    )

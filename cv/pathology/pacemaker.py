"""
Phase 21 – Pacemaker ECG Detection
====================================
Detection of pacing spikes, pacemaker mode classification (AAI, VVI, DDD),
capture and sensing analysis.

Camera analogy:
    A pacemaker is like a metronome placed inside the heart.  The ECG cameras
    see its "click" as a narrow spike followed by the forced contraction it
    triggers.  The mode tells us which chambers the metronome is conducting:
    AAI = atrium only, VVI = ventricle only, DDD = both chambers.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import numpy as np


# ---------------------------------------------------------------------------
# Pacing spike detection
# ---------------------------------------------------------------------------

def detect_pacing_spikes(
    trace: np.ndarray,
    fs: float,
    threshold: float = 0.3,
) -> List[int]:
    """Detect narrow pacing spikes in an ECG trace.

    Pacing spikes are characterised by:
    * Very narrow width (< 2 ms)
    * Sharp amplitude (high slew rate)
    * Distinct from QRS or T-wave morphology

    Parameters
    ----------
    trace : 1-D ndarray
        ECG signal in mV.
    fs : float
        Sampling frequency (Hz).
    threshold : float
        Minimum absolute amplitude change (mV) over 1-2 samples to qualify
        as a pacing spike (default 0.3 mV).

    Returns
    -------
    list[int]
        Sample indices of detected pacing spikes.
    """
    trace = np.asarray(trace, dtype=float)
    if len(trace) < 3:
        return []

    # Compute first derivative (sample-to-sample difference)
    diff1 = np.diff(trace)

    # Spike = large positive or negative jump followed quickly by reversal
    max_spike_width = max(1, int(0.002 * fs))  # 2 ms in samples
    spikes: List[int] = []

    # Refractory period: min 100 ms between spikes (pacemakers don't fire faster)
    refractory_samples = int(0.10 * fs)
    last_spike = -refractory_samples - 1

    for i in range(len(diff1) - max_spike_width):
        # Check for sharp deflection
        if abs(diff1[i]) < threshold:
            continue

        # Check that it reverses within max_spike_width samples
        reversal = False
        for j in range(1, max_spike_width + 2):
            if i + j >= len(diff1):
                break
            # Opposite sign and similar magnitude
            if diff1[i] * diff1[i + j] < 0 and abs(diff1[i + j]) > 0.3 * abs(diff1[i]):
                reversal = True
                break

        if reversal and (i - last_spike) > refractory_samples:
            spikes.append(i)
            last_spike = i

    return spikes


# ---------------------------------------------------------------------------
# Pacemaker mode classification
# ---------------------------------------------------------------------------

def classify_pacemaker_mode(
    spikes: List[int],
    p_waves: List[int],
    qrs_complexes: List[int],
) -> str:
    """Classify pacemaker mode based on spike-to-event relationships.

    Simplified classification:
    * **AAI**: spikes precede P-waves only (no spike before QRS)
    * **VVI**: spikes precede QRS only (no spike before P-wave)
    * **DDD**: spikes precede both P-waves and QRS complexes
    * **indeterminate**: cannot classify

    Parameters
    ----------
    spikes : list[int]
        Sample indices of pacing spikes.
    p_waves : list[int]
        Sample indices of P-wave peaks.
    qrs_complexes : list[int]
        Sample indices of QRS peaks (R-peaks).

    Returns
    -------
    str
        Pacemaker mode: ``"AAI"``, ``"VVI"``, ``"DDD"``, or ``"indeterminate"``.
    """
    if not spikes:
        return "indeterminate"

    # For each spike, determine if it is followed by a P-wave or QRS within
    # a reasonable capture window
    ATRIAL_CAPTURE_WINDOW = 200   # samples — generous for variable fs
    VENTRICULAR_CAPTURE_WINDOW = 200

    atrial_paced = 0
    ventricular_paced = 0

    p_arr = np.array(p_waves) if p_waves else np.array([])
    qrs_arr = np.array(qrs_complexes) if qrs_complexes else np.array([])

    for sp in spikes:
        # Check for atrial capture: spike followed by P-wave
        if len(p_arr) > 0:
            diffs_p = p_arr - sp
            close_p = diffs_p[(diffs_p > 0) & (diffs_p < ATRIAL_CAPTURE_WINDOW)]
            if len(close_p) > 0:
                atrial_paced += 1

        # Check for ventricular capture: spike followed by QRS
        if len(qrs_arr) > 0:
            diffs_q = qrs_arr - sp
            close_q = diffs_q[(diffs_q > 0) & (diffs_q < VENTRICULAR_CAPTURE_WINDOW)]
            if len(close_q) > 0:
                ventricular_paced += 1

    total = len(spikes)
    atrial_ratio = atrial_paced / total if total > 0 else 0
    ventricular_ratio = ventricular_paced / total if total > 0 else 0

    # Classification thresholds
    has_atrial = atrial_ratio > 0.3
    has_ventricular = ventricular_ratio > 0.3

    if has_atrial and has_ventricular:
        return "DDD"
    elif has_atrial and not has_ventricular:
        return "AAI"
    elif has_ventricular and not has_atrial:
        return "VVI"
    else:
        return "indeterminate"


# ---------------------------------------------------------------------------
# Capture detection
# ---------------------------------------------------------------------------

def detect_capture(
    spikes: List[int],
    qrs_positions: List[int],
    max_latency_ms: float = 40,
    fs: float = 500.0,
) -> Dict:
    """Check if pacing spikes result in ventricular capture.

    A spike "captures" if it is followed by a QRS complex within
    *max_latency_ms* milliseconds.

    Parameters
    ----------
    spikes : list[int]
        Sample indices of pacing spikes.
    qrs_positions : list[int]
        Sample indices of QRS complexes.
    max_latency_ms : float
        Maximum spike-to-QRS latency for capture (default 40 ms).
    fs : float
        Sampling frequency (Hz).

    Returns
    -------
    dict
        ``total_spikes``, ``captured``, ``not_captured``,
        ``capture_rate`` (float 0-1), ``loss_of_capture`` (bool),
        ``latencies_ms`` (list[float]).
    """
    max_latency_samples = int(max_latency_ms * fs / 1000)
    qrs_arr = np.array(qrs_positions) if qrs_positions else np.array([])

    captured = 0
    not_captured = 0
    latencies: List[float] = []

    for sp in spikes:
        if len(qrs_arr) == 0:
            not_captured += 1
            continue

        diffs = qrs_arr - sp
        # QRS must be AFTER spike and within latency window
        valid = diffs[(diffs > 0) & (diffs <= max_latency_samples)]

        if len(valid) > 0:
            best = int(np.min(valid))
            latencies.append(round(best / fs * 1000, 1))
            captured += 1
        else:
            not_captured += 1

    total = len(spikes)
    capture_rate = captured / total if total > 0 else 0.0

    return {
        "total_spikes": total,
        "captured": captured,
        "not_captured": not_captured,
        "capture_rate": round(capture_rate, 3),
        "loss_of_capture": not_captured > 0,
        "latencies_ms": latencies,
    }


# ---------------------------------------------------------------------------
# Sensing detection
# ---------------------------------------------------------------------------

def detect_sensing(
    spikes: List[int],
    native_beats: List[int],
    fs: float = 500.0,
    min_inhibition_ms: float = 300,
) -> Dict:
    """Check appropriate sensing (inhibition of pacing when native beats occur).

    A properly sensing pacemaker should NOT fire a spike when it detects
    a native cardiac event within the sensing window.

    We check for *undersensing* (spike fires despite nearby native beat)
    and *oversensing* (inappropriately long pauses suggesting the pacemaker
    is sensing noise as cardiac activity).

    Parameters
    ----------
    spikes : list[int]
        Sample indices of pacing spikes.
    native_beats : list[int]
        Sample indices of native (non-paced) beats.
    fs : float
        Sampling frequency (Hz).
    min_inhibition_ms : float
        Minimum interval (ms) — if a spike occurs within this window after
        a native beat, it indicates undersensing.

    Returns
    -------
    dict
        ``undersensing_events`` (int), ``total_native_beats`` (int),
        ``sensing_appropriate`` (bool), ``details`` (str).
    """
    min_inhibition_samples = int(min_inhibition_ms * fs / 1000)
    spike_arr = np.array(spikes) if spikes else np.array([])

    undersensing = 0
    total_native = len(native_beats)

    for nb in native_beats:
        if len(spike_arr) == 0:
            continue
        # Check if any spike fires too close after this native beat
        diffs = spike_arr - nb
        # Spike after native beat within inhibition window = undersensing
        close = diffs[(diffs > 0) & (diffs < min_inhibition_samples)]
        if len(close) > 0:
            undersensing += 1

    sensing_ok = undersensing == 0

    if sensing_ok:
        details = "Sensoriamento adequado: marcapasso inibido por batimentos nativos."
    else:
        details = (
            f"Possível undersensing: {undersensing} evento(s) onde o marcapasso "
            f"disparou spike dentro de {min_inhibition_ms} ms após batimento nativo."
        )

    return {
        "undersensing_events": undersensing,
        "total_native_beats": total_native,
        "sensing_appropriate": sensing_ok,
        "details": details,
    }


# ---------------------------------------------------------------------------
# Educational
# ---------------------------------------------------------------------------

def explain_pacemaker_cameras() -> str:
    """Camera-analogy explanation of pacemaker ECG findings.

    Returns
    -------
    str
        Multi-paragraph explanation in Portuguese.
    """
    return (
        "Analogia das Câmeras — Marcapasso (Pacemaker)\n"
        "=" * 48 + "\n\n"
        "Imagine que o marcapasso é um metrônomo eletrônico implantado "
        "dentro do coração. Cada vez que ele 'bate', emite um sinal "
        "elétrico curtíssimo — o spike.\n\n"
        "As câmeras do ECG veem esse spike como uma linha vertical fina "
        "e afiada, seguida pela onda que ele provoca:\n\n"
        "Modos do metrônomo:\n"
        "• AAI — O metrônomo toca SÓ no átrio. As câmeras veem: spike → "
        "onda P → QRS normal (condução própria para os ventrículos).\n"
        "• VVI — O metrônomo toca SÓ no ventrículo. As câmeras veem: "
        "spike → QRS largo (condução forçada, não pelo sistema normal). "
        "A onda P pode estar dissociada.\n"
        "• DDD — O metrônomo toca nos DOIS: primeiro um spike no átrio "
        "(→ P), depois espera um intervalo AV e dispara outro spike no "
        "ventrículo (→ QRS). As câmeras veem dois spikes por ciclo.\n\n"
        "Captura:\n"
        "  Cada spike deve ser seguido por uma onda correspondente "
        "(P ou QRS). Se o spike aparece mas NÃO há onda — é perda de "
        "captura (o metrônomo bate mas o músculo não responde).\n\n"
        "Sensoriamento:\n"
        "  Um bom marcapasso 'ouve' os batimentos nativos e se cala. "
        "Se ele dispara spike mesmo quando o coração já bateu sozinho, "
        "há falha de sensoriamento (undersensing).\n\n"
        "No ECG, a câmera mais reveladora é V1 (direcionada ao VD onde "
        "a maioria dos eletrodos ventriculares é implantada)."
    )

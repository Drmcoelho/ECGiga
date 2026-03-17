"""
Synthetic ECG generator with controllable parameters.

Generates realistic 12-lead ECG waveforms with configurable heart rate,
interval durations, axis, noise, and pathological patterns.
"""

from __future__ import annotations

from typing import Any

import numpy as np

try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    HAS_PLOTLY = True
except ImportError:  # pragma: no cover
    HAS_PLOTLY = False

# Standard 12-lead names
LEAD_NAMES = ["I", "II", "III", "aVR", "aVL", "aVF", "V1", "V2", "V3", "V4", "V5", "V6"]

# Lead axis angles (degrees) for frontal plane leads
LEAD_AXES = {
    "I": 0,
    "II": 60,
    "III": 120,
    "aVR": -150,
    "aVL": -30,
    "aVF": 90,
}

# Precordial lead transition (relative R-wave amplitude factor)
PRECORDIAL_R_FACTOR = {
    "V1": -0.6,
    "V2": -0.3,
    "V3": 0.1,
    "V4": 0.7,
    "V5": 0.9,
    "V6": 0.8,
}
PRECORDIAL_S_FACTOR = {
    "V1": 0.8,
    "V2": 0.6,
    "V3": 0.3,
    "V4": 0.1,
    "V5": 0.05,
    "V6": 0.02,
}


def _gaussian(t: np.ndarray, center: float, width: float, amplitude: float) -> np.ndarray:
    """Generate a Gaussian pulse."""
    return amplitude * np.exp(-((t - center) ** 2) / (2 * width**2))


def _single_beat(
    duration_s: float,
    fs: int,
    pr_ms: float,
    qrs_ms: float,
    qt_ms: float,
) -> np.ndarray:
    """Generate a single ECG beat template (lead II-like morphology).

    Returns a 1-D array representing one cardiac cycle.
    """
    n = int(duration_s * fs)
    t = np.linspace(0, duration_s, n, endpoint=False)

    # Convert intervals to seconds
    pr_s = pr_ms / 1000.0
    qrs_s = qrs_ms / 1000.0
    qt_s = qt_ms / 1000.0

    # Timing landmarks
    p_center = pr_s * 0.5
    p_width = pr_s * 0.15
    q_center = pr_s
    r_center = pr_s + qrs_s * 0.4
    s_center = pr_s + qrs_s * 0.8
    t_center = pr_s + qt_s * 0.7
    t_width = qt_s * 0.1

    # Component waves
    p_wave = _gaussian(t, p_center, p_width, 0.15)
    q_wave = _gaussian(t, q_center, qrs_s * 0.08, -0.1)
    r_wave = _gaussian(t, r_center, qrs_s * 0.06, 1.0)
    s_wave = _gaussian(t, s_center, qrs_s * 0.07, -0.25)
    t_wave = _gaussian(t, t_center, t_width, 0.3)

    # Small U wave
    u_center = pr_s + qt_s + 0.04
    if u_center < duration_s:
        u_wave = _gaussian(t, u_center, 0.02, 0.03)
    else:
        u_wave = np.zeros_like(t)

    beat = p_wave + q_wave + r_wave + s_wave + t_wave + u_wave
    return beat


def _project_frontal(beat_ii: np.ndarray, axis_deg: float, lead_name: str) -> np.ndarray:
    """Project an ideal lead-II beat onto a frontal-plane lead using vector projection."""
    if lead_name not in LEAD_AXES:
        return beat_ii  # fallback for precordial
    lead_angle = LEAD_AXES[lead_name]
    # Projection factor = cos(axis - lead_angle)
    angle_diff = np.radians(axis_deg - lead_angle)
    factor = np.cos(angle_diff)
    return beat_ii * factor


def _generate_precordial(beat_ii: np.ndarray, lead_name: str) -> np.ndarray:
    """Generate a precordial lead from the lead-II template.

    Simulates R-wave progression and S-wave regression across V1-V6.
    """
    n = len(beat_ii)
    result = beat_ii.copy()

    r_factor = PRECORDIAL_R_FACTOR.get(lead_name, 0.5)
    s_factor = PRECORDIAL_S_FACTOR.get(lead_name, 0.1)

    # Find the QRS complex region (highest amplitude region)
    abs_signal = np.abs(beat_ii)
    qrs_peak = np.argmax(abs_signal)
    qrs_region = slice(max(0, qrs_peak - n // 20), min(n, qrs_peak + n // 20))

    # Scale QRS region according to R and S factors
    for i in range(qrs_region.start, qrs_region.stop):
        if beat_ii[i] > 0:
            result[i] = beat_ii[i] * r_factor
        else:
            result[i] = beat_ii[i] * s_factor

    # V1-V2: invert T wave slightly
    if lead_name in ("V1", "V2"):
        # T wave region: after QRS
        t_start = min(n - 1, qrs_peak + n // 10)
        t_end = min(n, t_start + n // 5)
        result[t_start:t_end] *= -0.5 if lead_name == "V1" else -0.2

    return result


def generate_ecg(
    hr_bpm: float = 72,
    pr_ms: float = 160,
    qrs_ms: float = 90,
    qt_ms: float = 380,
    axis_deg: float = 60,
    noise: float = 0.02,
    duration_s: float = 10,
    fs: int = 500,
) -> dict[str, Any]:
    """Generate a synthetic 12-lead ECG.

    Parameters
    ----------
    hr_bpm : float
        Heart rate in beats per minute.
    pr_ms : float
        PR interval in milliseconds.
    qrs_ms : float
        QRS duration in milliseconds.
    qt_ms : float
        QT interval in milliseconds.
    axis_deg : float
        Electrical axis in degrees (frontal plane).
    noise : float
        Noise standard deviation (mV).
    duration_s : float
        Total ECG duration in seconds.
    fs : int
        Sampling frequency (Hz).

    Returns
    -------
    dict
        {"time": np.ndarray, "leads": dict[str, np.ndarray], "params": dict}
    """
    n_total = int(duration_s * fs)
    t = np.linspace(0, duration_s, n_total, endpoint=False)

    # Beat-to-beat interval
    rr_s = 60.0 / hr_bpm
    beat_samples = int(rr_s * fs)
    if beat_samples < 10:
        beat_samples = 10

    # Generate single beat template
    beat_template = _single_beat(rr_s, fs, pr_ms, qrs_ms, qt_ms)

    # Tile beats to fill duration
    n_beats = int(np.ceil(n_total / beat_samples)) + 1
    tiled = np.tile(beat_template, n_beats)[:n_total]

    # Generate all 12 leads
    leads: dict[str, np.ndarray] = {}

    for lead_name in LEAD_NAMES:
        if lead_name in LEAD_AXES:
            lead_signal = _project_frontal(tiled, axis_deg, lead_name)
        else:
            lead_signal = _generate_precordial(tiled, lead_name)

        # Add baseline wander (low-frequency sinusoid)
        wander = 0.05 * np.sin(2 * np.pi * 0.15 * t + np.random.uniform(0, 2 * np.pi))

        # Add noise
        lead_noise = np.random.normal(0, noise, n_total) if noise > 0 else np.zeros(n_total)

        leads[lead_name] = lead_signal + wander + lead_noise

    return {
        "time": t,
        "leads": leads,
        "params": {
            "hr_bpm": hr_bpm,
            "pr_ms": pr_ms,
            "qrs_ms": qrs_ms,
            "qt_ms": qt_ms,
            "axis_deg": axis_deg,
            "noise": noise,
            "duration_s": duration_s,
            "fs": fs,
        },
    }


# ---------------------------------------------------------------------------
# Pathological ECG generation
# ---------------------------------------------------------------------------

_PATHOLOGY_CONFIGS: dict[str, dict[str, Any]] = {
    "normal": {},
    "stemi_anterior": {
        "description_pt": "STEMI anterior — supradesnivelamento de ST em V1-V4",
    },
    "stemi_inferior": {
        "description_pt": "STEMI inferior — supradesnivelamento de ST em II, III, aVF",
    },
    "lbbb": {
        "qrs_ms": 150,
        "description_pt": "Bloqueio de ramo esquerdo — QRS > 120 ms, padrão QS em V1",
    },
    "rbbb": {
        "qrs_ms": 140,
        "description_pt": "Bloqueio de ramo direito — QRS > 120 ms, RSR' em V1",
    },
    "af": {
        "description_pt": "Fibrilação atrial — ritmo irregularmente irregular, sem onda P",
    },
    "wpw": {
        "pr_ms": 100,
        "description_pt": "Wolf-Parkinson-White — PR curto, onda delta, QRS alargado",
    },
    "hyperkalemia": {
        "description_pt": "Hipercalemia — T apiculadas, QRS alargado",
    },
    "hyperkalemia_severe": {
        "qrs_ms": 160,
        "description_pt": "Hipercalemia grave — sine wave, QRS muito alargado",
    },
    "hypokalemia": {
        "description_pt": "Hipocalemia — T achatada, onda U proeminente, infra de ST",
    },
    "hypercalcemia": {
        "qt_ms": 280,
        "description_pt": "Hipercalcemia — QT curto, ST quase ausente",
    },
    "hypocalcemia": {
        "qt_ms": 520,
        "description_pt": "Hipocalcemia — QT longo por prolongamento do ST",
    },
    "long_qt": {
        "qt_ms": 520,
        "description_pt": "QT longo — risco de Torsades de Pointes",
    },
}


def generate_pathological_ecg(pathology: str = "stemi_anterior") -> dict[str, Any]:
    """Generate an ECG with a specific pathological pattern.

    Parameters
    ----------
    pathology : str
        One of: "normal", "stemi_anterior", "stemi_inferior", "lbbb",
        "rbbb", "af", "wpw", "hyperkalemia", "long_qt".

    Returns
    -------
    dict
        Same format as ``generate_ecg`` with an additional "pathology" key.
    """
    pathology = pathology.lower()
    if pathology not in _PATHOLOGY_CONFIGS:
        raise ValueError(
            f"Unknown pathology '{pathology}'. "
            f"Available: {list(_PATHOLOGY_CONFIGS.keys())}"
        )

    config = _PATHOLOGY_CONFIGS[pathology]

    # Base parameters (may be overridden by config)
    hr = config.get("hr_bpm", 72)
    pr = config.get("pr_ms", 160)
    qrs = config.get("qrs_ms", 90)
    qt = config.get("qt_ms", 380)
    axis = config.get("axis_deg", 60)

    ecg_data = generate_ecg(
        hr_bpm=hr,
        pr_ms=pr,
        qrs_ms=qrs,
        qt_ms=qt,
        axis_deg=axis,
        noise=0.02,
        duration_s=10,
        fs=500,
    )

    # Apply pathology-specific modifications
    if pathology == "stemi_anterior":
        # Elevate ST in V1-V4
        for lead in ("V1", "V2", "V3", "V4"):
            signal = ecg_data["leads"][lead]
            n = len(signal)
            rr_samples = int(500 * 60.0 / hr)
            for beat_start in range(0, n, rr_samples):
                st_start = beat_start + int(rr_samples * 0.35)
                st_end = beat_start + int(rr_samples * 0.55)
                if st_end > n:
                    break
                seg_len = st_end - st_start
                elevation = 0.3 * np.ones(seg_len)
                ramp = min(10, seg_len)
                elevation[:ramp] = np.linspace(0, 0.3, ramp)
                elevation[-ramp:] = np.linspace(0.3, 0, ramp)
                signal[st_start:st_end] += elevation
        # Reciprocal depression in II, III, aVF
        for lead in ("II", "III", "aVF"):
            signal = ecg_data["leads"][lead]
            n = len(signal)
            for beat_start in range(0, n, rr_samples):
                st_start = beat_start + int(rr_samples * 0.35)
                st_end = beat_start + int(rr_samples * 0.55)
                if st_end > n:
                    break
                seg_len = st_end - st_start
                depression = 0.1 * np.ones(seg_len)
                ramp = min(10, seg_len)
                depression[:ramp] = np.linspace(0, 0.1, ramp)
                depression[-ramp:] = np.linspace(0.1, 0, ramp)
                signal[st_start:st_end] -= depression

    elif pathology == "stemi_inferior":
        rr_samples = int(500 * 60.0 / hr)
        for lead in ("II", "III", "aVF"):
            signal = ecg_data["leads"][lead]
            n = len(signal)
            for beat_start in range(0, n, rr_samples):
                st_start = beat_start + int(rr_samples * 0.35)
                st_end = beat_start + int(rr_samples * 0.55)
                if st_end > n:
                    break
                seg_len = st_end - st_start
                elevation = 0.25 * np.ones(seg_len)
                ramp = min(10, seg_len)
                elevation[:ramp] = np.linspace(0, 0.25, ramp)
                elevation[-ramp:] = np.linspace(0.25, 0, ramp)
                signal[st_start:st_end] += elevation
        # Reciprocal in I, aVL
        for lead in ("I", "aVL"):
            signal = ecg_data["leads"][lead]
            n = len(signal)
            for beat_start in range(0, n, rr_samples):
                st_start = beat_start + int(rr_samples * 0.35)
                st_end = beat_start + int(rr_samples * 0.55)
                if st_end > n:
                    break
                seg_len = st_end - st_start
                depression = 0.1 * np.ones(seg_len)
                ramp = min(10, seg_len)
                depression[:ramp] = np.linspace(0, 0.1, ramp)
                depression[-ramp:] = np.linspace(0.1, 0, ramp)
                signal[st_start:st_end] -= depression

    elif pathology == "lbbb":
        # Wide QRS already set. Make V1 predominantly negative, V6 positive broad R
        signal_v1 = ecg_data["leads"]["V1"]
        ecg_data["leads"]["V1"] = -np.abs(signal_v1) * 0.8
        signal_v6 = ecg_data["leads"]["V6"]
        ecg_data["leads"]["V6"] = np.abs(signal_v6) * 1.2

    elif pathology == "rbbb":
        # RSR' pattern in V1
        signal_v1 = ecg_data["leads"]["V1"]
        n = len(signal_v1)
        rr_samples = int(500 * 60.0 / hr)
        for beat_start in range(0, n, rr_samples):
            # Add secondary R' wave
            r_prime_center = beat_start + int(rr_samples * 0.28)
            if r_prime_center + 20 > n:
                break
            t_local = np.arange(40) - 20
            r_prime = 0.4 * np.exp(-(t_local**2) / (2 * 8**2))
            start = max(0, r_prime_center - 20)
            end = min(n, r_prime_center + 20)
            actual_len = end - start
            signal_v1[start:end] += r_prime[:actual_len]
        # Deep S in I, V6
        for lead in ("I", "V6"):
            signal = ecg_data["leads"][lead]
            n = len(signal)
            for beat_start in range(0, n, rr_samples):
                s_center = beat_start + int(rr_samples * 0.25)
                if s_center + 15 > n:
                    break
                t_local = np.arange(30) - 15
                s_deep = -0.3 * np.exp(-(t_local**2) / (2 * 6**2))
                start = max(0, s_center - 15)
                end = min(n, s_center + 15)
                actual_len = end - start
                signal[start:end] += s_deep[:actual_len]

    elif pathology == "af":
        # Remove P waves and make RR irregular
        rr_base = int(500 * 60.0 / hr)
        n_total = len(ecg_data["time"])
        for lead_name in LEAD_NAMES:
            signal = ecg_data["leads"][lead_name]
            # Add fibrillatory baseline
            fibrillation = 0.05 * np.sin(
                2 * np.pi * 6 * ecg_data["time"] + np.random.uniform(0, 2 * np.pi)
            )
            fibrillation += 0.03 * np.sin(
                2 * np.pi * 8.5 * ecg_data["time"] + np.random.uniform(0, 2 * np.pi)
            )
            signal += fibrillation
            # Suppress P waves: zero out early portion of each beat
            for beat_start in range(0, n_total, rr_base):
                p_end = beat_start + int(rr_base * 0.15)
                if p_end > n_total:
                    break
                signal[beat_start:p_end] *= 0.1  # suppress P wave
            ecg_data["leads"][lead_name] = signal

    elif pathology == "wpw":
        # Add delta wave (slurred upstroke) to all leads
        rr_samples = int(500 * 60.0 / hr)
        for lead_name in LEAD_NAMES:
            signal = ecg_data["leads"][lead_name]
            n = len(signal)
            for beat_start in range(0, n, rr_samples):
                delta_start = beat_start + int(rr_samples * 0.18)
                delta_end = delta_start + int(rr_samples * 0.06)
                if delta_end > n:
                    break
                seg_len = delta_end - delta_start
                delta = np.linspace(0, 0.3, seg_len)
                signal[delta_start:delta_end] += delta

    elif pathology == "hyperkalemia":
        # Peaked T waves + widened QRS
        rr_samples = int(500 * 60.0 / hr)
        for lead_name in LEAD_NAMES:
            signal = ecg_data["leads"][lead_name]
            n = len(signal)
            for beat_start in range(0, n, rr_samples):
                # Peak the T wave
                t_center = beat_start + int(rr_samples * 0.55)
                if t_center + 20 > n:
                    break
                t_local = np.arange(40) - 20
                peaked_t = 0.5 * np.exp(-(t_local**2) / (2 * 5**2))
                start = max(0, t_center - 20)
                end = min(n, t_center + 20)
                actual_len = end - start
                signal[start:end] += peaked_t[:actual_len]

            # Widen QRS via smoothing
            kernel = np.ones(7) / 7
            qrs_end = int(rr_samples * 0.35)
            for beat_start in range(0, n, rr_samples):
                seg_start = beat_start
                seg_end = min(n, beat_start + qrs_end)
                seg = signal[seg_start:seg_end]
                if len(seg) > len(kernel):
                    padded = np.pad(seg, 3, mode="edge")
                    signal[seg_start:seg_end] = np.convolve(padded, kernel, mode="valid")[
                        : len(seg)
                    ]

    elif pathology == "hyperkalemia_severe":
        # Sine wave pattern: very peaked T + very wide QRS fusing together
        rr_samples = int(500 * 60.0 / hr)
        for lead_name in LEAD_NAMES:
            signal = ecg_data["leads"][lead_name]
            n = len(signal)
            for beat_start in range(0, n, rr_samples):
                # Very peaked T wave
                t_center = beat_start + int(rr_samples * 0.55)
                if t_center + 30 > n:
                    break
                t_local = np.arange(60) - 30
                peaked_t = 0.8 * np.exp(-(t_local**2) / (2 * 7**2))
                start = max(0, t_center - 30)
                end = min(n, t_center + 30)
                actual_len = end - start
                signal[start:end] += peaked_t[:actual_len]

            # Heavy QRS smoothing (sine wave effect)
            kernel = np.ones(15) / 15
            for beat_start in range(0, n, rr_samples):
                seg_end = min(n, beat_start + rr_samples)
                seg = signal[beat_start:seg_end]
                if len(seg) > len(kernel):
                    padded = np.pad(seg, 7, mode="edge")
                    signal[beat_start:seg_end] = np.convolve(
                        padded, kernel, mode="valid"
                    )[: len(seg)]

            # Suppress P waves
            for beat_start in range(0, n, rr_samples):
                p_end = min(n, beat_start + int(rr_samples * 0.15))
                signal[beat_start:p_end] *= 0.1

    elif pathology == "hypokalemia":
        # Flattened T waves + ST depression + prominent U waves
        rr_samples = int(500 * 60.0 / hr)
        for lead_name in LEAD_NAMES:
            signal = ecg_data["leads"][lead_name]
            n = len(signal)
            for beat_start in range(0, n, rr_samples):
                # Flatten T wave (reduce amplitude)
                t_start = beat_start + int(rr_samples * 0.45)
                t_end = beat_start + int(rr_samples * 0.65)
                if t_end > n:
                    break
                signal[t_start:t_end] *= 0.25

                # ST depression
                st_start = beat_start + int(rr_samples * 0.35)
                st_end = beat_start + int(rr_samples * 0.50)
                if st_end > n:
                    break
                seg_len = st_end - st_start
                depression = 0.12 * np.ones(seg_len)
                ramp = min(8, seg_len)
                depression[:ramp] = np.linspace(0, 0.12, ramp)
                depression[-ramp:] = np.linspace(0.12, 0, ramp)
                signal[st_start:st_end] -= depression

                # Prominent U wave after T
                u_center = beat_start + int(rr_samples * 0.72)
                if u_center + 15 > n:
                    break
                t_local = np.arange(30) - 15
                u_wave = 0.15 * np.exp(-(t_local**2) / (2 * 8**2))
                start = max(0, u_center - 15)
                end = min(n, u_center + 15)
                actual_len = end - start
                signal[start:end] += u_wave[:actual_len]

    elif pathology == "hypercalcemia":
        # Short QT already set via config; further shorten ST segment
        rr_samples = int(500 * 60.0 / hr)
        for lead_name in LEAD_NAMES:
            signal = ecg_data["leads"][lead_name]
            n = len(signal)
            for beat_start in range(0, n, rr_samples):
                # Compress ST segment (bring T closer to QRS)
                st_start = beat_start + int(rr_samples * 0.30)
                st_end = beat_start + int(rr_samples * 0.42)
                if st_end > n:
                    break
                seg_len = st_end - st_start
                # Elevate ST slightly to simulate T merging with QRS
                bump = 0.08 * np.ones(seg_len)
                signal[st_start:st_end] += bump

    elif pathology == "hypocalcemia":
        pass  # QT prolongation already set via config (qt_ms=520)

    elif pathology == "long_qt":
        pass  # QT already set to 520 ms via config

    ecg_data["pathology"] = pathology
    ecg_data["pathology_description_pt"] = config.get("description_pt", "ECG normal")
    return ecg_data


# ---------------------------------------------------------------------------
# Noise
# ---------------------------------------------------------------------------


def add_noise(signal: np.ndarray, snr_db: float = 20) -> np.ndarray:
    """Add Gaussian noise to a signal at a specified SNR.

    Parameters
    ----------
    signal : np.ndarray
        Input signal.
    snr_db : float
        Desired signal-to-noise ratio in dB.

    Returns
    -------
    np.ndarray
        Noisy signal.
    """
    sig_power = np.mean(signal**2)
    if sig_power == 0:
        return signal.copy()
    noise_power = sig_power / (10 ** (snr_db / 10))
    noise = np.random.normal(0, np.sqrt(noise_power), len(signal))
    return signal + noise


# ---------------------------------------------------------------------------
# Plotly visualization
# ---------------------------------------------------------------------------


def ecg_to_plotly_figure(ecg_data: dict, layout: str = "3x4") -> "go.Figure":
    """Convert ECG data to a Plotly figure.

    Parameters
    ----------
    ecg_data : dict
        Output from ``generate_ecg`` or ``generate_pathological_ecg``.
    layout : str
        Layout format: "3x4" (standard), "6x2", or "12x1".

    Returns
    -------
    plotly.graph_objects.Figure
        A Plotly figure ready for display.

    Raises
    ------
    ImportError
        If plotly is not installed.
    """
    if not HAS_PLOTLY:
        raise ImportError("Plotly is required for ecg_to_plotly_figure. pip install plotly")

    time_arr = ecg_data["time"]
    leads_data = ecg_data["leads"]

    # Determine grid layout
    if layout == "3x4":
        rows, cols = 3, 4
        lead_order = [
            ["I", "aVR", "V1", "V4"],
            ["II", "aVL", "V2", "V5"],
            ["III", "aVF", "V3", "V6"],
        ]
    elif layout == "6x2":
        rows, cols = 6, 2
        lead_order = [
            ["I", "V1"],
            ["II", "V2"],
            ["III", "V3"],
            ["aVR", "V4"],
            ["aVL", "V5"],
            ["aVF", "V6"],
        ]
    elif layout == "12x1":
        rows, cols = 12, 1
        lead_order = [[name] for name in LEAD_NAMES]
    else:
        raise ValueError(f"Unknown layout '{layout}'. Use '3x4', '6x2', or '12x1'.")

    # Flatten for subplot titles
    flat_leads = [lead for row in lead_order for lead in row]

    fig = make_subplots(
        rows=rows,
        cols=cols,
        subplot_titles=flat_leads,
        vertical_spacing=0.03,
        horizontal_spacing=0.03,
    )

    # Show only 2.5 seconds per strip (standard)
    t_max = min(2.5, time_arr[-1])
    mask = time_arr <= t_max

    for r_idx, row_leads in enumerate(lead_order):
        for c_idx, lead_name in enumerate(row_leads):
            signal = leads_data.get(lead_name, np.zeros_like(time_arr))
            fig.add_trace(
                go.Scatter(
                    x=time_arr[mask],
                    y=signal[mask],
                    mode="lines",
                    line=dict(color="black", width=1),
                    name=lead_name,
                    showlegend=False,
                ),
                row=r_idx + 1,
                col=c_idx + 1,
            )

    # Style
    title = "ECG 12 Derivações"
    pathology = ecg_data.get("pathology")
    if pathology and pathology != "normal":
        desc = ecg_data.get("pathology_description_pt", pathology)
        title = f"ECG — {desc}"

    fig.update_layout(
        title=title,
        height=200 * rows,
        width=300 * cols,
        paper_bgcolor="#FFF5F5",
        plot_bgcolor="#FFF5F5",
        font=dict(size=10),
        margin=dict(l=40, r=20, t=60, b=20),
    )

    # Grid lines to simulate ECG paper
    for i in range(1, rows * cols + 1):
        fig.update_xaxes(
            showgrid=True,
            gridcolor="rgba(255,150,150,0.4)",
            dtick=0.2,
            row=(i - 1) // cols + 1,
            col=(i - 1) % cols + 1,
        )
        fig.update_yaxes(
            showgrid=True,
            gridcolor="rgba(255,150,150,0.4)",
            dtick=0.5,
            row=(i - 1) // cols + 1,
            col=(i - 1) % cols + 1,
        )

    return fig

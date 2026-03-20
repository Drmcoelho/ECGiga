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


def _generate_rr_intervals(
    hr_bpm: float, n_beats: int, mode: str = "sinus",
    rsa_amplitude: float = 0.03, rsa_freq: float = 0.2,
) -> np.ndarray:
    """Generate physiologically realistic RR intervals with HRV.

    Parameters
    ----------
    hr_bpm : float
        Mean heart rate in BPM.
    n_beats : int
        Number of beats to generate.
    mode : str
        "sinus" — normal sinus rhythm with respiratory sinus arrhythmia (RSA)
        "af" — atrial fibrillation (irregularly irregular)
        "regular" — perfectly regular (pacemaker-like)
    rsa_amplitude : float
        Amplitude of RSA modulation (fraction of RR, default 3%).
    rsa_freq : float
        Respiratory rate in Hz (default 0.2 Hz = 12 breaths/min).

    Returns
    -------
    np.ndarray
        Array of RR intervals in seconds.
    """
    rr_mean = 60.0 / hr_bpm

    if mode == "regular":
        return np.full(n_beats, rr_mean)

    if mode == "af":
        # Irregularly irregular: exponential distribution clipped to reasonable range
        rr_intervals = np.random.exponential(rr_mean * 0.85, n_beats)
        rr_intervals = np.clip(rr_intervals, 0.35, 1.8)
        return rr_intervals

    # Normal sinus: HRV with RSA + small random jitter
    beat_times = np.arange(n_beats) * rr_mean
    # Respiratory sinus arrhythmia (RSA)
    rsa = rr_mean * rsa_amplitude * np.sin(2 * np.pi * rsa_freq * beat_times)
    # Random beat-to-beat jitter (SDNN ~30-50ms for normal)
    jitter = np.random.normal(0, rr_mean * 0.025, n_beats)  # 2.5% CV
    rr_intervals = rr_mean + rsa + jitter
    rr_intervals = np.clip(rr_intervals, rr_mean * 0.7, rr_mean * 1.3)
    return rr_intervals


def generate_ecg(
    hr_bpm: float = 72,
    pr_ms: float = 160,
    qrs_ms: float = 90,
    qt_ms: float = 380,
    axis_deg: float = 60,
    noise: float = 0.02,
    duration_s: float = 10,
    fs: int = 500,
    hrv_mode: str = "sinus",
) -> dict[str, Any]:
    """Generate a synthetic 12-lead ECG with realistic beat-to-beat variability.

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
    hrv_mode : str
        HRV mode: "sinus" (default), "af", or "regular".

    Returns
    -------
    dict
        {"time": np.ndarray, "leads": dict[str, np.ndarray], "params": dict}
    """
    n_total = int(duration_s * fs)
    t = np.linspace(0, duration_s, n_total, endpoint=False)

    # Estimate number of beats needed
    rr_mean = 60.0 / hr_bpm
    n_beats_est = int(np.ceil(duration_s / rr_mean)) + 2
    rr_intervals = _generate_rr_intervals(hr_bpm, n_beats_est, mode=hrv_mode)

    # Build signal beat-by-beat with individual RR intervals and morphology variation
    signal_ii = np.zeros(n_total)
    sample_pos = 0
    beat_boundaries: list[int] = []

    for beat_idx in range(n_beats_est):
        rr_s = float(rr_intervals[beat_idx])
        beat_samples = int(rr_s * fs)
        if beat_samples < 10:
            beat_samples = 10
        if sample_pos >= n_total:
            break

        # Generate this beat with slight morphology variation
        p_amp_var = 1.0 + np.random.uniform(-0.10, 0.10)   # ±10% P amplitude
        t_amp_var = 1.0 + np.random.uniform(-0.05, 0.05)   # ±5% T amplitude
        r_amp_var = 1.0 + np.random.uniform(-0.03, 0.03)   # ±3% R amplitude

        beat = _single_beat(rr_s, fs, pr_ms, qrs_ms, qt_ms)

        # Apply morphology variation (P is first 15%, R is center, T is last 30%)
        n_beat = len(beat)
        p_end = int(n_beat * 0.15)
        qrs_start = int(n_beat * 0.15)
        qrs_end = int(n_beat * 0.35)
        t_start = int(n_beat * 0.45)

        beat[:p_end] *= p_amp_var
        beat[qrs_start:qrs_end] *= r_amp_var
        beat[t_start:] *= t_amp_var

        # Place beat in signal
        end_pos = min(sample_pos + n_beat, n_total)
        actual_len = end_pos - sample_pos
        signal_ii[sample_pos:end_pos] = beat[:actual_len]
        beat_boundaries.append(sample_pos)
        sample_pos += n_beat

    # Generate all 12 leads
    leads: dict[str, np.ndarray] = {}

    for lead_name in LEAD_NAMES:
        if lead_name in LEAD_AXES:
            lead_signal = _project_frontal(signal_ii, axis_deg, lead_name)
        else:
            lead_signal = _generate_precordial(signal_ii, lead_name)

        # Add baseline wander (respiratory + low-frequency drift)
        phase = np.random.uniform(0, 2 * np.pi)
        wander = 0.04 * np.sin(2 * np.pi * 0.15 * t + phase)
        wander += 0.02 * np.sin(2 * np.pi * 0.05 * t + phase * 0.7)  # slow drift

        # Add EMG-like noise (higher frequency component)
        lead_noise = np.zeros(n_total)
        if noise > 0:
            lead_noise = np.random.normal(0, noise, n_total)
            # Add occasional 50/60Hz powerline artifact (very subtle)
            powerline = 0.005 * np.sin(2 * np.pi * 60 * t + np.random.uniform(0, 2 * np.pi))
            lead_noise += powerline

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
            "hrv_mode": hrv_mode,
        },
        "beat_boundaries": beat_boundaries,
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
    "stemi_lateral": {
        "description_pt": "STEMI lateral — supradesnivelamento de ST em I, aVL, V5-V6",
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
        "hrv_mode": "af",
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
    "brugada_type1": {
        "description_pt": "Brugada tipo 1 — ST coved em V1-V2, T negativa",
    },
    "pericarditis": {
        "description_pt": "Pericardite aguda — supra ST côncavo difuso, depressão PR, infra aVR",
    },
    "pe_pattern": {
        "hr_bpm": 110,
        "axis_deg": 105,
        "description_pt": "Padrão de TEP — S1Q3T3, taquicardia sinusal, eixo à direita",
    },
    "lvh_strain": {
        "description_pt": "HVE com strain — R alto em V5-V6, infra ST + T invertida lateral",
    },
    "first_degree_avb": {
        "pr_ms": 240,
        "description_pt": "BAV 1° grau — PR prolongado (> 200 ms)",
    },
    "early_repolarization": {
        "description_pt": "Repolarização precoce — supra ST côncavo com entalhe J, benigno",
    },
    # ── Sobrecarga / Hipertrofia ──────────────────────────────────────────
    "rae": {
        "description_pt": "Sobrecarga Atrial Direita — P pulmonale: onda P apiculada ≥2.5 mm em DII/III/aVF",
    },
    "lae": {
        "description_pt": "Sobrecarga Atrial Esquerda — P mitrale: onda P bífida em DII, componente negativo terminal em V1",
    },
    "rvh": {
        "axis_deg": 110,
        "description_pt": "Hipertrofia Ventricular Direita — R>S em V1, desvio do eixo direita, strain em V1-V2",
    },
    # ── Bloqueios AV de 2° e 3° grau ────────────────────────────────────
    "bav_mobitz1": {
        "pr_ms": 180,
        "description_pt": "BAV 2° Grau Mobitz I (Wenckebach) — PR progressivamente longo até batida bloqueada",
    },
    "bav_mobitz2": {
        "pr_ms": 180,
        "description_pt": "BAV 2° Grau Mobitz II — PR fixo com bloqueio súbito, risco alto de BAV total",
    },
    "bav_complete": {
        "hr_bpm": 40,
        "pr_ms": 180,
        "qrs_ms": 130,
        "description_pt": "BAV Total (3° Grau) — dissociação AV completa, ritmo de escape ventricular ~40 bpm",
    },
    # ── Equivalentes de STEMI ────────────────────────────────────────────
    "wellens_a": {
        "description_pt": "Síndrome de Wellens tipo A — T bifásica em V2-V3: suboclusão proximal da DAE",
    },
    "wellens_b": {
        "description_pt": "Síndrome de Wellens tipo B — T invertida profunda simétrica em V2-V3: suboclusão proximal da DAE",
    },
    "de_winter": {
        "description_pt": "Padrão de De Winter — infradesnivelamento ST + onda T alta em V1-V4: oclusão proximal da DAE",
    },
    "stemi_posterior": {
        "description_pt": "STEMI Posterior — infradesnivelamento ST V1-V4 (espelho do supra posterior); R dominante em V1-V2",
    },
    "stemi_avr": {
        "description_pt": "Supra em aVR — doença de tronco ou coronária esquerda proximal: supra aVR + infra ST difuso",
    },
    # ── Bradicardia / Taquicardia sinusal ────────────────────────────────
    "sinus_bradycardia": {
        "hr_bpm": 45,
        "description_pt": "Bradicardia Sinusal — FC <60 bpm, morfologia normal; atletas, vagotonia, beta-bloqueador",
    },
    "sinus_tachycardia": {
        "hr_bpm": 120,
        "qt_ms": 320,
        "description_pt": "Taquicardia Sinusal — FC >100 bpm, onda P sinusal, PR normal; febre, dor, hipovolemia, TEP",
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
    hrv_mode = config.get("hrv_mode", "sinus")

    ecg_data = generate_ecg(
        hr_bpm=hr,
        pr_ms=pr,
        qrs_ms=qrs,
        qt_ms=qt,
        axis_deg=axis,
        noise=0.02,
        duration_s=10,
        fs=500,
        hrv_mode=hrv_mode,
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

    elif pathology == "stemi_lateral":
        rr_samples = int(500 * 60.0 / hr)
        for lead in ("I", "aVL", "V5", "V6"):
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
        # Reciprocal in III, aVF
        for lead in ("III", "aVF"):
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

    elif pathology == "brugada_type1":
        # Coved ST elevation in V1-V2 with negative T wave
        rr_samples = int(500 * 60.0 / hr)
        for lead in ("V1", "V2"):
            signal = ecg_data["leads"][lead]
            n = len(signal)
            for beat_start in range(0, n, rr_samples):
                # Coved ST: sharp rise at J-point then downsloping
                j_point = beat_start + int(rr_samples * 0.28)
                st_end = beat_start + int(rr_samples * 0.55)
                if st_end > n:
                    break
                seg_len = st_end - j_point
                # Coved pattern: starts high, slopes down
                coved = 0.25 * np.exp(-np.linspace(0, 3, seg_len))
                signal[j_point:st_end] += coved
                # Invert T wave
                t_start = beat_start + int(rr_samples * 0.50)
                t_end = beat_start + int(rr_samples * 0.70)
                if t_end > n:
                    break
                signal[t_start:t_end] *= -0.8

    elif pathology == "pericarditis":
        # Diffuse concave-up ST elevation + PR depression + aVR ST depression
        rr_samples = int(500 * 60.0 / hr)
        diffuse_leads = ["I", "II", "III", "aVL", "aVF", "V2", "V3", "V4", "V5", "V6"]
        for lead in diffuse_leads:
            signal = ecg_data["leads"][lead]
            n = len(signal)
            for beat_start in range(0, n, rr_samples):
                # Concave-up ST elevation (less than STEMI, more diffuse)
                st_start = beat_start + int(rr_samples * 0.30)
                st_end = beat_start + int(rr_samples * 0.55)
                if st_end > n:
                    break
                seg_len = st_end - st_start
                x = np.linspace(0, np.pi, seg_len)
                concave_up = 0.12 * np.sin(x)  # concave up shape
                signal[st_start:st_end] += concave_up
                # PR depression
                pr_start = beat_start + int(rr_samples * 0.12)
                pr_end = beat_start + int(rr_samples * 0.20)
                if pr_end > n:
                    break
                pr_seg = pr_end - pr_start
                signal[pr_start:pr_end] -= 0.05 * np.ones(pr_seg)

        # aVR: ST depression + PR elevation (mirror)
        signal_avr = ecg_data["leads"]["aVR"]
        n = len(signal_avr)
        for beat_start in range(0, n, rr_samples):
            st_start = beat_start + int(rr_samples * 0.30)
            st_end = beat_start + int(rr_samples * 0.55)
            if st_end > n:
                break
            seg_len = st_end - st_start
            signal_avr[st_start:st_end] -= 0.15 * np.ones(seg_len)

    elif pathology == "pe_pattern":
        # S1Q3T3: deep S in I, Q in III, inverted T in III/V1-V3
        rr_samples = int(500 * 60.0 / hr)
        # Deep S in lead I
        signal_i = ecg_data["leads"]["I"]
        n = len(signal_i)
        for beat_start in range(0, n, rr_samples):
            s_center = beat_start + int(rr_samples * 0.25)
            if s_center + 15 > n:
                break
            t_local = np.arange(30) - 15
            s_deep = -0.35 * np.exp(-(t_local**2) / (2 * 6**2))
            start = max(0, s_center - 15)
            end = min(n, s_center + 15)
            signal_i[start:end] += s_deep[:end - start]

        # Q in III
        signal_iii = ecg_data["leads"]["III"]
        for beat_start in range(0, n, rr_samples):
            q_center = beat_start + int(rr_samples * 0.19)
            if q_center + 10 > n:
                break
            t_local = np.arange(20) - 10
            q_wave = -0.25 * np.exp(-(t_local**2) / (2 * 4**2))
            start = max(0, q_center - 10)
            end = min(n, q_center + 10)
            signal_iii[start:end] += q_wave[:end - start]

        # Inverted T in III, V1-V3
        for lead in ("III", "V1", "V2", "V3"):
            signal = ecg_data["leads"][lead]
            for beat_start in range(0, n, rr_samples):
                t_start = beat_start + int(rr_samples * 0.50)
                t_end = beat_start + int(rr_samples * 0.70)
                if t_end > n:
                    break
                signal[t_start:t_end] *= -0.7

    elif pathology == "lvh_strain":
        # Tall R in V5-V6, deep S in V1-V2, ST depression + T inversion in laterals
        rr_samples = int(500 * 60.0 / hr)
        n = len(ecg_data["time"])
        # Amplify R in V5-V6
        for lead in ("V5", "V6"):
            ecg_data["leads"][lead] *= 1.8
        # Deep S in V1-V2
        for lead in ("V1", "V2"):
            signal = ecg_data["leads"][lead]
            for beat_start in range(0, n, rr_samples):
                # Deepen S wave region
                s_start = beat_start + int(rr_samples * 0.22)
                s_end = beat_start + int(rr_samples * 0.30)
                if s_end > n:
                    break
                signal[s_start:s_end] -= 0.4

        # Strain pattern in lateral leads: downsloping ST + asymmetric T inversion
        for lead in ("I", "aVL", "V5", "V6"):
            signal = ecg_data["leads"][lead]
            for beat_start in range(0, n, rr_samples):
                # Downsloping ST depression
                st_start = beat_start + int(rr_samples * 0.32)
                st_end = beat_start + int(rr_samples * 0.50)
                if st_end > n:
                    break
                seg_len = st_end - st_start
                downslopping = -np.linspace(0.05, 0.15, seg_len)
                signal[st_start:st_end] += downslopping
                # Asymmetric T inversion (slow descent, rapid return)
                t_start = beat_start + int(rr_samples * 0.50)
                t_end = beat_start + int(rr_samples * 0.70)
                if t_end > n:
                    break
                signal[t_start:t_end] *= -0.6

    elif pathology == "first_degree_avb":
        pass  # PR already set to 240 ms via config

    elif pathology == "rae":
        # P pulmonale: peaked P ≥2.5 mm in II, III, aVF; narrow
        rr_samples = int(500 * 60.0 / hr)
        n = len(ecg_data["time"])
        for lead in ("II", "III", "aVF"):
            signal = ecg_data["leads"][lead]
            for beat_start in range(0, n, rr_samples):
                p_center = beat_start + int(rr_samples * 0.08)
                if p_center + 20 > n:
                    break
                t_local = np.arange(40) - 20
                # Tall, narrow, peaked P
                peaked_p = 0.20 * np.exp(-(t_local**2) / (2 * 4**2))
                start = max(0, p_center - 20)
                end = min(n, p_center + 20)
                signal[start:end] += peaked_p[:end - start]
        # V1: biphasic P — positive first component
        signal_v1 = ecg_data["leads"]["V1"]
        for beat_start in range(0, n, rr_samples):
            p_center = beat_start + int(rr_samples * 0.08)
            if p_center + 20 > n:
                break
            t_local = np.arange(40) - 20
            peaked_p = 0.15 * np.exp(-(t_local**2) / (2 * 4**2))
            start = max(0, p_center - 20)
            end = min(n, p_center + 20)
            signal_v1[start:end] += peaked_p[:end - start]

    elif pathology == "lae":
        # P mitrale: notched/bifid P in II (duration ≥120 ms); deep negative terminal in V1
        rr_samples = int(500 * 60.0 / hr)
        n = len(ecg_data["time"])
        for lead in ("I", "II", "aVL"):
            signal = ecg_data["leads"][lead]
            for beat_start in range(0, n, rr_samples):
                p_start = beat_start + int(rr_samples * 0.04)
                if p_start + 60 > n:
                    break
                t_local = np.arange(60)
                # Two humps separated by slight dip → notched appearance
                first_hump = 0.10 * np.exp(-((t_local - 15)**2) / (2 * 5**2))
                second_hump = 0.08 * np.exp(-((t_local - 38)**2) / (2 * 5**2))
                bifid_p = first_hump + second_hump
                end = min(n, p_start + 60)
                signal[p_start:end] += bifid_p[:end - p_start]
        # V1: deep negative terminal component of P
        signal_v1 = ecg_data["leads"]["V1"]
        for beat_start in range(0, n, rr_samples):
            p_center = beat_start + int(rr_samples * 0.09)
            if p_center + 25 > n:
                break
            t_local = np.arange(50) - 25
            neg_terminal = -0.12 * np.exp(-((t_local - 8)**2) / (2 * 5**2))
            start = max(0, p_center - 25)
            end = min(n, p_center + 25)
            signal_v1[start:end] += neg_terminal[:end - start]

    elif pathology == "rvh":
        # R > S in V1, right axis (set via config), T inversion V1-V3 (strain)
        rr_samples = int(500 * 60.0 / hr)
        n = len(ecg_data["time"])
        # Dominant R in V1
        signal_v1 = ecg_data["leads"]["V1"]
        for beat_start in range(0, n, rr_samples):
            r_center = beat_start + int(rr_samples * 0.22)
            if r_center + 20 > n:
                break
            t_local = np.arange(40) - 20
            r_tall = 0.7 * np.exp(-(t_local**2) / (2 * 5**2))
            start = max(0, r_center - 20)
            end = min(n, r_center + 20)
            signal_v1[start:end] += r_tall[:end - start]
        # Strain: T inversion in V1-V3
        for lead in ("V1", "V2", "V3"):
            signal = ecg_data["leads"][lead]
            for beat_start in range(0, n, rr_samples):
                t_start = beat_start + int(rr_samples * 0.48)
                t_end = beat_start + int(rr_samples * 0.68)
                if t_end > n:
                    break
                signal[t_start:t_end] *= -0.7
        # Deep S in V5-V6 (RVH hallmark)
        for lead in ("V5", "V6"):
            signal = ecg_data["leads"][lead]
            for beat_start in range(0, n, rr_samples):
                s_center = beat_start + int(rr_samples * 0.26)
                if s_center + 15 > n:
                    break
                t_local = np.arange(30) - 15
                s_deep = -0.35 * np.exp(-(t_local**2) / (2 * 6**2))
                start = max(0, s_center - 15)
                end = min(n, s_center + 15)
                signal[start:end] += s_deep[:end - start]

    elif pathology == "bav_mobitz1":
        # Wenckebach: PR progressively lengthens over 3 beats then 1 dropped beat (4:3 pattern)
        rr_samples = int(500 * 60.0 / hr)
        n = len(ecg_data["time"])
        wenckebach_pr_increments = [0, 30, 60]  # extra ms added per beat in cycle
        cycle_len = 4  # 3 conducted + 1 dropped
        beat_num = 0
        for beat_start in range(0, n, rr_samples):
            pos_in_cycle = beat_num % cycle_len
            if pos_in_cycle == 3:
                # Dropped beat: suppress QRS and T wave
                qrs_start = beat_start + int(rr_samples * 0.20)
                qrs_end = beat_start + int(rr_samples * 0.75)
                if qrs_end > n:
                    break
                for lead_name in LEAD_NAMES:
                    ecg_data["leads"][lead_name][qrs_start:qrs_end] *= 0.05
            beat_num += 1

    elif pathology == "bav_mobitz2":
        # Fixed PR with sudden dropped beat every 3rd beat (3:2 pattern)
        rr_samples = int(500 * 60.0 / hr)
        n = len(ecg_data["time"])
        cycle_len = 3  # 2 conducted + 1 dropped
        beat_num = 0
        for beat_start in range(0, n, rr_samples):
            pos_in_cycle = beat_num % cycle_len
            if pos_in_cycle == 2:
                # Dropped beat: preserve P wave, suppress QRS+T
                qrs_start = beat_start + int(rr_samples * 0.22)
                qrs_end = beat_start + int(rr_samples * 0.75)
                if qrs_end > n:
                    break
                for lead_name in LEAD_NAMES:
                    ecg_data["leads"][lead_name][qrs_start:qrs_end] *= 0.04
            beat_num += 1

    elif pathology == "bav_complete":
        # Complete AV block: P waves and QRS are independent (dissociated)
        # The ecg is generated at escape rate ~40bpm; add extra P waves at atrial rate ~75bpm
        rr_samples = int(500 * 60.0 / hr)  # ventricular escape: ~40bpm → large RR
        n = len(ecg_data["time"])
        atrial_rate_bpm = 80
        p_rr = int(500 * 60.0 / atrial_rate_bpm)  # ~375 samples at 75bpm
        # Superimpose independent P waves on the signal
        for lead_name in LEAD_NAMES:
            signal = ecg_data["leads"][lead_name]
            p_amplitude = 0.12 if lead_name in ("II", "aVF", "I") else (-0.10 if lead_name == "aVR" else 0.06)
            for p_start in range(0, n, p_rr):
                p_center = p_start + int(p_rr * 0.5)
                if p_center + 15 > n:
                    break
                t_local = np.arange(30) - 15
                p_wave = p_amplitude * np.exp(-(t_local**2) / (2 * 5**2))
                start = max(0, p_center - 15)
                end = min(n, p_center + 15)
                signal[start:end] += p_wave[:end - start]

    elif pathology == "wellens_a":
        # Wellens type A: biphasic T (positive→negative) in V2-V3
        rr_samples = int(500 * 60.0 / hr)
        n = len(ecg_data["time"])
        for lead in ("V2", "V3"):
            signal = ecg_data["leads"][lead]
            for beat_start in range(0, n, rr_samples):
                t_start = beat_start + int(rr_samples * 0.46)
                t_mid = beat_start + int(rr_samples * 0.54)
                t_end = beat_start + int(rr_samples * 0.68)
                if t_end > n:
                    break
                # First half positive, second half negative
                seg1 = t_mid - t_start
                seg2 = t_end - t_mid
                signal[t_start:t_mid] *= -0.4  # flatten existing T
                signal[t_start:t_mid] += 0.08 * np.sin(np.linspace(0, np.pi, seg1))
                signal[t_mid:t_end] = -0.12 * np.sin(np.linspace(0, np.pi, seg2))

    elif pathology == "wellens_b":
        # Wellens type B: deep symmetric T inversion in V2-V3 (± V1, V4)
        rr_samples = int(500 * 60.0 / hr)
        n = len(ecg_data["time"])
        for lead in ("V1", "V2", "V3", "V4"):
            signal = ecg_data["leads"][lead]
            depth = {"V1": -0.25, "V2": -0.45, "V3": -0.40, "V4": -0.20}[lead]
            for beat_start in range(0, n, rr_samples):
                t_start = beat_start + int(rr_samples * 0.46)
                t_end = beat_start + int(rr_samples * 0.70)
                if t_end > n:
                    break
                seg_len = t_end - t_start
                signal[t_start:t_end] *= 0.05  # suppress existing T
                # Symmetric inverted T
                x = np.linspace(0, np.pi, seg_len)
                signal[t_start:t_end] += depth * np.sin(x)

    elif pathology == "de_winter":
        # De Winter: ST depression at J-point + tall upright T waves in V1-V4
        rr_samples = int(500 * 60.0 / hr)
        n = len(ecg_data["time"])
        for lead in ("V1", "V2", "V3", "V4"):
            signal = ecg_data["leads"][lead]
            for beat_start in range(0, n, rr_samples):
                # ST depression starting at J-point
                st_start = beat_start + int(rr_samples * 0.28)
                st_end = beat_start + int(rr_samples * 0.48)
                if st_end > n:
                    break
                seg_len = st_end - st_start
                depression = -np.linspace(0.1, 0.2, seg_len)
                signal[st_start:st_end] += depression
                # Tall, symmetric, upright T waves (taller than normal)
                t_center = beat_start + int(rr_samples * 0.60)
                if t_center + 30 > n:
                    break
                t_local = np.arange(60) - 30
                tall_t = 0.5 * np.exp(-(t_local**2) / (2 * 10**2))
                start = max(0, t_center - 30)
                end = min(n, t_center + 30)
                signal[start:end] += tall_t[:end - start]

    elif pathology == "stemi_posterior":
        # Posterior STEMI: mirror image → ST depression + tall R + upright T in V1-V4
        rr_samples = int(500 * 60.0 / hr)
        n = len(ecg_data["time"])
        for lead in ("V1", "V2", "V3", "V4"):
            signal = ecg_data["leads"][lead]
            for beat_start in range(0, n, rr_samples):
                # ST depression (mirror of posterior elevation)
                st_start = beat_start + int(rr_samples * 0.32)
                st_end = beat_start + int(rr_samples * 0.52)
                if st_end > n:
                    break
                seg_len = st_end - st_start
                depression = 0.20 * np.ones(seg_len)
                ramp = min(10, seg_len)
                depression[:ramp] = np.linspace(0, 0.20, ramp)
                depression[-ramp:] = np.linspace(0.20, 0, ramp)
                signal[st_start:st_end] -= depression
                # Tall upright T (mirror of posterior T inversion)
                t_center = beat_start + int(rr_samples * 0.58)
                if t_center + 25 > n:
                    break
                t_local = np.arange(50) - 25
                tall_t = 0.35 * np.exp(-(t_local**2) / (2 * 8**2))
                start = max(0, t_center - 25)
                end = min(n, t_center + 25)
                signal[start:end] += tall_t[:end - start]
        # Tall R (dominant) in V1-V2 → R/S ratio > 1
        for lead in ("V1", "V2"):
            signal = ecg_data["leads"][lead]
            for beat_start in range(0, n, rr_samples):
                r_center = beat_start + int(rr_samples * 0.22)
                if r_center + 15 > n:
                    break
                t_local = np.arange(30) - 15
                r_boost = 0.5 * np.exp(-(t_local**2) / (2 * 5**2))
                start = max(0, r_center - 15)
                end = min(n, r_center + 15)
                signal[start:end] += r_boost[:end - start]

    elif pathology == "stemi_avr":
        # Left main / 3VD pattern: ST elevation in aVR + diffuse ST depression
        rr_samples = int(500 * 60.0 / hr)
        n = len(ecg_data["time"])
        # ST elevation in aVR (and V1 as secondary)
        for lead in ("aVR", "V1"):
            signal = ecg_data["leads"][lead]
            elev = 0.20 if lead == "aVR" else 0.10
            for beat_start in range(0, n, rr_samples):
                st_start = beat_start + int(rr_samples * 0.32)
                st_end = beat_start + int(rr_samples * 0.52)
                if st_end > n:
                    break
                seg_len = st_end - st_start
                elevation = elev * np.ones(seg_len)
                ramp = min(8, seg_len)
                elevation[:ramp] = np.linspace(0, elev, ramp)
                elevation[-ramp:] = np.linspace(elev, 0, ramp)
                signal[st_start:st_end] += elevation
        # Diffuse ST depression in all other leads
        for lead in ("I", "II", "III", "aVL", "aVF", "V2", "V3", "V4", "V5", "V6"):
            signal = ecg_data["leads"][lead]
            for beat_start in range(0, n, rr_samples):
                st_start = beat_start + int(rr_samples * 0.32)
                st_end = beat_start + int(rr_samples * 0.52)
                if st_end > n:
                    break
                seg_len = st_end - st_start
                depression = 0.15 * np.ones(seg_len)
                ramp = min(8, seg_len)
                depression[:ramp] = np.linspace(0, 0.15, ramp)
                depression[-ramp:] = np.linspace(0.15, 0, ramp)
                signal[st_start:st_end] -= depression

    elif pathology in ("sinus_bradycardia", "sinus_tachycardia"):
        pass  # HR already set via config; normal morphology

    elif pathology == "early_repolarization":
        # Concave-up ST elevation with J-point notch in inferior/lateral leads
        rr_samples = int(500 * 60.0 / hr)
        for lead in ("II", "III", "aVF", "V4", "V5", "V6"):
            signal = ecg_data["leads"][lead]
            n = len(signal)
            for beat_start in range(0, n, rr_samples):
                # J-point notch
                j_point = beat_start + int(rr_samples * 0.27)
                if j_point + 8 > n:
                    break
                t_local = np.arange(16) - 8
                notch = 0.08 * np.exp(-(t_local**2) / (2 * 3**2))
                start = max(0, j_point - 8)
                end = min(n, j_point + 8)
                signal[start:end] += notch[:end - start]
                # Subtle concave-up ST elevation
                st_start = beat_start + int(rr_samples * 0.30)
                st_end = beat_start + int(rr_samples * 0.50)
                if st_end > n:
                    break
                seg_len = st_end - st_start
                x = np.linspace(0, np.pi, seg_len)
                elevation = 0.08 * np.sin(x)
                signal[st_start:st_end] += elevation

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


def ecg_to_plotly_figure(ecg_data: dict, layout: str = "3x4",
                         rhythm_strip: bool = True) -> "go.Figure":
    """Convert ECG data to a Plotly figure with standard clinical format.

    Parameters
    ----------
    ecg_data : dict
        Output from ``generate_ecg`` or ``generate_pathological_ecg``.
    layout : str
        Layout format: "3x4" (standard), "6x2", or "12x1".
    rhythm_strip : bool
        If True and layout is "3x4", add a long rhythm strip (lead II) at bottom.

    Returns
    -------
    plotly.graph_objects.Figure
        A Plotly figure ready for display.
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
        if rhythm_strip:
            rows = 4  # Extra row for rhythm strip
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
        rhythm_strip = False
    elif layout == "12x1":
        rows, cols = 12, 1
        lead_order = [[name] for name in LEAD_NAMES]
        rhythm_strip = False
    else:
        raise ValueError(f"Unknown layout '{layout}'. Use '3x4', '6x2', or '12x1'.")

    # Flatten for subplot titles
    flat_leads = [lead for row in lead_order for lead in row]
    if rhythm_strip:
        flat_leads.extend(["II (ritmo contínuo)"] + [""] * (cols - 1))

    # Row heights: rhythm strip gets more space
    row_heights = [1.0] * (rows - (1 if rhythm_strip else 0))
    if rhythm_strip:
        row_heights.append(0.6)

    # Specs for rhythm strip spanning all columns
    specs = [[{} for _ in range(cols)] for _ in range(rows)]
    if rhythm_strip:
        specs[-1] = [{"colspan": cols}] + [None] * (cols - 1)

    fig = make_subplots(
        rows=rows,
        cols=cols,
        subplot_titles=flat_leads,
        vertical_spacing=0.04,
        horizontal_spacing=0.03,
        row_heights=row_heights,
        specs=specs,
    )

    # Show 2.5 seconds per strip (standard clinical)
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
                    line=dict(color="#111111", width=1.2),
                    name=lead_name,
                    showlegend=False,
                    hovertemplate=f"{lead_name}: %{{y:.2f}} mV<br>t=%{{x:.3f}}s",
                ),
                row=r_idx + 1,
                col=c_idx + 1,
            )

    # Rhythm strip: lead II, 10 seconds
    if rhythm_strip:
        signal_ii = leads_data.get("II", np.zeros_like(time_arr))
        # Show full 10s rhythm strip
        rhythm_mask = time_arr <= min(10.0, time_arr[-1])
        fig.add_trace(
            go.Scatter(
                x=time_arr[rhythm_mask],
                y=signal_ii[rhythm_mask],
                mode="lines",
                line=dict(color="#111111", width=1.2),
                name="II (ritmo)",
                showlegend=False,
                hovertemplate="II: %{y:.2f} mV<br>t=%{x:.3f}s",
            ),
            row=rows,
            col=1,
        )

    # Style — clinical ECG paper
    title = "ECG 12 Derivações"
    pathology = ecg_data.get("pathology")
    if pathology and pathology != "normal":
        desc = ecg_data.get("pathology_description_pt", pathology)
        title = f"ECG — {desc}"

    fig.update_layout(
        title=dict(text=title, font=dict(size=14, family="Arial")),
        height=180 * rows + 40,
        width=300 * cols,
        paper_bgcolor="#FFF5F5",
        plot_bgcolor="#FFF5F5",
        font=dict(size=9, family="Arial"),
        margin=dict(l=35, r=15, t=50, b=15),
    )

    # ECG paper grid: major grid (5mm=0.2s/0.5mV) and styling
    total_subplots = rows * cols
    for i in range(1, total_subplots + 1):
        r = (i - 1) // cols + 1
        c = (i - 1) % cols + 1
        # Skip None cells (colspan for rhythm strip)
        if rhythm_strip and r == rows and c > 1:
            continue
        fig.update_xaxes(
            showgrid=True,
            gridcolor="rgba(220,100,100,0.35)",
            dtick=0.2,
            minor=dict(dtick=0.04, showgrid=True, gridcolor="rgba(220,100,100,0.12)"),
            showticklabels=False,
            zeroline=False,
            row=r, col=c,
        )
        fig.update_yaxes(
            showgrid=True,
            gridcolor="rgba(220,100,100,0.35)",
            dtick=0.5,
            minor=dict(dtick=0.1, showgrid=True, gridcolor="rgba(220,100,100,0.12)"),
            showticklabels=False,
            zeroline=False,
            range=[-1.5, 1.5],
            row=r, col=c,
        )

    # Rhythm strip: show time labels
    if rhythm_strip:
        fig.update_xaxes(showticklabels=True, title_text="Tempo (s)",
                         row=rows, col=1)
        fig.update_yaxes(range=[-1.5, 1.5], row=rows, col=1)

    return fig

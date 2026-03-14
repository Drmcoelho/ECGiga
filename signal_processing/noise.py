"""ECG signal noise detection and quality assessment.

Provides tools for detecting noisy segments, estimating signal-to-noise
ratio, and computing a composite signal quality index (SQI).

References:
- Clifford et al., "Signal quality indices and data fusion for
  determining clinical acceptability of electrocardiograms", Physiol Meas, 2012.
- Li et al., "Robust heart rate estimation from multiple asynchronous
  noisy sources", IEEE TBME, 2008.
"""

from __future__ import annotations

from typing import Any

import numpy as np
from numpy.typing import NDArray


def estimate_snr(
    signal: NDArray[np.floating[Any]],
    fs: float,
    method: str = "power_ratio",
) -> float:
    """Estimate signal-to-noise ratio of an ECG signal.

    Parameters
    ----------
    signal : ndarray
        1D ECG signal.
    fs : float
        Sampling frequency in Hz.
    method : str
        Estimation method:
        - 'power_ratio': Ratio of QRS-band power to high-frequency noise power
        - 'template': Template-based SNR using average beat

    Returns
    -------
    float
        Estimated SNR in decibels (dB).
    """
    if signal.ndim != 1:
        raise ValueError("signal must be 1D for SNR estimation")
    if len(signal) < int(fs * 2):
        raise ValueError("Need at least 2 seconds of signal for SNR estimation")

    if method == "power_ratio":
        return _snr_power_ratio(signal, fs)
    elif method == "template":
        return _snr_template(signal, fs)
    else:
        raise ValueError(f"Unknown method: {method}")


def _snr_power_ratio(signal: NDArray, fs: float) -> float:
    """SNR via spectral power ratio.

    Signal band: 5-40 Hz (contains QRS and main ECG components)
    Noise band: 60-fs/2 Hz (contains mainly noise and powerline)
    """
    from scipy.signal import welch

    freqs, psd = welch(signal, fs=fs, nperseg=min(len(signal), int(fs * 4)))

    # Signal band: 5-40 Hz
    signal_mask = (freqs >= 5) & (freqs <= 40)
    signal_power = np.trapz(psd[signal_mask], freqs[signal_mask])

    # Noise band: 60 Hz to Nyquist (or 50-Nyquist depending on powerline)
    noise_mask = freqs >= 60
    noise_power = np.trapz(psd[noise_mask], freqs[noise_mask]) if noise_mask.any() else 1e-10

    if noise_power <= 0:
        noise_power = 1e-10

    snr_db = 10 * np.log10(signal_power / noise_power)
    return float(snr_db)


def _snr_template(signal: NDArray, fs: float) -> float:
    """Template-based SNR estimation.

    Creates average beat template from detected R-peaks, then computes
    SNR as ratio of template power to residual power.
    """
    # Simple R-peak detection for template extraction
    from scipy.signal import find_peaks

    # Bandpass the signal first for peak detection
    from signal_processing.filters import bandpass_filter
    filtered = bandpass_filter(signal, fs, lowcut=5, highcut=30)

    # Detect R-peaks
    height = np.std(filtered) * 1.5
    distance = int(0.4 * fs)  # minimum 400ms between beats
    peaks, _ = find_peaks(filtered, height=height, distance=distance)

    if len(peaks) < 5:
        # Not enough beats for template, fall back to power ratio
        return _snr_power_ratio(signal, fs)

    # Extract beats (150ms before, 250ms after R-peak)
    pre = int(0.15 * fs)
    post = int(0.25 * fs)
    beats = []
    for p in peaks:
        if p - pre >= 0 and p + post < len(signal):
            beats.append(signal[p - pre : p + post])

    if len(beats) < 3:
        return _snr_power_ratio(signal, fs)

    beats_arr = np.array(beats)
    template = np.mean(beats_arr, axis=0)

    # Compute residual noise
    residuals = beats_arr - template[np.newaxis, :]
    signal_power = np.mean(template ** 2)
    noise_power = np.mean(residuals ** 2)

    if noise_power <= 0:
        noise_power = 1e-10

    snr_db = 10 * np.log10(signal_power / noise_power)
    return float(snr_db)


def detect_noise_segments(
    signal: NDArray[np.floating[Any]],
    fs: float,
    window_s: float = 1.0,
    threshold_factor: float = 3.0,
) -> list[dict[str, Any]]:
    """Detect noisy segments in an ECG signal.

    Uses sliding window analysis to identify segments with abnormally
    high variance, flat-line detection, and saturation detection.

    Parameters
    ----------
    signal : ndarray
        1D ECG signal.
    fs : float
        Sampling frequency in Hz.
    window_s : float
        Analysis window duration in seconds.
    threshold_factor : float
        Number of standard deviations above median variance to flag as noisy.

    Returns
    -------
    list[dict]
        List of noisy segments, each with:
        - start_sample: int
        - end_sample: int
        - start_s: float (seconds)
        - end_s: float (seconds)
        - noise_type: str ('high_variance', 'flatline', 'saturation', 'spike')
        - severity: str ('low', 'moderate', 'high')
    """
    if signal.ndim != 1:
        raise ValueError("signal must be 1D")

    window = int(window_s * fs)
    if window < 10:
        window = 10

    n_windows = max(1, len(signal) // window)
    segments: list[dict[str, Any]] = []

    # Compute per-window statistics
    variances = []
    ranges = []
    for i in range(n_windows):
        start = i * window
        end = min(start + window, len(signal))
        chunk = signal[start:end]
        variances.append(np.var(chunk))
        ranges.append(np.ptp(chunk))

    variances = np.array(variances)
    ranges = np.array(ranges)

    if len(variances) == 0:
        return segments

    median_var = np.median(variances)
    std_var = np.std(variances) if len(variances) > 1 else median_var

    # Avoid division by zero
    if median_var < 1e-10:
        median_var = 1e-10
    if std_var < 1e-10:
        std_var = median_var * 0.1

    for i in range(n_windows):
        start = i * window
        end = min(start + window, len(signal))
        chunk = signal[start:end]

        # 1. High variance (muscle artifact, electrode noise)
        if variances[i] > median_var + threshold_factor * std_var:
            severity = "high" if variances[i] > median_var + 5 * std_var else "moderate"
            segments.append({
                "start_sample": start,
                "end_sample": end,
                "start_s": start / fs,
                "end_s": end / fs,
                "noise_type": "high_variance",
                "severity": severity,
            })

        # 2. Flatline detection (electrode disconnection)
        elif ranges[i] < median_var * 0.01:
            segments.append({
                "start_sample": start,
                "end_sample": end,
                "start_s": start / fs,
                "end_s": end / fs,
                "noise_type": "flatline",
                "severity": "high",
            })

        # 3. Saturation detection (signal clipping)
        elif _detect_saturation(chunk):
            segments.append({
                "start_sample": start,
                "end_sample": end,
                "start_s": start / fs,
                "end_s": end / fs,
                "noise_type": "saturation",
                "severity": "high",
            })

    # 4. Spike detection (across whole signal)
    spike_segments = _detect_spikes(signal, fs, window)
    segments.extend(spike_segments)

    # Sort by start sample and merge overlapping segments
    segments.sort(key=lambda s: s["start_sample"])

    return segments


def _detect_saturation(chunk: NDArray) -> bool:
    """Detect signal saturation (clipping) in a chunk."""
    if len(chunk) < 5:
        return False
    # Check if many consecutive samples are at the same extreme value
    max_val = chunk.max()
    min_val = chunk.min()
    at_max = (chunk == max_val).sum()
    at_min = (chunk == min_val).sum()
    # More than 10% of samples at exact same extreme = likely saturation
    return (at_max > len(chunk) * 0.1) or (at_min > len(chunk) * 0.1)


def _detect_spikes(signal: NDArray, fs: float, window: int) -> list[dict]:
    """Detect isolated spikes that are physiologically implausible."""
    segments = []
    # Compute first derivative
    diff = np.diff(signal)
    abs_diff = np.abs(diff)
    median_diff = np.median(abs_diff)
    if median_diff < 1e-10:
        median_diff = 1e-10

    # Spikes: derivative > 10x median
    spike_threshold = median_diff * 10
    spike_indices = np.where(abs_diff > spike_threshold)[0]

    if len(spike_indices) == 0:
        return segments

    # Group consecutive spike indices
    groups = []
    current_group = [spike_indices[0]]
    for idx in spike_indices[1:]:
        if idx - current_group[-1] <= 3:  # within 3 samples
            current_group.append(idx)
        else:
            groups.append(current_group)
            current_group = [idx]
    groups.append(current_group)

    # Only flag isolated spikes (very short duration)
    for group in groups:
        duration_ms = len(group) * 1000 / fs
        if duration_ms < 10:  # < 10ms = likely artifact, not QRS
            start = max(0, group[0] - int(0.01 * fs))
            end = min(len(signal), group[-1] + int(0.01 * fs))
            segments.append({
                "start_sample": start,
                "end_sample": end,
                "start_s": start / fs,
                "end_s": end / fs,
                "noise_type": "spike",
                "severity": "low",
            })

    return segments


def signal_quality_index(
    signal: NDArray[np.floating[Any]],
    fs: float,
) -> dict[str, Any]:
    """Compute composite signal quality index (SQI) for an ECG signal.

    Combines multiple quality metrics into a composite score (0-100).

    Parameters
    ----------
    signal : ndarray
        1D ECG signal.
    fs : float
        Sampling frequency in Hz.

    Returns
    -------
    dict
        - sqi_score: float (0-100, higher is better)
        - snr_db: float
        - noise_segments: int (count of detected noisy segments)
        - noise_fraction: float (0-1, fraction of signal that is noisy)
        - has_baseline_wander: bool
        - has_powerline_interference: bool
        - quality_label: str ('excellent', 'good', 'acceptable', 'poor', 'unusable')
        - details: dict with sub-scores
    """
    if signal.ndim != 1:
        raise ValueError("signal must be 1D")

    min_length = int(fs * 2)
    if len(signal) < min_length:
        return {
            "sqi_score": 0.0,
            "snr_db": 0.0,
            "noise_segments": 0,
            "noise_fraction": 1.0,
            "has_baseline_wander": False,
            "has_powerline_interference": False,
            "quality_label": "unusable",
            "details": {"reason": "signal too short"},
        }

    # 1. SNR score (0-30 points)
    snr = estimate_snr(signal, fs)
    snr_score = min(30.0, max(0.0, (snr + 10) * 1.5))  # -10dB=0, 10dB=30

    # 2. Noise segment score (0-30 points)
    noise_segs = detect_noise_segments(signal, fs)
    noise_samples = sum(s["end_sample"] - s["start_sample"] for s in noise_segs)
    noise_fraction = noise_samples / len(signal) if len(signal) > 0 else 0
    noise_score = max(0.0, 30.0 * (1.0 - noise_fraction * 2))

    # 3. Baseline wander score (0-20 points)
    has_bw = _check_baseline_wander(signal, fs)
    bw_score = 0.0 if has_bw else 20.0

    # 4. Powerline interference score (0-20 points)
    has_pli = _check_powerline_interference(signal, fs)
    pli_score = 10.0 if has_pli else 20.0

    # Composite SQI
    sqi = snr_score + noise_score + bw_score + pli_score

    # Quality label
    if sqi >= 85:
        label = "excellent"
    elif sqi >= 70:
        label = "good"
    elif sqi >= 50:
        label = "acceptable"
    elif sqi >= 30:
        label = "poor"
    else:
        label = "unusable"

    return {
        "sqi_score": round(sqi, 1),
        "snr_db": round(snr, 1),
        "noise_segments": len(noise_segs),
        "noise_fraction": round(noise_fraction, 3),
        "has_baseline_wander": has_bw,
        "has_powerline_interference": has_pli,
        "quality_label": label,
        "details": {
            "snr_score": round(snr_score, 1),
            "noise_score": round(noise_score, 1),
            "bw_score": round(bw_score, 1),
            "pli_score": round(pli_score, 1),
        },
    }


def _check_baseline_wander(signal: NDArray, fs: float) -> bool:
    """Check if signal has significant baseline wander (<1 Hz energy)."""
    from scipy.signal import welch

    nperseg = min(len(signal), int(fs * 4))
    if nperseg < 64:
        return False

    freqs, psd = welch(signal, fs=fs, nperseg=nperseg)

    # Energy below 1 Hz vs total energy
    bw_mask = freqs < 1.0
    total_mask = freqs < 50.0

    bw_power = np.trapz(psd[bw_mask], freqs[bw_mask]) if bw_mask.any() else 0
    total_power = np.trapz(psd[total_mask], freqs[total_mask]) if total_mask.any() else 1e-10

    # If >30% of diagnostic-band power is below 1 Hz, likely baseline wander
    return (bw_power / max(total_power, 1e-10)) > 0.3


def _check_powerline_interference(signal: NDArray, fs: float) -> bool:
    """Check for 50 Hz or 60 Hz powerline interference."""
    from scipy.signal import welch

    nperseg = min(len(signal), int(fs * 4))
    if nperseg < 64:
        return False

    freqs, psd = welch(signal, fs=fs, nperseg=nperseg)
    freq_res = freqs[1] - freqs[0] if len(freqs) > 1 else 1.0

    for pli_freq in [50.0, 60.0]:
        if pli_freq >= fs / 2:
            continue
        # Check for spike at powerline frequency
        idx = np.argmin(np.abs(freqs - pli_freq))
        if idx < 2 or idx >= len(psd) - 2:
            continue

        peak_power = psd[idx]
        # Compare to surrounding frequencies (±5 Hz)
        neighbors = psd[max(0, idx - int(5 / freq_res)):idx - int(2 / freq_res)]
        if len(neighbors) > 0:
            neighbor_power = np.median(neighbors)
            if neighbor_power > 0 and peak_power / neighbor_power > 5:
                return True

    return False

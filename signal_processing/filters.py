"""Digital filters for ECG signal processing.

Implements Butterworth bandpass, highpass, lowpass, and notch filters
with zero-phase filtering (filtfilt) for distortion-free ECG processing.

All filters use second-order sections (SOS) for numerical stability.

References:
- AHA/ACC ECG filtering recommendations: 0.05-150 Hz for diagnostic quality
- IEC 60601-2-51: 0.05-40 Hz for monitoring, 0.05-150 Hz for diagnostic
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np
from numpy.typing import NDArray


def _validate_signal(signal: NDArray[np.floating[Any]], fs: float) -> None:
    """Validate signal and sampling frequency parameters."""
    if not isinstance(signal, np.ndarray):
        raise TypeError("signal must be a numpy array")
    if signal.ndim not in (1, 2):
        raise ValueError(f"signal must be 1D or 2D, got {signal.ndim}D")
    if len(signal) < 10:
        raise ValueError(f"signal too short: {len(signal)} samples (minimum 10)")
    if fs <= 0:
        raise ValueError(f"sampling frequency must be positive, got {fs}")


def _pad_length(signal_length: int, order: int) -> int:
    """Calculate appropriate padding length for filtfilt."""
    # filtfilt needs at least 3 * max(len(a), len(b)) samples
    # For SOS, each section is order 2, so padding = 3 * (2 * n_sections + 1)
    pad = 3 * (2 * order + 1)
    # But don't pad more than signal length
    return min(pad, signal_length - 1)


def bandpass_filter(
    signal: NDArray[np.floating[Any]],
    fs: float,
    lowcut: float = 0.05,
    highcut: float = 150.0,
    order: int = 4,
) -> NDArray[np.floating[Any]]:
    """Apply zero-phase Butterworth bandpass filter.

    Parameters
    ----------
    signal : ndarray
        ECG signal (1D single-lead or 2D multi-lead with shape [samples, leads]).
    fs : float
        Sampling frequency in Hz.
    lowcut : float
        Lower cutoff frequency in Hz (default 0.05 Hz per AHA).
    highcut : float
        Upper cutoff frequency in Hz (default 150 Hz for diagnostic quality).
    order : int
        Filter order (default 4, giving 8th-order after filtfilt).

    Returns
    -------
    ndarray
        Filtered signal with same shape as input.
    """
    from scipy.signal import butter, sosfiltfilt

    _validate_signal(signal, fs)
    nyq = fs / 2.0

    if lowcut <= 0 or highcut <= 0:
        raise ValueError("Cutoff frequencies must be positive")
    if lowcut >= highcut:
        raise ValueError(f"lowcut ({lowcut}) must be less than highcut ({highcut})")
    if highcut >= nyq:
        highcut = nyq * 0.99  # Clamp to just below Nyquist

    low = lowcut / nyq
    high = highcut / nyq

    sos = butter(order, [low, high], btype="band", output="sos")

    if signal.ndim == 1:
        padlen = _pad_length(len(signal), order)
        return sosfiltfilt(sos, signal, padlen=padlen)
    else:
        # Multi-lead: filter each lead independently
        result = np.empty_like(signal)
        padlen = _pad_length(signal.shape[0], order)
        for i in range(signal.shape[1]):
            result[:, i] = sosfiltfilt(sos, signal[:, i], padlen=padlen)
        return result


def highpass_filter(
    signal: NDArray[np.floating[Any]],
    fs: float,
    cutoff: float = 0.05,
    order: int = 4,
) -> NDArray[np.floating[Any]]:
    """Apply zero-phase Butterworth highpass filter.

    Primarily used for baseline wander removal. The AHA recommends
    0.05 Hz for diagnostic ECG and 0.67 Hz for monitoring.

    Parameters
    ----------
    signal : ndarray
        ECG signal.
    fs : float
        Sampling frequency in Hz.
    cutoff : float
        Cutoff frequency in Hz (default 0.05 Hz).
    order : int
        Filter order.

    Returns
    -------
    ndarray
        Highpass-filtered signal.
    """
    from scipy.signal import butter, sosfiltfilt

    _validate_signal(signal, fs)
    nyq = fs / 2.0

    if cutoff <= 0:
        raise ValueError("Cutoff frequency must be positive")
    if cutoff >= nyq:
        raise ValueError(f"Cutoff ({cutoff}) must be below Nyquist ({nyq})")

    sos = butter(order, cutoff / nyq, btype="high", output="sos")

    if signal.ndim == 1:
        padlen = _pad_length(len(signal), order)
        return sosfiltfilt(sos, signal, padlen=padlen)
    else:
        result = np.empty_like(signal)
        padlen = _pad_length(signal.shape[0], order)
        for i in range(signal.shape[1]):
            result[:, i] = sosfiltfilt(sos, signal[:, i], padlen=padlen)
        return result


def lowpass_filter(
    signal: NDArray[np.floating[Any]],
    fs: float,
    cutoff: float = 40.0,
    order: int = 4,
) -> NDArray[np.floating[Any]]:
    """Apply zero-phase Butterworth lowpass filter.

    Used for high-frequency noise removal. 40 Hz is typical for
    monitoring mode; 150 Hz for diagnostic mode.

    Parameters
    ----------
    signal : ndarray
        ECG signal.
    fs : float
        Sampling frequency in Hz.
    cutoff : float
        Cutoff frequency in Hz (default 40 Hz).
    order : int
        Filter order.

    Returns
    -------
    ndarray
        Lowpass-filtered signal.
    """
    from scipy.signal import butter, sosfiltfilt

    _validate_signal(signal, fs)
    nyq = fs / 2.0

    if cutoff <= 0:
        raise ValueError("Cutoff frequency must be positive")
    if cutoff >= nyq:
        cutoff = nyq * 0.99

    sos = butter(order, cutoff / nyq, btype="low", output="sos")

    if signal.ndim == 1:
        padlen = _pad_length(len(signal), order)
        return sosfiltfilt(sos, signal, padlen=padlen)
    else:
        result = np.empty_like(signal)
        padlen = _pad_length(signal.shape[0], order)
        for i in range(signal.shape[1]):
            result[:, i] = sosfiltfilt(sos, signal[:, i], padlen=padlen)
        return result


def notch_filter(
    signal: NDArray[np.floating[Any]],
    fs: float,
    freq: float = 60.0,
    quality: float = 30.0,
    harmonics: int = 3,
) -> NDArray[np.floating[Any]]:
    """Apply notch filter for powerline interference removal.

    Removes the fundamental frequency and its harmonics.

    Parameters
    ----------
    signal : ndarray
        ECG signal.
    fs : float
        Sampling frequency in Hz.
    freq : float
        Powerline frequency (50 Hz in Europe/Brazil, 60 Hz in Americas).
    quality : float
        Quality factor (Q = f0 / bandwidth). Higher = narrower notch.
    harmonics : int
        Number of harmonics to remove (default 3: f0, 2*f0, 3*f0).

    Returns
    -------
    ndarray
        Filtered signal with powerline interference removed.
    """
    from scipy.signal import iirnotch, sosfiltfilt

    _validate_signal(signal, fs)
    nyq = fs / 2.0
    result = signal.copy()

    for h in range(1, harmonics + 1):
        notch_freq = freq * h
        if notch_freq >= nyq:
            break

        b, a = iirnotch(notch_freq, quality, fs)
        # Convert to SOS for stability
        # iirnotch returns b,a so we use filtfilt directly
        from scipy.signal import filtfilt
        if result.ndim == 1:
            result = filtfilt(b, a, result)
        else:
            for i in range(result.shape[1]):
                result[:, i] = filtfilt(b, a, result[:, i])

    return result


def remove_baseline_wander(
    signal: NDArray[np.floating[Any]],
    fs: float,
    method: str = "highpass",
    cutoff: float = 0.5,
    window_s: float = 0.6,
) -> NDArray[np.floating[Any]]:
    """Remove baseline wander from ECG signal.

    Supports two methods:
    - 'highpass': Butterworth highpass filter (fast, standard)
    - 'median': Cascaded median filter (preserves morphology better)

    Parameters
    ----------
    signal : ndarray
        ECG signal.
    fs : float
        Sampling frequency in Hz.
    method : str
        'highpass' or 'median'.
    cutoff : float
        Cutoff frequency for highpass method (default 0.5 Hz).
    window_s : float
        Window duration in seconds for median method (default 0.6s ~ QT interval).

    Returns
    -------
    ndarray
        Signal with baseline wander removed.
    """
    _validate_signal(signal, fs)

    if method == "highpass":
        return highpass_filter(signal, fs, cutoff=cutoff, order=2)

    elif method == "median":
        return _median_baseline_removal(signal, fs, window_s)

    else:
        raise ValueError(f"Unknown method: {method}. Use 'highpass' or 'median'.")


def _median_baseline_removal(
    signal: NDArray[np.floating[Any]],
    fs: float,
    window_s: float = 0.6,
) -> NDArray[np.floating[Any]]:
    """Two-pass median filter baseline removal.

    First pass: median filter with ~200ms window (captures QRS)
    Second pass: median filter with ~600ms window (captures T wave)
    Baseline = second pass result, subtract from original.

    Reference: de Chazal et al., IEEE TBME 2004.
    """
    from scipy.ndimage import median_filter

    def _apply_1d(sig: NDArray) -> NDArray:
        # First pass: short window to remove QRS
        win1 = max(int(0.2 * fs), 3)
        if win1 % 2 == 0:
            win1 += 1
        baseline1 = median_filter(sig, size=win1)

        # Second pass: longer window on first-pass result
        win2 = max(int(window_s * fs), 3)
        if win2 % 2 == 0:
            win2 += 1
        baseline2 = median_filter(baseline1, size=win2)

        return sig - baseline2

    if signal.ndim == 1:
        return _apply_1d(signal)
    else:
        result = np.empty_like(signal)
        for i in range(signal.shape[1]):
            result[:, i] = _apply_1d(signal[:, i])
        return result

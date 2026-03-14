"""Complete ECG preprocessing pipeline.

Chains baseline wander removal, powerline notch filtering, bandpass filtering,
and quality assessment into a single configurable pipeline.

Reference pipeline order (recommended):
1. Baseline wander removal (highpass 0.5 Hz or median filter)
2. Powerline notch filter (50/60 Hz + harmonics)
3. Bandpass filter (0.05-150 Hz diagnostic / 0.5-40 Hz monitoring)
4. Quality assessment
"""

from __future__ import annotations

from typing import Any

import numpy as np
from numpy.typing import NDArray


def preprocess_ecg(
    signal: NDArray[np.floating[Any]],
    fs: float,
    mode: str = "diagnostic",
    powerline_freq: float = 60.0,
    remove_baseline: bool = True,
    baseline_method: str = "highpass",
    remove_powerline: bool = True,
    apply_bandpass: bool = True,
    compute_quality: bool = True,
) -> dict[str, Any]:
    """Full ECG preprocessing pipeline.

    Parameters
    ----------
    signal : ndarray
        Raw ECG signal (1D or 2D [samples, leads]).
    fs : float
        Sampling frequency in Hz.
    mode : str
        'diagnostic' (0.05-150 Hz) or 'monitoring' (0.5-40 Hz).
    powerline_freq : float
        Powerline frequency: 50 Hz (Europe/Brazil) or 60 Hz (Americas).
    remove_baseline : bool
        Whether to remove baseline wander.
    baseline_method : str
        'highpass' or 'median' for baseline removal.
    remove_powerline : bool
        Whether to apply notch filter for powerline.
    apply_bandpass : bool
        Whether to apply bandpass filter.
    compute_quality : bool
        Whether to compute signal quality index.

    Returns
    -------
    dict
        - signal: ndarray (preprocessed signal)
        - fs: float
        - mode: str
        - steps_applied: list[str]
        - quality: dict (if compute_quality=True)
    """
    from signal_processing.filters import (
        bandpass_filter,
        notch_filter,
        remove_baseline_wander,
    )
    from signal_processing.noise import signal_quality_index

    if not isinstance(signal, np.ndarray):
        signal = np.asarray(signal, dtype=np.float64)

    if signal.dtype not in (np.float32, np.float64):
        signal = signal.astype(np.float64)

    # Validate mode
    if mode == "diagnostic":
        bp_low, bp_high = 0.05, 150.0
        bw_cutoff = 0.5
    elif mode == "monitoring":
        bp_low, bp_high = 0.5, 40.0
        bw_cutoff = 0.67
    else:
        raise ValueError(f"Unknown mode: {mode}. Use 'diagnostic' or 'monitoring'.")

    steps: list[str] = []
    processed = signal.copy()

    # Step 1: Baseline wander removal
    if remove_baseline:
        processed = remove_baseline_wander(
            processed, fs,
            method=baseline_method,
            cutoff=bw_cutoff,
        )
        steps.append(f"baseline_wander_removal({baseline_method}, cutoff={bw_cutoff}Hz)")

    # Step 2: Powerline notch filter
    if remove_powerline:
        processed = notch_filter(
            processed, fs,
            freq=powerline_freq,
            quality=30.0,
            harmonics=3,
        )
        steps.append(f"notch_filter({powerline_freq}Hz, harmonics=3)")

    # Step 3: Bandpass filter
    if apply_bandpass:
        processed = bandpass_filter(
            processed, fs,
            lowcut=bp_low,
            highcut=bp_high,
        )
        steps.append(f"bandpass_filter({bp_low}-{bp_high}Hz)")

    result: dict[str, Any] = {
        "signal": processed,
        "fs": fs,
        "mode": mode,
        "steps_applied": steps,
    }

    # Step 4: Quality assessment (on preprocessed signal)
    if compute_quality:
        if processed.ndim == 1:
            result["quality"] = signal_quality_index(processed, fs)
        else:
            # Multi-lead: assess each lead, report worst
            lead_qualities = []
            for i in range(processed.shape[1]):
                q = signal_quality_index(processed[:, i], fs)
                q["lead_index"] = i
                lead_qualities.append(q)

            # Overall quality is the worst lead
            worst = min(lead_qualities, key=lambda q: q["sqi_score"])
            result["quality"] = worst
            result["quality_per_lead"] = lead_qualities

    return result

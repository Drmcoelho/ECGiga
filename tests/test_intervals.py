"""Test interval extraction from ECG signals."""

from __future__ import annotations
import numpy as np
import pytest
from typing import Dict, List, Tuple


def extract_pr_interval(
    signal: np.ndarray,
    rpeak_idx: int,
    sampling_rate_hz: int = 500
) -> Tuple[int, int]:
    """Extract PR interval (P wave onset to QRS onset).
    
    Args:
        signal: ECG signal array
        rpeak_idx: R-peak sample index
        sampling_rate_hz: Sampling rate in Hz
        
    Returns:
        Tuple of (p_onset_idx, pr_duration_samples)
    """
    # Search window: 200-400ms before R-peak for P wave
    search_start = max(0, rpeak_idx - int(0.4 * sampling_rate_hz))
    search_end = max(0, rpeak_idx - int(0.08 * sampling_rate_hz))  # QRS starts ~80ms before R
    
    if search_start >= search_end:
        return rpeak_idx, 0
    
    search_signal = signal[search_start:search_end]
    
    # Find P wave peak (positive deflection)
    p_peak_rel = np.argmax(search_signal)
    p_peak_idx = search_start + p_peak_rel
    
    # P wave onset: find where signal starts rising before P peak
    p_onset_idx = p_peak_idx
    for i in range(p_peak_rel, 0, -1):
        if i < len(search_signal) - 1:
            if search_signal[i] < search_signal[i + 1]:
                p_onset_idx = search_start + i
                break
    
    # QRS onset: typically 40-80ms before R-peak
    qrs_onset_idx = rpeak_idx - int(0.06 * sampling_rate_hz)  # 60ms before R
    
    pr_duration = max(0, qrs_onset_idx - p_onset_idx)
    return p_onset_idx, pr_duration


def extract_qrs_duration(
    signal: np.ndarray,
    rpeak_idx: int,
    sampling_rate_hz: int = 500
) -> int:
    """Extract QRS duration.
    
    Args:
        signal: ECG signal array
        rpeak_idx: R-peak sample index
        sampling_rate_hz: Sampling rate in Hz
        
    Returns:
        QRS duration in samples
    """
    # QRS typically spans 60-120ms
    search_before = int(0.06 * sampling_rate_hz)  # 60ms
    search_after = int(0.08 * sampling_rate_hz)   # 80ms
    
    qrs_start = max(0, rpeak_idx - search_before)
    qrs_end = min(len(signal), rpeak_idx + search_after)
    
    # Simple method: find return to baseline after S wave
    baseline = np.mean(signal[:100])  # Estimate baseline from start
    
    # Find S wave end (return toward baseline)
    s_end_idx = rpeak_idx
    for i in range(rpeak_idx + 5, qrs_end):  # Start after R peak
        if abs(signal[i] - baseline) < 0.1 * abs(signal[rpeak_idx] - baseline):
            s_end_idx = i
            break
    else:
        s_end_idx = qrs_end
    
    # Find Q wave start
    q_start_idx = rpeak_idx
    for i in range(rpeak_idx - 5, qrs_start, -1):  # Go backward from R
        if abs(signal[i] - baseline) < 0.1 * abs(signal[rpeak_idx] - baseline):
            q_start_idx = i
            break
    else:
        q_start_idx = qrs_start
    
    qrs_duration = s_end_idx - q_start_idx
    return max(int(0.04 * sampling_rate_hz), qrs_duration)  # Minimum 40ms


def extract_qt_interval(
    signal: np.ndarray,
    rpeak_idx: int,
    sampling_rate_hz: int = 500
) -> Tuple[int, int]:
    """Extract QT interval (QRS onset to T wave end).
    
    Args:
        signal: ECG signal array
        rpeak_idx: R-peak sample index
        sampling_rate_hz: Sampling rate in Hz
        
    Returns:
        Tuple of (q_onset_idx, qt_duration_samples)
    """
    # Q wave onset (start of QRS)
    q_onset_idx = max(0, rpeak_idx - int(0.06 * sampling_rate_hz))
    
    # Search for T wave end: 200-500ms after R-peak
    search_start = rpeak_idx + int(0.2 * sampling_rate_hz)
    search_end = min(len(signal), rpeak_idx + int(0.5 * sampling_rate_hz))
    
    if search_start >= search_end:
        return q_onset_idx, int(0.35 * sampling_rate_hz)  # Default 350ms
    
    search_signal = signal[search_start:search_end]
    
    # Find T wave peak
    t_peak_rel = np.argmax(search_signal)
    t_peak_idx = search_start + t_peak_rel
    
    # T wave end: find return to baseline after T peak
    baseline = np.mean(signal[:100])
    t_end_idx = t_peak_idx
    
    for i in range(t_peak_rel, len(search_signal)):
        if abs(search_signal[i] - baseline) < 0.1 * abs(search_signal[t_peak_rel] - baseline):
            t_end_idx = search_start + i
            break
    else:
        t_end_idx = search_end
    
    qt_duration = t_end_idx - q_onset_idx
    return q_onset_idx, max(int(0.25 * sampling_rate_hz), qt_duration)  # Minimum 250ms


def calculate_qtc(qt_ms: float, rr_ms: float, method: str = "bazett") -> float:
    """Calculate corrected QT interval.
    
    Args:
        qt_ms: QT interval in milliseconds
        rr_ms: RR interval in milliseconds
        method: Correction method ("bazett" or "fridericia")
        
    Returns:
        QTc in milliseconds
    """
    rr_s = rr_ms / 1000.0
    
    if method.lower() == "bazett":
        return qt_ms / (rr_s ** 0.5)
    elif method.lower() == "fridericia":
        return qt_ms / (rr_s ** (1/3))
    else:
        raise ValueError(f"Unknown QTc method: {method}")


def generate_test_ecg_with_intervals(
    duration_s: float = 10.0,
    sampling_rate_hz: int = 500,
    heart_rate_bpm: float = 75.0,
    pr_ms: float = 160.0,
    qrs_ms: float = 90.0,
    qt_ms: float = 380.0
) -> Tuple[np.ndarray, List[int], Dict[str, float]]:
    """Generate test ECG with known interval durations.
    
    Returns:
        Tuple of (signal, rpeak_indices, true_intervals_dict)
    """
    # Generate basic ECG structure
    num_samples = int(duration_s * sampling_rate_hz)
    signal = np.zeros(num_samples)
    
    # Calculate beat spacing
    rr_interval_s = 60.0 / heart_rate_bpm
    num_beats = int(duration_s / rr_interval_s)
    
    rpeak_indices = []
    
    # Place R-peaks
    for i in range(num_beats):
        rpeak_time = (i + 1) * rr_interval_s
        if rpeak_time < duration_s:
            rpeak_idx = int(rpeak_time * sampling_rate_hz)
            if rpeak_idx < num_samples - 100:  # Leave room for T wave
                rpeak_indices.append(rpeak_idx)
    
    # Add ECG components for each beat
    for rpeak_idx in rpeak_indices:
        # P wave (PR interval before QRS)
        pr_samples = int(pr_ms * sampling_rate_hz / 1000.0)
        p_peak_idx = rpeak_idx - pr_samples + int(0.06 * sampling_rate_hz)  # P peak
        if p_peak_idx >= 20 and p_peak_idx < num_samples:
            for i in range(max(0, p_peak_idx - 10), min(num_samples, p_peak_idx + 10)):
                signal[i] += 0.2 * np.exp(-0.5 * ((i - p_peak_idx) / 4) ** 2)
        
        # QRS complex
        qrs_samples = int(qrs_ms * sampling_rate_hz / 1000.0)
        qrs_start = rpeak_idx - int(0.4 * qrs_samples)
        qrs_end = rpeak_idx + int(0.6 * qrs_samples)
        
        # Q wave
        q_idx = qrs_start + int(0.2 * qrs_samples)
        if 0 <= q_idx < num_samples:
            signal[q_idx] -= 0.1
        
        # R wave (peak)
        if 0 <= rpeak_idx < num_samples:
            for i in range(max(0, rpeak_idx - 3), min(num_samples, rpeak_idx + 4)):
                signal[i] += 1.0 * np.exp(-0.5 * ((i - rpeak_idx) / 2) ** 2)
        
        # S wave
        s_idx = qrs_end - int(0.2 * qrs_samples)
        if 0 <= s_idx < num_samples:
            signal[s_idx] -= 0.3
        
        # T wave (QT interval after QRS onset)
        qt_samples = int(qt_ms * sampling_rate_hz / 1000.0)
        t_peak_idx = qrs_start + int(0.6 * qt_samples)  # T peak
        if t_peak_idx < num_samples - 10:
            for i in range(max(0, t_peak_idx - 8), min(num_samples, t_peak_idx + 12)):
                signal[i] += 0.3 * np.exp(-0.5 * ((i - t_peak_idx) / 6) ** 2)
    
    # Add small amount of noise
    noise = 0.02 * np.random.normal(0, 1, num_samples)
    signal += noise
    
    true_intervals = {
        "pr_ms": pr_ms,
        "qrs_ms": qrs_ms,
        "qt_ms": qt_ms,
        "rr_ms": 60000.0 / heart_rate_bpm
    }
    
    return signal, rpeak_indices, true_intervals


class TestIntervalExtraction:
    """Test suite for ECG interval extraction."""
    
    def test_pr_interval_extraction(self):
        """Test PR interval extraction."""
        signal, rpeaks, true_intervals = generate_test_ecg_with_intervals(
            pr_ms=180.0,  # Slightly prolonged PR
            qrs_ms=85.0,
            qt_ms=400.0
        )
        
        if not rpeaks:
            pytest.skip("No R-peaks generated")
        
        # Test on first R-peak
        rpeak_idx = rpeaks[0]
        p_onset_idx, pr_duration_samples = extract_pr_interval(signal, rpeak_idx)
        pr_duration_ms = pr_duration_samples * 1000.0 / 500.0
        
        # Should be within reasonable range (allowing 30% tolerance)
        expected_pr = true_intervals["pr_ms"]
        assert 0.7 * expected_pr <= pr_duration_ms <= 1.3 * expected_pr
        
        # PR should be in normal clinical range
        assert 120.0 <= pr_duration_ms <= 300.0
    
    def test_qrs_duration_extraction(self):
        """Test QRS duration extraction."""
        signal, rpeaks, true_intervals = generate_test_ecg_with_intervals(
            pr_ms=150.0,
            qrs_ms=110.0,  # Wide QRS
            qt_ms=380.0
        )
        
        if not rpeaks:
            pytest.skip("No R-peaks generated")
        
        rpeak_idx = rpeaks[0]
        qrs_duration_samples = extract_qrs_duration(signal, rpeak_idx)
        qrs_duration_ms = qrs_duration_samples * 1000.0 / 500.0
        
        # Should be within reasonable range
        expected_qrs = true_intervals["qrs_ms"]
        assert 0.6 * expected_qrs <= qrs_duration_ms <= 1.4 * expected_qrs
        
        # QRS should be in physiological range
        assert 40.0 <= qrs_duration_ms <= 200.0
    
    def test_qt_interval_extraction(self):
        """Test QT interval extraction."""
        signal, rpeaks, true_intervals = generate_test_ecg_with_intervals(
            pr_ms=160.0,
            qrs_ms=90.0,
            qt_ms=420.0  # Prolonged QT
        )
        
        if not rpeaks:
            pytest.skip("No R-peaks generated")
        
        rpeak_idx = rpeaks[0]
        q_onset_idx, qt_duration_samples = extract_qt_interval(signal, rpeak_idx)
        qt_duration_ms = qt_duration_samples * 1000.0 / 500.0
        
        # Should be within reasonable range
        expected_qt = true_intervals["qt_ms"]
        assert 0.7 * expected_qt <= qt_duration_ms <= 1.3 * expected_qt
        
        # QT should be in physiological range
        assert 250.0 <= qt_duration_ms <= 600.0
    
    def test_qtc_calculation(self):
        """Test QTc calculation methods."""
        # Test Bazett correction
        qt_ms = 400.0
        rr_ms = 1000.0  # 60 bpm
        
        qtc_bazett = calculate_qtc(qt_ms, rr_ms, "bazett")
        assert abs(qtc_bazett - 400.0) < 1.0  # Should be ~400ms at 60 bpm
        
        # Test Fridericia correction
        qtc_fridericia = calculate_qtc(qt_ms, rr_ms, "fridericia")
        assert abs(qtc_fridericia - 400.0) < 1.0  # Should be ~400ms at 60 bpm
        
        # Test different heart rate
        rr_ms_fast = 600.0  # 100 bpm
        qtc_bazett_fast = calculate_qtc(qt_ms, rr_ms_fast, "bazett")
        assert qtc_bazett_fast > qt_ms  # Should be corrected upward for fast HR
        
        # Test invalid method
        with pytest.raises(ValueError):
            calculate_qtc(qt_ms, rr_ms, "invalid_method")
    
    def test_interval_bounds_validation(self):
        """Test interval extraction with boundary conditions."""
        # Very short signal
        signal = np.random.normal(0, 0.1, 100)  # Only 200ms at 500Hz
        rpeak_idx = 50
        
        # Should handle short signals gracefully
        p_onset, pr_duration = extract_pr_interval(signal, rpeak_idx)
        qrs_duration = extract_qrs_duration(signal, rpeak_idx)
        q_onset, qt_duration = extract_qt_interval(signal, rpeak_idx)
        
        # Should return reasonable minimum values
        assert pr_duration >= 0
        assert qrs_duration >= 20  # At least 40ms at 500Hz = 20 samples
        assert qt_duration >= 125  # At least 250ms at 500Hz = 125 samples
    
    @pytest.mark.parametrize("heart_rate", [50, 75, 100, 150])
    def test_intervals_different_heart_rates(self, heart_rate):
        """Test interval extraction at different heart rates."""
        signal, rpeaks, true_intervals = generate_test_ecg_with_intervals(
            duration_s=8.0,
            heart_rate_bpm=heart_rate,
            pr_ms=160.0,
            qrs_ms=90.0,
            qt_ms=380.0
        )
        
        if not rpeaks:
            pytest.skip(f"No R-peaks generated for HR {heart_rate}")
        
        # Test interval extraction on first beat
        rpeak_idx = rpeaks[0]
        
        _, pr_duration = extract_pr_interval(signal, rpeak_idx)
        qrs_duration = extract_qrs_duration(signal, rpeak_idx)
        _, qt_duration = extract_qt_interval(signal, rpeak_idx)
        
        # Convert to milliseconds
        pr_ms = pr_duration * 1000.0 / 500.0
        qrs_ms = qrs_duration * 1000.0 / 500.0
        qt_ms = qt_duration * 1000.0 / 500.0
        
        # All intervals should be in physiological ranges
        assert 80.0 <= pr_ms <= 350.0
        assert 40.0 <= qrs_ms <= 180.0
        assert 200.0 <= qt_ms <= 600.0
        
        # QTc should be relatively stable across heart rates
        rr_ms = 60000.0 / heart_rate
        qtc_bazett = calculate_qtc(qt_ms, rr_ms, "bazett")
        qtc_fridericia = calculate_qtc(qt_ms, rr_ms, "fridericia")
        
        assert 300.0 <= qtc_bazett <= 550.0
        assert 300.0 <= qtc_fridericia <= 550.0
    
    def test_multiple_beats_consistency(self):
        """Test consistency of interval extraction across multiple beats."""
        signal, rpeaks, true_intervals = generate_test_ecg_with_intervals(
            duration_s=10.0,
            heart_rate_bpm=75.0,
            pr_ms=160.0,
            qrs_ms=85.0,
            qt_ms=380.0
        )
        
        if len(rpeaks) < 3:
            pytest.skip("Need at least 3 R-peaks for consistency test")
        
        # Extract intervals from first 3 beats
        pr_durations = []
        qrs_durations = []
        qt_durations = []
        
        for i in range(min(3, len(rpeaks))):
            rpeak_idx = rpeaks[i]
            
            _, pr_dur = extract_pr_interval(signal, rpeak_idx)
            qrs_dur = extract_qrs_duration(signal, rpeak_idx)
            _, qt_dur = extract_qt_interval(signal, rpeak_idx)
            
            pr_durations.append(pr_dur * 1000.0 / 500.0)
            qrs_durations.append(qrs_dur * 1000.0 / 500.0)
            qt_durations.append(qt_dur * 1000.0 / 500.0)
        
        # Check consistency (coefficient of variation should be reasonable)
        def cv(values):
            return np.std(values) / np.mean(values) if np.mean(values) > 0 else 0
        
        # Intervals should be relatively consistent across beats
        assert cv(pr_durations) < 0.3  # Less than 30% variation
        assert cv(qrs_durations) < 0.3
        assert cv(qt_durations) < 0.3


if __name__ == "__main__":
    pytest.main([__file__])
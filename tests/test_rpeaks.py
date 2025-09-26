"""Test R-peak detection with synthetic ECG data."""

from __future__ import annotations
import numpy as np
import pytest
from unittest.mock import Mock


def generate_synthetic_ecg(
    duration_s: float = 10.0,
    sampling_rate_hz: int = 500,
    heart_rate_bpm: float = 75.0,
    noise_level: float = 0.05,
    random_seed: int = 42
) -> tuple[np.ndarray, np.ndarray, list[int]]:
    """Generate synthetic ECG signal with known R-peak locations.
    
    Args:
        duration_s: Signal duration in seconds
        sampling_rate_hz: Sampling rate in Hz
        heart_rate_bpm: Heart rate in beats per minute
        noise_level: Noise amplitude relative to signal
        random_seed: Random seed for reproducibility
        
    Returns:
        Tuple of (time_array, signal_array, true_rpeak_indices)
    """
    np.random.seed(random_seed)
    
    # Time array
    num_samples = int(duration_s * sampling_rate_hz)
    time = np.linspace(0, duration_s, num_samples)
    
    # R-peak timing (approximate)
    rr_interval_s = 60.0 / heart_rate_bpm
    num_beats = int(duration_s / rr_interval_s)
    
    # Generate beat times with slight variability
    beat_times = []
    current_time = rr_interval_s  # Start after one interval
    
    for i in range(num_beats - 1):
        # Add HRV (±5% variation)
        variation = np.random.uniform(-0.05, 0.05) * rr_interval_s
        current_time += rr_interval_s + variation
        if current_time < duration_s:
            beat_times.append(current_time)
    
    # Convert beat times to sample indices
    true_rpeak_indices = [int(t * sampling_rate_hz) for t in beat_times]
    
    # Generate ECG signal
    signal = np.zeros(num_samples)
    
    # Add QRS complexes
    for idx in true_rpeak_indices:
        # Simple QRS template (triangular R-wave with Q and S)
        if idx >= 10 and idx < num_samples - 10:
            # Q wave (negative deflection)
            for i in range(max(0, idx - 6), idx - 2):
                signal[i] -= 0.2 * np.exp(-0.5 * ((i - (idx - 4)) / 2) ** 2)
            
            # R wave (positive peak)
            for i in range(max(0, idx - 3), min(num_samples, idx + 4)):
                signal[i] += 1.0 * np.exp(-0.5 * ((i - idx) / 2) ** 2)
            
            # S wave (negative deflection)
            for i in range(idx + 2, min(num_samples, idx + 8)):
                signal[i] -= 0.3 * np.exp(-0.5 * ((i - (idx + 4)) / 2) ** 2)
    
    # Add T waves (smaller positive deflections)
    for idx in true_rpeak_indices:
        t_wave_idx = idx + int(0.3 * sampling_rate_hz)  # ~300ms after R
        if t_wave_idx < num_samples - 15:
            for i in range(max(0, t_wave_idx - 10), min(num_samples, t_wave_idx + 10)):
                signal[i] += 0.3 * np.exp(-0.5 * ((i - t_wave_idx) / 5) ** 2)
    
    # Add baseline wander
    baseline = 0.1 * np.sin(2 * np.pi * 0.5 * time)  # 0.5 Hz baseline wander
    signal += baseline
    
    # Add noise
    noise = noise_level * np.random.normal(0, 1, num_samples)
    signal += noise
    
    return time, signal, true_rpeak_indices


def pan_tompkins_rpeak_detection(
    signal: np.ndarray,
    sampling_rate_hz: int = 500,
    min_distance_ms: int = 200
) -> list[int]:
    """Simplified Pan-Tompkins R-peak detection algorithm.
    
    Args:
        signal: ECG signal array
        sampling_rate_hz: Sampling rate in Hz
        min_distance_ms: Minimum distance between peaks in ms
        
    Returns:
        List of R-peak sample indices
    """
    # Bandpass filter (simplified - just differentiate and square)
    # In real implementation, would use proper bandpass filter
    diff_signal = np.diff(signal)
    squared_signal = diff_signal ** 2
    
    # Integration window (moving average)
    window_size = int(0.15 * sampling_rate_hz)  # 150ms window
    integrated_signal = np.convolve(squared_signal, np.ones(window_size) / window_size, mode='same')
    
    # Find peaks
    from scipy.signal import find_peaks
    
    # Adaptive threshold
    mean_amplitude = np.mean(integrated_signal)
    threshold = 0.3 * mean_amplitude
    
    peaks, _ = find_peaks(
        integrated_signal,
        height=threshold,
        distance=int(min_distance_ms * sampling_rate_hz / 1000)
    )
    
    return peaks.tolist()


class TestRPeaks:
    """Test suite for R-peak detection algorithms."""
    
    def test_synthetic_ecg_generation(self):
        """Test synthetic ECG signal generation."""
        time, signal, true_peaks = generate_synthetic_ecg(
            duration_s=5.0,
            sampling_rate_hz=500,
            heart_rate_bpm=60.0,
            noise_level=0.01
        )
        
        # Check signal properties
        assert len(time) == len(signal) == 2500  # 5s at 500Hz
        assert len(true_peaks) >= 4  # At least 4 beats in 5s at 60 bpm
        assert all(0 <= idx < len(signal) for idx in true_peaks)
        
        # Check signal amplitude range
        assert -2.0 <= np.min(signal) <= 2.0
        assert -2.0 <= np.max(signal) <= 2.0
    
    def test_rpeak_detection_clean_signal(self):
        """Test R-peak detection on clean synthetic signal."""
        time, signal, true_peaks = generate_synthetic_ecg(
            duration_s=10.0,
            sampling_rate_hz=500,
            heart_rate_bpm=75.0,
            noise_level=0.01,  # Very low noise
            random_seed=123
        )
        
        detected_peaks = pan_tompkins_rpeak_detection(signal, sampling_rate_hz=500)
        
        # Should detect most peaks (allowing some tolerance)
        assert len(detected_peaks) >= len(true_peaks) * 0.8  # At least 80% detected
        assert len(detected_peaks) <= len(true_peaks) * 1.2  # Not too many false positives
    
    def test_rpeak_detection_noisy_signal(self):
        """Test R-peak detection on noisy synthetic signal."""
        time, signal, true_peaks = generate_synthetic_ecg(
            duration_s=10.0,
            sampling_rate_hz=500,
            heart_rate_bpm=80.0,
            noise_level=0.1,  # Higher noise
            random_seed=456
        )
        
        detected_peaks = pan_tompkins_rpeak_detection(signal, sampling_rate_hz=500)
        
        # Should still detect most peaks despite noise
        assert len(detected_peaks) >= len(true_peaks) * 0.6  # At least 60% detected
        assert len(detected_peaks) <= len(true_peaks) * 1.5  # Allow more false positives
    
    def test_rpeak_detection_different_heart_rates(self):
        """Test R-peak detection across different heart rates."""
        test_heart_rates = [60, 80, 100, 120]
        
        for hr in test_heart_rates:
            time, signal, true_peaks = generate_synthetic_ecg(
                duration_s=8.0,
                heart_rate_bpm=hr,
                noise_level=0.05,
                random_seed=hr  # Use HR as seed for reproducibility
            )
            
            detected_peaks = pan_tompkins_rpeak_detection(signal, sampling_rate_hz=500)
            
            # Adaptive expectations based on heart rate
            expected_beats = int(8.0 * hr / 60.0)  # Approximate number of beats
            
            # Should detect reasonable number of peaks
            assert len(detected_peaks) >= expected_beats * 0.7
            assert len(detected_peaks) <= expected_beats * 1.3
    
    def test_rpeak_detection_edge_cases(self):
        """Test R-peak detection edge cases."""
        # Very short signal
        time, signal, true_peaks = generate_synthetic_ecg(
            duration_s=2.0,
            heart_rate_bpm=75.0,
            noise_level=0.05
        )
        
        detected_peaks = pan_tompkins_rpeak_detection(signal, sampling_rate_hz=500)
        assert len(detected_peaks) >= 1  # Should detect at least one peak
        
        # Very low heart rate
        time, signal, true_peaks = generate_synthetic_ecg(
            duration_s=10.0,
            heart_rate_bpm=45.0,  # Bradycardia
            noise_level=0.05
        )
        
        detected_peaks = pan_tompkins_rpeak_detection(signal, sampling_rate_hz=500)
        expected_beats = int(10.0 * 45.0 / 60.0)
        assert len(detected_peaks) >= expected_beats * 0.6
    
    def test_rpeak_timing_accuracy(self):
        """Test accuracy of R-peak timing."""
        time, signal, true_peaks = generate_synthetic_ecg(
            duration_s=10.0,
            heart_rate_bpm=75.0,
            noise_level=0.02,
            random_seed=789
        )
        
        detected_peaks = pan_tompkins_rpeak_detection(signal, sampling_rate_hz=500)
        
        # For each detected peak, find closest true peak
        timing_errors = []
        for det_peak in detected_peaks:
            if true_peaks:
                closest_true = min(true_peaks, key=lambda x: abs(x - det_peak))
                timing_error = abs(det_peak - closest_true)
                timing_errors.append(timing_error)
        
        if timing_errors:
            # Most timing errors should be small (within 50ms = 25 samples at 500Hz)
            median_error = np.median(timing_errors)
            assert median_error <= 25, f"Median timing error too high: {median_error} samples"
    
    @pytest.mark.parametrize("noise_level", [0.01, 0.05, 0.1, 0.2])
    def test_rpeak_detection_noise_robustness(self, noise_level):
        """Test R-peak detection robustness to various noise levels."""
        time, signal, true_peaks = generate_synthetic_ecg(
            duration_s=8.0,
            heart_rate_bpm=75.0,
            noise_level=noise_level,
            random_seed=42
        )
        
        detected_peaks = pan_tompkins_rpeak_detection(signal, sampling_rate_hz=500)
        
        # Detection performance should degrade gracefully with noise
        expected_beats = len(true_peaks)
        detection_rate = len(detected_peaks) / expected_beats if expected_beats > 0 else 0
        
        if noise_level <= 0.05:
            assert detection_rate >= 0.8  # Good performance for low noise
        elif noise_level <= 0.1:
            assert detection_rate >= 0.6  # Acceptable performance for medium noise
        else:
            assert detection_rate >= 0.4  # Minimum performance for high noise


def test_scipy_available():
    """Test that scipy is available for peak detection."""
    try:
        import scipy.signal
        assert hasattr(scipy.signal, 'find_peaks')
    except ImportError:
        pytest.skip("SciPy not available for peak detection tests")


if __name__ == "__main__":
    pytest.main([__file__])
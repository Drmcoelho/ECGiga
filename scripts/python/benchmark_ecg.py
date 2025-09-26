#!/usr/bin/env python3
"""Synthetic ECG benchmarking script for R-peak detection performance evaluation.

This script generates synthetic ECG signals with known R-peak locations
and evaluates the performance of R-peak detection algorithms.
"""

from __future__ import annotations
import argparse
import json
import pathlib
import time
from typing import Dict, List, Tuple, Any, Optional

import numpy as np

# Configuration for benchmarking
DEFAULT_HEART_RATES = [60, 75, 90, 100, 120]
DEFAULT_NOISE_LEVELS = [0.01, 0.05, 0.1, 0.2]
DEFAULT_DURATION_S = 10.0
DEFAULT_SAMPLING_RATE = 500


def generate_synthetic_ecg(
    duration_s: float,
    sampling_rate_hz: int,
    heart_rate_bpm: float,
    noise_level: float = 0.05,
    random_seed: int = None
) -> Tuple[np.ndarray, List[int]]:
    """Generate synthetic ECG signal with known R-peak locations.
    
    Args:
        duration_s: Signal duration in seconds
        sampling_rate_hz: Sampling rate in Hz
        heart_rate_bpm: Heart rate in beats per minute
        noise_level: Noise amplitude relative to signal
        random_seed: Random seed for reproducibility
        
    Returns:
        Tuple of (signal_array, true_rpeak_indices)
    """
    if random_seed is not None:
        np.random.seed(random_seed)
    
    # Calculate signal parameters
    num_samples = int(duration_s * sampling_rate_hz)
    rr_interval_s = 60.0 / heart_rate_bpm
    
    # Generate beat timing with HRV (heart rate variability)
    beat_times = []
    current_time = rr_interval_s  # Start after first RR interval
    
    while current_time < duration_s - rr_interval_s:
        # Add realistic HRV (±3% variation)
        hrv_factor = np.random.uniform(0.97, 1.03)
        beat_times.append(current_time)
        current_time += rr_interval_s * hrv_factor
    
    # Convert to sample indices
    true_rpeak_indices = [int(t * sampling_rate_hz) for t in beat_times]
    
    # Initialize signal
    signal = np.zeros(num_samples)
    
    # Add ECG components for each beat
    for rpeak_idx in true_rpeak_indices:
        if rpeak_idx >= 20 and rpeak_idx < num_samples - 50:
            # P wave (150ms before QRS)
            p_idx = rpeak_idx - int(0.15 * sampling_rate_hz)
            if p_idx >= 10:
                for i in range(p_idx - 8, min(num_samples, p_idx + 12)):
                    if 0 <= i < num_samples:
                        signal[i] += 0.2 * np.exp(-0.5 * ((i - p_idx) / 6) ** 2)
            
            # QRS complex
            # Q wave
            q_idx = rpeak_idx - int(0.02 * sampling_rate_hz)  # 20ms before R
            if 0 <= q_idx < num_samples:
                signal[q_idx] -= 0.15
            
            # R wave (main peak)
            for i in range(max(0, rpeak_idx - 4), min(num_samples, rpeak_idx + 5)):
                signal[i] += 1.0 * np.exp(-0.5 * ((i - rpeak_idx) / 3) ** 2)
            
            # S wave
            s_idx = rpeak_idx + int(0.04 * sampling_rate_hz)  # 40ms after R
            if s_idx < num_samples:
                signal[s_idx] -= 0.25
            
            # T wave (300ms after R peak)
            t_idx = rpeak_idx + int(0.3 * sampling_rate_hz)
            if t_idx < num_samples - 15:
                for i in range(max(0, t_idx - 12), min(num_samples, t_idx + 18)):
                    signal[i] += 0.3 * np.exp(-0.5 * ((i - t_idx) / 8) ** 2)
    
    # Add baseline wander (respiratory and motion artifacts)
    baseline_freq1 = 0.3  # Respiratory frequency ~0.3 Hz
    baseline_freq2 = 0.05  # Low frequency drift
    time_array = np.arange(num_samples) / sampling_rate_hz
    
    baseline = (0.1 * np.sin(2 * np.pi * baseline_freq1 * time_array) +
                0.05 * np.sin(2 * np.pi * baseline_freq2 * time_array))
    signal += baseline
    
    # Add noise
    noise = noise_level * np.random.normal(0, 1, num_samples)
    signal += noise
    
    return signal, true_rpeak_indices


def simple_rpeak_detector(
    signal: np.ndarray,
    sampling_rate_hz: int,
    min_distance_ms: int = 200
) -> List[int]:
    """Simple R-peak detector for benchmarking."""
    # Basic preprocessing: differentiation and squaring
    diff_signal = np.diff(signal)
    squared_signal = diff_signal ** 2
    
    # Moving window integration
    window_size = int(0.1 * sampling_rate_hz)  # 100ms window
    if window_size < 1:
        window_size = 1
    
    integrated = np.convolve(squared_signal, np.ones(window_size) / window_size, mode='same')
    
    # Find peaks using simple threshold
    threshold = 0.2 * np.max(integrated)
    min_distance_samples = int(min_distance_ms * sampling_rate_hz / 1000)
    
    peaks = []
    last_peak = -min_distance_samples
    
    for i in range(len(integrated)):
        if (integrated[i] > threshold and 
            i - last_peak >= min_distance_samples):
            # Local maximum search
            search_start = max(0, i - 5)
            search_end = min(len(signal), i + 6)
            local_max_idx = search_start + np.argmax(signal[search_start:search_end])
            
            peaks.append(local_max_idx)
            last_peak = i
    
    return peaks


def advanced_rpeak_detector(
    signal: np.ndarray,
    sampling_rate_hz: int,
    min_distance_ms: int = 200
) -> List[int]:
    """More advanced R-peak detector using Pan-Tompkins-like algorithm."""
    # Bandpass filter simulation (simplified)
    # High-pass: differentiation
    highpass = np.diff(signal)
    
    # Low-pass: simple moving average
    lowpass_window = int(0.03 * sampling_rate_hz)  # 30ms
    if lowpass_window < 1:
        lowpass_window = 1
    
    lowpass = np.convolve(highpass, np.ones(lowpass_window) / lowpass_window, mode='same')
    
    # Derivative (emphasizes QRS slope)
    derivative = np.diff(lowpass)
    
    # Squaring
    squared = derivative ** 2
    
    # Integration (moving window)
    integration_window = int(0.08 * sampling_rate_hz)  # 80ms
    if integration_window < 1:
        integration_window = 1
    
    integrated = np.convolve(squared, np.ones(integration_window) / integration_window, mode='same')
    
    # Adaptive thresholding
    signal_level = np.mean(integrated)
    noise_level = 0.1 * signal_level
    
    threshold_i1 = noise_level + 0.25 * (signal_level - noise_level)
    threshold_i2 = 0.5 * threshold_i1
    
    # Peak detection with adaptive threshold
    peaks = []
    min_distance_samples = int(min_distance_ms * sampling_rate_hz / 1000)
    last_peak = -min_distance_samples
    
    for i in range(len(integrated)):
        if (integrated[i] > threshold_i1 and 
            i - last_peak >= min_distance_samples):
            
            # Find actual R peak in original signal around this location
            search_start = max(0, i - int(0.05 * sampling_rate_hz))
            search_end = min(len(signal), i + int(0.05 * sampling_rate_hz))
            
            if search_end > search_start:
                local_max_idx = search_start + np.argmax(signal[search_start:search_end])
                peaks.append(local_max_idx)
                last_peak = i
                
                # Update thresholds
                signal_level = 0.875 * signal_level + 0.125 * integrated[i]
                threshold_i1 = noise_level + 0.25 * (signal_level - noise_level)
                threshold_i2 = 0.5 * threshold_i1
        
        elif (integrated[i] > threshold_i2 and 
              i - last_peak >= min_distance_samples):
            # Lower threshold detection (missed beat recovery)
            noise_level = 0.875 * noise_level + 0.125 * integrated[i]
    
    return peaks


def calculate_performance_metrics(
    true_peaks: List[int],
    detected_peaks: List[int],
    tolerance_samples: int = 25  # ~50ms at 500Hz
) -> Dict[str, float]:
    """Calculate performance metrics for R-peak detection.
    
    Args:
        true_peaks: Ground truth R-peak locations
        detected_peaks: Detected R-peak locations  
        tolerance_samples: Tolerance window for matching peaks
        
    Returns:
        Dictionary with performance metrics
    """
    if not true_peaks:
        return {
            "precision": 0.0,
            "recall": 0.0,
            "f1_score": 0.0,
            "true_positives": 0,
            "false_positives": len(detected_peaks),
            "false_negatives": 0,
            "detection_rate": 0.0
        }
    
    # Match detected peaks to true peaks
    true_positives = 0
    used_true_peaks = set()
    
    for det_peak in detected_peaks:
        # Find closest true peak within tolerance
        closest_true = None
        min_distance = float('inf')
        
        for i, true_peak in enumerate(true_peaks):
            if i in used_true_peaks:
                continue
                
            distance = abs(det_peak - true_peak)
            if distance <= tolerance_samples and distance < min_distance:
                min_distance = distance
                closest_true = i
        
        if closest_true is not None:
            true_positives += 1
            used_true_peaks.add(closest_true)
    
    false_positives = len(detected_peaks) - true_positives
    false_negatives = len(true_peaks) - true_positives
    
    # Calculate metrics
    precision = true_positives / len(detected_peaks) if detected_peaks else 0.0
    recall = true_positives / len(true_peaks) if true_peaks else 0.0
    f1_score = (2 * precision * recall / (precision + recall) 
                if precision + recall > 0 else 0.0)
    detection_rate = len(detected_peaks) / len(true_peaks) if true_peaks else 0.0
    
    return {
        "precision": precision,
        "recall": recall,
        "f1_score": f1_score,
        "true_positives": true_positives,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "detection_rate": detection_rate,
        "total_true_peaks": len(true_peaks),
        "total_detected_peaks": len(detected_peaks)
    }


def run_benchmark_scenario(
    heart_rate_bpm: float,
    noise_level: float,
    duration_s: float = 10.0,
    sampling_rate_hz: int = 500,
    random_seed: int = None
) -> Dict[str, Any]:
    """Run benchmark for a single scenario."""
    # Generate synthetic ECG
    signal, true_peaks = generate_synthetic_ecg(
        duration_s=duration_s,
        sampling_rate_hz=sampling_rate_hz,
        heart_rate_bpm=heart_rate_bpm,
        noise_level=noise_level,
        random_seed=random_seed
    )
    
    # Test multiple detectors
    detectors = {
        "simple": simple_rpeak_detector,
        "advanced": advanced_rpeak_detector
    }
    
    results = {
        "scenario": {
            "heart_rate_bpm": heart_rate_bpm,
            "noise_level": noise_level,
            "duration_s": duration_s,
            "sampling_rate_hz": sampling_rate_hz,
            "random_seed": random_seed
        },
        "ground_truth": {
            "num_beats": len(true_peaks),
            "avg_rr_interval_ms": (60000.0 / heart_rate_bpm) if heart_rate_bpm > 0 else None
        },
        "detectors": {}
    }
    
    tolerance_samples = int(0.05 * sampling_rate_hz)  # 50ms tolerance
    
    for detector_name, detector_func in detectors.items():
        try:
            start_time = time.time()
            detected_peaks = detector_func(signal, sampling_rate_hz)
            detection_time = time.time() - start_time
            
            metrics = calculate_performance_metrics(true_peaks, detected_peaks, tolerance_samples)
            metrics["detection_time_ms"] = detection_time * 1000
            
            results["detectors"][detector_name] = metrics
            
        except Exception as e:
            results["detectors"][detector_name] = {
                "error": str(e),
                "detection_time_ms": None
            }
    
    return results


def run_comprehensive_benchmark(
    heart_rates: List[float],
    noise_levels: List[float],
    duration_s: float = 10.0,
    sampling_rate_hz: int = 500,
    num_trials: int = 3,
    verbose: bool = False
) -> Dict[str, Any]:
    """Run comprehensive benchmark across multiple scenarios."""
    all_results = []
    total_scenarios = len(heart_rates) * len(noise_levels) * num_trials
    scenario_count = 0
    
    start_time = time.time()
    
    for hr in heart_rates:
        for noise in noise_levels:
            for trial in range(num_trials):
                scenario_count += 1
                
                if verbose:
                    print(f"[{scenario_count}/{total_scenarios}] HR={hr} bpm, noise={noise:.3f}, trial={trial+1}")
                
                # Use different seed for each trial
                seed = hash((hr, noise, trial)) % 10000
                
                scenario_result = run_benchmark_scenario(
                    heart_rate_bpm=hr,
                    noise_level=noise,
                    duration_s=duration_s,
                    sampling_rate_hz=sampling_rate_hz,
                    random_seed=seed
                )
                
                scenario_result["trial"] = trial + 1
                all_results.append(scenario_result)
    
    total_time = time.time() - start_time
    
    # Aggregate results
    summary = {
        "benchmark_info": {
            "total_scenarios": total_scenarios,
            "unique_scenarios": len(heart_rates) * len(noise_levels),
            "trials_per_scenario": num_trials,
            "total_duration_s": total_time,
            "avg_time_per_scenario_ms": (total_time * 1000) / total_scenarios,
            "parameters": {
                "heart_rates_bpm": heart_rates,
                "noise_levels": noise_levels,
                "signal_duration_s": duration_s,
                "sampling_rate_hz": sampling_rate_hz
            }
        },
        "results": all_results,
        "summary": calculate_benchmark_summary(all_results)
    }
    
    return summary


def calculate_benchmark_summary(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate summary statistics from benchmark results."""
    if not results:
        return {}
    
    # Extract detector names
    detector_names = set()
    for result in results:
        detector_names.update(result.get("detectors", {}).keys())
    
    summary = {
        "detectors": {},
        "by_heart_rate": {},
        "by_noise_level": {}
    }
    
    # Overall detector performance
    for detector in detector_names:
        metrics_list = []
        for result in results:
            detector_data = result.get("detectors", {}).get(detector, {})
            if "f1_score" in detector_data:  # Valid result
                metrics_list.append(detector_data)
        
        if metrics_list:
            summary["detectors"][detector] = {
                "avg_f1_score": np.mean([m["f1_score"] for m in metrics_list]),
                "avg_precision": np.mean([m["precision"] for m in metrics_list]),
                "avg_recall": np.mean([m["recall"] for m in metrics_list]),
                "avg_detection_time_ms": np.mean([m.get("detection_time_ms", 0) for m in metrics_list]),
                "num_scenarios": len(metrics_list)
            }
    
    # Performance by heart rate
    hr_groups = {}
    for result in results:
        hr = result["scenario"]["heart_rate_bpm"]
        if hr not in hr_groups:
            hr_groups[hr] = []
        hr_groups[hr].append(result)
    
    for hr, hr_results in hr_groups.items():
        hr_summary = {}
        for detector in detector_names:
            metrics = []
            for result in hr_results:
                detector_data = result.get("detectors", {}).get(detector, {})
                if "f1_score" in detector_data:
                    metrics.append(detector_data["f1_score"])
            
            if metrics:
                hr_summary[detector] = {
                    "avg_f1_score": np.mean(metrics),
                    "std_f1_score": np.std(metrics),
                    "num_trials": len(metrics)
                }
        
        summary["by_heart_rate"][hr] = hr_summary
    
    # Performance by noise level
    noise_groups = {}
    for result in results:
        noise = result["scenario"]["noise_level"]
        if noise not in noise_groups:
            noise_groups[noise] = []
        noise_groups[noise].append(result)
    
    for noise, noise_results in noise_groups.items():
        noise_summary = {}
        for detector in detector_names:
            metrics = []
            for result in noise_results:
                detector_data = result.get("detectors", {}).get(detector, {})
                if "f1_score" in detector_data:
                    metrics.append(detector_data["f1_score"])
            
            if metrics:
                noise_summary[detector] = {
                    "avg_f1_score": np.mean(metrics),
                    "std_f1_score": np.std(metrics),
                    "num_trials": len(metrics)
                }
        
        summary["by_noise_level"][noise] = noise_summary
    
    return summary


def print_benchmark_summary(summary: Dict[str, Any]) -> None:
    """Print human-readable benchmark summary."""
    print("\n" + "="*60)
    print("📊 ECG R-Peak Detection Benchmark Summary")
    print("="*60)
    
    info = summary["benchmark_info"]
    print(f"Total scenarios: {info['total_scenarios']}")
    print(f"Total duration: {info['total_duration_s']:.1f}s")
    print(f"Average time per scenario: {info['avg_time_per_scenario_ms']:.1f}ms")
    
    print(f"\nParameters:")
    print(f"  Heart rates: {info['parameters']['heart_rates_bpm']} bpm")
    print(f"  Noise levels: {info['parameters']['noise_levels']}")
    print(f"  Signal duration: {info['parameters']['signal_duration_s']}s")
    print(f"  Sampling rate: {info['parameters']['sampling_rate_hz']}Hz")
    
    # Overall detector performance
    print(f"\n🎯 Overall Detector Performance:")
    detector_summary = summary["summary"]["detectors"]
    
    for detector, metrics in detector_summary.items():
        print(f"\n  {detector.upper()}:")
        print(f"    F1 Score: {metrics['avg_f1_score']:.3f}")
        print(f"    Precision: {metrics['avg_precision']:.3f}")
        print(f"    Recall: {metrics['avg_recall']:.3f}")
        print(f"    Avg detection time: {metrics['avg_detection_time_ms']:.2f}ms")
        print(f"    Scenarios tested: {metrics['num_scenarios']}")
    
    # Best detector
    if detector_summary:
        best_detector = max(detector_summary.keys(), 
                           key=lambda d: detector_summary[d]['avg_f1_score'])
        best_f1 = detector_summary[best_detector]['avg_f1_score']
        print(f"\n🏆 Best detector: {best_detector.upper()} (F1={best_f1:.3f})")


def main():
    """Main benchmark script entry point."""
    parser = argparse.ArgumentParser(
        description="Benchmark ECG R-peak detection algorithms on synthetic data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Quick benchmark with default parameters
  python benchmark_ecg.py
  
  # Custom heart rates and noise levels
  python benchmark_ecg.py --heart-rates 60 80 100 --noise-levels 0.01 0.1
  
  # Save results to JSON
  python benchmark_ecg.py --out benchmark_results.json
  
  # Verbose output with more trials
  python benchmark_ecg.py --trials 5 --verbose
        """
    )
    
    parser.add_argument(
        "--heart-rates",
        nargs="+",
        type=float,
        default=DEFAULT_HEART_RATES,
        help=f"Heart rates to test (default: {DEFAULT_HEART_RATES})"
    )
    
    parser.add_argument(
        "--noise-levels",
        nargs="+",
        type=float,
        default=DEFAULT_NOISE_LEVELS,
        help=f"Noise levels to test (default: {DEFAULT_NOISE_LEVELS})"
    )
    
    parser.add_argument(
        "--duration",
        type=float,
        default=DEFAULT_DURATION_S,
        help=f"Signal duration in seconds (default: {DEFAULT_DURATION_S})"
    )
    
    parser.add_argument(
        "--sampling-rate",
        type=int,
        default=DEFAULT_SAMPLING_RATE,
        help=f"Sampling rate in Hz (default: {DEFAULT_SAMPLING_RATE})"
    )
    
    parser.add_argument(
        "--trials",
        type=int,
        default=3,
        help="Number of trials per scenario (default: 3)"
    )
    
    parser.add_argument(
        "--out",
        type=str,
        help="Output JSON file path for detailed results"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    try:
        print("🚀 Starting ECG R-Peak Detection Benchmark")
        
        # Run comprehensive benchmark
        results = run_comprehensive_benchmark(
            heart_rates=args.heart_rates,
            noise_levels=args.noise_levels,
            duration_s=args.duration,
            sampling_rate_hz=args.sampling_rate,
            num_trials=args.trials,
            verbose=args.verbose
        )
        
        # Print summary
        print_benchmark_summary(results)
        
        # Save detailed results if requested
        if args.out:
            output_path = pathlib.Path(args.out)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2, default=str)
            
            print(f"\n💾 Detailed results saved to: {output_path}")
        
        print("\n✅ Benchmark completed successfully!")
        
    except KeyboardInterrupt:
        print("\n⏹️  Benchmark interrupted by user")
        return 130
    except Exception as e:
        print(f"\n❌ Benchmark failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
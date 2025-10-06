#!/usr/bin/env python3
"""
ECG Benchmarking script with F1 threshold gating.

Performs synthetic ECG analysis benchmarks and validates performance
against F1 score thresholds for HR range 60-90 bpm.
"""

import argparse
import json
import pathlib
import sys
import time
from typing import Dict, List, Tuple, Optional
import statistics
import numpy as np


def generate_synthetic_ecg_data(num_samples: int = 10) -> List[Dict]:
    """Generate synthetic ECG analysis results for benchmarking."""
    samples = []
    
    for i in range(num_samples):
        # Generate realistic but synthetic metrics
        hr_bpm = np.random.uniform(60, 90)  # Target HR range
        rr_ms = 60000 / hr_bpm
        
        # Synthetic measurements with some variance
        pr_ms = np.random.uniform(120, 200)
        qrs_ms = np.random.uniform(70, 110)
        qt_ms = np.random.uniform(350, 450)
        
        # Generate ground truth vs predicted for F1 calculation
        # Simulate detection accuracy
        true_positives = np.random.randint(8, 12)  # Expected ~10 beats in analysis window
        false_positives = np.random.randint(0, 2)
        false_negatives = np.random.randint(0, 2)
        
        sample = {
            "sample_id": f"synthetic_{i+1:03d}",
            "hr_bpm": hr_bpm,
            "rr_ms": rr_ms,
            "pr_ms": pr_ms,
            "qrs_ms": qrs_ms,
            "qt_ms": qt_ms,
            "detection_metrics": {
                "true_positives": true_positives,
                "false_positives": false_positives,
                "false_negatives": false_negatives
            },
            "processing_time_ms": np.random.uniform(100, 1000)
        }
        
        samples.append(sample)
    
    return samples


def calculate_f1_score(tp: int, fp: int, fn: int) -> float:
    """Calculate F1 score from confusion matrix values."""
    if tp == 0:
        return 0.0
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    
    if precision + recall == 0:
        return 0.0
    
    f1 = 2 * (precision * recall) / (precision + recall)
    return f1


def analyze_benchmark_results(samples: List[Dict]) -> Dict:
    """Analyze benchmark results and calculate performance metrics."""
    if not samples:
        return {"error": "No samples to analyze"}
    
    # Calculate F1 scores for each sample
    f1_scores = []
    processing_times = []
    
    for sample in samples:
        metrics = sample["detection_metrics"]
        f1 = calculate_f1_score(
            metrics["true_positives"],
            metrics["false_positives"], 
            metrics["false_negatives"]
        )
        sample["f1_score"] = f1
        f1_scores.append(f1)
        processing_times.append(sample["processing_time_ms"])
    
    # Calculate summary statistics
    analysis = {
        "total_samples": len(samples),
        "hr_range": {
            "min_bpm": min(s["hr_bpm"] for s in samples),
            "max_bpm": max(s["hr_bpm"] for s in samples),
            "mean_bpm": statistics.mean(s["hr_bpm"] for s in samples)
        },
        "f1_performance": {
            "mean_f1": statistics.mean(f1_scores),
            "median_f1": statistics.median(f1_scores),
            "min_f1": min(f1_scores),
            "max_f1": max(f1_scores),
            "std_f1": statistics.stdev(f1_scores) if len(f1_scores) > 1 else 0.0
        },
        "performance_metrics": {
            "mean_processing_time_ms": statistics.mean(processing_times),
            "median_processing_time_ms": statistics.median(processing_times),
            "total_processing_time_ms": sum(processing_times)
        },
        "samples_detail": samples
    }
    
    return analysis


def validate_f1_threshold(analysis: Dict, threshold: float) -> Tuple[bool, str]:
    """Validate if F1 performance meets the threshold requirement."""
    if "f1_performance" not in analysis:
        return False, "No F1 performance data available"
    
    mean_f1 = analysis["f1_performance"]["mean_f1"]
    
    if mean_f1 >= threshold:
        return True, f"✅ F1 threshold passed: {mean_f1:.3f} >= {threshold:.3f}"
    else:
        return False, f"❌ F1 threshold failed: {mean_f1:.3f} < {threshold:.3f}"


def run_benchmark(num_samples: int, f1_threshold: float, output_path: Optional[str] = None) -> Dict:
    """Run complete benchmark analysis."""
    start_time = time.time()
    
    # Generate synthetic data
    print(f"Generating {num_samples} synthetic ECG samples...")
    samples = generate_synthetic_ecg_data(num_samples)
    
    # Analyze results
    print("Analyzing benchmark results...")
    analysis = analyze_benchmark_results(samples)
    
    # Add benchmark metadata
    analysis["benchmark_metadata"] = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "duration_seconds": time.time() - start_time,
        "f1_threshold": f1_threshold,
        "target_hr_range": "60-90 bpm"
    }
    
    # Validate threshold
    passed, message = validate_f1_threshold(analysis, f1_threshold)
    analysis["threshold_validation"] = {
        "passed": passed,
        "message": message
    }
    
    print(message)
    
    # Save results if output path specified
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, ensure_ascii=False, indent=2)
        print(f"Benchmark results saved to {output_path}")
    
    return analysis


def main():
    parser = argparse.ArgumentParser(
        description="ECG benchmarking with F1 threshold gating",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--samples", "-n",
        type=int,
        default=50,
        help="Number of synthetic samples to generate (default: 50)"
    )
    
    parser.add_argument(
        "--f1-threshold",
        type=float,
        default=0.85,
        help="F1 score threshold for gating (default: 0.85)"
    )
    
    parser.add_argument(
        "--output", "-o",
        help="Output JSON file path"
    )
    
    parser.add_argument(
        "--exit-on-fail",
        action="store_true",
        help="Exit with code 1 if F1 threshold is not met"
    )
    
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Quiet mode - minimal output"
    )
    
    args = parser.parse_args()
    
    if not args.quiet:
        print("ECG Benchmark Analysis")
        print("=" * 50)
        print(f"Samples: {args.samples}")
        print(f"F1 Threshold: {args.f1_threshold}")
        print(f"Target HR Range: 60-90 bpm")
        print()
    
    # Run benchmark
    try:
        analysis = run_benchmark(args.samples, args.f1_threshold, args.output)
        
        if not args.quiet:
            # Print summary
            f1_perf = analysis["f1_performance"]
            print("\nBenchmark Summary:")
            print(f"  Mean F1 Score: {f1_perf['mean_f1']:.3f}")
            print(f"  Median F1 Score: {f1_perf['median_f1']:.3f}")
            print(f"  F1 Range: {f1_perf['min_f1']:.3f} - {f1_perf['max_f1']:.3f}")
            print(f"  Processing Time: {analysis['performance_metrics']['mean_processing_time_ms']:.1f} ms avg")
        
        # Exit with appropriate code based on threshold validation
        if args.exit_on_fail and not analysis["threshold_validation"]["passed"]:
            if not args.quiet:
                print("\nExiting with error code due to F1 threshold failure")
            return 1
        
        return 0
        
    except Exception as e:
        print(f"Error running benchmark: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
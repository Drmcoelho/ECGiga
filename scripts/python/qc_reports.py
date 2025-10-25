#!/usr/bin/env python3
"""
Quality Control script for ECG reports.

Analyzes report files for consistency, structural integrity, and quality metrics.
Generates JSON summary with statistics, validation results, and quality flags.
"""

import argparse
import json
import pathlib
import sys
from typing import Dict, List, Any, Optional
import statistics

from jsonschema import Draft202012Validator, ValidationError


def load_schema(schema_path: Optional[str] = None) -> Dict:
    """Load the report schema for validation."""
    if schema_path is None:
        # Default to v0.5 schema
        repo_root = pathlib.Path(__file__).parents[2]
        schema_path = repo_root / "reporting" / "schema" / "report.schema.v0.5.json"
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def validate_report_structure(report: Dict, schema: Dict) -> List[str]:
    """Validate report against schema and return validation errors."""
    errors = []
    validator = Draft202012Validator(schema)
    
    for error in validator.iter_errors(report):
        errors.append(f"{error.json_path}: {error.message}")
    
    return errors


def analyze_quality_metrics(report: Dict) -> Dict:
    """Analyze quality-related aspects of the report."""
    quality_analysis = {
        "has_quality_block": "quality" in report,
        "overall_score": None,
        "confidence_scores": {},
        "validation_flags_count": 0,
        "quality_issues": []
    }
    
    # Check quality block
    quality_block = report.get("quality", {})
    if quality_block:
        quality_analysis["overall_score"] = quality_block.get("overall_score")
        
        # Analyze confidence scores
        analysis_confidence = quality_block.get("analysis_confidence", {})
        for metric, score in analysis_confidence.items():
            quality_analysis["confidence_scores"][metric] = score
            if score and score < 0.5:
                quality_analysis["quality_issues"].append(f"Low {metric}: {score:.2f}")
        
        # Count validation flags
        validation_flags = quality_block.get("validation_flags", [])
        quality_analysis["validation_flags_count"] = len(validation_flags)
        if validation_flags:
            quality_analysis["quality_issues"].extend(validation_flags)
    
    return quality_analysis


def analyze_measurement_consistency(report: Dict) -> Dict:
    """Check consistency of measurements across different analysis blocks."""
    consistency_analysis = {
        "rr_consistency": None,
        "axis_consistency": None,
        "interval_consistency": None,
        "consistency_issues": []
    }
    
    # Check RR interval consistency between different blocks
    rpeaks_data = report.get("rpeaks", {})
    measures_data = report.get("measures", {})
    
    if "rr_ms" in measures_data and rpeaks_data.get("peaks_idx"):
        # Could add RR consistency checks here
        pass
    
    # Check axis consistency between different calculation methods
    axis_data = report.get("axis", {})
    axis_hex_data = report.get("axis_hex", {})
    
    if axis_data.get("angle_deg") is not None and axis_hex_data.get("angle_deg") is not None:
        angle_diff = abs(axis_data["angle_deg"] - axis_hex_data["angle_deg"])
        consistency_analysis["axis_consistency"] = angle_diff
        if angle_diff > 30:  # Significant difference threshold
            consistency_analysis["consistency_issues"].append(
                f"Large axis discrepancy: {angle_diff:.1f}° between methods"
            )
    
    return consistency_analysis


def analyze_completeness(report: Dict) -> Dict:
    """Analyze completeness of the report."""
    expected_blocks = [
        "meta", "acquisition", "segmentation", "rpeaks", 
        "intervals", "measures", "flags", "version"
    ]
    
    completeness_analysis = {
        "total_blocks": len(expected_blocks),
        "present_blocks": 0,
        "missing_blocks": [],
        "completeness_score": 0.0
    }
    
    for block in expected_blocks:
        if block in report and report[block]:
            completeness_analysis["present_blocks"] += 1
        else:
            completeness_analysis["missing_blocks"].append(block)
    
    completeness_analysis["completeness_score"] = (
        completeness_analysis["present_blocks"] / completeness_analysis["total_blocks"]
    )
    
    return completeness_analysis


def analyze_clinical_flags(report: Dict) -> Dict:
    """Analyze clinical flags and interpretations."""
    flags_analysis = {
        "total_flags": 0,
        "critical_flags": 0,
        "warning_flags": 0,
        "suggestion_count": 0,
        "flag_categories": {}
    }
    
    flags = report.get("flags", [])
    flags_analysis["total_flags"] = len(flags)
    
    # Categorize flags by severity
    critical_keywords = ["QTc prolongado", "BAV", "bloqueio", "taquicardia", "bradicardia"]
    warning_keywords = ["suspeita", "considerar", "possível"]
    
    for flag in flags:
        flag_lower = flag.lower()
        if any(keyword in flag_lower for keyword in critical_keywords):
            flags_analysis["critical_flags"] += 1
        elif any(keyword in flag_lower for keyword in warning_keywords):
            flags_analysis["warning_flags"] += 1
        
        # Simple categorization by main topic
        if "qtc" in flag_lower:
            flags_analysis["flag_categories"]["qtc"] = flags_analysis["flag_categories"].get("qtc", 0) + 1
        elif "pr" in flag_lower:
            flags_analysis["flag_categories"]["conduction"] = flags_analysis["flag_categories"].get("conduction", 0) + 1
        elif "qrs" in flag_lower:
            flags_analysis["flag_categories"]["qrs"] = flags_analysis["flag_categories"].get("qrs", 0) + 1
    
    # Count suggestions
    suggestions = report.get("suggested_interpretations", [])
    flags_analysis["suggestion_count"] = len(suggestions)
    
    return flags_analysis


def qc_single_report(report_path: pathlib.Path, schema: Dict) -> Dict:
    """Perform QC analysis on a single report file."""
    try:
        with open(report_path, 'r', encoding='utf-8') as f:
            report = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        return {
            "file": str(report_path),
            "error": str(e),
            "valid": False
        }
    
    # Perform all analyses
    validation_errors = validate_report_structure(report, schema)
    quality_metrics = analyze_quality_metrics(report)
    consistency_analysis = analyze_measurement_consistency(report)
    completeness_analysis = analyze_completeness(report)
    flags_analysis = analyze_clinical_flags(report)
    
    return {
        "file": str(report_path),
        "valid": len(validation_errors) == 0,
        "validation_errors": validation_errors,
        "quality_metrics": quality_metrics,
        "consistency_analysis": consistency_analysis,
        "completeness_analysis": completeness_analysis,
        "flags_analysis": flags_analysis,
        "version": report.get("version", "unknown")
    }


def qc_reports_directory(reports_dir: pathlib.Path, schema: Dict) -> Dict:
    """Perform QC analysis on all report files in a directory."""
    report_files = list(reports_dir.glob("*.json"))
    
    if not report_files:
        return {
            "error": f"No JSON files found in {reports_dir}",
            "summary": {"total_files": 0}
        }
    
    # Analyze each report
    results = []
    for report_file in report_files:
        result = qc_single_report(report_file, schema)
        results.append(result)
    
    # Generate summary statistics
    total_files = len(results)
    valid_files = sum(1 for r in results if r.get("valid", False))
    
    # Aggregate quality scores
    quality_scores = [
        r["quality_metrics"]["overall_score"] 
        for r in results 
        if r.get("quality_metrics", {}).get("overall_score") is not None
    ]
    
    # Aggregate completeness scores
    completeness_scores = [
        r["completeness_analysis"]["completeness_score"]
        for r in results
        if "completeness_analysis" in r
    ]
    
    # Count issues
    total_validation_errors = sum(len(r.get("validation_errors", [])) for r in results)
    total_quality_issues = sum(len(r.get("quality_metrics", {}).get("quality_issues", [])) for r in results)
    
    summary = {
        "total_files": total_files,
        "valid_files": valid_files,
        "invalid_files": total_files - valid_files,
        "validation_success_rate": valid_files / total_files if total_files > 0 else 0,
        "total_validation_errors": total_validation_errors,
        "total_quality_issues": total_quality_issues,
        "quality_metrics": {
            "files_with_quality_block": sum(1 for r in results if r.get("quality_metrics", {}).get("has_quality_block", False)),
            "mean_quality_score": statistics.mean(quality_scores) if quality_scores else None,
            "median_quality_score": statistics.median(quality_scores) if quality_scores else None
        },
        "completeness_metrics": {
            "mean_completeness": statistics.mean(completeness_scores) if completeness_scores else None,
            "median_completeness": statistics.median(completeness_scores) if completeness_scores else None
        }
    }
    
    return {
        "summary": summary,
        "individual_results": results
    }


def main():
    parser = argparse.ArgumentParser(
        description="Quality control analysis for ECG reports",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "reports_path",
        help="Path to directory containing report JSON files or single report file"
    )
    
    parser.add_argument(
        "--schema",
        help="Path to custom schema file (default: use v0.5 schema)"
    )
    
    parser.add_argument(
        "--output",
        help="Output JSON file path (default: stdout)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Include detailed individual results in output"
    )
    
    args = parser.parse_args()
    
    # Load schema
    try:
        schema = load_schema(args.schema)
    except Exception as e:
        print(f"Error loading schema: {e}", file=sys.stderr)
        return 1
    
    # Determine if input is file or directory
    reports_path = pathlib.Path(args.reports_path)
    
    if reports_path.is_file():
        # Single file analysis
        result = qc_single_report(reports_path, schema)
        output_data = {"single_file_analysis": result}
    elif reports_path.is_dir():
        # Directory analysis
        result = qc_reports_directory(reports_path, schema)
        output_data = result
        if not args.verbose:
            # Remove individual results for brevity
            output_data.pop("individual_results", None)
    else:
        print(f"Error: {reports_path} is not a valid file or directory", file=sys.stderr)
        return 1
    
    # Output results
    output_json = json.dumps(output_data, ensure_ascii=False, indent=2)
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output_json)
        print(f"QC results saved to {args.output}")
    else:
        print(output_json)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
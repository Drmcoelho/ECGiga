#!/usr/bin/env python3
"""Schema migration script for ECG reports from legacy versions to v0.4.

This script reads legacy ECG reports (v0.1, v0.2, v0.3) and migrates them
to the v0.4 schema format with capabilities inference.
"""

from __future__ import annotations
import argparse
import json
import pathlib
import sys
import time
from typing import Dict, Any, List

# Import migration functions from tests (for real implementation would be in separate module)
sys.path.append(str(pathlib.Path(__file__).parent.parent.parent / "tests"))
from test_migration import migrate_report_to_v04, infer_capabilities_from_v04


def load_json_file(file_path: pathlib.Path) -> Dict[str, Any]:
    """Load JSON file with error handling."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {file_path}: {e}")
    except Exception as e:
        raise ValueError(f"Error reading {file_path}: {e}")


def save_json_file(file_path: pathlib.Path, data: Dict[str, Any]) -> None:
    """Save JSON file with formatting."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def detect_report_version(report: Dict[str, Any]) -> str:
    """Detect the version of an ECG report."""
    # Check explicit version fields
    if "schema_version" in report:
        return report["schema_version"]
    elif "version" in report:
        return report["version"]
    
    # Infer from structure
    if "ecg_analysis" in report:
        return "v0.3"
    elif "intervals" in report and "axis" in report:
        return "v0.2"
    elif "measurements" in report and "interpretation" in report:
        return "v0.1"
    
    return "unknown"


def process_single_file(
    input_path: pathlib.Path,
    output_path: pathlib.Path,
    force: bool = False
) -> Dict[str, Any]:
    """Process a single ECG report file.
    
    Returns:
        Dictionary with processing statistics
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    if output_path.exists() and not force:
        return {
            "status": "skipped",
            "reason": "output_exists",
            "input_file": str(input_path),
            "output_file": str(output_path)
        }
    
    try:
        # Load and detect version
        original_report = load_json_file(input_path)
        original_version = detect_report_version(original_report)
        
        # Migrate to v0.4
        if original_version == "v0.4":
            # Already v0.4, just ensure capabilities are present
            migrated_report = original_report.copy()
            if "capabilities" not in migrated_report:
                migrated_report["capabilities"] = infer_capabilities_from_v04(migrated_report)
        else:
            migrated_report = migrate_report_to_v04(original_report)
        
        # Add migration metadata
        if "metadata" not in migrated_report:
            migrated_report["metadata"] = {}
        
        if "processing_info" not in migrated_report["metadata"]:
            migrated_report["metadata"]["processing_info"] = {}
        
        migrated_report["metadata"]["processing_info"].update({
            "migration_from": original_version,
            "migrated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "migrated_by": "migrate_reports.py",
            "original_file": str(input_path)
        })
        
        # Save migrated report
        save_json_file(output_path, migrated_report)
        
        return {
            "status": "migrated",
            "from_version": original_version,
            "to_version": "v0.4",
            "capabilities_count": len(migrated_report.get("capabilities", [])),
            "input_file": str(input_path),
            "output_file": str(output_path)
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "input_file": str(input_path),
            "output_file": str(output_path)
        }


def migrate_directory(
    input_dir: pathlib.Path,
    output_dir: pathlib.Path,
    pattern: str = "*.json",
    force: bool = False,
    verbose: bool = False
) -> Dict[str, Any]:
    """Migrate all JSON files in a directory.
    
    Returns:
        Migration summary statistics
    """
    if not input_dir.exists() or not input_dir.is_dir():
        raise NotADirectoryError(f"Input directory not found: {input_dir}")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Find all JSON files
    json_files = list(input_dir.glob(pattern))
    if not json_files:
        return {
            "total_files": 0,
            "migrated": 0,
            "skipped": 0,
            "errors": 0,
            "files_processed": []
        }
    
    results = {
        "total_files": len(json_files),
        "migrated": 0,
        "skipped": 0,
        "errors": 0,
        "version_counts": {},
        "files_processed": []
    }
    
    for i, input_file in enumerate(json_files, 1):
        if verbose:
            print(f"[{i}/{len(json_files)}] Processing {input_file.name}...")
        
        # Determine output path
        output_file = output_dir / input_file.name
        
        # Process file
        file_result = process_single_file(input_file, output_file, force)
        results["files_processed"].append(file_result)
        
        # Update counters
        if file_result["status"] == "migrated":
            results["migrated"] += 1
            from_version = file_result.get("from_version", "unknown")
            results["version_counts"][from_version] = results["version_counts"].get(from_version, 0) + 1
        elif file_result["status"] == "skipped":
            results["skipped"] += 1
        elif file_result["status"] == "error":
            results["errors"] += 1
            if verbose:
                print(f"  ERROR: {file_result['error']}")
    
    return results


def generate_migration_report(
    results: Dict[str, Any],
    output_path: pathlib.Path
) -> None:
    """Generate a migration report file."""
    report = {
        "migration_summary": {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "total_files": results["total_files"],
            "successful_migrations": results["migrated"],
            "skipped_files": results["skipped"],
            "failed_migrations": results["errors"],
            "version_breakdown": results.get("version_counts", {})
        },
        "file_details": results["files_processed"]
    }
    
    save_json_file(output_path, report)


def main():
    """Main migration script entry point."""
    parser = argparse.ArgumentParser(
        description="Migrate ECG reports from legacy versions to v0.4 schema",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Migrate single file
  python migrate_reports.py --in report.json --out report_v04.json
  
  # Migrate directory
  python migrate_reports.py --in legacy_reports/ --out migrated_reports/
  
  # Force overwrite existing files
  python migrate_reports.py --in reports/ --out migrated/ --force
  
  # Generate migration report
  python migrate_reports.py --in reports/ --out migrated/ --report migration_log.json
        """
    )
    
    parser.add_argument(
        "--in", "--input",
        dest="input_path",
        type=str,
        required=True,
        help="Input file or directory path"
    )
    
    parser.add_argument(
        "--out", "--output",
        dest="output_path",
        type=str,
        required=True,
        help="Output file or directory path"
    )
    
    parser.add_argument(
        "--pattern",
        type=str,
        default="*.json",
        help="File pattern for directory processing (default: *.json)"
    )
    
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing output files"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    
    parser.add_argument(
        "--report",
        type=str,
        help="Generate migration report at specified path"
    )
    
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate migrated files can be loaded"
    )
    
    args = parser.parse_args()
    
    # Convert to Path objects
    input_path = pathlib.Path(args.input_path)
    output_path = pathlib.Path(args.output_path)
    
    try:
        if input_path.is_file():
            # Single file migration
            if args.verbose:
                print(f"Migrating single file: {input_path} -> {output_path}")
            
            result = process_single_file(input_path, output_path, args.force)
            
            if result["status"] == "migrated":
                print(f"✅ Successfully migrated {input_path.name}")
                print(f"   From: {result['from_version']}")
                print(f"   To: {result['to_version']}")
                print(f"   Capabilities: {result['capabilities_count']}")
            elif result["status"] == "skipped":
                print(f"⏭️  Skipped {input_path.name} (output exists, use --force to overwrite)")
            elif result["status"] == "error":
                print(f"❌ Failed to migrate {input_path.name}: {result['error']}")
                sys.exit(1)
            
            # Single file report
            if args.report:
                report_results = {
                    "total_files": 1,
                    "migrated": 1 if result["status"] == "migrated" else 0,
                    "skipped": 1 if result["status"] == "skipped" else 0,
                    "errors": 1 if result["status"] == "error" else 0,
                    "files_processed": [result]
                }
                generate_migration_report(report_results, pathlib.Path(args.report))
                print(f"📋 Migration report saved to {args.report}")
        
        elif input_path.is_dir():
            # Directory migration
            if args.verbose:
                print(f"Migrating directory: {input_path} -> {output_path}")
                print(f"Pattern: {args.pattern}")
            
            results = migrate_directory(
                input_path,
                output_path,
                args.pattern,
                args.force,
                args.verbose
            )
            
            # Print summary
            print(f"\n📊 Migration Summary:")
            print(f"   Total files: {results['total_files']}")
            print(f"   ✅ Migrated: {results['migrated']}")
            print(f"   ⏭️  Skipped: {results['skipped']}")
            print(f"   ❌ Errors: {results['errors']}")
            
            if results.get("version_counts"):
                print(f"\n📈 Version breakdown:")
                for version, count in results["version_counts"].items():
                    print(f"   {version}: {count} files")
            
            # Generate report if requested
            if args.report:
                generate_migration_report(results, pathlib.Path(args.report))
                print(f"\n📋 Detailed migration report saved to {args.report}")
            
            # Validation if requested
            if args.validate and results["migrated"] > 0:
                print(f"\n🔍 Validating migrated files...")
                validation_errors = 0
                
                for file_info in results["files_processed"]:
                    if file_info["status"] == "migrated":
                        try:
                            migrated_file = pathlib.Path(file_info["output_file"])
                            with open(migrated_file, 'r') as f:
                                json.load(f)  # Just check it can be loaded
                        except Exception as e:
                            print(f"   ❌ Validation failed for {migrated_file.name}: {e}")
                            validation_errors += 1
                
                if validation_errors == 0:
                    print(f"   ✅ All {results['migrated']} migrated files validated successfully")
                else:
                    print(f"   ❌ {validation_errors} files failed validation")
            
            # Exit with error if any files failed
            if results["errors"] > 0:
                sys.exit(1)
        
        else:
            print(f"❌ Input path does not exist: {input_path}")
            sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n⏹️  Migration interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
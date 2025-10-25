"""Test schema migration from legacy formats to v0.4."""

from __future__ import annotations
import json
import tempfile
import pathlib
from typing import Dict, Any
import pytest


def create_v01_report() -> Dict[str, Any]:
    """Create a v0.1 format report for testing."""
    return {
        "version": "v0.1",
        "timestamp": "2024-01-15T10:30:00Z",
        "image_info": {
            "filename": "ecg_001.png",
            "width": 800,
            "height": 600
        },
        "measurements": {
            "pr_ms": 160,
            "qrs_ms": 90,
            "qt_ms": 380,
            "qtc_bazett": 420
        },
        "interpretation": {
            "rhythm": "sinus_rhythm",
            "heart_rate": 75
        }
    }


def create_v02_report() -> Dict[str, Any]:
    """Create a v0.2 format report for testing."""
    return {
        "version": "v0.2",
        "timestamp": "2024-01-15T10:30:00Z",
        "metadata": {
            "image_file": "ecg_002.png",
            "dimensions": {"width": 1024, "height": 768},
            "processing_time_ms": 1250
        },
        "intervals": {
            "pr_interval_ms": 165,
            "qrs_duration_ms": 85,
            "qt_interval_ms": 390,
            "qtc_bazett_ms": 425,
            "qtc_fridericia_ms": 410
        },
        "axis": {
            "frontal_axis_degrees": 45,
            "axis_classification": "normal"
        },
        "findings": [
            "Normal sinus rhythm",
            "Normal QTc interval"
        ]
    }


def create_v03_report() -> Dict[str, Any]:
    """Create a v0.3 format report for testing."""
    return {
        "version": "v0.3",
        "generated_at": "2024-01-15T10:30:00Z",
        "ecg_analysis": {
            "image_metadata": {
                "source_file": "ecg_003.png",
                "resolution": {"width": 1200, "height": 900},
                "grid_detected": True,
                "grid_spacing_mm": 1.0
            },
            "rhythm_analysis": {
                "rhythm_type": "sinus_rhythm",
                "ventricular_rate_bpm": 78,
                "atrial_rate_bpm": 78,
                "regularity": "regular"
            },
            "interval_measurements": {
                "pr_ms": 158,
                "qrs_ms": 92,
                "qt_ms": 385,
                "qtc_bazett_ms": 422,
                "qtc_fridericia_ms": 408,
                "rr_ms": 769
            },
            "morphology": {
                "frontal_axis": {
                    "angle_degrees": 52,
                    "classification": "normal",
                    "lead_i_mv": 0.8,
                    "avf_mv": 1.2
                },
                "qrs_morphology": {
                    "dominant_r_wave_lead": "V4",
                    "q_waves": []
                }
            },
            "clinical_flags": [
                "Normal ECG",
                "No significant abnormalities detected"
            ]
        }
    }


def migrate_v01_to_v04(v01_report: Dict[str, Any]) -> Dict[str, Any]:
    """Migrate v0.1 report to v0.4 format."""
    measurements = v01_report.get("measurements", {})
    interpretation = v01_report.get("interpretation", {})
    image_info = v01_report.get("image_info", {})
    
    # Infer capabilities from available data
    capabilities = []
    if measurements.get("pr_ms") is not None:
        capabilities.append("pr_interval")
    if measurements.get("qrs_ms") is not None:
        capabilities.append("qrs_duration")
    if measurements.get("qt_ms") is not None:
        capabilities.append("qt_interval")
        capabilities.append("qtc_calculation")
    if interpretation.get("rhythm") is not None:
        capabilities.append("rhythm_analysis")
    if interpretation.get("heart_rate") is not None:
        capabilities.append("heart_rate")
    
    v04_report = {
        "schema_version": "v0.4",
        "generated_at": v01_report.get("timestamp", "1970-01-01T00:00:00Z"),
        "capabilities": capabilities,
        "metadata": {
            "source_image": image_info.get("filename", "unknown.png"),
            "image_dimensions": {
                "width": image_info.get("width", 0),
                "height": image_info.get("height", 0)
            },
            "processing_info": {
                "migration_from": "v0.1",
                "migrated_at": "2024-01-15T12:00:00Z"
            }
        },
        "measurements": {
            "intervals": {
                "pr_ms": measurements.get("pr_ms"),
                "qrs_ms": measurements.get("qrs_ms"),
                "qt_ms": measurements.get("qt_ms"),
                "rr_ms": None,  # Not available in v0.1
                "qtc_bazett_ms": measurements.get("qtc_bazett"),
                "qtc_fridericia_ms": None  # Not available in v0.1
            },
            "rhythm": {
                "type": interpretation.get("rhythm"),
                "rate_bpm": interpretation.get("heart_rate"),
                "regularity": None  # Not available in v0.1
            },
            "axis": {
                "frontal_angle_degrees": None,  # Not available in v0.1
                "classification": None
            }
        },
        "clinical_interpretation": {
            "primary_rhythm": interpretation.get("rhythm", "unknown"),
            "clinical_flags": [],
            "automated_interpretation": f"Migrated from v0.1: {interpretation.get('rhythm', 'unknown')} at {interpretation.get('heart_rate', 'unknown')} bpm"
        }
    }
    
    return v04_report


def migrate_v02_to_v04(v02_report: Dict[str, Any]) -> Dict[str, Any]:
    """Migrate v0.2 report to v0.4 format."""
    intervals = v02_report.get("intervals", {})
    axis = v02_report.get("axis", {})
    metadata = v02_report.get("metadata", {})
    findings = v02_report.get("findings", [])
    
    # Infer capabilities
    capabilities = []
    if intervals.get("pr_interval_ms") is not None:
        capabilities.append("pr_interval")
    if intervals.get("qrs_duration_ms") is not None:
        capabilities.append("qrs_duration")
    if intervals.get("qt_interval_ms") is not None:
        capabilities.append("qt_interval")
        capabilities.append("qtc_calculation")
    if axis.get("frontal_axis_degrees") is not None:
        capabilities.append("axis_calculation")
    
    v04_report = {
        "schema_version": "v0.4",
        "generated_at": v02_report.get("timestamp", "1970-01-01T00:00:00Z"),
        "capabilities": capabilities,
        "metadata": {
            "source_image": metadata.get("image_file", "unknown.png"),
            "image_dimensions": {
                "width": metadata.get("dimensions", {}).get("width", 0),
                "height": metadata.get("dimensions", {}).get("height", 0)
            },
            "processing_info": {
                "migration_from": "v0.2",
                "migrated_at": "2024-01-15T12:00:00Z",
                "original_processing_time_ms": metadata.get("processing_time_ms")
            }
        },
        "measurements": {
            "intervals": {
                "pr_ms": intervals.get("pr_interval_ms"),
                "qrs_ms": intervals.get("qrs_duration_ms"),
                "qt_ms": intervals.get("qt_interval_ms"),
                "rr_ms": None,  # Not available in v0.2
                "qtc_bazett_ms": intervals.get("qtc_bazett_ms"),
                "qtc_fridericia_ms": intervals.get("qtc_fridericia_ms")
            },
            "rhythm": {
                "type": None,  # Not explicitly available in v0.2
                "rate_bpm": None,  # Not available in v0.2
                "regularity": None
            },
            "axis": {
                "frontal_angle_degrees": axis.get("frontal_axis_degrees"),
                "classification": axis.get("axis_classification")
            }
        },
        "clinical_interpretation": {
            "primary_rhythm": "unknown",
            "clinical_flags": findings,
            "automated_interpretation": f"Migrated from v0.2. Findings: {', '.join(findings) if findings else 'None'}"
        }
    }
    
    return v04_report


def migrate_v03_to_v04(v03_report: Dict[str, Any]) -> Dict[str, Any]:
    """Migrate v0.3 report to v0.4 format."""
    ecg_analysis = v03_report.get("ecg_analysis", {})
    image_meta = ecg_analysis.get("image_metadata", {})
    rhythm = ecg_analysis.get("rhythm_analysis", {})
    intervals = ecg_analysis.get("interval_measurements", {})
    morphology = ecg_analysis.get("morphology", {})
    flags = ecg_analysis.get("clinical_flags", [])
    
    # Infer capabilities from v0.3 data
    capabilities = []
    if intervals.get("pr_ms") is not None:
        capabilities.append("pr_interval")
    if intervals.get("qrs_ms") is not None:
        capabilities.append("qrs_duration")
    if intervals.get("qt_ms") is not None:
        capabilities.append("qt_interval")
        capabilities.append("qtc_calculation")
    if rhythm.get("rhythm_type") is not None:
        capabilities.append("rhythm_analysis")
    if rhythm.get("ventricular_rate_bpm") is not None:
        capabilities.append("heart_rate")
    if morphology.get("frontal_axis") is not None:
        capabilities.append("axis_calculation")
    
    v04_report = {
        "schema_version": "v0.4",
        "generated_at": v03_report.get("generated_at", "1970-01-01T00:00:00Z"),
        "capabilities": capabilities,
        "metadata": {
            "source_image": image_meta.get("source_file", "unknown.png"),
            "image_dimensions": {
                "width": image_meta.get("resolution", {}).get("width", 0),
                "height": image_meta.get("resolution", {}).get("height", 0)
            },
            "processing_info": {
                "migration_from": "v0.3",
                "migrated_at": "2024-01-15T12:00:00Z",
                "grid_detected": image_meta.get("grid_detected"),
                "grid_spacing_mm": image_meta.get("grid_spacing_mm")
            }
        },
        "measurements": {
            "intervals": {
                "pr_ms": intervals.get("pr_ms"),
                "qrs_ms": intervals.get("qrs_ms"),
                "qt_ms": intervals.get("qt_ms"),
                "rr_ms": intervals.get("rr_ms"),
                "qtc_bazett_ms": intervals.get("qtc_bazett_ms"),
                "qtc_fridericia_ms": intervals.get("qtc_fridericia_ms")
            },
            "rhythm": {
                "type": rhythm.get("rhythm_type"),
                "rate_bpm": rhythm.get("ventricular_rate_bpm"),
                "regularity": rhythm.get("regularity")
            },
            "axis": {
                "frontal_angle_degrees": morphology.get("frontal_axis", {}).get("angle_degrees"),
                "classification": morphology.get("frontal_axis", {}).get("classification")
            }
        },
        "clinical_interpretation": {
            "primary_rhythm": rhythm.get("rhythm_type", "unknown"),
            "clinical_flags": flags,
            "automated_interpretation": f"Migrated from v0.3. Primary rhythm: {rhythm.get('rhythm_type', 'unknown')}"
        }
    }
    
    return v04_report


def migrate_report_to_v04(report: Dict[str, Any]) -> Dict[str, Any]:
    """Migrate report from any version to v0.4."""
    version = report.get("version") or report.get("schema_version")
    
    if version == "v0.1":
        return migrate_v01_to_v04(report)
    elif version == "v0.2":
        return migrate_v02_to_v04(report)
    elif version == "v0.3":
        return migrate_v03_to_v04(report)
    elif version == "v0.4":
        # Already v0.4, ensure capabilities field exists
        if "capabilities" not in report:
            report["capabilities"] = infer_capabilities_from_v04(report)
        return report
    else:
        raise ValueError(f"Unknown or unsupported version: {version}")


def infer_capabilities_from_v04(v04_report: Dict[str, Any]) -> list[str]:
    """Infer capabilities from a v0.4 report structure."""
    capabilities = []
    measurements = v04_report.get("measurements", {})
    
    intervals = measurements.get("intervals", {})
    if intervals.get("pr_ms") is not None:
        capabilities.append("pr_interval")
    if intervals.get("qrs_ms") is not None:
        capabilities.append("qrs_duration")
    if intervals.get("qt_ms") is not None:
        capabilities.append("qt_interval")
    if intervals.get("qtc_bazett_ms") is not None or intervals.get("qtc_fridericia_ms") is not None:
        capabilities.append("qtc_calculation")
    
    rhythm = measurements.get("rhythm", {})
    if rhythm.get("type") is not None:
        capabilities.append("rhythm_analysis")
    if rhythm.get("rate_bpm") is not None:
        capabilities.append("heart_rate")
    
    axis = measurements.get("axis", {})
    if axis.get("frontal_angle_degrees") is not None:
        capabilities.append("axis_calculation")
    
    return capabilities


class TestMigration:
    """Test suite for schema migration functionality."""
    
    def test_v01_to_v04_migration(self):
        """Test migration from v0.1 to v0.4."""
        v01_report = create_v01_report()
        v04_report = migrate_v01_to_v04(v01_report)
        
        # Check schema version
        assert v04_report["schema_version"] == "v0.4"
        
        # Check capabilities inference
        capabilities = v04_report["capabilities"]
        assert "pr_interval" in capabilities
        assert "qrs_duration" in capabilities
        assert "qt_interval" in capabilities
        assert "qtc_calculation" in capabilities
        assert "rhythm_analysis" in capabilities
        assert "heart_rate" in capabilities
        
        # Check data mapping
        assert v04_report["metadata"]["source_image"] == "ecg_001.png"
        assert v04_report["measurements"]["intervals"]["pr_ms"] == 160
        assert v04_report["measurements"]["intervals"]["qrs_ms"] == 90
        assert v04_report["measurements"]["intervals"]["qt_ms"] == 380
        assert v04_report["measurements"]["intervals"]["qtc_bazett_ms"] == 420
        assert v04_report["measurements"]["rhythm"]["type"] == "sinus_rhythm"
        assert v04_report["measurements"]["rhythm"]["rate_bpm"] == 75
    
    def test_v02_to_v04_migration(self):
        """Test migration from v0.2 to v0.4."""
        v02_report = create_v02_report()
        v04_report = migrate_v02_to_v04(v02_report)
        
        # Check schema version
        assert v04_report["schema_version"] == "v0.4"
        
        # Check capabilities
        capabilities = v04_report["capabilities"]
        assert "pr_interval" in capabilities
        assert "qrs_duration" in capabilities
        assert "qt_interval" in capabilities
        assert "qtc_calculation" in capabilities
        assert "axis_calculation" in capabilities
        
        # Check data mapping
        assert v04_report["metadata"]["source_image"] == "ecg_002.png"
        assert v04_report["measurements"]["intervals"]["pr_ms"] == 165
        assert v04_report["measurements"]["intervals"]["qrs_ms"] == 85
        assert v04_report["measurements"]["intervals"]["qtc_fridericia_ms"] == 410
        assert v04_report["measurements"]["axis"]["frontal_angle_degrees"] == 45
        assert v04_report["measurements"]["axis"]["classification"] == "normal"
        assert v04_report["clinical_interpretation"]["clinical_flags"] == ["Normal sinus rhythm", "Normal QTc interval"]
    
    def test_v03_to_v04_migration(self):
        """Test migration from v0.3 to v0.4."""
        v03_report = create_v03_report()
        v04_report = migrate_v03_to_v04(v03_report)
        
        # Check schema version
        assert v04_report["schema_version"] == "v0.4"
        
        # Check comprehensive capabilities
        capabilities = v04_report["capabilities"]
        assert "pr_interval" in capabilities
        assert "qrs_duration" in capabilities
        assert "qt_interval" in capabilities
        assert "qtc_calculation" in capabilities
        assert "rhythm_analysis" in capabilities
        assert "heart_rate" in capabilities
        assert "axis_calculation" in capabilities
        
        # Check complete data mapping
        assert v04_report["metadata"]["source_image"] == "ecg_003.png"
        assert v04_report["measurements"]["intervals"]["rr_ms"] == 769
        assert v04_report["measurements"]["rhythm"]["type"] == "sinus_rhythm"
        assert v04_report["measurements"]["rhythm"]["rate_bpm"] == 78
        assert v04_report["measurements"]["rhythm"]["regularity"] == "regular"
        assert v04_report["measurements"]["axis"]["frontal_angle_degrees"] == 52
        assert v04_report["clinical_interpretation"]["primary_rhythm"] == "sinus_rhythm"
    
    def test_generic_migration_function(self):
        """Test generic migration function with different versions."""
        # Test v0.1
        v01_report = create_v01_report()
        migrated = migrate_report_to_v04(v01_report)
        assert migrated["schema_version"] == "v0.4"
        assert "capabilities" in migrated
        
        # Test v0.2
        v02_report = create_v02_report()
        migrated = migrate_report_to_v04(v02_report)
        assert migrated["schema_version"] == "v0.4"
        assert "capabilities" in migrated
        
        # Test v0.3
        v03_report = create_v03_report()
        migrated = migrate_report_to_v04(v03_report)
        assert migrated["schema_version"] == "v0.4"
        assert "capabilities" in migrated
    
    def test_v04_passthrough(self):
        """Test that v0.4 reports pass through unchanged (except capabilities)."""
        v04_report = {
            "schema_version": "v0.4",
            "generated_at": "2024-01-15T10:30:00Z",
            "metadata": {"source_image": "test.png"},
            "measurements": {
                "intervals": {"pr_ms": 160, "qt_ms": 400},
                "rhythm": {"type": "sinus_rhythm", "rate_bpm": 75}
            }
        }
        
        migrated = migrate_report_to_v04(v04_report)
        
        # Should be essentially the same but with capabilities added
        assert migrated["schema_version"] == "v0.4"
        assert "capabilities" in migrated
        assert "pr_interval" in migrated["capabilities"]
        assert "qt_interval" in migrated["capabilities"]
        assert "rhythm_analysis" in migrated["capabilities"]
        assert "heart_rate" in migrated["capabilities"]
    
    def test_capabilities_inference(self):
        """Test capabilities inference logic."""
        # Minimal report
        minimal_report = {
            "schema_version": "v0.4",
            "measurements": {
                "intervals": {"pr_ms": 150},
                "rhythm": {},
                "axis": {}
            }
        }
        
        capabilities = infer_capabilities_from_v04(minimal_report)
        assert capabilities == ["pr_interval"]
        
        # Complete report
        complete_report = {
            "schema_version": "v0.4",
            "measurements": {
                "intervals": {
                    "pr_ms": 160,
                    "qrs_ms": 90,
                    "qt_ms": 400,
                    "qtc_bazett_ms": 420
                },
                "rhythm": {
                    "type": "sinus_rhythm",
                    "rate_bpm": 75
                },
                "axis": {
                    "frontal_angle_degrees": 45
                }
            }
        }
        
        capabilities = infer_capabilities_from_v04(complete_report)
        expected_caps = ["pr_interval", "qrs_duration", "qt_interval", "qtc_calculation", 
                        "rhythm_analysis", "heart_rate", "axis_calculation"]
        for cap in expected_caps:
            assert cap in capabilities
    
    def test_migration_with_missing_data(self):
        """Test migration handles missing or incomplete data gracefully."""
        # Incomplete v0.1 report
        incomplete_v01 = {
            "version": "v0.1",
            "measurements": {"pr_ms": 160},  # Missing other fields
            "interpretation": {}  # Empty
        }
        
        migrated = migrate_v01_to_v04(incomplete_v01)
        assert migrated["schema_version"] == "v0.4"
        assert migrated["capabilities"] == ["pr_interval"]
        assert migrated["measurements"]["intervals"]["pr_ms"] == 160
        assert migrated["measurements"]["intervals"]["qt_ms"] is None
    
    def test_invalid_version_handling(self):
        """Test handling of invalid or unknown versions."""
        invalid_report = {
            "version": "v99.invalid",
            "data": "test"
        }
        
        with pytest.raises(ValueError, match="Unknown or unsupported version"):
            migrate_report_to_v04(invalid_report)
    
    def test_migration_preserves_timestamps(self):
        """Test that original timestamps are preserved in migration."""
        original_time = "2024-01-15T08:45:30Z"
        
        v01_report = create_v01_report()
        v01_report["timestamp"] = original_time
        
        migrated = migrate_v01_to_v04(v01_report)
        assert migrated["generated_at"] == original_time
        
        # Check migration timestamp is added
        assert "migrated_at" in migrated["metadata"]["processing_info"]
    
    def test_file_based_migration(self):
        """Test migration of actual JSON files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            
            # Create test files
            v01_file = temp_path / "report_v01.json"
            v02_file = temp_path / "report_v02.json"
            
            with open(v01_file, 'w') as f:
                json.dump(create_v01_report(), f)
            
            with open(v02_file, 'w') as f:
                json.dump(create_v02_report(), f)
            
            # Load and migrate
            with open(v01_file, 'r') as f:
                v01_data = json.load(f)
            
            migrated_v01 = migrate_report_to_v04(v01_data)
            assert migrated_v01["schema_version"] == "v0.4"
            
            # Save migrated version
            migrated_file = temp_path / "migrated_v01.json"
            with open(migrated_file, 'w') as f:
                json.dump(migrated_v01, f, indent=2)
            
            # Verify it can be loaded back
            with open(migrated_file, 'r') as f:
                reloaded = json.load(f)
            
            assert reloaded["schema_version"] == "v0.4"
            assert "capabilities" in reloaded


if __name__ == "__main__":
    pytest.main([__file__])
"""
FHIR Stub Exporter for ECG Reports

Creates educational FHIR Bundle structures for ECG reports.
This is for educational purposes only and should not be used for clinical decisions.
"""

import uuid
from datetime import datetime
from typing import Any, Dict


def report_to_fhir(report: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert an ECG report to a FHIR Bundle stub.

    Args:
        report: ECG report dictionary

    Returns:
        FHIR Bundle dictionary structure

    Note:
        This is an educational stub and should not be used for clinical purposes.
    """
    # Generate bundle ID
    bundle_id = str(uuid.uuid4())

    # Extract report ID from meta if available
    report_id = report.get("meta", {}).get("id", f"ecg-{bundle_id[:8]}")

    bundle = {
        "resourceType": "Bundle",
        "id": bundle_id,
        "meta": {
            "profile": ["https://example.org/fhir/profiles/educational-ecg-bundle"],
            "tag": [
                {
                    "system": "https://example.org/fhir/tags",
                    "code": "educational-only",
                    "display": "Educational Use Only - Not for Clinical Decisions",
                }
            ],
        },
        "type": "document",
        "timestamp": datetime.now().isoformat() + "Z",
        "entry": [],
    }

    # Add observations based on available data
    measures = report.get("measures", {})
    intervals_refined = report.get("intervals_refined", {})
    median = intervals_refined.get("median", {}) if intervals_refined else {}
    axis = report.get("axis", {})
    flags = report.get("flags", [])

    entry_count = 0

    # Heart Rate Observation
    if measures.get("fc_bpm") or measures.get("rr_ms"):
        hr = measures.get("fc_bpm") or (
            60000.0 / measures.get("rr_ms") if measures.get("rr_ms") else None
        )
        if hr:
            entry_count += 1
            hr_observation = {
                "resource": {
                    "resourceType": "Observation",
                    "id": f"hr-{report_id}-{entry_count}",
                    "status": "final",
                    "code": {
                        "coding": [
                            {
                                "system": "http://loinc.org",
                                "code": "8867-4",
                                "display": "Heart rate",
                            }
                        ],
                        "text": "Heart Rate",
                    },
                    "valueQuantity": {
                        "value": round(hr, 1),
                        "unit": "beats/min",
                        "system": "http://unitsofmeasure.org",
                        "code": "/min",
                    },
                    "effectiveDateTime": datetime.now().isoformat() + "Z",
                }
            }
            bundle["entry"].append(hr_observation)

    # QTc Observation
    if median.get("QTc_B") or median.get("QTc_F"):
        qtc_value = median.get("QTc_B") or median.get("QTc_F")
        if qtc_value:
            entry_count += 1
            qtc_observation = {
                "resource": {
                    "resourceType": "Observation",
                    "id": f"qtc-{report_id}-{entry_count}",
                    "status": "final",
                    "code": {
                        "coding": [
                            {
                                "system": "http://loinc.org",
                                "code": "8634-8",
                                "display": "QT corrected",
                            }
                        ],
                        "text": "QT Corrected",
                    },
                    "valueQuantity": {
                        "value": qtc_value,
                        "unit": "ms",
                        "system": "http://unitsofmeasure.org",
                        "code": "ms",
                    },
                    "effectiveDateTime": datetime.now().isoformat() + "Z",
                    "note": [
                        {
                            "text": f"Formula used: {'Bazett' if median.get('QTc_B') else 'Fridericia'}"
                        }
                    ],
                }
            }
            bundle["entry"].append(qtc_observation)

    # QRS Duration Observation
    if median.get("QRS_ms"):
        entry_count += 1
        qrs_observation = {
            "resource": {
                "resourceType": "Observation",
                "id": f"qrs-{report_id}-{entry_count}",
                "status": "final",
                "code": {
                    "coding": [
                        {"system": "http://loinc.org", "code": "8633-0", "display": "QRS duration"}
                    ],
                    "text": "QRS Duration",
                },
                "valueQuantity": {
                    "value": median.get("QRS_ms"),
                    "unit": "ms",
                    "system": "http://unitsofmeasure.org",
                    "code": "ms",
                },
                "effectiveDateTime": datetime.now().isoformat() + "Z",
            }
        }
        bundle["entry"].append(qrs_observation)

    # Cardiac Axis Observation (if present)
    if axis.get("angle_deg") is not None and axis.get("label"):
        entry_count += 1
        axis_observation = {
            "resource": {
                "resourceType": "Observation",
                "id": f"axis-{report_id}-{entry_count}",
                "status": "final",
                "code": {
                    "coding": [
                        {
                            "system": "http://snomed.info/sct",
                            "code": "251208008",
                            "display": "Cardiac axis",
                        }
                    ],
                    "text": "Cardiac Axis",
                },
                "valueQuantity": {
                    "value": axis.get("angle_deg"),
                    "unit": "deg",
                    "system": "http://unitsofmeasure.org",
                    "code": "deg",
                },
                "effectiveDateTime": datetime.now().isoformat() + "Z",
                "interpretation": [{"text": axis.get("label")}],
            }
        }
        bundle["entry"].append(axis_observation)

    # Flags Observation (combined as text)
    if flags:
        entry_count += 1
        flags_observation = {
            "resource": {
                "resourceType": "Observation",
                "id": f"flags-{report_id}-{entry_count}",
                "status": "final",
                "code": {"text": "ECG Flags"},
                "valueString": "; ".join(flags),
                "effectiveDateTime": datetime.now().isoformat() + "Z",
            }
        }
        bundle["entry"].append(flags_observation)

    return bundle

"""FHIR R4 export for ECG reports.

Converts ECG report dicts to FHIR Observation and DiagnosticReport resources.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

FHIR_LOINC_CODES: dict[str, str] = {
    "heart_rate": "8867-4",
    "pr_interval": "8625-6",
    "qrs_duration": "8633-0",
    "qt_interval": "8634-8",
    "qtc_interval": "8636-3",
    "frontal_axis": "8632-2",
}

_MEASUREMENT_MAP = {
    "heart_rate": {"unit": "/min", "system": "http://unitsofmeasure.org", "code": "/min"},
    "pr_interval": {"unit": "ms", "system": "http://unitsofmeasure.org", "code": "ms"},
    "qrs_duration": {"unit": "ms", "system": "http://unitsofmeasure.org", "code": "ms"},
    "qt_interval": {"unit": "ms", "system": "http://unitsofmeasure.org", "code": "ms"},
    "qtc_interval": {"unit": "ms", "system": "http://unitsofmeasure.org", "code": "ms"},
    "frontal_axis": {"unit": "deg", "system": "http://unitsofmeasure.org", "code": "deg"},
}


def _extract_measurements(report: dict) -> dict[str, float | None]:
    """Extract standard ECG measurements from report dict."""
    iv = (report.get("intervals_refined") or report.get("intervals") or {}).get("median", {})
    axis = report.get("axis") or {}
    rr = iv.get("RR_s")
    hr = round(60.0 / rr) if rr and rr > 0 else None

    return {
        "heart_rate": hr,
        "pr_interval": iv.get("PR_ms"),
        "qrs_duration": iv.get("QRS_ms"),
        "qt_interval": iv.get("QT_ms"),
        "qtc_interval": iv.get("QTc_B"),
        "frontal_axis": axis.get("angle_deg"),
    }


def _make_observation(
    measurement_key: str,
    value: float,
    patient_id: str | None = None,
) -> dict:
    """Create a single FHIR Observation resource for one measurement."""
    loinc = FHIR_LOINC_CODES[measurement_key]
    unit_info = _MEASUREMENT_MAP[measurement_key]
    obs_id = str(uuid.uuid4())

    obs: dict = {
        "resourceType": "Observation",
        "id": obs_id,
        "status": "final",
        "category": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                        "code": "procedure",
                        "display": "Procedure",
                    }
                ]
            }
        ],
        "code": {
            "coding": [
                {
                    "system": "http://loinc.org",
                    "code": loinc,
                    "display": measurement_key.replace("_", " ").title(),
                }
            ],
            "text": measurement_key.replace("_", " ").title(),
        },
        "valueQuantity": {
            "value": value,
            "unit": unit_info["unit"],
            "system": unit_info["system"],
            "code": unit_info["code"],
        },
        "effectiveDateTime": datetime.now(timezone.utc).isoformat(),
    }

    if patient_id:
        obs["subject"] = {"reference": f"Patient/{patient_id}"}

    return obs


def report_to_fhir_observation(report: dict, patient_id: str | None = None) -> dict:
    """Convert ECG report to a FHIR Observation resource (Bundle of observations).

    Returns a FHIR Bundle containing one Observation per available measurement.
    """
    measurements = _extract_measurements(report)
    entries = []

    for key, value in measurements.items():
        if value is None:
            continue
        obs = _make_observation(key, value, patient_id)
        entries.append({
            "fullUrl": f"urn:uuid:{obs['id']}",
            "resource": obs,
        })

    bundle = {
        "resourceType": "Bundle",
        "id": str(uuid.uuid4()),
        "type": "collection",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "entry": entries,
    }

    return bundle


def report_to_fhir_diagnostic_report(report: dict, patient_id: str | None = None) -> dict:
    """Convert ECG report to a full FHIR DiagnosticReport with contained Observations.

    The DiagnosticReport contains all individual Observation resources and
    includes interpretation text from the report flags.
    """
    measurements = _extract_measurements(report)
    contained = []
    result_refs = []

    for key, value in measurements.items():
        if value is None:
            continue
        obs = _make_observation(key, value, patient_id)
        contained.append(obs)
        result_refs.append({"reference": f"#{obs['id']}"})

    flags = report.get("flags", [])
    conclusion = "; ".join(flags) if flags else "No significant findings."

    diag_id = str(uuid.uuid4())
    diag_report: dict = {
        "resourceType": "DiagnosticReport",
        "id": diag_id,
        "status": "final",
        "category": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/v2-0074",
                        "code": "CUS",
                        "display": "Cardiac Ultrasound",
                    }
                ]
            }
        ],
        "code": {
            "coding": [
                {
                    "system": "http://loinc.org",
                    "code": "11524-6",
                    "display": "EKG study",
                }
            ],
            "text": "ECG Report",
        },
        "effectiveDateTime": datetime.now(timezone.utc).isoformat(),
        "issued": datetime.now(timezone.utc).isoformat(),
        "conclusion": conclusion,
        "contained": contained,
        "result": result_refs,
    }

    if patient_id:
        diag_report["subject"] = {"reference": f"Patient/{patient_id}"}

    meta = report.get("meta", {})
    if meta:
        diag_report["presentedForm"] = [
            {
                "contentType": "application/json",
                "title": f"ECG source: {meta.get('src', 'unknown')}",
            }
        ]

    return diag_report


def validate_fhir_resource(resource: dict) -> list[str]:
    """Basic structural validation of a FHIR resource.

    Checks for required fields and correct types. Not a full FHIR validator,
    but catches common issues.

    Returns list of error strings (empty if valid).
    """
    errors: list[str] = []

    if not isinstance(resource, dict):
        errors.append("Resource must be a dict")
        return errors

    resource_type = resource.get("resourceType")
    if not resource_type:
        errors.append("Missing required field: resourceType")
        return errors

    if not isinstance(resource_type, str):
        errors.append("resourceType must be a string")

    if "id" not in resource:
        errors.append("Missing recommended field: id")

    if resource_type == "Observation":
        if "status" not in resource:
            errors.append("Observation missing required field: status")
        if "code" not in resource:
            errors.append("Observation missing required field: code")
        else:
            code = resource["code"]
            if not isinstance(code, dict):
                errors.append("Observation.code must be a dict")
            elif "coding" not in code and "text" not in code:
                errors.append("Observation.code must have coding or text")

        if "valueQuantity" in resource:
            vq = resource["valueQuantity"]
            if not isinstance(vq, dict):
                errors.append("valueQuantity must be a dict")
            elif "value" not in vq:
                errors.append("valueQuantity missing required field: value")

    elif resource_type == "DiagnosticReport":
        if "status" not in resource:
            errors.append("DiagnosticReport missing required field: status")
        if "code" not in resource:
            errors.append("DiagnosticReport missing required field: code")

    elif resource_type == "Bundle":
        if "type" not in resource:
            errors.append("Bundle missing required field: type")
        entries = resource.get("entry", [])
        if not isinstance(entries, list):
            errors.append("Bundle.entry must be a list")
        else:
            for i, entry in enumerate(entries):
                if not isinstance(entry, dict):
                    errors.append(f"Bundle.entry[{i}] must be a dict")
                elif "resource" not in entry:
                    errors.append(f"Bundle.entry[{i}] missing resource")

    return errors

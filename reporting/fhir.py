"""FHIR R4 export for ECG reports.

Converts ECG report dicts to FHIR Observation and DiagnosticReport resources
conformant with HL7 FHIR R4 specification.

References:
- Observation: https://www.hl7.org/fhir/R4/observation.html
- DiagnosticReport: https://www.hl7.org/fhir/R4/diagnosticreport.html
- ECG LOINC codes: https://loinc.org/search/?q=electrocardiogram
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

# Standard LOINC codes for ECG measurements
FHIR_LOINC_CODES: dict[str, str] = {
    "heart_rate": "8867-4",       # Heart rate
    "pr_interval": "8625-6",     # PR interval
    "qrs_duration": "8633-0",    # QRS duration
    "qt_interval": "8634-8",     # QT interval
    "qtc_interval": "8636-3",    # QTc interval (corrected)
    "frontal_axis": "8632-2",    # QRS axis
}

# LOINC code for 12-lead ECG study
_ECG_STUDY_LOINC = "11524-6"

_MEASUREMENT_MAP: dict[str, dict[str, str]] = {
    "heart_rate": {"unit": "/min", "system": "http://unitsofmeasure.org", "code": "/min"},
    "pr_interval": {"unit": "ms", "system": "http://unitsofmeasure.org", "code": "ms"},
    "qrs_duration": {"unit": "ms", "system": "http://unitsofmeasure.org", "code": "ms"},
    "qt_interval": {"unit": "ms", "system": "http://unitsofmeasure.org", "code": "ms"},
    "qtc_interval": {"unit": "ms", "system": "http://unitsofmeasure.org", "code": "ms"},
    "frontal_axis": {"unit": "deg", "system": "http://unitsofmeasure.org", "code": "deg"},
}

# Reference ranges for ECG measurements (adult)
_REFERENCE_RANGES: dict[str, dict[str, Any]] = {
    "heart_rate": {"low": 60, "high": 100, "unit": "/min"},
    "pr_interval": {"low": 120, "high": 200, "unit": "ms"},
    "qrs_duration": {"low": 60, "high": 120, "unit": "ms"},
    "qt_interval": {"low": 350, "high": 440, "unit": "ms"},
    "qtc_interval": {"low": 350, "high": 460, "unit": "ms"},
    "frontal_axis": {"low": -30, "high": 90, "unit": "deg"},
}

# Valid FHIR resource statuses
_VALID_OBSERVATION_STATUS = {
    "registered", "preliminary", "final", "amended",
    "corrected", "cancelled", "entered-in-error", "unknown",
}
_VALID_REPORT_STATUS = {
    "registered", "partial", "preliminary", "final",
    "amended", "corrected", "appended", "cancelled", "entered-in-error",
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
    performer_id: str | None = None,
    effective_dt: str | None = None,
) -> dict:
    """Create a single FHIR Observation resource for one ECG measurement."""
    loinc = FHIR_LOINC_CODES[measurement_key]
    unit_info = _MEASUREMENT_MAP[measurement_key]
    obs_id = str(uuid.uuid4())
    now = effective_dt or datetime.now(timezone.utc).isoformat()

    obs: dict = {
        "resourceType": "Observation",
        "id": obs_id,
        "status": "final",
        "category": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                        "code": "exam",
                        "display": "Exam",
                    }
                ],
                "text": "Exam",
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
        "effectiveDateTime": now,
    }

    # Subject reference
    if patient_id:
        obs["subject"] = {"reference": f"Patient/{patient_id}"}

    # Performer reference
    if performer_id:
        obs["performer"] = [{"reference": f"Practitioner/{performer_id}"}]

    # Reference range (if defined)
    ref = _REFERENCE_RANGES.get(measurement_key)
    if ref:
        obs["referenceRange"] = [
            {
                "low": {"value": ref["low"], "unit": ref["unit"]},
                "high": {"value": ref["high"], "unit": ref["unit"]},
                "text": f"{ref['low']}-{ref['high']} {ref['unit']}",
            }
        ]
        # Interpretation code
        if value < ref["low"]:
            obs["interpretation"] = [
                {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                             "code": "L", "display": "Low"}]}
            ]
        elif value > ref["high"]:
            obs["interpretation"] = [
                {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                             "code": "H", "display": "High"}]}
            ]
        else:
            obs["interpretation"] = [
                {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                             "code": "N", "display": "Normal"}]}
            ]

    return obs


def report_to_fhir_observation(
    report: dict,
    patient_id: str | None = None,
    performer_id: str | None = None,
) -> dict:
    """Convert ECG report to a FHIR Bundle of Observation resources.

    Returns a FHIR Bundle (type=collection) containing one Observation
    per available measurement, with LOINC codes and reference ranges.
    """
    measurements = _extract_measurements(report)
    effective_dt = datetime.now(timezone.utc).isoformat()
    entries = []

    for key, value in measurements.items():
        if value is None:
            continue
        obs = _make_observation(key, value, patient_id, performer_id, effective_dt)
        entries.append({
            "fullUrl": f"urn:uuid:{obs['id']}",
            "resource": obs,
        })

    bundle: dict = {
        "resourceType": "Bundle",
        "id": str(uuid.uuid4()),
        "type": "collection",
        "timestamp": effective_dt,
        "total": len(entries),
        "entry": entries,
    }

    return bundle


def report_to_fhir_diagnostic_report(
    report: dict,
    patient_id: str | None = None,
    performer_id: str | None = None,
) -> dict:
    """Convert ECG report to a full FHIR DiagnosticReport.

    The DiagnosticReport contains all individual Observation resources,
    includes interpretation text from the report flags, and uses
    correct FHIR R4 category codes for ECG.
    """
    measurements = _extract_measurements(report)
    effective_dt = datetime.now(timezone.utc).isoformat()
    contained: list[dict] = []
    result_refs: list[dict] = []

    for key, value in measurements.items():
        if value is None:
            continue
        obs = _make_observation(key, value, patient_id, performer_id, effective_dt)
        contained.append(obs)
        result_refs.append({"reference": f"#{obs['id']}"})

    flags = report.get("flags", [])
    conclusion = "; ".join(flags) if flags else "No significant findings."

    # Coded conclusion (SNOMED CT)
    conclusion_code: list[dict] = []
    for flag in flags:
        fl = flag.lower()
        if "sinusal" in fl and ("normal" in fl or "sem" in fl):
            conclusion_code.append({
                "coding": [{"system": "http://snomed.info/sct", "code": "426783006",
                            "display": "Normal sinus rhythm"}],
            })
        elif "taquicardia" in fl:
            conclusion_code.append({
                "coding": [{"system": "http://snomed.info/sct", "code": "3424008",
                            "display": "Tachycardia"}],
            })
        elif "bradicardia" in fl:
            conclusion_code.append({
                "coding": [{"system": "http://snomed.info/sct", "code": "48867003",
                            "display": "Bradycardia"}],
            })

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
                        "code": "EC",
                        "display": "Electrocardiac (e.g., EKG, ECG, Holter)",
                    }
                ],
                "text": "ECG",
            }
        ],
        "code": {
            "coding": [
                {
                    "system": "http://loinc.org",
                    "code": _ECG_STUDY_LOINC,
                    "display": "EKG study",
                }
            ],
            "text": "ECG Report",
        },
        "effectiveDateTime": effective_dt,
        "issued": effective_dt,
        "conclusion": conclusion,
        "contained": contained,
        "result": result_refs,
    }

    if conclusion_code:
        diag_report["conclusionCode"] = conclusion_code

    if patient_id:
        diag_report["subject"] = {"reference": f"Patient/{patient_id}"}

    if performer_id:
        diag_report["performer"] = [{"reference": f"Practitioner/{performer_id}"}]
        diag_report["resultsInterpreter"] = [{"reference": f"Practitioner/{performer_id}"}]

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
    """Structural validation of a FHIR resource.

    Checks required fields, correct types, value set membership,
    and reference format. Not a full FHIR validator, but catches
    common issues per the R4 specification.

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

    # --- Observation ---
    if resource_type == "Observation":
        if "status" not in resource:
            errors.append("Observation missing required field: status")
        elif resource["status"] not in _VALID_OBSERVATION_STATUS:
            errors.append(
                f"Observation.status '{resource['status']}' not in allowed values: "
                f"{_VALID_OBSERVATION_STATUS}"
            )

        if "code" not in resource:
            errors.append("Observation missing required field: code")
        else:
            code = resource["code"]
            if not isinstance(code, dict):
                errors.append("Observation.code must be a dict")
            elif "coding" not in code and "text" not in code:
                errors.append("Observation.code must have coding or text")
            elif "coding" in code:
                for i, c in enumerate(code["coding"]):
                    if "code" not in c:
                        errors.append(f"Observation.code.coding[{i}] missing 'code'")
                    if "system" not in c:
                        errors.append(f"Observation.code.coding[{i}] missing 'system'")

        if "valueQuantity" in resource:
            vq = resource["valueQuantity"]
            if not isinstance(vq, dict):
                errors.append("valueQuantity must be a dict")
            elif "value" not in vq:
                errors.append("valueQuantity missing required field: value")
            elif not isinstance(vq["value"], (int, float)):
                errors.append("valueQuantity.value must be numeric")

        # Validate category codes
        for cat in resource.get("category", []):
            for coding in cat.get("coding", []):
                if coding.get("code") == "procedure":
                    errors.append(
                        "Observation category 'procedure' is incorrect for ECG measurements; "
                        "use 'exam' or 'vital-signs'"
                    )

        # Validate referenceRange
        for i, rr in enumerate(resource.get("referenceRange", [])):
            if not isinstance(rr, dict):
                errors.append(f"referenceRange[{i}] must be a dict")

    # --- DiagnosticReport ---
    elif resource_type == "DiagnosticReport":
        if "status" not in resource:
            errors.append("DiagnosticReport missing required field: status")
        elif resource["status"] not in _VALID_REPORT_STATUS:
            errors.append(
                f"DiagnosticReport.status '{resource['status']}' not in allowed values"
            )

        if "code" not in resource:
            errors.append("DiagnosticReport missing required field: code")

        # Check category is NOT cardiac ultrasound for ECG reports
        for cat in resource.get("category", []):
            for coding in cat.get("coding", []):
                if coding.get("code") == "CUS":
                    errors.append(
                        "DiagnosticReport category 'CUS' (Cardiac Ultrasound) is incorrect for ECG; "
                        "use 'EC' (Electrocardiac)"
                    )

        # Check contained observations have valid references
        contained_ids = {c.get("id") for c in resource.get("contained", []) if isinstance(c, dict)}
        for ref in resource.get("result", []):
            ref_str = ref.get("reference", "")
            if ref_str.startswith("#"):
                ref_id = ref_str[1:]
                if ref_id not in contained_ids:
                    errors.append(f"result reference '{ref_str}' not found in contained resources")

    # --- Bundle ---
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
                else:
                    # Recursively validate contained resources
                    sub_errors = validate_fhir_resource(entry["resource"])
                    for e in sub_errors:
                        errors.append(f"Bundle.entry[{i}].resource: {e}")

    return errors

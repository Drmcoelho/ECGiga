"""Sex- and age-adjusted thresholds for ECG measurements.

Provides demographic-adjusted reference ranges for:
- STEMI criteria (different ST elevation thresholds by sex, age, lead)
- QTc intervals (different upper limits by sex)
- Heart rate ranges (pediatric vs adult vs elderly)
- QRS duration limits (age-adjusted)

References:
- Thygesen et al., "Fourth Universal Definition of Myocardial Infarction", JACC, 2018.
- Goldenberg et al., "QT interval: how to measure it and what is 'normal'",
  J Cardiovasc Electrophysiol, 2006.
- AHA/ACC/HRS Guideline for Management of Patients with Ventricular Arrhythmias, 2017.
"""

from __future__ import annotations

from typing import Any


# STEMI ST-elevation criteria by lead group, sex, and age
# Values in millivolts (mm on standard calibration = 0.1 mV)
# From Fourth Universal Definition of MI (2018)
_STEMI_CRITERIA: dict[str, dict[str, float]] = {
    # V2-V3 leads (anterior) — most variable by demographics
    "V2_V3_male_ge40": 0.2,      # Men ≥40: ≥2mm (0.2 mV)
    "V2_V3_male_lt40": 0.25,     # Men <40: ≥2.5mm (0.25 mV)
    "V2_V3_female": 0.15,        # Women: ≥1.5mm (0.15 mV)
    # All other leads (same for all demographics)
    "other_leads": 0.1,           # ≥1mm (0.1 mV)
    # Posterior leads (V7-V9)
    "posterior": 0.05,            # ≥0.5mm (0.05 mV)
    # Right-sided leads (V3R-V4R)
    "right_sided": 0.05,         # ≥0.5mm for RV infarction
}

# QTc normal ranges by sex
# From AHA/ACC/HRS guidelines
_QTC_THRESHOLDS: dict[str, dict[str, float]] = {
    "male": {
        "normal_upper": 450,     # ms
        "borderline": 470,       # ms
        "prolonged": 500,        # ms (high risk TdP)
        "short_lower": 340,      # ms
        "short_concerning": 320, # ms
    },
    "female": {
        "normal_upper": 460,     # ms
        "borderline": 480,       # ms
        "prolonged": 500,        # ms
        "short_lower": 340,      # ms
        "short_concerning": 320, # ms
    },
    "unknown": {
        "normal_upper": 460,
        "borderline": 480,
        "prolonged": 500,
        "short_lower": 340,
        "short_concerning": 320,
    },
}

# Heart rate ranges by age group
_HR_RANGES: dict[str, dict[str, tuple[int, int]]] = {
    "neonate": {"normal": (100, 180), "age_range": "0-28 days"},
    "infant": {"normal": (100, 160), "age_range": "1-12 months"},
    "toddler": {"normal": (90, 150), "age_range": "1-3 years"},
    "child": {"normal": (70, 120), "age_range": "4-11 years"},
    "adolescent": {"normal": (60, 100), "age_range": "12-17 years"},
    "adult": {"normal": (60, 100), "age_range": "18-64 years"},
    "elderly": {"normal": (55, 100), "age_range": "≥65 years"},
    "athlete": {"normal": (40, 100), "age_range": "trained athletes"},
}

# PR interval ranges by age
_PR_RANGES: dict[str, tuple[int, int]] = {
    "neonate": (80, 160),
    "infant": (80, 160),
    "child": (100, 180),
    "adolescent": (120, 200),
    "adult": (120, 200),
    "elderly": (120, 220),  # Slightly longer acceptable in elderly
}

# QRS duration limits by age
_QRS_LIMITS: dict[str, int] = {
    "neonate": 80,
    "infant": 80,
    "child": 90,
    "adolescent": 100,
    "adult": 120,
    "elderly": 120,
}


def _age_to_group(age: int | None) -> str:
    """Convert age in years to age group."""
    if age is None:
        return "adult"
    if age < 0:
        return "neonate"
    if age == 0:
        return "neonate"
    if age < 1:
        return "infant"
    if age < 4:
        return "toddler"
    if age < 12:
        return "child"
    if age < 18:
        return "adolescent"
    if age < 65:
        return "adult"
    return "elderly"


def get_adjusted_thresholds(
    age: int | None = None,
    sex: str | None = None,
    is_athlete: bool = False,
) -> dict[str, Any]:
    """Get comprehensive age/sex-adjusted ECG thresholds.

    Parameters
    ----------
    age : int, optional
        Patient age in years.
    sex : str, optional
        'M', 'F', or None.
    is_athlete : bool
        Whether patient is a trained athlete.

    Returns
    -------
    dict
        - hr_range: tuple[int, int]
        - pr_range: tuple[int, int]
        - qrs_upper: int (ms)
        - qtc_upper: float (ms)
        - qtc_prolonged: float (ms, high-risk threshold)
        - qtc_short: float (ms)
        - stemi_v2v3: float (mV)
        - stemi_other: float (mV)
        - age_group: str
        - sex: str
    """
    age_group = _age_to_group(age)
    sex_key = "male" if sex == "M" else "female" if sex == "F" else "unknown"

    # Heart rate
    if is_athlete:
        hr_range = _HR_RANGES["athlete"]["normal"]
    else:
        hr_range = _HR_RANGES.get(age_group, _HR_RANGES["adult"])["normal"]

    # PR interval
    pr_range = _PR_RANGES.get(age_group, _PR_RANGES["adult"])

    # QRS upper limit
    qrs_upper = _QRS_LIMITS.get(age_group, _QRS_LIMITS["adult"])

    # QTc thresholds
    qtc_info = _QTC_THRESHOLDS.get(sex_key, _QTC_THRESHOLDS["unknown"])
    qtc_upper = qtc_info["normal_upper"]
    qtc_prolonged = qtc_info["prolonged"]
    qtc_short = qtc_info["short_lower"]

    # STEMI V2-V3 threshold
    if sex == "M":
        if age is not None and age < 40:
            stemi_v2v3 = _STEMI_CRITERIA["V2_V3_male_lt40"]
        else:
            stemi_v2v3 = _STEMI_CRITERIA["V2_V3_male_ge40"]
    elif sex == "F":
        stemi_v2v3 = _STEMI_CRITERIA["V2_V3_female"]
    else:
        stemi_v2v3 = _STEMI_CRITERIA["V2_V3_male_ge40"]  # Default conservative

    stemi_other = _STEMI_CRITERIA["other_leads"]

    return {
        "hr_range": hr_range,
        "pr_range_ms": pr_range,
        "qrs_upper_ms": qrs_upper,
        "qtc_upper_ms": qtc_upper,
        "qtc_prolonged_ms": qtc_prolonged,
        "qtc_short_ms": qtc_short,
        "stemi_v2v3_mv": stemi_v2v3,
        "stemi_other_mv": stemi_other,
        "age_group": age_group,
        "sex": sex_key,
    }


def get_stemi_criteria(
    lead: str,
    sex: str | None = None,
    age: int | None = None,
) -> float:
    """Get STEMI ST-elevation threshold for a specific lead.

    Parameters
    ----------
    lead : str
        ECG lead name (e.g., 'V2', 'II', 'V7').
    sex : str, optional
        'M' or 'F'.
    age : int, optional
        Patient age in years.

    Returns
    -------
    float
        Minimum ST elevation in millivolts to meet STEMI criteria.
    """
    lead_upper = lead.upper()

    # V2-V3: sex/age dependent
    if lead_upper in ("V2", "V3"):
        if sex == "M":
            if age is not None and age < 40:
                return _STEMI_CRITERIA["V2_V3_male_lt40"]
            return _STEMI_CRITERIA["V2_V3_male_ge40"]
        elif sex == "F":
            return _STEMI_CRITERIA["V2_V3_female"]
        else:
            return _STEMI_CRITERIA["V2_V3_male_ge40"]

    # Posterior leads
    if lead_upper in ("V7", "V8", "V9"):
        return _STEMI_CRITERIA["posterior"]

    # Right-sided leads
    if lead_upper in ("V3R", "V4R", "V5R", "V6R"):
        return _STEMI_CRITERIA["right_sided"]

    # All other standard leads
    return _STEMI_CRITERIA["other_leads"]


def get_qtc_thresholds(
    sex: str | None = None,
) -> dict[str, float]:
    """Get QTc threshold values adjusted by sex.

    Parameters
    ----------
    sex : str, optional
        'M' or 'F'.

    Returns
    -------
    dict
        - normal_upper: float (ms)
        - borderline: float (ms)
        - prolonged: float (ms)
        - short_lower: float (ms)
        - short_concerning: float (ms)
    """
    sex_key = "male" if sex == "M" else "female" if sex == "F" else "unknown"
    return dict(_QTC_THRESHOLDS[sex_key])


def evaluate_measurement(
    measurement: str,
    value: float,
    age: int | None = None,
    sex: str | None = None,
    is_athlete: bool = False,
) -> dict[str, Any]:
    """Evaluate a single ECG measurement against adjusted thresholds.

    Parameters
    ----------
    measurement : str
        'heart_rate', 'pr_interval', 'qrs_duration', 'qtc', 'st_elevation'.
    value : float
        Measured value (bpm, ms, or mV depending on measurement).
    age : int, optional
        Patient age in years.
    sex : str, optional
        'M' or 'F'.
    is_athlete : bool
        Whether patient is a trained athlete.

    Returns
    -------
    dict
        - status: str ('normal', 'low', 'high', 'critical')
        - reference_range: str
        - value: float
        - details: str
    """
    thresholds = get_adjusted_thresholds(age, sex, is_athlete)

    if measurement == "heart_rate":
        low, high = thresholds["hr_range"]
        if value < low * 0.65:
            status = "critical"
        elif value < low:
            status = "low"
        elif value > high * 1.5:
            status = "critical"
        elif value > high:
            status = "high"
        else:
            status = "normal"
        ref = f"{low}-{high} bpm"

    elif measurement == "pr_interval":
        low, high = thresholds["pr_range_ms"]
        if value < low:
            status = "low"
        elif value > high * 1.5:
            status = "critical"
        elif value > high:
            status = "high"
        else:
            status = "normal"
        ref = f"{low}-{high} ms"

    elif measurement == "qrs_duration":
        upper = thresholds["qrs_upper_ms"]
        if value > upper * 1.33:
            status = "critical"
        elif value > upper:
            status = "high"
        else:
            status = "normal"
        ref = f"< {upper} ms"

    elif measurement == "qtc":
        qtc_upper = thresholds["qtc_upper_ms"]
        qtc_prolonged = thresholds["qtc_prolonged_ms"]
        qtc_short = thresholds["qtc_short_ms"]

        if value > qtc_prolonged:
            status = "critical"
        elif value > qtc_upper:
            status = "high"
        elif value < qtc_short:
            status = "low"
        else:
            status = "normal"
        ref = f"{qtc_short}-{qtc_upper} ms"

    else:
        return {
            "status": "unknown",
            "reference_range": "N/A",
            "value": value,
            "details": f"Medição '{measurement}' não reconhecida.",
        }

    details = (
        f"{measurement}: {value:.0f} (ref: {ref}, "
        f"grupo: {thresholds['age_group']}, sexo: {thresholds['sex']})"
    )

    return {
        "status": status,
        "reference_range": ref,
        "value": value,
        "details": details,
    }

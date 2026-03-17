"""Limiares ajustados por sexo e idade para medições de ECG.

Fornece faixas de referência ajustadas por dados demográficos para:
- Critérios de STEMI (limiares de supradesnivelamento de ST por sexo, idade, derivação)
- Intervalos QTc (limites superiores diferentes por sexo)
- Faixas de frequência cardíaca (pediátrico vs adulto vs idoso)
- Limites de duração do QRS (ajustados por idade)

Referências:
- Thygesen et al., "Fourth Universal Definition of Myocardial Infarction", JACC, 2018.
- Goldenberg et al., "QT interval: how to measure it and what is 'normal'",
  J Cardiovasc Electrophysiol, 2006.
- AHA/ACC/HRS Guideline for Management of Patients with Ventricular Arrhythmias, 2017.
"""

from __future__ import annotations

from typing import Any


# Critérios de supradesnivelamento de ST para STEMI por grupo de derivações, sexo e idade
# Valores em milivolts (mm na calibração padrão = 0,1 mV)
# Da Quarta Definição Universal de IAM (2018)
_STEMI_CRITERIA: dict[str, dict[str, float]] = {
    # Derivações V2-V3 (anterior) — mais variável por dados demográficos
    "V2_V3_male_ge40": 0.2,      # Homens >= 40: >= 2mm (0,2 mV)
    "V2_V3_male_lt40": 0.25,     # Homens < 40: >= 2,5mm (0,25 mV)
    "V2_V3_female": 0.15,        # Mulheres: >= 1,5mm (0,15 mV)
    # Todas as outras derivações (igual para todos os dados demográficos)
    "other_leads": 0.1,           # >= 1mm (0,1 mV)
    # Derivações posteriores (V7-V9)
    "posterior": 0.05,            # >= 0,5mm (0,05 mV)
    # Derivações do lado direito (V3R-V4R)
    "right_sided": 0.05,         # >= 0,5mm para infarto do VD
}

# Faixas normais de QTc por sexo
# Das diretrizes AHA/ACC/HRS
_QTC_THRESHOLDS: dict[str, dict[str, float]] = {
    "male": {
        "normal_upper": 450,     # ms
        "borderline": 470,       # ms
        "prolonged": 500,        # ms (alto risco de TdP)
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

# Faixas de frequência cardíaca por grupo etário
_HR_RANGES: dict[str, dict[str, tuple[int, int]]] = {
    "neonate": {"normal": (100, 180), "age_range": "0-28 dias"},
    "infant": {"normal": (100, 160), "age_range": "1-12 meses"},
    "toddler": {"normal": (90, 150), "age_range": "1-3 anos"},
    "child": {"normal": (70, 120), "age_range": "4-11 anos"},
    "adolescent": {"normal": (60, 100), "age_range": "12-17 anos"},
    "adult": {"normal": (60, 100), "age_range": "18-64 anos"},
    "elderly": {"normal": (55, 100), "age_range": ">=65 anos"},
    "athlete": {"normal": (40, 100), "age_range": "atletas treinados"},
}

# Faixas de intervalo PR por idade
_PR_RANGES: dict[str, tuple[int, int]] = {
    "neonate": (80, 160),
    "infant": (80, 160),
    "child": (100, 180),
    "adolescent": (120, 200),
    "adult": (120, 200),
    "elderly": (120, 220),  # Ligeiramente mais longo aceitável em idosos
}

# Limites de duração do QRS por idade
_QRS_LIMITS: dict[str, int] = {
    "neonate": 80,
    "infant": 80,
    "child": 90,
    "adolescent": 100,
    "adult": 120,
    "elderly": 120,
}


def _age_to_group(age: int | None) -> str:
    """Converte idade em anos para grupo etário."""
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
    """Obtém limiares de ECG abrangentes ajustados por idade/sexo.

    Parâmetros
    ----------
    age : int, opcional
        Idade do paciente em anos.
    sex : str, opcional
        'M', 'F', ou None.
    is_athlete : bool
        Se o paciente é atleta treinado.

    Retorna
    -------
    dict
        - hr_range: tuple[int, int]
        - pr_range: tuple[int, int]
        - qrs_upper: int (ms)
        - qtc_upper: float (ms)
        - qtc_prolonged: float (ms, limiar de alto risco)
        - qtc_short: float (ms)
        - stemi_v2v3: float (mV)
        - stemi_other: float (mV)
        - age_group: str
        - sex: str
    """
    age_group = _age_to_group(age)
    sex_key = "male" if sex == "M" else "female" if sex == "F" else "unknown"

    # Frequência cardíaca
    if is_athlete:
        hr_range = _HR_RANGES["athlete"]["normal"]
    else:
        hr_range = _HR_RANGES.get(age_group, _HR_RANGES["adult"])["normal"]

    # Intervalo PR
    pr_range = _PR_RANGES.get(age_group, _PR_RANGES["adult"])

    # Limite superior do QRS
    qrs_upper = _QRS_LIMITS.get(age_group, _QRS_LIMITS["adult"])

    # Limiares de QTc
    qtc_info = _QTC_THRESHOLDS.get(sex_key, _QTC_THRESHOLDS["unknown"])
    qtc_upper = qtc_info["normal_upper"]
    qtc_prolonged = qtc_info["prolonged"]
    qtc_short = qtc_info["short_lower"]

    # Limiar de STEMI V2-V3
    if sex == "M":
        if age is not None and age < 40:
            stemi_v2v3 = _STEMI_CRITERIA["V2_V3_male_lt40"]
        else:
            stemi_v2v3 = _STEMI_CRITERIA["V2_V3_male_ge40"]
    elif sex == "F":
        stemi_v2v3 = _STEMI_CRITERIA["V2_V3_female"]
    else:
        stemi_v2v3 = _STEMI_CRITERIA["V2_V3_male_ge40"]  # Padrão conservador

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
    """Obtém o limiar de supradesnivelamento de ST para STEMI de uma derivação específica.

    Parâmetros
    ----------
    lead : str
        Nome da derivação de ECG (ex.: 'V2', 'II', 'V7').
    sex : str, opcional
        'M' ou 'F'.
    age : int, opcional
        Idade do paciente em anos.

    Retorna
    -------
    float
        Supradesnivelamento mínimo de ST em milivolts para preencher critérios de STEMI.
    """
    lead_upper = lead.upper()

    # V2-V3: dependente de sexo/idade
    if lead_upper in ("V2", "V3"):
        if sex == "M":
            if age is not None and age < 40:
                return _STEMI_CRITERIA["V2_V3_male_lt40"]
            return _STEMI_CRITERIA["V2_V3_male_ge40"]
        elif sex == "F":
            return _STEMI_CRITERIA["V2_V3_female"]
        else:
            return _STEMI_CRITERIA["V2_V3_male_ge40"]

    # Derivações posteriores
    if lead_upper in ("V7", "V8", "V9"):
        return _STEMI_CRITERIA["posterior"]

    # Derivações do lado direito
    if lead_upper in ("V3R", "V4R", "V5R", "V6R"):
        return _STEMI_CRITERIA["right_sided"]

    # Todas as outras derivações padrão
    return _STEMI_CRITERIA["other_leads"]


def get_qtc_thresholds(
    sex: str | None = None,
) -> dict[str, float]:
    """Obtém valores de limiares de QTc ajustados por sexo.

    Parâmetros
    ----------
    sex : str, opcional
        'M' ou 'F'.

    Retorna
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
    """Avalia uma medição de ECG individual contra limiares ajustados.

    Parâmetros
    ----------
    measurement : str
        'heart_rate', 'pr_interval', 'qrs_duration', 'qtc', 'st_elevation'.
    value : float
        Valor medido (bpm, ms, ou mV dependendo da medição).
    age : int, opcional
        Idade do paciente em anos.
    sex : str, opcional
        'M' ou 'F'.
    is_athlete : bool
        Se o paciente é atleta treinado.

    Retorna
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

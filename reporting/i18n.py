"""Internationalization support for ECG reports.

Provides translations between Portuguese (PT) and English (EN) for all
report fields, clinical flags, and UI labels.
"""

from __future__ import annotations

TRANSLATIONS: dict[str, dict[str, str]] = {
    "pt": {
        # Report sections
        "report_title": "Laudo ECG",
        "patient_info": "Informações do Paciente",
        "measurements": "Medições",
        "interpretation": "Interpretação",
        "flags": "Flags Clínicas",
        "differential_diagnosis": "Diagnóstico Diferencial",
        "educational_notes": "Notas Educacionais",
        "conclusion": "Conclusão",
        "disclaimer": "Aviso Legal",
        # Measurement labels
        "heart_rate": "Frequencia Cardiaca",
        "pr_interval": "Intervalo PR",
        "qrs_duration": "Duração QRS",
        "qt_interval": "Intervalo QT",
        "qtc_interval": "Intervalo QTc (Bazett)",
        "frontal_axis": "Eixo Frontal",
        "rr_interval": "Intervalo RR",
        # Units
        "bpm": "bpm",
        "ms": "ms",
        "degrees": "graus",
        "seconds": "segundos",
        # Axis labels
        "normal_axis": "Eixo normal",
        "left_axis_deviation": "Desvio do eixo para a esquerda",
        "right_axis_deviation": "Desvio do eixo para a direita",
        "extreme_axis": "Eixo extremo (terra de ninguém)",
        # Common flags
        "no_significant_flags": "Sem flags relevantes",
        "sinus_rhythm": "Ritmo sinusal",
        "sinus_tachycardia": "Taquicardia sinusal",
        "sinus_bradycardia": "Bradicardia sinusal",
        "wide_qrs": "QRS alargado (>=120 ms)",
        "prolonged_pr": "PR prolongado (>200 ms) — BAV 1º grau",
        "prolonged_qtc": "QTc prolongado",
        "short_qtc": "QTc curto",
        "left_axis": "Desvio do eixo para a esquerda",
        "right_axis": "Desvio do eixo para a direita",
        # Status
        "normal": "Normal",
        "abnormal_low": "Abaixo do normal",
        "abnormal_high": "Acima do normal",
        "critical": "CRÍTICO",
        # Educational / camera analogy
        "camera_analogy_title": "Analogia da Câmera",
        "camera_analogy_body": (
            "Imagine o coração como um objeto sendo fotografado por 12 câmeras (derivações). "
            "Cada derivação vê o mesmo evento elétrico de um ângulo diferente. "
            "O eixo elétrico é como a direção principal da luz — "
            "as câmeras que veem a luz de frente registram deflexões positivas.\n\n"
            "Mnemônico CAFÉ:\n"
            "  C — Câmera = polo positivo\n"
            "  A — Aproximando = deflexão positiva\n"
            "  F — Fugindo = deflexão negativa\n"
            "  É — Esquece (perpendicular) = bifásico"
        ),
        # Disclaimer
        "disclaimer_text": (
            "AVISO: Este laudo foi gerado automaticamente pelo sistema ECGiga "
            "e tem finalidade exclusivamente educacional. NÃO substitui a "
            "avaliação de um médico cardiologista. Qualquer decisão clínica "
            "deve ser baseada na avaliação profissional presencial."
        ),
        # Page labels
        "page": "Página",
        "of": "de",
        "generated_by": "Gerado por ECGiga",
        "date": "Data",
        "report_id": "ID do Laudo",
        "clinical_summary": "Resumo Clínico",
    },
    "en": {
        # Report sections
        "report_title": "ECG Report",
        "patient_info": "Patient Information",
        "measurements": "Measurements",
        "interpretation": "Interpretation",
        "flags": "Clinical Flags",
        "differential_diagnosis": "Differential Diagnosis",
        "educational_notes": "Educational Notes",
        "conclusion": "Conclusion",
        "disclaimer": "Disclaimer",
        # Measurement labels
        "heart_rate": "Heart Rate",
        "pr_interval": "PR Interval",
        "qrs_duration": "QRS Duration",
        "qt_interval": "QT Interval",
        "qtc_interval": "QTc Interval (Bazett)",
        "frontal_axis": "Frontal Axis",
        "rr_interval": "RR Interval",
        # Units
        "bpm": "bpm",
        "ms": "ms",
        "degrees": "degrees",
        "seconds": "seconds",
        # Axis labels
        "normal_axis": "Normal axis",
        "left_axis_deviation": "Left axis deviation",
        "right_axis_deviation": "Right axis deviation",
        "extreme_axis": "Extreme axis (no man's land)",
        # Common flags
        "no_significant_flags": "No significant flags",
        "sinus_rhythm": "Sinus rhythm",
        "sinus_tachycardia": "Sinus tachycardia",
        "sinus_bradycardia": "Sinus bradycardia",
        "wide_qrs": "Wide QRS (>=120 ms)",
        "prolonged_pr": "Prolonged PR (>200 ms) — First degree AV block",
        "prolonged_qtc": "Prolonged QTc",
        "short_qtc": "Short QTc",
        "left_axis": "Left axis deviation",
        "right_axis": "Right axis deviation",
        # Status
        "normal": "Normal",
        "abnormal_low": "Below normal",
        "abnormal_high": "Above normal",
        "critical": "CRITICAL",
        # Educational / camera analogy
        "camera_analogy_title": "Camera Analogy",
        "camera_analogy_body": (
            "Think of the heart as an object being photographed by 12 cameras (leads). "
            "Each lead sees the same electrical event from a different angle. "
            "The electrical axis is like the main direction of light — "
            "cameras facing the light record positive deflections.\n\n"
            "CAFE Mnemonic:\n"
            "  C — Camera = positive pole\n"
            "  A — Approaching = positive deflection\n"
            "  F — Fleeing = negative deflection\n"
            "  E — Equidistant (perpendicular) = biphasic"
        ),
        # Disclaimer
        "disclaimer_text": (
            "DISCLAIMER: This report was automatically generated by the ECGiga system "
            "and is intended for educational purposes ONLY. It does NOT replace "
            "evaluation by a qualified cardiologist. Any clinical decisions must "
            "be based on professional in-person assessment."
        ),
        # Page labels
        "page": "Page",
        "of": "of",
        "generated_by": "Generated by ECGiga",
        "date": "Date",
        "report_id": "Report ID",
        "clinical_summary": "Clinical Summary",
    },
}

# Mapping of Portuguese flag text patterns to translation keys
_FLAG_PT_TO_KEY: dict[str, str] = {
    "Sem flags relevantes": "no_significant_flags",
    "Ritmo sinusal": "sinus_rhythm",
    "Taquicardia sinusal": "sinus_tachycardia",
    "Bradicardia sinusal": "sinus_bradycardia",
    "QRS alargado": "wide_qrs",
    "PR prolongado": "prolonged_pr",
    "QTc prolongado": "prolonged_qtc",
    "QTc curto": "short_qtc",
    "Desvio do eixo para a esquerda": "left_axis",
    "Desvio do eixo para a direita": "right_axis",
}

# Mapping of English flag text patterns to translation keys
_FLAG_EN_TO_KEY: dict[str, str] = {
    "No significant flags": "no_significant_flags",
    "Sinus rhythm": "sinus_rhythm",
    "Sinus tachycardia": "sinus_tachycardia",
    "Sinus bradycardia": "sinus_bradycardia",
    "Wide QRS": "wide_qrs",
    "Prolonged PR": "prolonged_pr",
    "Prolonged QTc": "prolonged_qtc",
    "Short QTc": "short_qtc",
    "Left axis deviation": "left_axis",
    "Right axis deviation": "right_axis",
}


def t(key: str, lang: str = "pt") -> str:
    """Translate a key to the specified language.

    Falls back to English, then to the key itself if no translation found.
    """
    lang = lang.lower()
    if lang in TRANSLATIONS and key in TRANSLATIONS[lang]:
        return TRANSLATIONS[lang][key]
    if key in TRANSLATIONS.get("en", {}):
        return TRANSLATIONS["en"][key]
    return key


def translate_report(report: dict, target_lang: str = "en") -> dict:
    """Translate report field names to the target language.

    Creates a new dict with translated keys for known fields.
    Unknown fields are passed through unchanged.
    """
    field_map_pt_to_en = {
        "Frequencia Cardiaca": "heart_rate",
        "Intervalo PR": "pr_interval",
        "Duracao QRS": "qrs_duration",
        "Intervalo QT": "qt_interval",
        "Intervalo QTc": "qtc_interval",
        "Eixo Frontal": "frontal_axis",
    }

    result = {}
    for key, value in report.items():
        translated_key = key
        if key in field_map_pt_to_en:
            trans_key = field_map_pt_to_en[key]
            translated_key = t(trans_key, target_lang)
        elif key in TRANSLATIONS.get(target_lang, {}):
            translated_key = TRANSLATIONS[target_lang][key]

        if isinstance(value, dict):
            result[translated_key] = translate_report(value, target_lang)
        elif isinstance(value, list) and all(isinstance(v, str) for v in value):
            result[translated_key] = translate_flags(value, target_lang)
        else:
            result[translated_key] = value

    return result


def translate_flags(flags: list[str], target_lang: str = "en") -> list[str]:
    """Translate clinical flags to the target language.

    Attempts pattern matching on known flag texts. Unknown flags are returned as-is.
    """
    translated = []
    for flag in flags:
        found = False
        for pattern, key in _FLAG_PT_TO_KEY.items():
            if pattern.lower() in flag.lower():
                translated.append(t(key, target_lang))
                found = True
                break
        if not found:
            for pattern, key in _FLAG_EN_TO_KEY.items():
                if pattern.lower() in flag.lower():
                    translated.append(t(key, target_lang))
                    found = True
                    break
        if not found:
            translated.append(flag)
    return translated

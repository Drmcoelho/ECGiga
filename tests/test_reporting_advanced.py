"""Tests for Phase 25: Advanced Clinical Report (FHIR, PDF, i18n)."""

import json
import pathlib

import pytest

from reporting.fhir import (
    FHIR_LOINC_CODES,
    report_to_fhir_observation,
    report_to_fhir_diagnostic_report,
    validate_fhir_resource,
)
from reporting.i18n import t, translate_flags, translate_report, TRANSLATIONS
from reporting.pdf_report import generate_pdf_report, _render_measurements_table


# ── FHIR Tests ──────────────────────────────────────────────


class TestFHIRObservation:
    def test_observation_bundle_structure(self, sample_report):
        bundle = report_to_fhir_observation(sample_report)
        assert bundle["resourceType"] == "Bundle"
        assert bundle["type"] == "collection"
        assert "entry" in bundle
        assert len(bundle["entry"]) > 0

    def test_observation_has_loinc_codes(self, sample_report):
        bundle = report_to_fhir_observation(sample_report)
        loinc_codes_found = set()
        for entry in bundle["entry"]:
            obs = entry["resource"]
            assert obs["resourceType"] == "Observation"
            coding = obs["code"]["coding"][0]
            assert coding["system"] == "http://loinc.org"
            loinc_codes_found.add(coding["code"])
        # At least some LOINC codes should be present
        expected_codes = set(FHIR_LOINC_CODES.values())
        assert len(loinc_codes_found & expected_codes) > 0

    def test_observation_with_patient_id(self, sample_report):
        bundle = report_to_fhir_observation(sample_report, patient_id="patient-123")
        for entry in bundle["entry"]:
            obs = entry["resource"]
            assert obs["subject"]["reference"] == "Patient/patient-123"

    def test_observation_without_patient_id(self, sample_report):
        bundle = report_to_fhir_observation(sample_report)
        for entry in bundle["entry"]:
            obs = entry["resource"]
            assert "subject" not in obs

    def test_observation_value_quantity(self, sample_report):
        bundle = report_to_fhir_observation(sample_report)
        for entry in bundle["entry"]:
            obs = entry["resource"]
            vq = obs["valueQuantity"]
            assert "value" in vq
            assert "unit" in vq
            assert isinstance(vq["value"], (int, float))


class TestFHIRDiagnosticReport:
    def test_diagnostic_report_structure(self, sample_report):
        dr = report_to_fhir_diagnostic_report(sample_report)
        assert dr["resourceType"] == "DiagnosticReport"
        assert dr["status"] == "final"
        assert "code" in dr
        assert "contained" in dr
        assert "result" in dr
        assert len(dr["contained"]) > 0

    def test_diagnostic_report_with_patient(self, sample_report):
        dr = report_to_fhir_diagnostic_report(sample_report, patient_id="p-456")
        assert dr["subject"]["reference"] == "Patient/p-456"

    def test_diagnostic_report_conclusion(self, sample_report):
        dr = report_to_fhir_diagnostic_report(sample_report)
        assert "conclusion" in dr
        assert isinstance(dr["conclusion"], str)
        assert len(dr["conclusion"]) > 0


class TestFHIRLoincCodes:
    def test_all_required_codes_present(self):
        required = ["heart_rate", "pr_interval", "qrs_duration",
                     "qt_interval", "qtc_interval", "frontal_axis"]
        for key in required:
            assert key in FHIR_LOINC_CODES

    def test_specific_loinc_values(self):
        assert FHIR_LOINC_CODES["heart_rate"] == "8867-4"
        assert FHIR_LOINC_CODES["pr_interval"] == "8625-6"
        assert FHIR_LOINC_CODES["qrs_duration"] == "8633-0"
        assert FHIR_LOINC_CODES["qt_interval"] == "8634-8"
        assert FHIR_LOINC_CODES["qtc_interval"] == "8636-3"
        assert FHIR_LOINC_CODES["frontal_axis"] == "8632-2"


class TestFHIRValidation:
    def test_validate_valid_observation(self, sample_report):
        bundle = report_to_fhir_observation(sample_report)
        errors = validate_fhir_resource(bundle)
        assert errors == []

    def test_validate_valid_diagnostic_report(self, sample_report):
        dr = report_to_fhir_diagnostic_report(sample_report)
        errors = validate_fhir_resource(dr)
        assert errors == []

    def test_validate_missing_resource_type(self):
        errors = validate_fhir_resource({"id": "test"})
        assert any("resourceType" in e for e in errors)

    def test_validate_non_dict(self):
        errors = validate_fhir_resource("not a dict")
        assert len(errors) > 0


# ── i18n Tests ───────────────────────────────────────────────


class TestTranslation:
    def test_translate_key_pt(self):
        result = t("report_title", "pt")
        assert result == "Laudo ECG"

    def test_translate_key_en(self):
        result = t("report_title", "en")
        assert result == "ECG Report"

    def test_translate_key_fallback(self):
        result = t("nonexistent_key", "pt")
        assert result == "nonexistent_key"

    def test_translate_pt_to_en(self):
        assert t("heart_rate", "en") == "Heart Rate"
        assert t("heart_rate", "pt") == "Frequencia Cardiaca"

    def test_translations_have_both_languages(self):
        assert "pt" in TRANSLATIONS
        assert "en" in TRANSLATIONS
        # Both should have the same keys
        pt_keys = set(TRANSLATIONS["pt"].keys())
        en_keys = set(TRANSLATIONS["en"].keys())
        assert pt_keys == en_keys


class TestTranslateFlags:
    def test_translate_flags_pt_to_en(self):
        flags_pt = ["Sem flags relevantes"]
        flags_en = translate_flags(flags_pt, "en")
        assert flags_en[0] == "No significant flags"

    def test_translate_flags_unknown_passthrough(self):
        flags = ["Some unknown flag"]
        result = translate_flags(flags, "en")
        assert result[0] == "Some unknown flag"

    def test_translate_multiple_flags(self):
        flags_pt = ["Taquicardia sinusal", "QTc prolongado"]
        flags_en = translate_flags(flags_pt, "en")
        assert "Sinus tachycardia" in flags_en
        assert "Prolonged QTc" in flags_en

    def test_translate_flags_to_pt(self):
        flags_en = ["No significant flags"]
        flags_pt = translate_flags(flags_en, "pt")
        assert flags_pt[0] == "Sem flags relevantes"


class TestTranslateReport:
    def test_translate_report_basic(self):
        report = {"heart_rate": 72, "flags": ["Sem flags relevantes"]}
        translated = translate_report(report, "en")
        assert isinstance(translated, dict)

    def test_translate_report_preserves_values(self):
        report = {"some_key": 42}
        translated = translate_report(report, "en")
        assert 42 in translated.values()


# ── PDF Tests ────────────────────────────────────────────────


class TestPDFReport:
    def test_generate_pdf_report_creates_file(self, tmp_path, sample_report):
        out = str(tmp_path / "report.pdf")
        result = generate_pdf_report(sample_report, out, language="pt")
        assert result == out
        assert pathlib.Path(out).exists()
        assert pathlib.Path(out).stat().st_size > 0

    def test_generate_pdf_report_en(self, tmp_path, sample_report):
        out = str(tmp_path / "report_en.pdf")
        result = generate_pdf_report(sample_report, out, language="en")
        assert pathlib.Path(result).exists()

    def test_render_measurements_table(self, sample_report):
        import matplotlib.pyplot as plt
        fig = _render_measurements_table(sample_report, "pt")
        assert fig is not None
        plt.close(fig)

    def test_generate_pdf_returns_path(self, tmp_path, sample_report):
        out = str(tmp_path / "test_report.pdf")
        result = generate_pdf_report(sample_report, out)
        assert result == out

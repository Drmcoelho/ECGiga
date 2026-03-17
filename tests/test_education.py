"""
tests/test_education.py — Testes do módulo education (Phase 17 — Câmeras Cardíacas)
"""

import json
import math
import pathlib
import sys

import pytest

# Ensure project root is importable
ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from education.cameras import (
    LEAD_CAMERAS,
    MNEMONIC_CAFE,
    explain_axis,
    explain_deflection,
    explain_lead,
    get_camera_story,
)


# -----------------------------------------------------------------------
# LEAD_CAMERAS structure
# -----------------------------------------------------------------------

ALL_12_LEADS = ["I", "II", "III", "aVR", "aVL", "aVF",
                "V1", "V2", "V3", "V4", "V5", "V6"]


class TestLeadCameras:
    """Testes para o dicionário LEAD_CAMERAS."""

    def test_all_12_leads_present(self):
        for lead in ALL_12_LEADS:
            assert lead in LEAD_CAMERAS, f"Derivação {lead} ausente em LEAD_CAMERAS"

    def test_required_keys(self):
        required = {"angle_deg", "plane", "description_pt", "camera_analogy_pt"}
        for lead, info in LEAD_CAMERAS.items():
            for key in required:
                assert key in info, f"{lead} faltando chave '{key}'"

    def test_plane_values(self):
        frontal = {"I", "II", "III", "aVR", "aVL", "aVF"}
        horizontal = {"V1", "V2", "V3", "V4", "V5", "V6"}
        for lead, info in LEAD_CAMERAS.items():
            if lead in frontal:
                assert info["plane"] == "frontal"
            elif lead in horizontal:
                assert info["plane"] == "horizontal"

    def test_angles_are_numeric(self):
        for lead, info in LEAD_CAMERAS.items():
            assert isinstance(info["angle_deg"], (int, float)), (
                f"{lead} angle_deg não é numérico"
            )

    def test_known_angles(self):
        assert LEAD_CAMERAS["I"]["angle_deg"] == 0
        assert LEAD_CAMERAS["II"]["angle_deg"] == 60
        assert LEAD_CAMERAS["III"]["angle_deg"] == 120
        assert LEAD_CAMERAS["aVR"]["angle_deg"] == -150
        assert LEAD_CAMERAS["aVL"]["angle_deg"] == -30
        assert LEAD_CAMERAS["aVF"]["angle_deg"] == 90


# -----------------------------------------------------------------------
# MNEMONIC_CAFE
# -----------------------------------------------------------------------

class TestMnemonicCafe:
    def test_keys(self):
        for key in ["C", "A", "F", "E", "resumo"]:
            assert key in MNEMONIC_CAFE

    def test_resumo_is_string(self):
        assert isinstance(MNEMONIC_CAFE["resumo"], str)
        assert len(MNEMONIC_CAFE["resumo"]) > 20


# -----------------------------------------------------------------------
# explain_lead
# -----------------------------------------------------------------------

class TestExplainLead:
    @pytest.mark.parametrize("lead", ALL_12_LEADS)
    def test_returns_dict_for_each_lead(self, lead):
        result = explain_lead(lead)
        assert isinstance(result, dict)
        assert result["lead"] == lead

    def test_required_output_keys(self):
        result = explain_lead("II")
        for key in ["lead", "angle_deg", "plane", "description_pt",
                     "camera_analogy_pt", "mnemonic_cafe", "clinical_tip_pt"]:
            assert key in result, f"Chave '{key}' ausente no resultado"

    def test_invalid_lead_raises(self):
        with pytest.raises(ValueError):
            explain_lead("X99")


# -----------------------------------------------------------------------
# explain_deflection
# -----------------------------------------------------------------------

class TestExplainDeflection:
    def test_lead_II_vector_60_positive(self):
        """Vetor a 60° alinhado com DII (60°) → deflexão positiva."""
        result = explain_deflection("II", 60)
        assert result["deflection"] == "positiva"

    def test_lead_aVR_vector_60_negative(self):
        """Vetor a 60° afastando-se de aVR (-150°) → negativa."""
        result = explain_deflection("aVR", 60)
        assert result["deflection"] == "negativa"

    def test_lead_aVL_vector_60_biphasic(self):
        """Vetor a 60° perpendicular a aVL (-30°) → bifásico."""
        result = explain_deflection("aVL", 60)
        assert result["deflection"] == "bifásica"

    def test_lead_I_vector_0_positive(self):
        result = explain_deflection("I", 0)
        assert result["deflection"] == "positiva"

    def test_lead_I_vector_180_negative(self):
        result = explain_deflection("I", 180)
        assert result["deflection"] == "negativa"

    def test_output_keys(self):
        result = explain_deflection("V1", 45)
        for key in ["lead", "lead_angle_deg", "vector_deg",
                     "angle_diff", "deflection", "explanation_pt"]:
            assert key in result

    def test_invalid_lead(self):
        with pytest.raises(ValueError):
            explain_deflection("INVALID", 0)


# -----------------------------------------------------------------------
# explain_axis
# -----------------------------------------------------------------------

class TestExplainAxis:
    def test_normal_axis(self):
        result = explain_axis(60)
        assert result["classification"] == "normal"

    def test_left_axis_deviation(self):
        result = explain_axis(-45)
        assert result["classification"] == "desvio_esquerda"

    def test_right_axis_deviation(self):
        result = explain_axis(120)
        assert result["classification"] == "desvio_direita"

    def test_extreme_axis(self):
        result = explain_axis(-120)
        assert result["classification"] == "desvio_extremo"

    def test_output_keys(self):
        result = explain_axis(60)
        for key in ["axis_deg", "classification", "classification_text",
                     "best_cameras", "worst_cameras",
                     "perpendicular_cameras", "explanation_pt"]:
            assert key in result

    def test_best_cameras_for_60(self):
        result = explain_axis(60)
        assert "II" in result["best_cameras"]


# -----------------------------------------------------------------------
# get_camera_story
# -----------------------------------------------------------------------

class TestGetCameraStory:
    def test_generates_text(self):
        report = {"rhythm": "sinusal", "rate_bpm": 75, "axis_deg": 60}
        text = get_camera_story(report)
        assert isinstance(text, str)
        assert len(text) > 100

    def test_contains_cafe_mnemonic(self):
        text = get_camera_story({})
        assert "CAFÉ" in text

    def test_st_changes_narrative(self):
        report = {"st_changes": {"II": "supra", "aVL": "infra"}}
        text = get_camera_story(report)
        assert "supra" in text.lower() or "SUPRA" in text
        assert "infra" in text.lower() or "recíproca" in text.lower() or "espelho" in text.lower()

    def test_empty_report(self):
        text = get_camera_story({})
        assert isinstance(text, str)
        assert len(text) > 50


# -----------------------------------------------------------------------
# interactive — Plotly figures
# -----------------------------------------------------------------------

class TestInteractive:
    def test_camera_visualization_returns_figure(self):
        from education.interactive import create_camera_visualization_figure
        fig = create_camera_visualization_figure(active_lead="II", vector_angle=60)
        assert hasattr(fig, "data")
        assert hasattr(fig, "layout")
        assert len(fig.data) > 0

    def test_camera_visualization_different_leads(self):
        from education.interactive import create_camera_visualization_figure
        for lead in ["I", "V1", "aVR", "V6"]:
            fig = create_camera_visualization_figure(active_lead=lead)
            assert len(fig.data) > 0

    def test_deflection_animation_data(self):
        from education.interactive import create_deflection_animation_data
        data = create_deflection_animation_data("II", 0, 180, n_frames=10)
        assert "frames" in data
        assert len(data["frames"]) == 10
        assert data["lead"] == "II"
        # First frame: vector at 0°, DII at 60° → positive
        assert data["frames"][0]["deflection_type"] == "positiva"

    def test_axis_wheel_figure(self):
        from education.interactive import create_axis_wheel_figure
        fig = create_axis_wheel_figure(60)
        assert hasattr(fig, "data")
        assert len(fig.data) > 0


# -----------------------------------------------------------------------
# Quiz bank p17
# -----------------------------------------------------------------------

class TestQuizBankP17:
    QUIZ_DIR = ROOT / "quiz" / "bank" / "p17"

    def test_quiz_directory_exists(self):
        assert self.QUIZ_DIR.is_dir(), f"Diretório {self.QUIZ_DIR} não encontrado"

    def test_20_quiz_files(self):
        files = sorted(self.QUIZ_DIR.glob("cam_*.json"))
        assert len(files) == 20, f"Esperados 20 arquivos, encontrados {len(files)}"

    def test_quiz_schema(self):
        required_keys = {"id", "topic", "difficulty", "stem",
                         "options", "answer_index", "explanation"}
        for path in sorted(self.QUIZ_DIR.glob("cam_*.json")):
            with open(path, encoding="utf-8") as f:
                q = json.load(f)
            missing = required_keys - set(q.keys())
            assert not missing, f"{path.name} faltando chaves: {missing}"
            assert q["difficulty"] in ("easy", "medium", "hard")
            assert isinstance(q["options"], list)
            assert len(q["options"]) == 4
            assert 0 <= q["answer_index"] <= 3

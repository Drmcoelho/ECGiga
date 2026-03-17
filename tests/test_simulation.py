"""Tests for the simulation module (Phase 28).

Covers:
- ActionPotentialModel waveform generation
- Hyperkalemia / hypokalemia effects on K+ and QT
- Drug database completeness (>= 15 entries)
- Drug effect simulation returns modified waveform
- 12-lead ECG generation
- Pathological ECG generation for each supported pathology
- Plotly figure conversion
"""

from __future__ import annotations

import numpy as np
import pytest

from simulation.ion_channels import ActionPotentialModel
from simulation.drug_effects import (
    DRUG_DATABASE,
    simulate_drug_effect,
    get_drug_info,
    check_drug_interactions,
)
from simulation.ecg_generator import (
    LEAD_NAMES,
    generate_ecg,
    generate_pathological_ecg,
    add_noise,
    ecg_to_plotly_figure,
)


# ---------------------------------------------------------------------------
# ActionPotentialModel
# ---------------------------------------------------------------------------


def test_action_potential_generates_waveform():
    """compute_waveform returns a 1-D numpy array of expected length."""
    model = ActionPotentialModel()
    wf = model.compute_waveform(duration_ms=500, fs=1000)
    assert isinstance(wf, np.ndarray)
    assert wf.ndim == 1
    assert len(wf) == 500
    assert wf.max() > wf.min()


def test_waveform_has_depolarization():
    """The waveform should contain a positive peak (depolarization)."""
    model = ActionPotentialModel()
    wf = model.compute_waveform(duration_ms=1000, fs=1000)
    assert np.max(wf) > 0, "Expected positive depolarization peak"


def test_hyperkalemia_changes_k_and_affects_qt():
    """apply_hyperkalemia raises K+ and produces T-wave/QT changes."""
    model = ActionPotentialModel()
    original_k = model.k_extra

    model.apply_hyperkalemia("mild")
    assert model.k_extra > original_k

    model.apply_hyperkalemia("moderate")
    assert model.k_extra > 6.0

    model.apply_hyperkalemia("severe")
    assert model.k_extra > 7.0

    effects = model.get_ecg_effects()
    assert "apiculada" in effects["t_wave_change"].lower()
    assert effects["description_pt"] != ""
    # QT should be affected
    assert effects["qt_change"] != "Sem alteração"


def test_hypokalemia_changes_k():
    """apply_hypokalemia lowers K+ and prolongs QT."""
    model = ActionPotentialModel()
    original_k = model.k_extra
    model.apply_hypokalemia("mild")
    assert model.k_extra < original_k

    model.apply_hypokalemia("severe")
    assert model.k_extra < 2.5
    effects = model.get_ecg_effects()
    assert "prolongado" in effects["qt_change"].lower()


def test_hypercalcemia_shortens_qt():
    """Hypercalcemia should shorten QT."""
    model = ActionPotentialModel()
    model.apply_hypercalcemia()
    effects = model.get_ecg_effects()
    assert "encurtado" in effects["qt_change"].lower()


def test_hypocalcemia_prolongs_qt():
    """Hypocalcemia should prolong QT."""
    model = ActionPotentialModel()
    model.apply_hypocalcemia()
    effects = model.get_ecg_effects()
    assert "prolongado" in effects["qt_change"].lower()


def test_normal_ion_effects():
    """Normal concentrations should report no pathological changes."""
    model = ActionPotentialModel()
    effects = model.get_ecg_effects()
    assert "normalidade" in effects["description_pt"].lower()


# ---------------------------------------------------------------------------
# Drug database
# ---------------------------------------------------------------------------


def test_drug_database_has_at_least_15_entries():
    """Drug database must have at least 15 entries."""
    assert len(DRUG_DATABASE) >= 15, (
        f"Expected >= 15 drugs, got {len(DRUG_DATABASE)}"
    )


def test_required_drugs_present():
    """Key drugs from the spec must exist."""
    required = [
        "amiodarona", "digoxina", "betabloqueador", "verapamil",
        "antidepressivo_triciclico", "fluoroquinolona", "cocaina",
    ]
    for drug in required:
        assert drug in DRUG_DATABASE, f"Missing required drug: {drug}"


def test_all_drugs_have_description_and_analogy():
    """Every drug must have description_pt and camera_analogy."""
    for name, info in DRUG_DATABASE.items():
        assert "description_pt" in info, f"Drug '{name}' missing description_pt"
        assert len(info["description_pt"]) > 10
        assert "camera_analogy" in info, f"Drug '{name}' missing camera_analogy"


# ---------------------------------------------------------------------------
# Drug simulation
# ---------------------------------------------------------------------------


def test_simulate_drug_effect_returns_modified_waveform():
    """simulate_drug_effect returns an ndarray of the same length, different from input."""
    baseline = np.sin(np.linspace(0, 4 * np.pi, 1000))
    result = simulate_drug_effect(baseline, "amiodarona")
    assert isinstance(result, np.ndarray)
    assert len(result) == len(baseline)
    assert not np.allclose(baseline, result), "Drug should modify the waveform"


def test_simulate_each_drug():
    """Every drug in the database should be simulable without error."""
    baseline = np.sin(np.linspace(0, 4 * np.pi, 500))
    for drug_name in DRUG_DATABASE:
        result = simulate_drug_effect(baseline, drug_name)
        assert len(result) == len(baseline), f"Length mismatch for {drug_name}"
        assert np.all(np.isfinite(result)), f"Non-finite values for {drug_name}"


def test_simulate_unknown_drug_raises():
    """Unknown drug should raise ValueError."""
    with pytest.raises(ValueError, match="not found"):
        simulate_drug_effect(np.zeros(100), "droga_inexistente")


def test_get_drug_info_known():
    """get_drug_info returns details for known drugs."""
    info = get_drug_info("digoxina")
    assert info["name"] == "digoxina"
    assert "description_pt" in info
    assert "camera_analogy" in info


def test_get_drug_info_unknown():
    """get_drug_info returns error dict for unknown drugs."""
    info = get_drug_info("nao_existe")
    assert "error" in info
    assert "available_drugs" in info


def test_check_drug_interactions_qt():
    """Multiple QT-prolonging drugs should trigger warnings."""
    warnings = check_drug_interactions(["amiodarona", "fluoroquinolona", "haloperidol"])
    assert len(warnings) > 0
    assert any("QT" in w for w in warnings)


def test_check_drug_interactions_single_safe():
    """Single non-interacting drug should produce no high-risk warnings."""
    warnings = check_drug_interactions(["atropina"])
    assert not any("ALTO RISCO" in w for w in warnings)


def test_check_cocaine_betablocker():
    """Cocaine + betablocker should trigger contraindication."""
    warnings = check_drug_interactions(["cocaina", "betabloqueador"])
    assert any("CONTRAINDICAÇÃO" in w.upper() for w in warnings)


# ---------------------------------------------------------------------------
# ECG Generator — generate_ecg returns 12 leads
# ---------------------------------------------------------------------------


def test_generate_ecg_returns_12_leads():
    """generate_ecg must return all 12 standard leads."""
    ecg = generate_ecg(duration_s=2, fs=250)
    assert "leads" in ecg
    assert "time" in ecg
    assert "params" in ecg
    for lead in LEAD_NAMES:
        assert lead in ecg["leads"], f"Missing lead: {lead}"


def test_generate_ecg_lead_lengths_match_time():
    """All leads should have the same length as the time array."""
    ecg = generate_ecg(duration_s=3, fs=500)
    expected_len = len(ecg["time"])
    for lead_name, signal in ecg["leads"].items():
        assert len(signal) == expected_len, (
            f"Lead {lead_name}: expected {expected_len}, got {len(signal)}"
        )


def test_generate_ecg_stores_params():
    """Generated ECG should store input parameters."""
    ecg = generate_ecg(hr_bpm=80, pr_ms=180, qt_ms=400)
    assert ecg["params"]["hr_bpm"] == 80
    assert ecg["params"]["pr_ms"] == 180
    assert ecg["params"]["qt_ms"] == 400


def test_generate_ecg_different_hr():
    """Different heart rates should produce different signals."""
    ecg_slow = generate_ecg(hr_bpm=50, duration_s=2, fs=250, noise=0)
    ecg_fast = generate_ecg(hr_bpm=120, duration_s=2, fs=250, noise=0)
    assert not np.allclose(ecg_slow["leads"]["II"], ecg_fast["leads"]["II"])


# ---------------------------------------------------------------------------
# Pathological ECG — each supported pathology
# ---------------------------------------------------------------------------


SUPPORTED_PATHOLOGIES = [
    "normal", "stemi_anterior", "stemi_inferior", "lbbb", "rbbb",
    "af", "wpw", "hyperkalemia", "long_qt",
]


@pytest.mark.parametrize("pathology", SUPPORTED_PATHOLOGIES)
def test_generate_pathological_ecg(pathology):
    """Each supported pathology generates valid 12-lead ECG."""
    ecg = generate_pathological_ecg(pathology)
    assert ecg["pathology"] == pathology
    assert len(ecg["leads"]) == 12
    for lead_name in LEAD_NAMES:
        signal = ecg["leads"][lead_name]
        assert isinstance(signal, np.ndarray)
        assert len(signal) > 0
        assert np.all(np.isfinite(signal)), f"{lead_name} has non-finite values"


def test_unknown_pathology_raises():
    """Unknown pathology should raise ValueError."""
    with pytest.raises(ValueError, match="Unknown pathology"):
        generate_pathological_ecg("does_not_exist")


def test_long_qt_params():
    """long_qt should have QT >= 500 ms."""
    ecg = generate_pathological_ecg("long_qt")
    assert ecg["params"]["qt_ms"] >= 500


def test_lbbb_wide_qrs():
    """LBBB should have QRS >= 120 ms."""
    ecg = generate_pathological_ecg("lbbb")
    assert ecg["params"]["qrs_ms"] >= 120


def test_wpw_short_pr():
    """WPW should have short PR."""
    ecg = generate_pathological_ecg("wpw")
    assert ecg["params"]["pr_ms"] <= 120


# ---------------------------------------------------------------------------
# add_noise
# ---------------------------------------------------------------------------


def test_add_noise_changes_signal():
    """add_noise should alter the signal."""
    signal = np.sin(np.linspace(0, 2 * np.pi, 500))
    noisy = add_noise(signal, snr_db=10)
    assert not np.allclose(signal, noisy)
    assert len(noisy) == len(signal)


# ---------------------------------------------------------------------------
# ecg_to_plotly_figure returns valid figure
# ---------------------------------------------------------------------------


def test_ecg_to_plotly_figure_returns_valid_figure():
    """ecg_to_plotly_figure should return a Plotly Figure with 12 traces."""
    ecg = generate_ecg(duration_s=3, fs=250)
    fig = ecg_to_plotly_figure(ecg, layout="3x4")
    assert hasattr(fig, "data")
    assert hasattr(fig, "layout")
    assert len(fig.data) == 12


def test_ecg_to_plotly_figure_6x2():
    """6x2 layout should produce 12 traces."""
    ecg = generate_ecg(duration_s=3, fs=250)
    fig = ecg_to_plotly_figure(ecg, layout="6x2")
    assert len(fig.data) == 12


def test_ecg_to_plotly_figure_12x1():
    """12x1 layout should produce 12 traces."""
    ecg = generate_ecg(duration_s=3, fs=250)
    fig = ecg_to_plotly_figure(ecg, layout="12x1")
    assert len(fig.data) == 12


def test_ecg_to_plotly_invalid_layout():
    """Invalid layout should raise ValueError."""
    ecg = generate_ecg(duration_s=1, fs=250)
    with pytest.raises(ValueError, match="Unknown layout"):
        ecg_to_plotly_figure(ecg, layout="invalid")

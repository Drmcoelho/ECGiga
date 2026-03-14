"""Tests for simulation modules (p30)."""

import numpy as np

from simulation.ion_channels import ActionPotentialModel
from simulation.drug_effects import (
    DRUG_DATABASE,
    simulate_drug_effect,
    get_drug_info,
    check_drug_interactions,
)


def test_action_potential_normal():
    model = ActionPotentialModel()
    wf = model.compute_waveform(duration_ms=500, fs=1000)
    assert isinstance(wf, np.ndarray)
    assert len(wf) == 500
    assert wf.max() > wf.min()


def test_action_potential_hyperkalemia():
    model = ActionPotentialModel()
    model.apply_hyperkalemia("severe")
    assert model.k_extra > 7.0
    effects = model.get_ecg_effects()
    assert "apiculada" in effects["t_wave_change"].lower()


def test_action_potential_hypokalemia():
    model = ActionPotentialModel()
    model.apply_hypokalemia("severe")
    assert model.k_extra < 2.5
    effects = model.get_ecg_effects()
    assert "prolongado" in effects["qt_change"].lower()


def test_action_potential_hypercalcemia():
    model = ActionPotentialModel()
    model.apply_hypercalcemia()
    effects = model.get_ecg_effects()
    assert "encurtado" in effects["qt_change"].lower()


def test_ecg_effects_normal():
    model = ActionPotentialModel()
    effects = model.get_ecg_effects()
    assert "normalidade" in effects["description_pt"].lower() or "normal" in effects["description_pt"].lower()


# -- Drug effects --

def test_drug_database_not_empty():
    assert len(DRUG_DATABASE) >= 10


def test_get_drug_info_valid():
    info = get_drug_info("amiodarona")
    assert "camera_analogy" in info


def test_get_drug_info_invalid():
    info = get_drug_info("nonexistent_drug")
    assert "error" in info


def test_simulate_drug_effect():
    baseline = np.sin(np.linspace(0, 2 * np.pi, 500))
    modified = simulate_drug_effect(baseline, "digoxina")
    assert len(modified) == len(baseline)
    assert not np.array_equal(modified, baseline)


def test_check_drug_interactions_qt():
    warnings = check_drug_interactions(["amiodarona", "sotalol"])
    assert any("QT" in w for w in warnings)


def test_check_drug_interactions_safe():
    warnings = check_drug_interactions(["atropina"])
    # Single drug, no interactions expected (only warnings about specific combos)
    assert not any("ALTO RISCO" in w for w in warnings)


def test_check_drug_interactions_cocaine_beta():
    warnings = check_drug_interactions(["cocaina", "betabloqueador"])
    assert any("CONTRAINDICAÇÃO" in w.upper() for w in warnings)

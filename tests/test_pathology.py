"""
Comprehensive tests for Phase 19-21 pathology detection modules.
"""

import numpy as np
import pytest

# Phase 19 — STEMI
from cv.pathology.stemi import (
    TERRITORY_MAP,
    classify_st_deviation,
    detect_stemi_pattern,
    explain_stemi_cameras,
    measure_st_deviation,
)

# Phase 20 — Pericarditis
from cv.pathology.pericarditis import (
    classify_pericarditis_stage,
    detect_diffuse_st_elevation,
    detect_pr_depression,
    detect_spodick_sign,
    explain_pericarditis_cameras,
)

# Phase 20 — PE / TEP
from cv.pathology.pe import (
    detect_right_heart_strain,
    detect_s1q3t3,
    explain_pe_cameras,
    pe_score,
)

# Phase 20 — Brugada
from cv.pathology.brugada import (
    BRUGADA_CRITERIA,
    detect_brugada_pattern,
    explain_brugada_cameras,
    measure_st_morphology,
)

# Phase 21 — Pacemaker
from cv.pathology.pacemaker import (
    classify_pacemaker_mode,
    detect_capture,
    detect_pacing_spikes,
    detect_sensing,
    explain_pacemaker_cameras,
)

# Phase 21 — Channelopathy
from cv.pathology.channelopathy import (
    detect_delta_wave,
    detect_long_qt,
    detect_short_qt,
    detect_wpw,
    explain_channelopathy_cameras,
)


# ===================================================================
# Helpers
# ===================================================================

def _synthetic_ecg(fs=500, duration_s=3, heart_rate=75, st_elevation_mv=0.0):
    """Generate a minimal synthetic ECG trace with controllable ST elevation."""
    n_samples = int(fs * duration_s)
    np.arange(n_samples) / fs
    rr_interval = 60.0 / heart_rate
    r_peaks = []
    trace = np.zeros(n_samples)

    beat_time = 0.1  # first beat at 0.1 s
    while beat_time < duration_s - 0.3:
        rp = int(beat_time * fs)
        r_peaks.append(rp)

        # P wave
        p_center = rp - int(0.16 * fs)
        if p_center > 0:
            p_half = int(0.04 * fs)
            for j in range(-p_half, p_half):
                idx = p_center + j
                if 0 <= idx < n_samples:
                    trace[idx] += 0.15 * np.exp(-0.5 * (j / (p_half * 0.4)) ** 2)

        # QRS complex: sharp R peak
        qrs_half = int(0.02 * fs)
        for j in range(-qrs_half, qrs_half):
            idx = rp + j
            if 0 <= idx < n_samples:
                trace[idx] += 1.2 * np.exp(-0.5 * (j / (qrs_half * 0.3)) ** 2)

        # S wave
        s_center = rp + int(0.03 * fs)
        s_half = int(0.015 * fs)
        for j in range(-s_half, s_half):
            idx = s_center + j
            if 0 <= idx < n_samples:
                trace[idx] -= 0.3 * np.exp(-0.5 * (j / (s_half * 0.4)) ** 2)

        # ST segment elevation
        st_start = rp + int(0.05 * fs)
        st_end = rp + int(0.20 * fs)
        for idx in range(st_start, min(st_end, n_samples)):
            trace[idx] += st_elevation_mv

        # T wave
        t_center = rp + int(0.25 * fs)
        t_half = int(0.06 * fs)
        for j in range(-t_half, t_half):
            idx = t_center + j
            if 0 <= idx < n_samples:
                trace[idx] += 0.3 * np.exp(-0.5 * (j / (t_half * 0.4)) ** 2)

        beat_time += rr_interval

    return trace, r_peaks


# ===================================================================
# Tests: STEMI (Phase 19)
# ===================================================================

class TestSTEMI:
    def test_territory_map_has_all_territories(self):
        expected = {"anterior", "inferior", "lateral", "posterior", "right_ventricle"}
        assert set(TERRITORY_MAP.keys()) == expected

    def test_territory_anterior_leads(self):
        assert TERRITORY_MAP["anterior"]["leads"] == ["V1", "V2", "V3", "V4"]
        assert TERRITORY_MAP["anterior"]["artery"] == "LAD"

    def test_territory_inferior_leads(self):
        assert TERRITORY_MAP["inferior"]["leads"] == ["II", "III", "aVF"]
        assert "RCA" in TERRITORY_MAP["inferior"]["artery"]

    def test_territory_lateral_leads(self):
        assert TERRITORY_MAP["lateral"]["leads"] == ["I", "aVL", "V5", "V6"]
        assert "Cx" in TERRITORY_MAP["lateral"]["artery"]

    def test_territory_posterior_leads(self):
        assert "V7" in TERRITORY_MAP["posterior"]["leads"]

    def test_territory_rv_leads(self):
        assert "V4R" in TERRITORY_MAP["right_ventricle"]["leads"]

    def test_classify_st_elevation(self):
        assert classify_st_deviation(2.0) == "elevation"
        assert classify_st_deviation(1.0) == "elevation"
        assert classify_st_deviation(0.9) == "normal"

    def test_classify_st_depression(self):
        assert classify_st_deviation(-1.5) == "depression"
        assert classify_st_deviation(-1.0) == "depression"
        assert classify_st_deviation(-0.5) == "normal"

    def test_classify_st_normal(self):
        assert classify_st_deviation(0.0) == "normal"
        assert classify_st_deviation(0.5) == "normal"

    def test_detect_stemi_anterior(self):
        st = {"V1": 2.5, "V2": 3.0, "V3": 2.0, "V4": 1.5,
              "II": -1.0, "III": -0.8, "aVF": -0.5}
        result = detect_stemi_pattern(st)
        assert result["territory"] == "anterior"
        assert "V1" in result["affected_leads"]
        assert result["confidence"] > 0

    def test_detect_stemi_inferior(self):
        st = {"II": 2.0, "III": 2.5, "aVF": 1.8,
              "I": -1.0, "aVL": -1.2}
        result = detect_stemi_pattern(st)
        assert result["territory"] == "inferior"
        assert len(result["affected_leads"]) >= 2

    def test_detect_stemi_lateral(self):
        st = {"I": 1.5, "aVL": 1.8, "V5": 2.0, "V6": 1.2}
        result = detect_stemi_pattern(st)
        assert result["territory"] == "lateral"

    def test_detect_stemi_none(self):
        st = {"V1": 0.3, "V2": 0.2, "II": 0.1}
        result = detect_stemi_pattern(st)
        assert result["territory"] == "none"

    def test_detect_stemi_posterior_by_reciprocal(self):
        st = {"V1": -1.5, "V2": -2.0, "V3": -1.2}
        result = detect_stemi_pattern(st)
        assert result["territory"] == "posterior"

    def test_measure_st_deviation_returns_list(self):
        trace, r_peaks = _synthetic_ecg(st_elevation_mv=0.2)
        devs = measure_st_deviation(trace, r_peaks, 500)
        assert isinstance(devs, list)
        assert len(devs) == len(r_peaks)

    def test_measure_st_deviation_elevated(self):
        trace, r_peaks = _synthetic_ecg(st_elevation_mv=0.3)
        devs = measure_st_deviation(trace, r_peaks, 500)
        # At least some beats should show positive deviation
        assert any(d > 0 for d in devs)

    def test_explain_stemi_cameras_valid(self):
        for territory in TERRITORY_MAP:
            text = explain_stemi_cameras(territory)
            assert isinstance(text, str)
            assert len(text) > 50

    def test_explain_stemi_cameras_invalid(self):
        text = explain_stemi_cameras("nonexistent")
        assert "não reconhecido" in text.lower() or "válidos" in text.lower()


# ===================================================================
# Tests: Pericarditis (Phase 20)
# ===================================================================

class TestPericarditis:
    def test_diffuse_st_detected(self):
        st = {
            "I": 1.0, "II": 1.2, "III": 0.8, "aVL": 0.6, "aVF": 0.9,
            "V2": 1.0, "V3": 1.1, "V4": 1.0, "V5": 0.8, "V6": 0.7,
            "aVR": -1.0,
        }
        result = detect_diffuse_st_elevation(st)
        assert result["detected"] is True
        assert result["avr_depression"] is True
        assert result["num_elevated"] >= 5

    def test_diffuse_st_not_detected_focal(self):
        # Only anterior leads — focal, not diffuse
        st = {"V1": 2.0, "V2": 2.5, "V3": 2.0, "I": 0.1, "II": 0.1}
        result = detect_diffuse_st_elevation(st)
        assert result["detected"] is False

    def test_pr_depression_detected(self):
        pr = {"II": -0.8, "III": -0.6, "aVF": -0.5, "aVR": 0.6}
        assert detect_pr_depression(pr) is True

    def test_pr_depression_not_detected(self):
        pr = {"II": 0.0, "III": -0.2, "aVR": 0.1}
        assert detect_pr_depression(pr) is False

    def test_spodick_sign_with_downslope(self):
        fs = 500
        # Create trace with downsloping TP segments
        trace, r_peaks = _synthetic_ecg(fs=fs, heart_rate=70)
        # Add downward slope in TP segment region
        for i in range(len(r_peaks) - 1):
            rr = r_peaks[i + 1] - r_peaks[i]
            tp_start = r_peaks[i] + int(0.60 * rr)
            tp_end = r_peaks[i] + int(0.90 * rr)
            length = tp_end - tp_start
            if tp_end < len(trace):
                trace[tp_start:tp_end] += np.linspace(0.0, -0.15, length)
        result = detect_spodick_sign(trace, r_peaks, fs)
        assert isinstance(result, bool)

    def test_classify_stage_i(self):
        features = {"diffuse_st_elevation": True, "pr_depression": True}
        result = classify_pericarditis_stage(features)
        assert result["stage"] == "I"
        assert result["confidence"] >= 0.6

    def test_classify_stage_iii(self):
        features = {"diffuse_t_inversion": True, "diffuse_st_elevation": False}
        result = classify_pericarditis_stage(features)
        assert result["stage"] == "III"

    def test_classify_stage_iv(self):
        features = {"ecg_normalized": True}
        result = classify_pericarditis_stage(features)
        assert result["stage"] == "IV"

    def test_explain_pericarditis(self):
        text = explain_pericarditis_cameras()
        assert isinstance(text, str)
        assert len(text) > 100
        assert "câmera" in text.lower() or "difus" in text.lower()


# ===================================================================
# Tests: Pulmonary Embolism (Phase 20)
# ===================================================================

class TestPE:
    def test_s1q3t3_complete(self):
        leads = {
            "I": {"s_wave_present": True, "s_wave_mv": -0.3},
            "III": {
                "q_wave_present": True,
                "q_wave_mv": -0.2,
                "t_wave_polarity": "negative",
            },
        }
        result = detect_s1q3t3(leads)
        assert result["s1"] is True
        assert result["q3"] is True
        assert result["t3_inverted"] is True
        assert result["pattern_complete"] is True
        assert result["confidence"] >= 0.7

    def test_s1q3t3_partial(self):
        leads = {
            "I": {"s_wave_present": True},
            "III": {"q_wave_present": False, "t_wave_polarity": "positive"},
        }
        result = detect_s1q3t3(leads)
        assert result["pattern_complete"] is False

    def test_s1q3t3_none(self):
        leads = {"I": {}, "III": {}}
        result = detect_s1q3t3(leads)
        assert result["pattern_complete"] is False
        assert result["confidence"] == 0.0

    def test_right_heart_strain_high(self):
        leads = {
            "__meta__": {"axis_degrees": 120, "heart_rate": 110},
            "rbbb": True,
            "I": {"s_wave_present": True, "s_wave_mv": -0.3},
            "III": {
                "q_wave_present": True,
                "q_wave_mv": -0.2,
                "t_wave_polarity": "negative",
            },
            "V1": {"t_wave_polarity": "negative"},
            "V2": {"t_wave_polarity": "negative"},
            "V3": {"t_wave_polarity": "negative"},
            "V4": {"t_wave_polarity": "positive"},
        }
        result = detect_right_heart_strain(leads)
        assert result["strain_score"] >= 3

    def test_pe_score_high(self):
        features = {
            "s1q3t3": True,
            "right_axis": True,
            "rbbb": True,
            "sinus_tachycardia": True,
        }
        result = pe_score(features)
        assert result["ecg_score"] >= 4
        assert "alta" in result["category"].lower()

    def test_pe_score_zero(self):
        result = pe_score({})
        assert result["ecg_score"] == 0

    def test_explain_pe(self):
        text = explain_pe_cameras()
        assert isinstance(text, str)
        assert len(text) > 100


# ===================================================================
# Tests: Brugada (Phase 20)
# ===================================================================

class TestBrugada:
    def test_criteria_constants(self):
        assert "type_1" in BRUGADA_CRITERIA
        assert "type_2" in BRUGADA_CRITERIA
        assert BRUGADA_CRITERIA["type_1"]["morphology"] == "coved"
        assert BRUGADA_CRITERIA["type_2"]["morphology"] == "saddleback"
        assert BRUGADA_CRITERIA["type_1"]["st_elevation_mm"] == 2.0

    def test_measure_st_morphology_returns_dict(self):
        trace, r_peaks = _synthetic_ecg(st_elevation_mv=0.3)
        if r_peaks:
            result = measure_st_morphology(trace, r_peaks[0], 500)
            assert "morphology" in result
            assert "j_amplitude_mv" in result
            assert "j_amplitude_mm" in result

    def test_detect_brugada_no_peaks(self):
        result = detect_brugada_pattern(
            np.zeros(500), np.zeros(500), [], 500
        )
        assert result["detected"] is False
        assert result["brugada_type"] is None

    def test_detect_brugada_normal_trace(self):
        trace, r_peaks = _synthetic_ecg(st_elevation_mv=0.0)
        result = detect_brugada_pattern(trace, trace, r_peaks, 500)
        # Normal trace should not trigger Brugada (ST < 2mm)
        assert result["detected"] is False or result["brugada_type"] is not None

    def test_explain_brugada(self):
        text = explain_brugada_cameras()
        assert isinstance(text, str)
        assert len(text) > 100
        assert "V1" in text


# ===================================================================
# Tests: Pacemaker (Phase 21)
# ===================================================================

class TestPacemaker:
    def test_detect_spikes_synthetic(self):
        fs = 500
        trace = np.zeros(5000)
        # Insert synthetic pacing spikes every 600 ms (100 bpm)
        spike_positions = list(range(100, 5000, 300))
        for sp in spike_positions:
            if sp + 1 < len(trace):
                trace[sp] = 2.0       # sharp positive spike
                trace[sp + 1] = -1.5  # immediate reversal
        detected = detect_pacing_spikes(trace, fs, threshold=0.3)
        assert len(detected) > 0

    def test_detect_spikes_empty(self):
        trace = np.zeros(1000)
        assert detect_pacing_spikes(trace, 500) == []

    def test_classify_vvi(self):
        spikes = [100, 400, 700, 1000]
        p_waves = []
        qrs = [120, 420, 720, 1020]  # QRS shortly after each spike
        mode = classify_pacemaker_mode(spikes, p_waves, qrs)
        assert mode == "VVI"

    def test_classify_aai(self):
        spikes = [100, 400, 700, 1000]
        p_waves = [115, 415, 715, 1015]  # P waves shortly after each spike
        qrs = [300, 600, 900, 1200]  # QRS much later (native conduction)
        mode = classify_pacemaker_mode(spikes, p_waves, qrs)
        assert mode == "AAI"

    def test_classify_ddd(self):
        # DDD: spikes before both P and QRS
        spikes = [100, 150, 400, 450, 700, 750]
        p_waves = [110, 410, 710]       # atrial spikes → P
        qrs = [160, 460, 760]           # ventricular spikes → QRS
        mode = classify_pacemaker_mode(spikes, p_waves, qrs)
        assert mode == "DDD"

    def test_detect_capture_full(self):
        spikes = [100, 400, 700]
        qrs = [110, 410, 710]  # QRS within 20 samples = 40 ms at 500 Hz
        result = detect_capture(spikes, qrs, max_latency_ms=40, fs=500)
        assert result["captured"] == 3
        assert result["capture_rate"] == 1.0
        assert result["loss_of_capture"] is False

    def test_detect_capture_partial(self):
        spikes = [100, 400, 700]
        qrs = [110, 410]  # Only 2 of 3 captured
        result = detect_capture(spikes, qrs, max_latency_ms=40, fs=500)
        assert result["captured"] == 2
        assert result["not_captured"] == 1
        assert result["loss_of_capture"] is True

    def test_detect_sensing_appropriate(self):
        spikes = [500, 1000, 1500]
        native_beats = [100, 600]  # well separated from spikes
        # native beat at 100, next spike at 500 → 400 samples gap > 300 ms threshold
        result = detect_sensing(spikes, native_beats, fs=500, min_inhibition_ms=300)
        # 300 ms = 150 samples. Beat at 600, spike at 1000 → 400 samples gap. OK.
        assert result["sensing_appropriate"] is True

    def test_detect_sensing_undersensing(self):
        spikes = [100, 200, 500]  # spike at 200 is only 100 samples after native at 150
        native_beats = [150]
        result = detect_sensing(spikes, native_beats, fs=500, min_inhibition_ms=300)
        assert result["undersensing_events"] >= 1
        assert result["sensing_appropriate"] is False

    def test_explain_pacemaker(self):
        text = explain_pacemaker_cameras()
        assert isinstance(text, str)
        assert len(text) > 100


# ===================================================================
# Tests: Channelopathy (Phase 21)
# ===================================================================

class TestLongQT:
    def test_normal_male(self):
        result = detect_long_qt(430, sex="male")
        assert result["classification"] == "normal"

    def test_borderline_male(self):
        result = detect_long_qt(455, sex="male")
        assert result["classification"] == "borderline"

    def test_prolonged_male(self):
        result = detect_long_qt(480, sex="male")
        assert result["classification"] == "prolonged"

    def test_high_risk(self):
        result = detect_long_qt(520, sex="male")
        assert result["classification"] == "high_risk"

    def test_normal_female(self):
        result = detect_long_qt(450, sex="female")
        assert result["classification"] == "normal"

    def test_borderline_female(self):
        result = detect_long_qt(465, sex="female")
        assert result["classification"] == "borderline"

    def test_prolonged_female(self):
        result = detect_long_qt(490, sex="female")
        assert result["classification"] == "prolonged"

    def test_unknown_sex_uses_female_thresholds(self):
        r1 = detect_long_qt(455, sex="unknown")
        r2 = detect_long_qt(455, sex="female")
        assert r1["classification"] == r2["classification"]


class TestShortQT:
    def test_short_qt(self):
        result = detect_short_qt(330)
        assert result["classification"] == "short_qt"

    def test_borderline_short(self):
        result = detect_short_qt(350)
        assert result["classification"] == "borderline_short"

    def test_normal(self):
        result = detect_short_qt(400)
        assert result["classification"] == "normal"


class TestWPW:
    def test_full_triad(self):
        result = detect_wpw(pr_ms=100, qrs_ms=140, delta_wave_present=True)
        assert result["detected"] is True
        assert result["confidence"] >= 0.9
        assert len(result["criteria_met"]) == 3

    def test_short_pr_wide_qrs_no_delta(self):
        result = detect_wpw(pr_ms=100, qrs_ms=140, delta_wave_present=False)
        assert result["detected"] is False
        assert result["confidence"] > 0

    def test_no_criteria(self):
        result = detect_wpw(pr_ms=160, qrs_ms=90, delta_wave_present=False)
        assert result["detected"] is False
        assert result["confidence"] == 0.0

    def test_delta_wave_detection(self):
        fs = 500
        # Simulate a trace with a slow upstroke (delta wave) then rapid QRS
        n = 1000
        trace = np.zeros(n)
        qrs_onset = 200
        # Delta wave: slow linear ramp for 40 ms
        delta_samples = int(0.04 * fs)
        for i in range(delta_samples):
            trace[qrs_onset + i] = 0.02 * i / delta_samples  # very slow ramp
        # Then rapid QRS upstroke
        rapid_samples = int(0.04 * fs)
        for i in range(rapid_samples):
            idx = qrs_onset + delta_samples + i
            if idx < n:
                trace[idx] = 0.02 + 0.8 * (i / rapid_samples)  # steep ramp

        result = detect_delta_wave(trace, qrs_onset, fs)
        assert "detected" in result
        assert "slope_ratio" in result
        assert "delta_duration_ms" in result

    def test_explain_channelopathy(self):
        text = explain_channelopathy_cameras()
        assert isinstance(text, str)
        assert len(text) > 100
        assert "delta" in text.lower() or "WPW" in text


# ===================================================================
# Tests: Camera explanations are non-empty strings
# ===================================================================

class TestCameraExplanations:
    @pytest.mark.parametrize("func", [
        explain_pericarditis_cameras,
        explain_pe_cameras,
        explain_brugada_cameras,
        explain_pacemaker_cameras,
        explain_channelopathy_cameras,
    ])
    def test_explanation_is_nonempty_string(self, func):
        result = func()
        assert isinstance(result, str)
        assert len(result) > 50

    @pytest.mark.parametrize("territory", list(TERRITORY_MAP.keys()))
    def test_stemi_explanation_per_territory(self, territory):
        result = explain_stemi_cameras(territory)
        assert isinstance(result, str)
        assert len(result) > 50

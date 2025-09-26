import pytest
import math


def test_qtc_formulas():
    """Test QTc formulas correctness"""
    # Test data: QT=400ms, RR=800ms (HR=75 bpm)
    qt_ms = 400
    rr_ms = 800
    
    # QTc Bazett = QT / sqrt(RR_in_seconds)
    # RR = 800ms = 0.8s
    expected_bazett = qt_ms / math.sqrt(rr_ms / 1000.0)
    
    # QTc Fridericia = QT / (RR_in_seconds)^(1/3)
    expected_fridericia = qt_ms / ((rr_ms / 1000.0)**(1/3))
    
    # Manual calculation for verification
    # Bazett: 400 / sqrt(0.8) ≈ 400 / 0.8944 ≈ 447.2
    # Fridericia: 400 / (0.8)^(1/3) ≈ 400 / 0.9283 ≈ 430.9
    
    assert abs(expected_bazett - 447.2) < 1.0, f"Bazett calculation error: {expected_bazett}"
    assert abs(expected_fridericia - 430.9) < 1.0, f"Fridericia calculation error: {expected_fridericia}"


def test_axis_quadrant_classification():
    """Test axis classification based on lead I and aVF"""
    
    def classify_axis(lead_i_mv, avf_mv):
        """Classify cardiac axis based on lead I and aVF"""
        if lead_i_mv is None or avf_mv is None:
            return None
        if lead_i_mv >= 0 and avf_mv >= 0:
            return "Normal"
        if lead_i_mv >= 0 and avf_mv < 0:
            return "Desvio para a esquerda"
        if lead_i_mv < 0 and avf_mv >= 0:
            return "Desvio para a direita"
        return "Desvio extremo (noroeste)"
    
    # Test cases
    assert classify_axis(5, 3) == "Normal"  # Both positive
    assert classify_axis(5, -3) == "Desvio para a esquerda"  # I positive, aVF negative
    assert classify_axis(-5, 3) == "Desvio para a direita"  # I negative, aVF positive
    assert classify_axis(-5, -3) == "Desvio extremo (noroeste)"  # Both negative
    assert classify_axis(None, 3) is None  # Missing data
    assert classify_axis(5, None) is None  # Missing data


if __name__ == "__main__":
    pytest.main([__file__])
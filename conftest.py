"""Root conftest.py — shared fixtures for the ECGiga test suite."""

import json
import pathlib
import numpy as np
import pytest
from PIL import Image

REPO_ROOT = pathlib.Path(__file__).resolve().parent


def _make_synthetic_ecg_image(width=1200, height=400, grid_px=10):
    """Generate a synthetic ECG-like grayscale image with a visible grid."""
    img = np.full((height, width), 240, dtype=np.uint8)
    # Grid lines
    for x in range(0, width, grid_px):
        img[:, x] = 200
    for y in range(0, height, grid_px):
        img[y, :] = 200
    # Big grid
    for x in range(0, width, grid_px * 5):
        img[:, x] = 170
    for y in range(0, height, grid_px * 5):
        img[y, :] = 170
    # Synthetic trace (sine wave with QRS-like spikes)
    mid = height // 2
    for x in range(width):
        t = x / width
        # P wave
        y_p = int(5 * np.exp(-((t - 0.15) ** 2) / (2 * 0.001)))
        # QRS complex
        y_qrs = int(40 * np.exp(-((t - 0.3) ** 2) / (2 * 0.0002)))
        y_s = int(-15 * np.exp(-((t - 0.32) ** 2) / (2 * 0.0001)))
        # T wave
        y_t = int(10 * np.exp(-((t - 0.5) ** 2) / (2 * 0.005)))
        y_total = y_p + y_qrs + y_s + y_t
        y_pixel = mid - y_total
        y_pixel = max(0, min(height - 1, y_pixel))
        img[y_pixel, x] = 20  # dark trace
        # Thicken the trace
        for dy in range(-1, 2):
            yy = max(0, min(height - 1, y_pixel + dy))
            img[yy, x] = min(img[yy, x], 50)
    return img


def _make_12lead_image(width=1200, height=900, grid_px=10):
    """Generate a synthetic 12-lead ECG image (3 rows x 4 cols)."""
    img = np.full((height, width), 240, dtype=np.uint8)
    # Grid
    for x in range(0, width, grid_px):
        img[:, x] = 200
    for y in range(0, height, grid_px):
        img[y, :] = 200
    for x in range(0, width, grid_px * 5):
        img[:, x] = 170
    for y in range(0, height, grid_px * 5):
        img[y, :] = 170

    # Draw trace in each cell
    row_h = height // 3
    col_w = width // 4
    for r in range(3):
        for c in range(4):
            x0 = c * col_w
            y0 = r * row_h
            mid_y = y0 + row_h // 2
            phase = (r * 4 + c) * 0.3
            for x in range(x0, x0 + col_w):
                t = (x - x0) / col_w
                y_qrs = int(30 * np.exp(-((t - 0.3) ** 2) / (2 * 0.0003)))
                y_p = int(4 * np.exp(-((t - 0.15 + phase * 0.01) ** 2) / (2 * 0.001)))
                y_t = int(8 * np.exp(-((t - 0.5) ** 2) / (2 * 0.005)))
                y_pixel = mid_y - (y_qrs + y_p + y_t)
                y_pixel = max(0, min(height - 1, y_pixel))
                for dy in range(-1, 2):
                    yy = max(0, min(height - 1, y_pixel + dy))
                    img[yy, x] = min(img[yy, x], 50)
    return img


@pytest.fixture
def synthetic_gray():
    """A single-lead synthetic ECG grayscale numpy array."""
    return _make_synthetic_ecg_image()


@pytest.fixture
def synthetic_12lead():
    """A 12-lead synthetic ECG grayscale numpy array."""
    return _make_12lead_image()


@pytest.fixture
def synthetic_pil_image():
    """A single-lead synthetic ECG as PIL Image (RGB)."""
    gray = _make_synthetic_ecg_image()
    return Image.fromarray(np.stack([gray] * 3, axis=-1))


@pytest.fixture
def synthetic_12lead_pil():
    """A 12-lead synthetic ECG as PIL Image (RGB)."""
    gray = _make_12lead_image()
    return Image.fromarray(np.stack([gray] * 3, axis=-1))


@pytest.fixture
def synthetic_12lead_path(tmp_path, synthetic_12lead):
    """Save a 12-lead synthetic image to disk and return path."""
    path = tmp_path / "ecg_12lead.png"
    Image.fromarray(synthetic_12lead).save(str(path))
    return str(path)


@pytest.fixture
def sample_values_path():
    """Path to the sample values JSON."""
    return str(REPO_ROOT / "samples" / "values" / "exemplo1.json")


@pytest.fixture
def sample_values():
    """Loaded sample values dict."""
    p = REPO_ROOT / "samples" / "values" / "exemplo1.json"
    return json.loads(p.read_text(encoding="utf-8"))


@pytest.fixture
def sample_quiz_path():
    """Path to example quiz JSON."""
    return str(REPO_ROOT / "quiz" / "bank" / "exemplo_arrtimias.json")


@pytest.fixture
def mcq_schema():
    """Loaded MCQ schema dict."""
    p = REPO_ROOT / "quiz" / "schema" / "mcq.schema.json"
    return json.loads(p.read_text(encoding="utf-8"))


@pytest.fixture
def sample_report():
    """A minimal ECG report dict for testing quiz/export functionality."""
    return {
        "meta": {"src": "test.png", "w": 1200, "h": 900, "lead_used": "II"},
        "version": "0.5.0",
        "rpeaks": {"peaks_idx": [100, 350, 600], "rr_sec": [1.0, 1.0]},
        "intervals": {
            "median": {
                "PR_ms": 160.0,
                "QRS_ms": 90.0,
                "QT_ms": 380.0,
                "QTc_B": 380.0,
                "QTc_F": 370.0,
                "RR_s": 1.0,
            },
            "per_beat": {
                "PR_ms": [160.0],
                "QRS_ms": [90.0],
                "QT_ms": [380.0],
            },
        },
        "intervals_refined": {
            "median": {
                "PR_ms": 160.0,
                "QRS_ms": 90.0,
                "QT_ms": 380.0,
                "QTc_B": 380.0,
                "QTc_F": 370.0,
                "RR_s": 1.0,
            },
            "per_beat": {
                "PR_ms": [160.0, 162.0],
                "QRS_ms": [90.0, 92.0],
                "QT_ms": [380.0, 382.0],
                "onsets": [80, 330],
                "offsets": [120, 370],
                "t_end": [200, 450],
                "p_onset": [40, 290],
            },
        },
        "axis": {"angle_deg": 45.0, "label": "Normal"},
        "flags": ["Sem flags relevantes"],
    }

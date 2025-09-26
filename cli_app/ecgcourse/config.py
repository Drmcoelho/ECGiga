"""Central configuration constants for ECGCourse."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any


@dataclass(frozen=True)
class ECGConfig:
    """Typed configuration constants for ECGCourse."""
    
    # Image processing constants
    TARGET_PX_PER_MM: float = 10.0  # Target pixels per mm for normalization
    GRID_DETECTION_THRESHOLD: float = 0.7  # Confidence threshold for grid detection
    
    # R-peak detection thresholds
    RPEAK_MIN_HEIGHT: float = 0.3  # Minimum relative height for R-peak detection
    RPEAK_MIN_DISTANCE_MS: int = 200  # Minimum distance between R-peaks in ms
    RPEAK_WINDOW_SIZE: int = 15  # Window size for peak detection smoothing
    
    # QTc calculation constants
    QTC_MALE_THRESHOLD_MS: int = 450
    QTC_FEMALE_THRESHOLD_MS: int = 470
    QTC_DEFAULT_THRESHOLD_MS: int = 460
    QTC_SHORT_THRESHOLD_MS: int = 350
    
    # QRS width thresholds
    QRS_WIDE_THRESHOLD_MS: int = 120
    QRS_BORDERLINE_THRESHOLD_MS: int = 110
    
    # Heart rate constants
    MIN_HR_BPM: float = 30.0
    MAX_HR_BPM: float = 300.0
    
    # Lead analysis constants
    AXIS_NORMAL_RANGES: Dict[str, tuple[float, float]] = {
        "normal": (-30, 90),
        "left_deviation": (-90, -30),
        "right_deviation": (90, 180),
        "extreme": (-180, -90)
    }
    
    # Schema version constants
    DEFAULT_SCHEMA_VERSION: str = "v0.4"
    SUPPORTED_SCHEMA_VERSIONS: tuple[str, ...] = ("v0.1", "v0.2", "v0.3", "v0.4", "v0.5")
    
    # File processing
    SUPPORTED_IMAGE_FORMATS: tuple[str, ...] = (".png", ".jpg", ".jpeg", ".tiff", ".bmp")
    MAX_IMAGE_SIZE_MB: int = 50
    
    # Benchmarking constants
    SYNTHETIC_ECG_DURATION_S: float = 10.0
    SYNTHETIC_SAMPLING_RATE_HZ: int = 500
    NOISE_LEVELS: tuple[float, ...] = (0.01, 0.05, 0.1, 0.2)
    HEART_RATES_BPM: tuple[int, ...] = (60, 80, 100, 120)


# Global configuration instance
CONFIG = ECGConfig()
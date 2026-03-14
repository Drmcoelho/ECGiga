"""Pathology detection modules for ECG analysis.

Provides algorithmic detection of cardiac pathologies from ECG signal
features and interval measurements, including:

- Arrhythmia detection (AF, flutter, SVT, VT)
- Electrolyte disturbances (hyperkalemia, hypokalemia, hypercalcemia, hypocalcemia)
- Ischemia patterns (STEMI, NSTEMI, early repolarization differentiation)
- Conduction abnormalities (Brugada, WPW, bundle branch blocks)
- Demographic-adjusted thresholds (sex, age)
"""

from pathology.arrhythmia import (
    detect_atrial_fibrillation,
    detect_atrial_flutter,
    detect_rhythm_irregularity,
    classify_wide_complex_tachycardia,
)
from pathology.electrolyte import (
    detect_hyperkalemia_pattern,
    detect_hypokalemia_pattern,
    detect_calcium_abnormality,
)
from pathology.ischemia import (
    detect_nstemi_pattern,
    differentiate_stemi_vs_early_repol,
    detect_wellens_pattern,
    detect_de_winter_pattern,
)
from pathology.conduction import (
    detect_brugada_pattern,
    detect_digitalis_effect,
    classify_bundle_branch_block,
)
from pathology.thresholds import (
    get_adjusted_thresholds,
    get_stemi_criteria,
    get_qtc_thresholds,
)

__all__ = [
    "detect_atrial_fibrillation",
    "detect_atrial_flutter",
    "detect_rhythm_irregularity",
    "classify_wide_complex_tachycardia",
    "detect_hyperkalemia_pattern",
    "detect_hypokalemia_pattern",
    "detect_calcium_abnormality",
    "detect_nstemi_pattern",
    "differentiate_stemi_vs_early_repol",
    "detect_wellens_pattern",
    "detect_de_winter_pattern",
    "detect_brugada_pattern",
    "detect_digitalis_effect",
    "classify_bundle_branch_block",
    "get_adjusted_thresholds",
    "get_stemi_criteria",
    "get_qtc_thresholds",
]

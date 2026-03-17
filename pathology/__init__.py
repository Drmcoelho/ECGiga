"""Módulos de detecção de patologias para análise de ECG.

Fornece detecção algorítmica de patologias cardíacas a partir de
características do sinal de ECG e medições de intervalos, incluindo:

- Detecção de arritmias (FA, flutter, TSV, TV)
- Distúrbios eletrolíticos (hipercalemia, hipocalemia, hipercalcemia, hipocalcemia)
- Padrões isquêmicos (STEMI, NSTEMI, diferenciação de repolarização precoce)
- Anormalidades de condução (Brugada, WPW, bloqueios de ramo)
- Limiares ajustados por dados demográficos (sexo, idade)
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

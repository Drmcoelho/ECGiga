"""Utilitários de processamento de sinal para análise de ECG.

Fornece correção de oscilação de linha de base, filtragem passa-banda,
detecção de ruído, remoção de interferência da rede elétrica e
avaliação da qualidade do sinal.
"""

from signal_processing.filters import (
    bandpass_filter,
    highpass_filter,
    lowpass_filter,
    notch_filter,
    remove_baseline_wander,
)
from signal_processing.noise import (
    detect_noise_segments,
    estimate_snr,
    signal_quality_index,
)
from signal_processing.preprocessing import preprocess_ecg

__all__ = [
    "bandpass_filter",
    "highpass_filter",
    "lowpass_filter",
    "notch_filter",
    "remove_baseline_wander",
    "detect_noise_segments",
    "estimate_snr",
    "signal_quality_index",
    "preprocess_ecg",
]

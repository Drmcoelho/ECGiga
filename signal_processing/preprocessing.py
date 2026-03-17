"""Pipeline completo de pré-processamento de ECG.

Encadeia remoção de oscilação de linha de base, filtragem notch da rede elétrica,
filtragem passa-banda e avaliação de qualidade em um pipeline único e configurável.

Ordem recomendada do pipeline:
1. Remoção de oscilação de linha de base (passa-alta 0,5 Hz ou filtro mediano)
2. Filtro notch da rede elétrica (50/60 Hz + harmônicas)
3. Filtro passa-banda (0,05-150 Hz diagnóstico / 0,5-40 Hz monitorização)
4. Avaliação de qualidade
"""

from __future__ import annotations

from typing import Any

import numpy as np
from numpy.typing import NDArray


def preprocess_ecg(
    signal: NDArray[np.floating[Any]],
    fs: float,
    mode: str = "diagnostic",
    powerline_freq: float = 60.0,
    remove_baseline: bool = True,
    baseline_method: str = "highpass",
    remove_powerline: bool = True,
    apply_bandpass: bool = True,
    compute_quality: bool = True,
) -> dict[str, Any]:
    """Pipeline completo de pré-processamento de ECG.

    Parâmetros
    ----------
    signal : ndarray
        Sinal de ECG bruto (1D ou 2D [amostras, derivações]).
    fs : float
        Frequência de amostragem em Hz.
    mode : str
        'diagnostic' (0,05-150 Hz) ou 'monitoring' (0,5-40 Hz).
    powerline_freq : float
        Frequência da rede elétrica: 50 Hz (Europa/Brasil) ou 60 Hz (Américas).
    remove_baseline : bool
        Se deve remover oscilação de linha de base.
    baseline_method : str
        'highpass' ou 'median' para remoção de linha de base.
    remove_powerline : bool
        Se deve aplicar filtro notch para rede elétrica.
    apply_bandpass : bool
        Se deve aplicar filtro passa-banda.
    compute_quality : bool
        Se deve calcular o índice de qualidade do sinal.

    Retorna
    -------
    dict
        - signal: ndarray (sinal pré-processado)
        - fs: float
        - mode: str
        - steps_applied: list[str]
        - quality: dict (se compute_quality=True)
    """
    from signal_processing.filters import (
        bandpass_filter,
        notch_filter,
        remove_baseline_wander,
    )
    from signal_processing.noise import signal_quality_index

    if not isinstance(signal, np.ndarray):
        signal = np.asarray(signal, dtype=np.float64)

    if signal.dtype not in (np.float32, np.float64):
        signal = signal.astype(np.float64)

    # Valida modo
    if mode == "diagnostic":
        bp_low, bp_high = 0.05, 150.0
        bw_cutoff = 0.5
    elif mode == "monitoring":
        bp_low, bp_high = 0.5, 40.0
        bw_cutoff = 0.67
    else:
        raise ValueError(f"Unknown mode: {mode}. Use 'diagnostic' or 'monitoring'.")

    steps: list[str] = []
    processed = signal.copy()

    # Etapa 1: Remoção de oscilação de linha de base
    if remove_baseline:
        processed = remove_baseline_wander(
            processed, fs,
            method=baseline_method,
            cutoff=bw_cutoff,
        )
        steps.append(f"baseline_wander_removal({baseline_method}, cutoff={bw_cutoff}Hz)")

    # Etapa 2: Filtro notch da rede elétrica
    if remove_powerline:
        processed = notch_filter(
            processed, fs,
            freq=powerline_freq,
            quality=30.0,
            harmonics=3,
        )
        steps.append(f"notch_filter({powerline_freq}Hz, harmonics=3)")

    # Etapa 3: Filtro passa-banda
    if apply_bandpass:
        processed = bandpass_filter(
            processed, fs,
            lowcut=bp_low,
            highcut=bp_high,
        )
        steps.append(f"bandpass_filter({bp_low}-{bp_high}Hz)")

    result: dict[str, Any] = {
        "signal": processed,
        "fs": fs,
        "mode": mode,
        "steps_applied": steps,
    }

    # Etapa 4: Avaliação de qualidade (no sinal pré-processado)
    if compute_quality:
        if processed.ndim == 1:
            result["quality"] = signal_quality_index(processed, fs)
        else:
            # Multiderivação: avalia cada derivação, reporta a pior
            lead_qualities = []
            for i in range(processed.shape[1]):
                q = signal_quality_index(processed[:, i], fs)
                q["lead_index"] = i
                lead_qualities.append(q)

            # Qualidade geral é a pior derivação
            worst = min(lead_qualities, key=lambda q: q["sqi_score"])
            result["quality"] = worst
            result["quality_per_lead"] = lead_qualities

    return result

"""Filtros digitais para processamento de sinais de ECG.

Implementa filtros Butterworth passa-banda, passa-alta, passa-baixa e notch
com filtragem de fase zero (filtfilt) para processamento de ECG sem distorção.

Todos os filtros utilizam seções de segunda ordem (SOS) para estabilidade numérica.

Referências:
- Recomendações AHA/ACC para filtragem de ECG: 0,05-150 Hz para qualidade diagnóstica
- IEC 60601-2-51: 0,05-40 Hz para monitorização, 0,05-150 Hz para diagnóstico
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np
from numpy.typing import NDArray


def _validate_signal(signal: NDArray[np.floating[Any]], fs: float) -> None:
    """Valida os parâmetros de sinal e frequência de amostragem."""
    if not isinstance(signal, np.ndarray):
        raise TypeError("signal must be a numpy array")
    if signal.ndim not in (1, 2):
        raise ValueError(f"signal must be 1D or 2D, got {signal.ndim}D")
    if len(signal) < 10:
        raise ValueError(f"signal too short: {len(signal)} samples (minimum 10)")
    if fs <= 0:
        raise ValueError(f"sampling frequency must be positive, got {fs}")


def _pad_length(signal_length: int, order: int) -> int:
    """Calcula o comprimento de preenchimento apropriado para filtfilt."""
    # filtfilt precisa de pelo menos 3 * max(len(a), len(b)) amostras
    # Para SOS, cada seção é de ordem 2, então padding = 3 * (2 * n_sections + 1)
    pad = 3 * (2 * order + 1)
    # Não preencher mais do que o comprimento do sinal
    return min(pad, signal_length - 1)


def bandpass_filter(
    signal: NDArray[np.floating[Any]],
    fs: float,
    lowcut: float = 0.05,
    highcut: float = 150.0,
    order: int = 4,
) -> NDArray[np.floating[Any]]:
    """Aplica filtro passa-banda Butterworth de fase zero.

    Parâmetros
    ----------
    signal : ndarray
        Sinal de ECG (1D derivação única ou 2D multiderivação com forma [amostras, derivações]).
    fs : float
        Frequência de amostragem em Hz.
    lowcut : float
        Frequência de corte inferior em Hz (padrão 0,05 Hz conforme AHA).
    highcut : float
        Frequência de corte superior em Hz (padrão 150 Hz para qualidade diagnóstica).
    order : int
        Ordem do filtro (padrão 4, resultando em 8ª ordem após filtfilt).

    Retorna
    -------
    ndarray
        Sinal filtrado com a mesma forma da entrada.
    """
    from scipy.signal import butter, sosfiltfilt

    _validate_signal(signal, fs)
    nyq = fs / 2.0

    if lowcut <= 0 or highcut <= 0:
        raise ValueError("Cutoff frequencies must be positive")
    if lowcut >= highcut:
        raise ValueError(f"lowcut ({lowcut}) must be less than highcut ({highcut})")
    if highcut >= nyq:
        highcut = nyq * 0.99  # Limita logo abaixo de Nyquist

    low = lowcut / nyq
    high = highcut / nyq

    sos = butter(order, [low, high], btype="band", output="sos")

    if signal.ndim == 1:
        padlen = _pad_length(len(signal), order)
        return sosfiltfilt(sos, signal, padlen=padlen)
    else:
        # Multiderivação: filtra cada derivação independentemente
        result = np.empty_like(signal)
        padlen = _pad_length(signal.shape[0], order)
        for i in range(signal.shape[1]):
            result[:, i] = sosfiltfilt(sos, signal[:, i], padlen=padlen)
        return result


def highpass_filter(
    signal: NDArray[np.floating[Any]],
    fs: float,
    cutoff: float = 0.05,
    order: int = 4,
) -> NDArray[np.floating[Any]]:
    """Aplica filtro passa-alta Butterworth de fase zero.

    Utilizado principalmente para remoção de oscilação de linha de base.
    A AHA recomenda 0,05 Hz para ECG diagnóstico e 0,67 Hz para monitorização.

    Parâmetros
    ----------
    signal : ndarray
        Sinal de ECG.
    fs : float
        Frequência de amostragem em Hz.
    cutoff : float
        Frequência de corte em Hz (padrão 0,05 Hz).
    order : int
        Ordem do filtro.

    Retorna
    -------
    ndarray
        Sinal filtrado em passa-alta.
    """
    from scipy.signal import butter, sosfiltfilt

    _validate_signal(signal, fs)
    nyq = fs / 2.0

    if cutoff <= 0:
        raise ValueError("Cutoff frequency must be positive")
    if cutoff >= nyq:
        raise ValueError(f"Cutoff ({cutoff}) must be below Nyquist ({nyq})")

    sos = butter(order, cutoff / nyq, btype="high", output="sos")

    if signal.ndim == 1:
        padlen = _pad_length(len(signal), order)
        return sosfiltfilt(sos, signal, padlen=padlen)
    else:
        result = np.empty_like(signal)
        padlen = _pad_length(signal.shape[0], order)
        for i in range(signal.shape[1]):
            result[:, i] = sosfiltfilt(sos, signal[:, i], padlen=padlen)
        return result


def lowpass_filter(
    signal: NDArray[np.floating[Any]],
    fs: float,
    cutoff: float = 40.0,
    order: int = 4,
) -> NDArray[np.floating[Any]]:
    """Aplica filtro passa-baixa Butterworth de fase zero.

    Utilizado para remoção de ruído de alta frequência. 40 Hz é típico
    para modo de monitorização; 150 Hz para modo diagnóstico.

    Parâmetros
    ----------
    signal : ndarray
        Sinal de ECG.
    fs : float
        Frequência de amostragem em Hz.
    cutoff : float
        Frequência de corte em Hz (padrão 40 Hz).
    order : int
        Ordem do filtro.

    Retorna
    -------
    ndarray
        Sinal filtrado em passa-baixa.
    """
    from scipy.signal import butter, sosfiltfilt

    _validate_signal(signal, fs)
    nyq = fs / 2.0

    if cutoff <= 0:
        raise ValueError("Cutoff frequency must be positive")
    if cutoff >= nyq:
        cutoff = nyq * 0.99

    sos = butter(order, cutoff / nyq, btype="low", output="sos")

    if signal.ndim == 1:
        padlen = _pad_length(len(signal), order)
        return sosfiltfilt(sos, signal, padlen=padlen)
    else:
        result = np.empty_like(signal)
        padlen = _pad_length(signal.shape[0], order)
        for i in range(signal.shape[1]):
            result[:, i] = sosfiltfilt(sos, signal[:, i], padlen=padlen)
        return result


def notch_filter(
    signal: NDArray[np.floating[Any]],
    fs: float,
    freq: float = 60.0,
    quality: float = 30.0,
    harmonics: int = 3,
) -> NDArray[np.floating[Any]]:
    """Aplica filtro notch para remoção de interferência da rede elétrica.

    Remove a frequência fundamental e suas harmônicas.

    Parâmetros
    ----------
    signal : ndarray
        Sinal de ECG.
    fs : float
        Frequência de amostragem em Hz.
    freq : float
        Frequência da rede elétrica (50 Hz na Europa/Brasil, 60 Hz nas Américas).
    quality : float
        Fator de qualidade (Q = f0 / largura de banda). Maior = notch mais estreito.
    harmonics : int
        Número de harmônicas a remover (padrão 3: f0, 2*f0, 3*f0).

    Retorna
    -------
    ndarray
        Sinal filtrado com interferência da rede elétrica removida.
    """
    from scipy.signal import iirnotch, sosfiltfilt

    _validate_signal(signal, fs)
    nyq = fs / 2.0
    result = signal.copy()

    for h in range(1, harmonics + 1):
        notch_freq = freq * h
        if notch_freq >= nyq:
            break

        b, a = iirnotch(notch_freq, quality, fs)
        # Converte para SOS para estabilidade
        # iirnotch retorna b,a então usamos filtfilt diretamente
        from scipy.signal import filtfilt
        if result.ndim == 1:
            result = filtfilt(b, a, result)
        else:
            for i in range(result.shape[1]):
                result[:, i] = filtfilt(b, a, result[:, i])

    return result


def remove_baseline_wander(
    signal: NDArray[np.floating[Any]],
    fs: float,
    method: str = "highpass",
    cutoff: float = 0.5,
    window_s: float = 0.6,
) -> NDArray[np.floating[Any]]:
    """Remove oscilação de linha de base do sinal de ECG.

    Suporta dois métodos:
    - 'highpass': Filtro passa-alta Butterworth (rápido, padrão)
    - 'median': Filtro mediano em cascata (preserva melhor a morfologia)

    Parâmetros
    ----------
    signal : ndarray
        Sinal de ECG.
    fs : float
        Frequência de amostragem em Hz.
    method : str
        'highpass' ou 'median'.
    cutoff : float
        Frequência de corte para método highpass (padrão 0,5 Hz).
    window_s : float
        Duração da janela em segundos para método median (padrão 0,6s ~ intervalo QT).

    Retorna
    -------
    ndarray
        Sinal com oscilação de linha de base removida.
    """
    _validate_signal(signal, fs)

    if method == "highpass":
        return highpass_filter(signal, fs, cutoff=cutoff, order=2)

    elif method == "median":
        return _median_baseline_removal(signal, fs, window_s)

    else:
        raise ValueError(f"Unknown method: {method}. Use 'highpass' or 'median'.")


def _median_baseline_removal(
    signal: NDArray[np.floating[Any]],
    fs: float,
    window_s: float = 0.6,
) -> NDArray[np.floating[Any]]:
    """Remoção de linha de base por filtro mediano de duas passagens.

    Primeira passagem: filtro mediano com janela de ~200ms (captura QRS)
    Segunda passagem: filtro mediano com janela de ~600ms (captura onda T)
    Linha de base = resultado da segunda passagem, subtrai do original.

    Referência: de Chazal et al., IEEE TBME 2004.
    """
    from scipy.ndimage import median_filter

    def _apply_1d(sig: NDArray) -> NDArray:
        # Primeira passagem: janela curta para remover QRS
        win1 = max(int(0.2 * fs), 3)
        if win1 % 2 == 0:
            win1 += 1
        baseline1 = median_filter(sig, size=win1)

        # Segunda passagem: janela mais longa sobre resultado da primeira passagem
        win2 = max(int(window_s * fs), 3)
        if win2 % 2 == 0:
            win2 += 1
        baseline2 = median_filter(baseline1, size=win2)

        return sig - baseline2

    if signal.ndim == 1:
        return _apply_1d(signal)
    else:
        result = np.empty_like(signal)
        for i in range(signal.shape[1]):
            result[:, i] = _apply_1d(signal[:, i])
        return result

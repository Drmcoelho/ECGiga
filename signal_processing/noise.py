"""Detecção de ruído e avaliação de qualidade de sinal de ECG.

Fornece ferramentas para detecção de segmentos ruidosos, estimativa de
relação sinal-ruído e cálculo de índice composto de qualidade de sinal (SQI).

Referências:
- Clifford et al., "Signal quality indices and data fusion for
  determining clinical acceptability of electrocardiograms", Physiol Meas, 2012.
- Li et al., "Robust heart rate estimation from multiple asynchronous
  noisy sources", IEEE TBME, 2008.
"""

from __future__ import annotations

from typing import Any

import numpy as np
from numpy.typing import NDArray


def estimate_snr(
    signal: NDArray[np.floating[Any]],
    fs: float,
    method: str = "power_ratio",
) -> float:
    """Estima a relação sinal-ruído de um sinal de ECG.

    Parâmetros
    ----------
    signal : ndarray
        Sinal de ECG 1D.
    fs : float
        Frequência de amostragem em Hz.
    method : str
        Método de estimativa:
        - 'power_ratio': Razão entre potência na banda QRS e potência de ruído de alta frequência
        - 'template': SNR baseado em template usando batimento médio

    Retorna
    -------
    float
        SNR estimada em decibéis (dB).
    """
    if signal.ndim != 1:
        raise ValueError("signal must be 1D for SNR estimation")
    if len(signal) < int(fs * 2):
        raise ValueError("Need at least 2 seconds of signal for SNR estimation")

    if method == "power_ratio":
        return _snr_power_ratio(signal, fs)
    elif method == "template":
        return _snr_template(signal, fs)
    else:
        raise ValueError(f"Unknown method: {method}")


def _snr_power_ratio(signal: NDArray, fs: float) -> float:
    """SNR via razão de potência espectral.

    Banda de sinal: 5-40 Hz (contém QRS e principais componentes do ECG)
    Banda de ruído: 60-fs/2 Hz (contém principalmente ruído e rede elétrica)
    """
    from scipy.signal import welch

    freqs, psd = welch(signal, fs=fs, nperseg=min(len(signal), int(fs * 4)))

    # Banda de sinal: 5-40 Hz
    signal_mask = (freqs >= 5) & (freqs <= 40)
    signal_power = np.trapz(psd[signal_mask], freqs[signal_mask])

    # Banda de ruído: 60 Hz até Nyquist (ou 50-Nyquist dependendo da rede elétrica)
    noise_mask = freqs >= 60
    noise_power = np.trapz(psd[noise_mask], freqs[noise_mask]) if noise_mask.any() else 1e-10

    if noise_power <= 0:
        noise_power = 1e-10

    snr_db = 10 * np.log10(signal_power / noise_power)
    return float(snr_db)


def _snr_template(signal: NDArray, fs: float) -> float:
    """Estimativa de SNR baseada em template.

    Cria template de batimento médio a partir de picos R detectados, depois calcula
    SNR como razão entre potência do template e potência residual.
    """
    # Detecção simples de picos R para extração de template
    from scipy.signal import find_peaks

    # Aplica passa-banda no sinal primeiro para detecção de picos
    from signal_processing.filters import bandpass_filter
    filtered = bandpass_filter(signal, fs, lowcut=5, highcut=30)

    # Detecta picos R
    height = np.std(filtered) * 1.5
    distance = int(0.4 * fs)  # mínimo de 400ms entre batimentos
    peaks, _ = find_peaks(filtered, height=height, distance=distance)

    if len(peaks) < 5:
        # Batimentos insuficientes para template, recorre à razão de potência
        return _snr_power_ratio(signal, fs)

    # Extrai batimentos (150ms antes, 250ms após pico R)
    pre = int(0.15 * fs)
    post = int(0.25 * fs)
    beats = []
    for p in peaks:
        if p - pre >= 0 and p + post < len(signal):
            beats.append(signal[p - pre : p + post])

    if len(beats) < 3:
        return _snr_power_ratio(signal, fs)

    beats_arr = np.array(beats)
    template = np.mean(beats_arr, axis=0)

    # Calcula ruído residual
    residuals = beats_arr - template[np.newaxis, :]
    signal_power = np.mean(template ** 2)
    noise_power = np.mean(residuals ** 2)

    if noise_power <= 0:
        noise_power = 1e-10

    snr_db = 10 * np.log10(signal_power / noise_power)
    return float(snr_db)


def detect_noise_segments(
    signal: NDArray[np.floating[Any]],
    fs: float,
    window_s: float = 1.0,
    threshold_factor: float = 3.0,
) -> list[dict[str, Any]]:
    """Detecta segmentos ruidosos em um sinal de ECG.

    Utiliza análise de janela deslizante para identificar segmentos com
    variância anormalmente alta, detecção de linha plana e detecção de saturação.

    Parâmetros
    ----------
    signal : ndarray
        Sinal de ECG 1D.
    fs : float
        Frequência de amostragem em Hz.
    window_s : float
        Duração da janela de análise em segundos.
    threshold_factor : float
        Número de desvios padrão acima da variância mediana para classificar como ruidoso.

    Retorna
    -------
    list[dict]
        Lista de segmentos ruidosos, cada um com:
        - start_sample: int
        - end_sample: int
        - start_s: float (segundos)
        - end_s: float (segundos)
        - noise_type: str ('high_variance', 'flatline', 'saturation', 'spike')
        - severity: str ('low', 'moderate', 'high')
    """
    if signal.ndim != 1:
        raise ValueError("signal must be 1D")

    window = int(window_s * fs)
    if window < 10:
        window = 10

    n_windows = max(1, len(signal) // window)
    segments: list[dict[str, Any]] = []

    # Calcula estatísticas por janela
    variances = []
    ranges = []
    for i in range(n_windows):
        start = i * window
        end = min(start + window, len(signal))
        chunk = signal[start:end]
        variances.append(np.var(chunk))
        ranges.append(np.ptp(chunk))

    variances = np.array(variances)
    ranges = np.array(ranges)

    if len(variances) == 0:
        return segments

    median_var = np.median(variances)
    std_var = np.std(variances) if len(variances) > 1 else median_var

    # Evita divisão por zero
    if median_var < 1e-10:
        median_var = 1e-10
    if std_var < 1e-10:
        std_var = median_var * 0.1

    for i in range(n_windows):
        start = i * window
        end = min(start + window, len(signal))
        chunk = signal[start:end]

        # 1. Alta variância (artefato muscular, ruído de eletrodo)
        if variances[i] > median_var + threshold_factor * std_var:
            severity = "high" if variances[i] > median_var + 5 * std_var else "moderate"
            segments.append({
                "start_sample": start,
                "end_sample": end,
                "start_s": start / fs,
                "end_s": end / fs,
                "noise_type": "high_variance",
                "severity": severity,
            })

        # 2. Detecção de linha plana (desconexão de eletrodo)
        elif ranges[i] < median_var * 0.01:
            segments.append({
                "start_sample": start,
                "end_sample": end,
                "start_s": start / fs,
                "end_s": end / fs,
                "noise_type": "flatline",
                "severity": "high",
            })

        # 3. Detecção de saturação (clipagem do sinal)
        elif _detect_saturation(chunk):
            segments.append({
                "start_sample": start,
                "end_sample": end,
                "start_s": start / fs,
                "end_s": end / fs,
                "noise_type": "saturation",
                "severity": "high",
            })

    # 4. Detecção de espículas (no sinal inteiro)
    spike_segments = _detect_spikes(signal, fs, window)
    segments.extend(spike_segments)

    # Ordena por amostra inicial e mescla segmentos sobrepostos
    segments.sort(key=lambda s: s["start_sample"])

    return segments


def _detect_saturation(chunk: NDArray) -> bool:
    """Detecta saturação do sinal (clipagem) em um trecho."""
    if len(chunk) < 5:
        return False
    # Verifica se muitas amostras consecutivas estão no mesmo valor extremo
    max_val = chunk.max()
    min_val = chunk.min()
    at_max = (chunk == max_val).sum()
    at_min = (chunk == min_val).sum()
    # Mais de 10% das amostras no mesmo extremo = provável saturação
    return (at_max > len(chunk) * 0.1) or (at_min > len(chunk) * 0.1)


def _detect_spikes(signal: NDArray, fs: float, window: int) -> list[dict]:
    """Detecta espículas isoladas fisiologicamente implausíveis."""
    segments = []
    # Calcula primeira derivada
    diff = np.diff(signal)
    abs_diff = np.abs(diff)
    median_diff = np.median(abs_diff)
    if median_diff < 1e-10:
        median_diff = 1e-10

    # Espículas: derivada > 10x a mediana
    spike_threshold = median_diff * 10
    spike_indices = np.where(abs_diff > spike_threshold)[0]

    if len(spike_indices) == 0:
        return segments

    # Agrupa índices de espícula consecutivos
    groups = []
    current_group = [spike_indices[0]]
    for idx in spike_indices[1:]:
        if idx - current_group[-1] <= 3:  # dentro de 3 amostras
            current_group.append(idx)
        else:
            groups.append(current_group)
            current_group = [idx]
    groups.append(current_group)

    # Marca apenas espículas isoladas (duração muito curta)
    for group in groups:
        duration_ms = len(group) * 1000 / fs
        if duration_ms < 10:  # < 10ms = provável artefato, não QRS
            start = max(0, group[0] - int(0.01 * fs))
            end = min(len(signal), group[-1] + int(0.01 * fs))
            segments.append({
                "start_sample": start,
                "end_sample": end,
                "start_s": start / fs,
                "end_s": end / fs,
                "noise_type": "spike",
                "severity": "low",
            })

    return segments


def signal_quality_index(
    signal: NDArray[np.floating[Any]],
    fs: float,
) -> dict[str, Any]:
    """Calcula o índice composto de qualidade de sinal (SQI) para um sinal de ECG.

    Combina múltiplas métricas de qualidade em uma pontuação composta (0-100).

    Parâmetros
    ----------
    signal : ndarray
        Sinal de ECG 1D.
    fs : float
        Frequência de amostragem em Hz.

    Retorna
    -------
    dict
        - sqi_score: float (0-100, quanto maior melhor)
        - snr_db: float
        - noise_segments: int (quantidade de segmentos ruidosos detectados)
        - noise_fraction: float (0-1, fração do sinal que é ruidosa)
        - has_baseline_wander: bool
        - has_powerline_interference: bool
        - quality_label: str ('excellent', 'good', 'acceptable', 'poor', 'unusable')
        - details: dict com sub-pontuações
    """
    if signal.ndim != 1:
        raise ValueError("signal must be 1D")

    min_length = int(fs * 2)
    if len(signal) < min_length:
        return {
            "sqi_score": 0.0,
            "snr_db": 0.0,
            "noise_segments": 0,
            "noise_fraction": 1.0,
            "has_baseline_wander": False,
            "has_powerline_interference": False,
            "quality_label": "unusable",
            "details": {"reason": "signal too short"},
        }

    # 1. Pontuação de SNR (0-30 pontos)
    snr = estimate_snr(signal, fs)
    snr_score = min(30.0, max(0.0, (snr + 10) * 1.5))  # -10dB=0, 10dB=30

    # 2. Pontuação de segmentos ruidosos (0-30 pontos)
    noise_segs = detect_noise_segments(signal, fs)
    noise_samples = sum(s["end_sample"] - s["start_sample"] for s in noise_segs)
    noise_fraction = noise_samples / len(signal) if len(signal) > 0 else 0
    noise_score = max(0.0, 30.0 * (1.0 - noise_fraction * 2))

    # 3. Pontuação de oscilação de linha de base (0-20 pontos)
    has_bw = _check_baseline_wander(signal, fs)
    bw_score = 0.0 if has_bw else 20.0

    # 4. Pontuação de interferência da rede elétrica (0-20 pontos)
    has_pli = _check_powerline_interference(signal, fs)
    pli_score = 10.0 if has_pli else 20.0

    # SQI composto
    sqi = snr_score + noise_score + bw_score + pli_score

    # Rótulo de qualidade
    if sqi >= 85:
        label = "excellent"
    elif sqi >= 70:
        label = "good"
    elif sqi >= 50:
        label = "acceptable"
    elif sqi >= 30:
        label = "poor"
    else:
        label = "unusable"

    return {
        "sqi_score": round(sqi, 1),
        "snr_db": round(snr, 1),
        "noise_segments": len(noise_segs),
        "noise_fraction": round(noise_fraction, 3),
        "has_baseline_wander": has_bw,
        "has_powerline_interference": has_pli,
        "quality_label": label,
        "details": {
            "snr_score": round(snr_score, 1),
            "noise_score": round(noise_score, 1),
            "bw_score": round(bw_score, 1),
            "pli_score": round(pli_score, 1),
        },
    }


def _check_baseline_wander(signal: NDArray, fs: float) -> bool:
    """Verifica se o sinal possui oscilação de linha de base significativa (energia < 1 Hz)."""
    from scipy.signal import welch

    nperseg = min(len(signal), int(fs * 4))
    if nperseg < 64:
        return False

    freqs, psd = welch(signal, fs=fs, nperseg=nperseg)

    # Energia abaixo de 1 Hz vs energia total
    bw_mask = freqs < 1.0
    total_mask = freqs < 50.0

    bw_power = np.trapz(psd[bw_mask], freqs[bw_mask]) if bw_mask.any() else 0
    total_power = np.trapz(psd[total_mask], freqs[total_mask]) if total_mask.any() else 1e-10

    # Se >30% da potência da banda diagnóstica está abaixo de 1 Hz, provável oscilação de linha de base
    return (bw_power / max(total_power, 1e-10)) > 0.3


def _check_powerline_interference(signal: NDArray, fs: float) -> bool:
    """Verifica interferência da rede elétrica em 50 Hz ou 60 Hz."""
    from scipy.signal import welch

    nperseg = min(len(signal), int(fs * 4))
    if nperseg < 64:
        return False

    freqs, psd = welch(signal, fs=fs, nperseg=nperseg)
    freq_res = freqs[1] - freqs[0] if len(freqs) > 1 else 1.0

    for pli_freq in [50.0, 60.0]:
        if pli_freq >= fs / 2:
            continue
        # Verifica pico na frequência da rede elétrica
        idx = np.argmin(np.abs(freqs - pli_freq))
        if idx < 2 or idx >= len(psd) - 2:
            continue

        peak_power = psd[idx]
        # Compara com frequências vizinhas (±5 Hz)
        neighbors = psd[max(0, idx - int(5 / freq_res)):idx - int(2 / freq_res)]
        if len(neighbors) > 0:
            neighbor_power = np.median(neighbors)
            if neighbor_power > 0 and peak_power / neighbor_power > 5:
                return True

    return False

from typing import Dict, Optional

import numpy as np


def extract_trace_centerline(gray_crop: np.ndarray, band: float = 0.8) -> np.ndarray:
    """
    Constrói uma série 1D y(x) a partir do recorte da derivação:
    para cada coluna x, pega a posição do pixel mais escuro (mínimo) dentro de uma banda vertical central.
    'band' define a fração da altura considerada ao redor do meio (default 80%).
    Retorna vetor float com coordenadas y (em pixels, origem topo).
    """
    if gray_crop.ndim != 2:
        raise ValueError("Esperado gray 2D")
    h, w = gray_crop.shape
    cy0 = int((1 - band) * 0.5 * h)
    cy1 = int(h - cy0)
    center = []
    for x in range(w):
        col = gray_crop[cy0:cy1, x]
        y_local = int(np.argmin(col))
        center.append(cy0 + y_local)
    return np.array(center, dtype=float)


def smooth_signal(y: np.ndarray, win: int = 9) -> np.ndarray:
    win = max(3, int(win) | 1)  # ímpar
    ker = np.ones(win) / win
    return np.convolve(y, ker, mode="same")


def detect_rpeaks_from_trace(
    y: np.ndarray,
    px_per_sec: float,
    zthr: float = 2.0,
    min_bpm: float = 30.0,
    max_bpm: float = 220.0,
) -> Dict:
    """
    Detecção simples de R-peaks:
    - sinal invertido (picos para cima)
    - z-score e threshold (zthr)
    - distância mínima entre picos baseada em max_bpm
    Retorna dict com 'peaks_idx', 'rr_sec', 'hr_bpm_mean', 'hr_bpm_median'.
    """
    # converte posição (pixels) para "amplitude" invertida para destacar picos
    y_inv = -(y - np.median(y))
    # z-score
    z = (y_inv - np.mean(y_inv)) / (np.std(y_inv) + 1e-6)
    # distância mínima entre picos (em pixels)
    min_dist_sec = 60.0 / max_bpm
    min_dist_px = int(px_per_sec * min_dist_sec)
    if min_dist_px < 1:
        min_dist_px = 1
    # detecção: pico local com z > zthr e distância mínima
    peaks = []
    last = -1e9
    for i in range(1, len(z) - 1):
        if z[i] > zthr and z[i] >= z[i - 1] and z[i] >= z[i + 1]:
            if i - last >= min_dist_px:
                peaks.append(i)
                last = i
    # RR e FC
    rr_sec = []
    for a, b in zip(peaks, peaks[1:]):
        rr_sec.append((b - a) / px_per_sec)
    hr = [60.0 / r for r in rr_sec if r > 1e-6]
    hr_mean = float(np.mean(hr)) if hr else None
    hr_median = float(np.median(hr)) if hr else None
    return {
        "peaks_idx": peaks,
        "rr_sec": rr_sec,
        "hr_bpm_mean": hr_mean,
        "hr_bpm_median": hr_median,
    }


def estimate_px_per_sec(
    px_per_mm: Optional[float], speed_mm_per_sec: float = 25.0
) -> Optional[float]:
    return (px_per_mm * speed_mm_per_sec) if px_per_mm else None

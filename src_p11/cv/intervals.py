from typing import Dict, List, Optional, Tuple

import numpy as np


def _grad_abs(x: np.ndarray) -> np.ndarray:
    g = np.diff(x, prepend=x[:1])
    return np.abs(g)


def _find_onset_offset(
    sig: np.ndarray, center: int, fs: float, max_pre_ms=120.0, max_post_ms=120.0, th_rel=0.2
) -> Tuple[int, int]:
    """
    Encontra início/fim do QRS em torno do pico usando gradiente absoluto.
    th_rel: fração do pico de gradiente para limiar.
    """
    g = _grad_abs(sig)
    g = (g - g.min()) / (g.ptp() + 1e-6)
    # janelas
    pre = int(max_pre_ms * fs / 1000.0)
    pos = int(max_post_ms * fs / 1000.0)
    i0 = max(0, center - pre)
    i1 = min(len(sig) - 1, center + pos)
    gi = g[i0 : i1 + 1]
    # limiares
    gpk = gi.max()
    thr = th_rel * gpk
    # onset: último ponto antes do centro onde g < thr por 15 ms
    hold = int(0.015 * fs)
    onset = i0
    for i in range(center - i0, -1, -1):
        if np.all(gi[max(0, i - hold) : i + 1] < thr):
            onset = i0 + i
            break
    # offset: primeiro ponto depois onde g < thr por 15 ms
    offset = i1
    for i in range(center - i0, len(gi)):
        if np.all(gi[i : min(len(gi), i + hold)] < thr):
            offset = i0 + i
            break
    return onset, offset


def _t_end(sig: np.ndarray, qrs_off: int, fs: float, max_ms=520.0) -> Optional[int]:
    """
    Fim da onda T: após QRS, onde o gradiente retorna estável a ~0 por 30 ms.
    """
    g = _grad_abs(sig)
    g = (g - g.min()) / (g.ptp() + 1e-6)
    end_win = int(0.03 * fs)
    max_samp = int(max_ms * fs / 1000.0)
    i0 = qrs_off
    i1 = min(len(sig) - 1, qrs_off + max_samp)
    for i in range(i0, i1 - end_win):
        if np.all(g[i : i + end_win] < 0.08):
            return i
    return None


def _p_onset(sig: np.ndarray, qrs_on: int, fs: float, max_ms=280.0) -> Optional[int]:
    """
    Início da P: antes do QRS, procura pequeno aumento de energia sustentado por 20 ms.
    """
    g = _grad_abs(sig)
    g = (g - g.min()) / (g.ptp() + 1e-6)
    start_win = int(0.02 * fs)
    max_samp = int(max_ms * fs / 1000.0)
    i0 = max(0, qrs_on - max_samp)
    for i in range(qrs_on, i0, -1):
        if np.all(g[max(i - start_win, 0) : i] > 0.05):
            return i - start_win
    return None


def intervals_from_trace(y_px: np.ndarray, r_peaks: List[int], px_per_sec: float) -> Dict:
    """
    Calcula PR, QRS, QT e QTc (Bazett/Fridericia) a partir de traçado 1D e R-peaks.
    Usa medianas por batimento.
    """
    fs = float(px_per_sec)
    # centraliza para baseline
    y = y_px - np.median(y_px)
    onsets = []
    offsets = []
    Ts = []
    Ps = []
    for r in r_peaks:
        on, off = _find_onset_offset(y, r, fs)
        onsets.append(on)
        offsets.append(off)
        t_end = _t_end(y, off, fs)
        Ts.append(t_end)
        p_on = _p_onset(y, on, fs)
        Ps.append(p_on)
    # RR
    rr = [(b - a) / fs for a, b in zip(r_peaks, r_peaks[1:])]
    rr_med = float(np.median(rr)) if rr else None
    # PR, QRS, QT (em ms) por batimento
    PR = []
    QRS = []
    QT = []
    for i in range(len(r_peaks)):
        p = Ps[i]
        on = onsets[i]
        off = offsets[i]
        t = Ts[i]
        if p is not None and on is not None:
            PR.append((on - p) * 1000.0 / fs)
        if on is not None and off is not None:
            QRS.append((off - on) * 1000.0 / fs)
        if on is not None and t is not None:
            QT.append((t - on) * 1000.0 / fs)
    med = lambda arr: float(np.median(arr)) if arr else None
    pr_ms, qrs_ms, qt_ms = med(PR), med(QRS), med(QT)
    qtc_b = (qt_ms / (rr_med**0.5)) if (qt_ms and rr_med) else None
    qtc_f = (qt_ms / (rr_med ** (1 / 3))) if (qt_ms and rr_med) else None
    return {
        "per_beat": {"PR_ms": PR, "QRS_ms": QRS, "QT_ms": QT},
        "median": {
            "PR_ms": pr_ms,
            "QRS_ms": qrs_ms,
            "QT_ms": qt_ms,
            "QTc_B": qtc_b,
            "QTc_F": qtc_f,
            "RR_s": rr_med,
        },
    }

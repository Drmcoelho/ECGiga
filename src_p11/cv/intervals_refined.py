from typing import Dict, List, Optional, Tuple

import numpy as np


def _smooth(x: np.ndarray, win: int = 7) -> np.ndarray:
    win = max(3, int(win) | 1)
    k = np.ones(win) / win
    return np.convolve(x, k, mode="same")


def _grad(x):
    return np.diff(x, prepend=x[:1])


def _energy(x, win):
    win = max(3, int(win) | 1)
    k = np.ones(win) / win
    y = np.convolve(x * x, k, mode="same")
    return (y - y.min()) / (y.ptp() + 1e-9)


def _norm01(x):
    return (x - x.min()) / (x.ptp() + 1e-9)


def _stable(gabs, start, direction, fs, dur_ms=15, thr=0.12):
    dur = int(max(1, dur_ms * fs / 1000.0))
    if direction < 0:
        rng = range(start, -1, -1)
    else:
        rng = range(start, len(gabs))
    for i in rng:
        i0 = max(0, i - (dur if direction < 0 else 0))
        i1 = min(len(gabs), i + (dur if direction > 0 else 0))
        if np.all(gabs[i0:i1] < thr):
            return i
    return start


def find_onset_offset_refined(y_px: np.ndarray, r_idx: int, fs: float) -> Tuple[int, int]:
    y = y_px - np.median(y_px)
    y = _smooth(y, 7)
    g = _grad(y)
    gabs = _norm01(np.abs(g))
    E = _energy(y, win=int(0.04 * fs))
    pre = int(0.16 * fs)
    pos = int(0.18 * fs)
    i0 = max(0, r_idx - pre)
    i1 = min(len(y) - 1, r_idx + pos)
    gw = gabs[i0 : i1 + 1]
    Ew = E[i0 : i1 + 1]
    thr_g = 0.25 * np.quantile(gw, 0.98) + 0.05 * np.max(gw)
    thr_E = 0.25 * np.quantile(Ew, 0.98) + 0.05 * np.max(Ew)
    thr_g = float(np.clip(thr_g, 0.08, 0.6))
    thr_E = float(np.clip(thr_E, 0.08, 0.6))
    onset = i0
    for i in range(r_idx - i0, -1, -1):
        if gw[i] > thr_g or Ew[i] > thr_E:
            onset = i0 + _stable(gw, i, -1, fs, 15, 0.14)
            break
    offset = i1
    for i in range(r_idx - i0, len(gw)):
        if gw[i] > thr_g or Ew[i] > thr_E:
            offset = i0 + _stable(gw, i, +1, fs, 15, 0.14)
            break
    qrs_ms = (offset - onset) * 1000.0 / fs
    if qrs_ms < 60:
        offset = min(len(y) - 1, onset + int(0.08 * fs))
    if qrs_ms > 200:
        offset = onset + int(0.20 * fs)
    return int(onset), int(offset)


def p_onset_refined(y_px: np.ndarray, qrs_on: int, fs: float) -> Optional[int]:
    y = _smooth(y_px - np.median(y_px), 7)
    gabs = _norm01(np.abs(_grad(y)))
    i0 = max(0, qrs_on - int(0.32 * fs))
    thr = 0.06
    dur = int(0.02 * fs)
    for i in range(qrs_on, i0, -1):
        if np.all(gabs[max(0, i - dur) : i] > thr):
            return int(i - dur)
    return None


def t_end_refined(y_px: np.ndarray, qrs_off: int, fs: float) -> Optional[int]:
    y = _smooth(y_px - np.median(y_px), 7)
    gabs = _norm01(np.abs(_grad(y)))
    endw = int(0.03 * fs)
    i0 = qrs_off
    i1 = min(len(y) - 1, qrs_off + int(0.62 * fs))
    for i in range(i0 + endw, i1):
        if np.all(gabs[i - endw : i] < 0.10):
            return int(i)
    return None


def intervals_refined_from_trace(y_px: np.ndarray, r_peaks: List[int], px_per_sec: float) -> Dict:
    fs = float(px_per_sec)
    y = _smooth(y_px - np.median(y_px), 7)
    onsets = []
    offsets = []
    tend = []
    pons = []
    for r in r_peaks:
        on, off = find_onset_offset_refined(y, r, fs)
        onsets.append(on)
        offsets.append(off)
        tend.append(t_end_refined(y, off, fs))
        pons.append(p_onset_refined(y, on, fs))
    rr = [(b - a) / fs for a, b in zip(r_peaks, r_peaks[1:])]
    rr_med = float(np.median(rr)) if rr else None
    PR = []
    QRS = []
    QT = []
    for i in range(len(r_peaks)):
        po = pons[i]
        on = onsets[i]
        off = offsets[i]
        te = tend[i]
        if po is not None and on is not None:
            PR.append((on - po) * 1000.0 / fs)
        if on is not None and off is not None:
            QRS.append((off - on) * 1000.0 / fs)
        if on is not None and te is not None:
            QT.append((te - on) * 1000.0 / fs)
    med = lambda a: float(np.median(a)) if a else None
    pr_ms, qrs_ms, qt_ms = med(PR), med(QRS), med(QT)
    qtc_b = (qt_ms / (rr_med**0.5)) if (qt_ms and rr_med) else None
    qtc_f = (qt_ms / (rr_med ** (1 / 3))) if (qt_ms and rr_med) else None
    return {
        "method": "multi_evidence_v1",
        "per_beat": {
            "PR_ms": PR,
            "QRS_ms": QRS,
            "QT_ms": QT,
            "onsets": onsets,
            "offsets": offsets,
            "t_end": tend,
            "p_onset": pons,
        },
        "median": {
            "PR_ms": pr_ms,
            "QRS_ms": qrs_ms,
            "QT_ms": qt_ms,
            "QTc_B": qtc_b,
            "QTc_F": qtc_f,
            "RR_s": rr_med,
        },
    }

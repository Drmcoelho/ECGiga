from typing import Dict

import numpy as np


def _moving_avg(x: np.ndarray, win: int) -> np.ndarray:
    win = max(1, int(win))
    ker = np.ones(win, dtype=float) / win
    return np.convolve(x, ker, mode="same")


def _diff_ma_bandpass(x: np.ndarray, lo_win: int, hi_win: int) -> np.ndarray:
    """
    Filtro banda limitada usando diferença de médias móveis (hi-pass + low-pass simples).
    lo_win: janela curta (passa altas)  ~ 5-15 ms
    hi_win: janela longa (remove DC)    ~ 150-200 ms
    """
    lo = _moving_avg(x, lo_win)
    hi = _moving_avg(x, hi_win)
    return lo - hi


def _normalize(x: np.ndarray) -> np.ndarray:
    x = x - np.median(x)
    s = np.std(x) + 1e-6
    return x / s


def _integrator(y: np.ndarray, win: int) -> np.ndarray:
    # Integração por janela deslizante (média) — etapa final do Pan‑Tompkins
    return _moving_avg(y, win)


def pan_tompkins_like(
    y_px: np.ndarray,
    px_per_sec: float,
    lo_ms: float = 12.0,
    hi_ms: float = 180.0,
    deriv_ms: float = 8.0,
    integ_ms: float = 150.0,
    refractory_ms: float = 200.0,
    learn_sec: float = 2.0,
) -> Dict:
    """
    Pipeline Pan‑Tompkins-like sobre traçado 1D (posição em pixels ao longo do tempo em "colunas").
    Retorna picos R robustos e intermediários (sinais) para debug.
    """
    # 1) Sinal: inverter para que picos positivos representem complexos QRS
    y = -(y_px - np.median(y_px))
    fs = float(px_per_sec)
    # 2) Banda limitada (diferença de MAs)
    lo_win = max(1, int(lo_ms * fs / 1000.0))
    hi_win = max(lo_win + 1, int(hi_ms * fs / 1000.0))
    yb = _diff_ma_bandpass(y, lo_win, hi_win)
    # 3) Derivada e quadrado
    d_win = max(1, int(deriv_ms * fs / 1000.0))
    dy = np.diff(yb, prepend=yb[:1])
    dy = _moving_avg(dy, d_win)
    sq = dy * dy
    # 4) Integração janela
    i_win = max(1, int(integ_ms * fs / 1000.0))
    yi = _integrator(sq, i_win)
    yi = _normalize(yi)

    # 5) Threshold adaptativo estilo Pan‑Tompkins
    thr_spki = 0.0  # nível sinal
    thr_npki = 0.0  # nível ruído
    peaks = []
    rp = int(refractory_ms * fs / 1000.0)
    last_peak = -(10**9)

    # fase de aprendizado
    n_learn = int(learn_sec * fs)
    base = yi[: max(10, n_learn)]
    thr_npki = float(np.median(base))
    thr_spki = float(np.percentile(base, 95))
    THR1 = thr_npki + 0.25 * (thr_spki - thr_npki)

    for i in range(len(yi)):
        if yi[i] > THR1 and (i - last_peak) >= rp:
            # candidato a R: pico local
            if yi[i] >= yi[i - 1] and yi[i] >= yi[min(i + 1, len(yi) - 1)]:
                peaks.append(i)
                last_peak = i
                # atualiza níveis
                thr_spki = 0.875 * thr_spki + 0.125 * yi[i]
                THR1 = thr_npki + 0.25 * (thr_spki - thr_npki)
        else:
            # atualiza ruído lentamente
            thr_npki = 0.875 * thr_npki + 0.125 * yi[i]
            THR1 = thr_npki + 0.25 * (thr_spki - thr_npki)

    return {
        "peaks_idx": peaks,
        "fs_px": fs,
        "signals": {"yb": yb, "dy": dy, "sq": sq, "yi": yi},
        "params": {"lo_win": lo_win, "hi_win": hi_win, "d_win": d_win, "i_win": i_win, "rp": rp},
    }

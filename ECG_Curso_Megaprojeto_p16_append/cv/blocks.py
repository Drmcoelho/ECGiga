from __future__ import annotations

from typing import Dict, List, Tuple

import numpy as np
from PIL import Image

from .segmentation import find_content_bbox

try:
    from .segmentation_ext import segment_layout
except Exception:

    def segment_layout(gray, layout="3x4", bbox=None):
        x0, y0, x1, y1 = bbox or (0, 0, gray.shape[1], gray.shape[0])
        W, H = x1 - x0, y1 - y0
        LEADS = [["I", "II", "III", "aVR"], ["aVL", "aVF", "V1", "V2"], ["V3", "V4", "V5", "V6"]]
        out = []
        for r in range(3):
            for c in range(4):
                lx0 = x0 + int(c * W / 4)
                lx1 = x0 + int((c + 1) * W / 4)
                ly0 = y0 + int(r * H / 3)
                ly1 = y0 + int((r + 1) * H / 3)
                out.append({"lead": LEADS[r][c], "bbox": (lx0, ly0, lx1, ly1)})
        return out


from .grid_detect import estimate_grid_period_px
from .intervals_refined import intervals_refined_from_trace
from .rpeaks_from_image import estimate_px_per_sec
from .rpeaks_robust import pan_tompkins_like
from .trace import extract_trace_centerline, smooth_signal

PREC = ["V1", "V2", "V3", "V4", "V5", "V6"]


def _local_peaks(x: np.ndarray, win: int = 3) -> List[int]:
    """Pequenos picos locais (máximos) usando comparação de vizinhos."""
    idx = []
    for i in range(win, len(x) - win):
        seg = x[i - win : i + win + 1]
        if x[i] == seg.max() and (seg.argmax() == win):
            idx.append(i)
    return idx


def _rs_amplitudes(sig: np.ndarray, r_idx: int, fs: float) -> Tuple[float, float]:
    i0 = max(0, r_idx - int(0.06 * fs))
    i1 = min(len(sig) - 1, r_idx + int(0.12 * fs))
    basew0 = max(0, r_idx - int(0.12 * fs))
    basew1 = max(0, r_idx - int(0.08 * fs))
    base = (
        float(np.median(sig[basew0:basew1]))
        if (basew1 - basew0) > 3
        else float(np.median(sig[max(0, r_idx - 10) : r_idx]))
    )
    seg = sig[i0 : i1 + 1]
    if seg.size < 3:
        return 0.0, 0.0
    R = float(seg.max() - base)
    S = float(base - seg.min())
    return max(0.0, R), max(0.0, S)


def _qrs_peaks_pattern(sig: np.ndarray, rlist: List[int], fs: float) -> Dict[str, float]:
    """Conta picos positivos dentro da janela QRS (proxy para RSR' / entalhes)."""
    counts = []
    for r in rlist or []:
        i0 = max(0, r - int(0.06 * fs))
        i1 = min(len(sig) - 1, r + int(0.12 * fs))
        seg = sig[i0 : i1 + 1]
        idx = _local_peaks(seg, 2)
        counts.append(len(idx))
    return {"peaks_median": float(np.median(counts)) if counts else 0.0}


def detect_blocks(image_path: str, layout: str = "3x4", anchor_lead: str = "II") -> Dict:
    im = Image.open(image_path).convert("RGB")
    arr = np.asarray(im.convert("L"))
    bbox = find_content_bbox(arr)
    leads = segment_layout(arr, layout, bbox=bbox)
    lab2box = {d["lead"]: d["bbox"] for d in leads}
    # sampling
    g = estimate_grid_period_px(np.asarray(im))
    pxmm = g.get("px_small_x") or g.get("px_small_y") or 10.0
    fs = estimate_px_per_sec(pxmm, 25.0) or (pxmm * 25.0)

    # anchor for beats
    if anchor_lead not in lab2box:
        for cand in ("II", "V2", "V5", "I"):
            if cand in lab2box:
                anchor_lead = cand
                break
    x0, y0, x1, y1 = lab2box.get(anchor_lead, list(lab2box.values())[0])
    sig_anchor = smooth_signal(extract_trace_centerline(arr[y0:y1, x0:x1]), 11)
    rdet = pan_tompkins_like(sig_anchor, fs, zthr=2.0)
    rlist = rdet.get("peaks_idx") or []
    iv = intervals_refined_from_trace(sig_anchor, rlist, fs)
    qrs_ms = (iv.get("median") or {}).get("QRS_ms")

    # morphology V1/V2 and I/V6
    feats = {}
    # V1/V2: RSR' ou R dominante (BRD), V6: S alargado
    for lead in ("V1", "V2", "I", "V6"):
        if lead in lab2box:
            x0, y0, x1, y1 = lab2box[lead]
            sig = smooth_signal(extract_trace_centerline(arr[y0:y1, x0:x1]), 11)
            peaks = _qrs_peaks_pattern(sig, rlist, fs)["peaks_median"]
            ampR, ampS = 0.0, 0.0
            if rlist:
                valsR = []
                valsS = []
                for r in rlist:
                    R, S = _rs_amplitudes(sig, r, fs)
                    valsR.append(R)
                    valsS.append(S)
                ampR = float(np.median(valsR)) if valsR else 0.0
                ampS = float(np.median(valsS)) if valsS else 0.0
            feats[lead] = {"peaks": peaks, "R": ampR, "S": ampS, "RS_ratio": (ampR / (ampS + 1e-9))}

    # scoring simples
    brd_score = 0.0
    bre_score = 0.0
    if qrs_ms and qrs_ms >= 120:
        brd_score += 1.0
        bre_score += 1.0  # ambos exigem QRS largo
    v1 = feats.get("V1", {})
    v2 = feats.get("V2", {})
    v6 = feats.get("V6", {})
    leadI = feats.get("I", {})
    # BRD: em V1/V2 picos múltiplos (RSR') ou RS_ratio alto; e em I/V6 S proeminente
    if (
        max(v1.get("peaks", 0), v2.get("peaks", 0)) >= 2.0
        or max(v1.get("RS_ratio", 0), v2.get("RS_ratio", 0)) >= 1.5
    ):
        brd_score += 1.0
    if max(v6.get("S", 0), leadI.get("S", 0)) > 0.4 * max(v6.get("R", 1e-9), leadI.get("R", 1e-9)):
        brd_score += 0.5
    # BRE: I/V6 com R largo/entalhado (peaks>=2) e V1 negativo dominante (S≫R)
    if max(leadI.get("peaks", 0), v6.get("peaks", 0)) >= 2.0 and (
        v1.get("S", 0) > 1.2 * max(v1.get("R", 1e-9), 1e-9)
    ):
        bre_score += 1.5
    if max(leadI.get("R", 0), v6.get("R", 0)) > 1.5 * max(leadI.get("S", 1e-9), v6.get("S", 1e-9)):
        bre_score += 0.5

    label = "Sem bloqueio maior evidente"
    if max(brd_score, bre_score) >= 2.0:
        label = "Provável BRD" if brd_score >= bre_score else "Provável BRE"
    elif max(brd_score, bre_score) >= 1.5:
        label = "Sugerido bloqueio incompleto (ver morfologia)"
    evidence = {"qrs_ms": qrs_ms, "features": feats, "score": {"BRD": brd_score, "BRE": bre_score}}
    return {"label": label, **evidence}

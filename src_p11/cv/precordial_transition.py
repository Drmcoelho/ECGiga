from __future__ import annotations

from typing import Dict, List

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
from .rpeaks_from_image import estimate_px_per_sec
from .rpeaks_robust import pan_tompkins_like
from .trace import extract_trace_centerline, smooth_signal

PREC = ["V1", "V2", "V3", "V4", "V5", "V6"]


def _rs_ratio(sig: np.ndarray, rlist: List[int], fs: float) -> float:
    """R/S via pico e vale locais em janela ao redor de R. Retorna mediana dos batimentos."""
    vals = []
    for r in rlist or []:
        i0 = max(0, r - int(0.08 * fs))
        i1 = min(len(sig) - 1, r + int(0.12 * fs))
        seg = sig[i0 : i1 + 1]
        if seg.size < 3:
            continue
        R = float(seg.max())
        S = float(-min(0.0, seg.min()))
        if S <= 1e-6:
            continue
        vals.append(R / (S + 1e-9))
    return float(np.median(vals)) if vals else 0.0


def analyze_transition(image_path: str, layout: str = "3x4", anchor_lead: str = "II") -> Dict:
    im = Image.open(image_path).convert("RGB")
    arr = np.asarray(im.convert("L"))
    bbox = find_content_bbox(arr)
    leads = segment_layout(arr, layout, bbox=bbox)
    lab2box = {d["lead"]: d["bbox"] for d in leads}
    # batimentos de referência do lead âncora
    g = estimate_grid_period_px(np.asarray(im))
    pxmm = g.get("px_small_x") or g.get("px_small_y") or 10.0
    fs = estimate_px_per_sec(pxmm, 25.0) or (pxmm * 25.0)
    if anchor_lead not in lab2box:
        for cand in ("II", "V2", "V5", "I"):
            if cand in lab2box:
                anchor_lead = cand
                break
    x0, y0, x1, y1 = lab2box.get(anchor_lead, list(lab2box.values())[0])
    sig_anchor = smooth_signal(extract_trace_centerline(arr[y0:y1, x0:x1]), 11)
    rdet = pan_tompkins_like(sig_anchor, fs, zthr=2.0)
    rlist = rdet.get("peaks_idx") or []
    # R/S por precordial
    rs = {}
    for v in PREC:
        if v in lab2box:
            x0, y0, x1, y1 = lab2box[v]
            sig = smooth_signal(extract_trace_centerline(arr[y0:y1, x0:x1]), 11)
            rs[v] = _rs_ratio(sig, rlist, fs)
    # transição: primeira derivação com R/S >= 1
    trans = None
    for v in PREC:
        if v in rs and rs[v] >= 1.0:
            trans = v
            break
    pattern = "normal"
    if trans is not None:
        idx = PREC.index(trans)
        if idx <= 1:
            pattern = "transição precoce (≤V2)"
        elif idx >= 4:
            pattern = "transição tardia (≥V5)"
    return {"anchor": anchor_lead, "rs_ratio": rs, "transition_at": trans, "pattern": pattern}

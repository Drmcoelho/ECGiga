from __future__ import annotations

from typing import Dict

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
from .lvh_checklist import _px_per_mm_vertical, _r_s_mm
from .rpeaks_from_image import estimate_px_per_sec
from .rpeaks_robust import pan_tompkins_like
from .trace import extract_trace_centerline, smooth_signal


def hypertrophy_extended(image_path: str, sex: str = "male", layout: str = "3x4") -> Dict:
    im = Image.open(image_path).convert("RGB")
    arr = np.asarray(im.convert("L"))
    rgb = np.asarray(im)
    bbox = find_content_bbox(arr)
    leads = segment_layout(arr, layout, bbox=bbox)
    lab2box = {d["lead"]: d["bbox"] for d in leads}
    pxmm = (
        estimate_grid_period_px(rgb).get("px_small_x")
        or estimate_grid_period_px(rgb).get("px_small_y")
        or 10.0
    )
    fs = estimate_px_per_sec(pxmm, 25.0) or (pxmm * 25.0)
    py = _px_per_mm_vertical(rgb)
    # anchor for beats
    anchor = "II" if "II" in lab2box else next(iter(lab2box.keys()))
    x0, y0, x1, y1 = lab2box[anchor]
    sig_anchor = smooth_signal(extract_trace_centerline(arr[y0:y1, x0:x1]), 11)
    rdet = pan_tompkins_like(sig_anchor, fs, zthr=2.0)
    rlist = rdet.get("peaks_idx") or []
    iv = intervals_refined_from_trace(sig_anchor, rlist, fs)
    qrs_ms = (iv.get("median") or {}).get("QRS_ms") or 100.0

    # medidas necessárias
    def lead_sig(lead):
        x0, y0, x1, y1 = lab2box[lead]
        return smooth_signal(extract_trace_centerline(arr[y0:y1, x0:x1]), 11)

    RaVL = SV3 = SV1 = RV5 = RV6 = 0.0
    if "aVL" in lab2box:
        s = lead_sig("aVL")
        R, S = _r_s_mm(s, rlist, fs, py)
        RaVL = R
    if "V3" in lab2box:
        s = lead_sig("V3")
        R, S = _r_s_mm(s, rlist, fs, py)
        SV3 = S
    if "V1" in lab2box:
        s = lead_sig("V1")
        R, S = _r_s_mm(s, rlist, fs, py)
        SV1 = S
    if "V5" in lab2box:
        s = lead_sig("V5")
        R, S = _r_s_mm(s, rlist, fs, py)
        RV5 = R
    if "V6" in lab2box:
        s = lead_sig("V6")
        R, S = _r_s_mm(s, rlist, fs, py)
        RV6 = R

    cornell_mm = RaVL + SV3
    # Cornell product convencional em mm·ms (com calibração 10 mm = 1 mV)
    # Limiares usuais: > 2440 mm·ms (homem), > 2000 mm·ms (mulher)
    cornell_thr = 2440.0 if sex.lower().startswith("m") else 2000.0
    cornell_product = cornell_mm * qrs_ms
    cornell_pos = cornell_product > cornell_thr

    sokolow = SV1 + max(RV5, RV6)
    sokolow_pos = sokolow > 35.0

    # Eixo: se houver axis_hex em outro passo, decisão pode ser ajustada fora
    return {
        "sex": sex,
        "qrs_ms": qrs_ms,
        "measures_mm": {"R_aVL": RaVL, "S_V3": SV3, "S_V1": SV1, "R_V5": RV5, "R_V6": RV6},
        "sokolow_lyon_mm": sokolow,
        "cornell_mm": cornell_mm,
        "cornell_product_mm_ms": cornell_product,
        "thresholds": {"sokolow_mm": 35.0, "cornell_product_mm_ms": cornell_thr},
        "LVH_sokolow": bool(sokolow_pos),
        "LVH_cornell_product": bool(cornell_pos),
    }

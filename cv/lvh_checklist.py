
from __future__ import annotations
from typing import Dict, List, Tuple, Optional
import numpy as np
from PIL import Image
from .segmentation import find_content_bbox
try:
    from .segmentation_ext import segment_layout
except Exception:
    def segment_layout(gray, layout="3x4", bbox=None):
        x0,y0,x1,y1 = bbox or (0,0,gray.shape[1],gray.shape[0])
        W,H = x1-x0, y1-y0
        LEADS=[["I","II","III","aVR"],["aVL","aVF","V1","V2"],["V3","V4","V5","V6"]]
        out=[]
        for r in range(3):
            for c in range(4):
                lx0=x0+int(c*W/4); lx1=x0+int((c+1)*W/4)
                ly0=y0+int(r*H/3); ly1=y0+int((r+1)*H/3)
                out.append({"lead":LEADS[r][c], "bbox":(lx0,ly0,lx1,ly1)})
        return out

from .trace import extract_trace_centerline, smooth_signal
from .grid_detect import estimate_grid_period_px
from .rpeaks_from_image import estimate_px_per_sec
from .rpeaks_robust import pan_tompkins_like
from .intervals_refined import intervals_refined_from_trace

def _px_per_mm_vertical(rgb) -> float:
    """Usa grade para estimar px/mm vertical (y)."""
    from .grid_detect import estimate_grid_period_px
    g = estimate_grid_period_px(rgb)
    py = g.get("px_small_y") or g.get("px_small_x") or 10.0
    return float(py)

def _r_s_mm(sig: np.ndarray, rlist: List[int], fs: float, py_per_mm: float) -> Tuple[float,float]:
    """Medidas medianas de R (mm) e S (mm) via baseline local pré-QRS."""
    Rs, Ss = [], []
    for r in rlist:
        i0 = max(0, r - int(0.06*fs))
        i1 = min(len(sig)-1, r + int(0.12*fs))
        basew0 = max(0, r - int(0.12*fs)); basew1 = max(0, r - int(0.08*fs))
        base = float(np.median(sig[basew0:basew1])) if (basew1-basew0)>3 else float(np.median(sig[max(0,r-10):r]))
        seg = sig[i0:i1+1]
        if seg.size < 3: continue
        R = float(seg.max() - base)
        S = float(base - seg.min())
        Rs.append(max(0.0, R)/py_per_mm)
        Ss.append(max(0.0, S)/py_per_mm)
    med = lambda a: float(np.median(a)) if a else 0.0
    return med(Rs), med(Ss)

def lvh_checklist(image_path: str, sex: str = "male", layout: str = "3x4") -> Dict:
    im = Image.open(image_path).convert("RGB")
    arr = np.asarray(im.convert("L"))
    bbox = find_content_bbox(arr)
    leads = segment_layout(arr, layout, bbox=bbox)
    lab2box = {d["lead"]: d["bbox"] for d in leads}
    rgb = np.asarray(im)

    # amostragem temporal
    from .rpeaks_from_image import estimate_px_per_sec
    pxmm = (estimate_grid_period_px(rgb).get("px_small_x") or estimate_grid_period_px(rgb).get("px_small_y") or 10.0)
    fs = estimate_px_per_sec(pxmm, 25.0) or (pxmm*25.0)
    py = _px_per_mm_vertical(rgb)

    # picos a partir do lead II
    anchor = "II" if "II" in lab2box else next(iter(lab2box.keys()))
    x0,y0,x1,y1 = lab2box[anchor]
    sig_anchor = smooth_signal(extract_trace_centerline(arr[y0:y1, x0:x1]), 11)
    rdet = pan_tompkins_like(sig_anchor, fs, zthr=2.0); rlist = rdet.get("peaks_idx") or []

    def lead_sig(lead):
        x0,y0,x1,y1 = lab2box[lead]; return smooth_signal(extract_trace_centerline(arr[y0:y1, x0:x1]), 11)

    # S(V1), R(V5/V6), R(aVL), S(V3)
    SV1 = RV5 = RV6 = RaVL = SV3 = 0.0
    if "V1" in lab2box: 
        s = lead_sig("V1"); R,S = _r_s_mm(s, rlist, fs, py); SV1 = S
    if "V5" in lab2box:
        s = lead_sig("V5"); R,S = _r_s_mm(s, rlist, fs, py); RV5 = R
    if "V6" in lab2box:
        s = lead_sig("V6"); R,S = _r_s_mm(s, rlist, fs, py); RV6 = R
    if "aVL" in lab2box:
        s = lead_sig("aVL"); R,S = _r_s_mm(s, rlist, fs, py); RaVL = R
    if "V3" in lab2box:
        s = lead_sig("V3"); R,S = _r_s_mm(s, rlist, fs, py); SV3 = S

    # índices em mm (10 mm = 1 mV padrão)
    sokolow = SV1 + max(RV5, RV6)  # mm
    cornell_mm = RaVL + SV3        # mm
    cornell_mv = cornell_mm / 10.0 # mV

    # limiares: Sokolow-Lyon > 35 mm; Cornell > 28 mm (homem) / > 20 mm (mulher)
    cornell_thr_mm = 28.0 if sex.lower().startswith("m") else 20.0
    lvh_sokolow = sokolow > 35.0
    lvh_cornell = cornell_mm > cornell_thr_mm

    return {
        "anchor": anchor,
        "py_per_mm": py,
        "measures_mm": {"S_V1": SV1, "R_V5": RV5, "R_V6": RV6, "R_aVL": RaVL, "S_V3": SV3},
        "sokolow_lyon_mm": sokolow,
        "cornell_mm": cornell_mm,
        "cornell_mV": cornell_mv,
        "cornell_threshold_mm": cornell_thr_mm,
        "LVH_sokolow": bool(lvh_sokolow),
        "LVH_cornell": bool(lvh_cornell)
    }

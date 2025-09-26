
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

HEX_ANGLES = {
    "I":   0.0,
    "II":  60.0,
    "III": 120.0,
    "aVL": -30.0,
    "aVR": -150.0,  # ≡ +210°
    "aVF": 90.0,
}

def _net_qrs(sig: np.ndarray, r_idx: int, fs: float, pre_ms=80.0, post_ms=120.0) -> float:
    i0 = max(0, r_idx - int(pre_ms*fs/1000.0))
    i1 = min(len(sig)-1, r_idx + int(post_ms*fs/1000.0))
    seg = sig[i0:i1+1]
    if seg.size == 0: return 0.0
    return float(seg.max() + seg.min())

def _median_net(gray: np.ndarray, box: Tuple[int,int,int,int], rlist: List[int], fs: float) -> float:
    x0,y0,x1,y1 = box
    crop = gray[y0:y1, x0:x1]
    sig = extract_trace_centerline(crop)
    vals = [_net_qrs(sig, r, fs) for r in rlist] if rlist else [float(sig.max()+sig.min())]
    vals = [v for v in vals if abs(v) > 1e-6]
    return float(np.median(vals)) if vals else 0.0

def hexaxial_axis_from_image(image_path: str,
                             layout: str = "3x4",
                             anchor_lead: str = "II",
                             leads_set: Tuple[str,...] = ("I","II","III","aVR","aVL","aVF")) -> Dict:
    """Calcula o eixo por soma vetorial ponderada das 6 derivações frontais."""
    im = Image.open(image_path).convert("RGB")
    arr = np.asarray(im.convert("L"))
    bbox = find_content_bbox(arr)
    leads = segment_layout(arr, layout, bbox=bbox)
    lab2box = {d["lead"]: d["bbox"] for d in leads}
    # px/s
    g = estimate_grid_period_px(np.asarray(im))
    pxmm = g.get("px_small_x") or g.get("px_small_y") or 10.0
    fs = estimate_px_per_sec(pxmm, 25.0) or (pxmm*25.0)
    # R-peaks no anchor
    if anchor_lead not in lab2box:
        # fallback: usa aVF ou I
        for cand in ("II","I","aVF"):
            if cand in lab2box: anchor_lead = cand; break
    x0,y0,x1,y1 = lab2box.get(anchor_lead, list(lab2box.values())[0])
    crop_anchor = arr[y0:y1, x0:x1]
    sig_anchor = extract_trace_centerline(crop_anchor)
    rdet = pan_tompkins_like(smooth_signal(sig_anchor,11), fs, zthr=2.0)
    rlist = rdet.get("peaks_idx") or []
    # amplitudes por lead
    amps = {}
    used = []
    for lead in leads_set:
        box = lab2box.get(lead)
        if not box: 
            amps[lead] = 0.0
            continue
        a = _median_net(arr, box, rlist, fs)
        amps[lead] = a
        used.append(lead)
    # soma vetorial (ponderada por |amp|)
    vx, vy = 0.0, 0.0
    for lead, a in amps.items():
        ang = np.deg2rad(HEX_ANGLES[lead])
        w = abs(a) + 1e-9
        vx += w * np.cos(ang) * np.sign(a)
        vy += w * np.sin(ang) * np.sign(a)
    angle = float(np.degrees(np.arctan2(vy, vx)))
    if angle > 180: angle -= 360.0
    if angle <= -180: angle += 360.0
    # rótulo clínico
    label = "Normal"
    if angle < -30 and angle >= -90: label = "Desvio para a esquerda"
    elif angle > 90 and angle <= 180: label = "Desvio para a direita"
    elif angle < -90: label = "Desvio extremo (noroeste)"
    return {"angle_deg": angle, "label": label, "amps": amps, "leads_used": used, "anchor": anchor_lead}

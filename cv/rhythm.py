
from __future__ import annotations
from typing import Dict, List, Optional, Tuple
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

def _rr_features(peaks: List[int], fs: float) -> Dict[str, float]:
    if not peaks or len(peaks) < 2:
        return {"hr_bpm": None, "rr_mean_s": None, "sdnn_ms": None, "cv_rr": None}
    rr = np.diff(peaks)/fs
    hr = 60.0/np.median(rr)
    sdnn = 1000.0*float(np.std(rr, ddof=1)) if len(rr)>1 else 0.0
    cv = float(np.std(rr)/ (np.mean(rr)+1e-9))
    return {"hr_bpm": float(hr), "rr_mean_s": float(np.mean(rr)), "sdnn_ms": sdnn, "cv_rr": cv}

def _p_energy_heuristic(sig: np.ndarray, peaks: List[int], fs: float) -> float:
    """Energia média de baixa frequência antes do QRS (proxy rudimentar de P)."""
    if not peaks: return 0.0
    win = max(1, int(0.12*fs))
    e_vals = []
    for r in peaks:
        i0 = max(0, r - int(0.20*fs))
        i1 = max(0, r - int(0.06*fs))
        seg = sig[i0:i1]
        if seg.size > 3:
            y = seg - np.median(seg)
            e = float(np.mean(y*y))
            e_vals.append(e)
    return float(np.median(e_vals)) if e_vals else 0.0

def analyze_rhythm(image_path: str, lead: str = "II", layout: str = "3x4") -> Dict:
    im = Image.open(image_path).convert("RGB")
    arr = np.asarray(im.convert("L"))
    bbox = find_content_bbox(arr)
    leads = segment_layout(arr, layout, bbox=bbox)
    lab2box = {d["lead"]: d["bbox"] for d in leads}
    if lead not in lab2box:
        # fallback preferível
        for cand in ("II","I","V2","V5","aVF"):
            if cand in lab2box: lead = cand; break
    x0,y0,x1,y1 = lab2box.get(lead, list(lab2box.values())[0])
    crop = arr[y0:y1, x0:x1]
    sig = smooth_signal(extract_trace_centerline(crop), 11)
    # amostragem temporal
    g = estimate_grid_period_px(np.asarray(im))
    pxmm = g.get("px_small_x") or g.get("px_small_y") or 10.0
    fs = estimate_px_per_sec(pxmm, 25.0) or (pxmm*25.0)
    # picos
    rdet = pan_tompkins_like(sig, fs, zthr=2.0); peaks = rdet.get("peaks_idx") or []
    feats = _rr_features(peaks, fs)
    pE = _p_energy_heuristic(sig, peaks, fs)
    # Heurística de classificação (simples e honesta)
    label = "Indeterminado"
    notes = []
    if feats["hr_bpm"] is not None:
        if feats["cv_rr"] is not None and feats["cv_rr"] < 0.06 and feats["sdnn_ms"] < 60:
            label = "Provável sinusal (RR regular)"
        elif feats["cv_rr"] is not None and feats["cv_rr"] > 0.12 and feats["sdnn_ms"] > 100:
            label = "Irregular (suspeitar FA se P ausente)"
        else:
            label = "Possível irregularidade leve/variação sinusal"
    notes.append(f"P_heuristic_energy={pE:.3f}")
    return {"lead": lead, "fs": fs, "peaks": peaks, "features": feats, "p_hint": pE, "label": label, "notes": notes}

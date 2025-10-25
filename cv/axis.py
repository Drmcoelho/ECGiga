
import numpy as np
from typing import Dict, List, Optional, Tuple

def _centerline(gray_crop: np.ndarray, band: float = 0.8) -> np.ndarray:
    h, w = gray_crop.shape
    cy0 = int((1-band)*0.5*h); cy1 = int(h - cy0)
    y = []
    for x in range(w):
        col = gray_crop[cy0:cy1, x]
        y_local = int(np.argmin(col))
        y.append(cy0 + y_local)
    y = np.array(y, dtype=float)
    return -(y - np.median(y))

def _window(sig: np.ndarray, center: int, fs: float, pre_ms=80.0, post_ms=120.0) -> Tuple[int,int]:
    i0 = max(0, center - int(pre_ms*fs/1000.0))
    i1 = min(len(sig)-1, center + int(post_ms*fs/1000.0))
    return i0, i1

def net_qrs_amplitude(sig: np.ndarray, r_idx: int, fs: float) -> float:
    i0, i1 = _window(sig, r_idx, fs)
    seg = sig[i0:i1+1]
    if seg.size == 0: return 0.0
    return float(np.max(seg) + np.min(seg))

def frontal_axis_from_image(gray: np.ndarray,
                            boxes: Dict[str, Tuple[int,int,int,int]],
                            rpeaks: Dict[str, List[int]],
                            fs_map: Dict[str, float]) -> Dict:
    amps = {}
    for lead in ["I","aVF"]:
        box = boxes.get(lead)
        rlist = rpeaks.get(lead, [])
        if box is None: continue
        x0,y0,x1,y1 = box
        crop = gray[y0:y1, x0:x1]
        sig = _centerline(crop)
        fs = fs_map.get(lead, 250.0)
        vals = [net_qrs_amplitude(sig, r, fs) for r in rlist] if rlist else [float(sig.max()+sig.min())]
        vals = [v for v in vals if abs(v) > 1e-6]
        amps[lead] = float(np.median(vals)) if vals else 0.0
    I = amps.get("I", 0.0); aVF = amps.get("aVF", 0.0)
    angle = float(np.degrees(np.arctan2(aVF, I)))
    if angle > 180: angle -= 360.0
    if angle <= -180: angle += 360.0
    label = "Normal"
    if angle < -30 and angle >= -90: label = "Desvio para a esquerda"
    elif angle > 90 and angle <= 180: label = "Desvio para a direita"
    elif angle < -90: label = "Desvio extremo (noroeste)"
    return {"angle_deg": angle, "label": label, "amps": {"I": I, "aVF": aVF}}

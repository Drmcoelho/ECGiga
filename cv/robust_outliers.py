
from __future__ import annotations
from typing import Dict, List, Tuple
import numpy as np

def _nan_to_none(x):
    if x is None: return None
    try:
        if np.isnan(x): return None
    except Exception:
        pass
    return float(x)

def _mad_mask(vals: List[float], z: float = 2.5) -> List[bool]:
    """Retorna máscara booleana para valores dentro de z*MAD da mediana."""
    arr = np.asarray([v for v in vals if v is not None and not np.isnan(v)], dtype=float)
    if arr.size == 0:
        return [False]*len(vals)
    med = np.median(arr)
    mad = np.median(np.abs(arr - med)) + 1e-9
    lo, hi = med - z*1.4826*mad, med + z*1.4826*mad
    mask = []
    for v in vals:
        if v is None or (isinstance(v, float) and (v!=v)):
            mask.append(False)
        else:
            mask.append(lo <= v <= hi)
    return mask

def robust_from_intervals(intervals_refined: Dict, prefer: str = "QT_ms") -> Dict:
    """Calcula medianas robustas e máscara de batimentos usados a partir de intervals_refined.
    prefer: métrica-alvo para seleção primária de outliers (QT_ms por padrão)."""
    per = (intervals_refined or {}).get("per_beat") or {}
    PR  = per.get("PR_ms") or []
    QRS = per.get("QRS_ms") or []
    QT  = per.get("QT_ms") or []
    n = max(len(PR), len(QRS), len(QT))
    # normaliza tamanhos (preenche com None)
    def norm(a): 
        a = list(a); 
        if len(a) < n: a = a + [None]*(n-len(a)); 
        return a
    PR, QRS, QT = norm(PR), norm(QRS), norm(QT)
    base = QT if prefer == "QT_ms" else (QRS if prefer=="QRS_ms" else PR)
    m_mask = _mad_mask(base, z=2.7) if n>0 else []
    # máscara composta: também exclui QRS absurdos (<50 ou >240 ms)
    mask = []
    for i in range(n):
        ok = (m_mask[i] if i < len(m_mask) else True)
        if QRS[i] is not None:
            if QRS[i] < 50 or QRS[i] > 240: ok = False
        mask.append(bool(ok))
    # aplica máscara e recomputa medianas
    def med_masked(a):
        b = [x for x,m in zip(a, mask) if m and x is not None]
        return float(np.median(b)) if b else None
    pr_m, qrs_m, qt_m = med_masked(PR), med_masked(QRS), med_masked(QT)
    rr = (intervals_refined or {}).get("median",{}).get("RR_s")
    qtc_b = (qt_m/(rr**0.5)) if (qt_m and rr) else None
    qtc_f = (qt_m/(rr**(1/3))) if (qt_m and rr) else None
    return {
        "beats_total": n,
        "beats_used": int(sum(mask)),
        "mask": mask,
        "median_robust": {
            "PR_ms": _nan_to_none(pr_m),
            "QRS_ms": _nan_to_none(qrs_m),
            "QT_ms": _nan_to_none(qt_m),
            "QTc_B": _nan_to_none(qtc_b),
            "QTc_F": _nan_to_none(qtc_f),
            "RR_s": rr
        }
    }

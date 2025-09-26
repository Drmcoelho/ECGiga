
from __future__ import annotations
from typing import Dict, List, Tuple

def _is_num(x): 
    try:
        float(x); return True
    except Exception:
        return False

def validate_light(rep: Dict) -> List[str]:
    errs = []
    # chaves mínimas
    if "meta" not in rep: errs.append("faltando: meta")
    if "version" not in rep: errs.append("faltando: version")
    # intervals_refined (se presente)
    iv = rep.get("intervals_refined") or {}
    med = iv.get("median") or {}
    for k in ("PR_ms","QRS_ms","QT_ms","QTc_B","QTc_F"):
        v = med.get(k)
        if v is not None and not _is_num(v):
            errs.append(f"intervals_refined.median.{k} deve ser numérico")
    # eixo(s)
    for axk in ("axis","axis_hex"):
        ax = rep.get(axk)
        if ax:
            if not _is_num(ax.get("angle_deg")): errs.append(f"{axk}.angle_deg deve ser numérico")
            if "label" not in ax: errs.append(f"{axk}.label ausente")
    # flags string
    if "flags" in rep:
        if not isinstance(rep["flags"], list): errs.append("flags deve ser lista")
        else:
            for f in rep["flags"]:
                if not isinstance(f, str): errs.append("flags.* deve ser string")
    return errs

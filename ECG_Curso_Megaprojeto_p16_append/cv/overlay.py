from __future__ import annotations

from typing import Dict, List, Tuple

import numpy as np
from PIL import Image, ImageDraw

from .segmentation import find_content_bbox

try:
    from .segmentation_ext import segment_layout
except Exception:
    # fallback: quadrícula 3x4 simples
    def segment_layout(gray, layout="3x4", bbox=None):
        x0, y0, x1, y1 = bbox or (0, 0, gray.shape[1], gray.shape[0])  # (W,H)
        W, H = x1 - x0, y1 - y0
        rows, cols = 3, 4
        LEADS = [["I", "II", "III", "aVR"], ["aVL", "aVF", "V1", "V2"], ["V3", "V4", "V5", "V6"]]
        out = []
        for r in range(rows):
            for c in range(cols):
                lx0 = x0 + int(c * W / cols)
                lx1 = x0 + int((c + 1) * W / cols)
                ly0 = y0 + int(r * H / rows)
                ly1 = y0 + int((r + 1) * H / rows)
                out.append({"lead": LEADS[r][c], "bbox": (lx0, ly0, lx1, ly1)})
        return out


def draw_overlay(
    image_path: str,
    leads_boxes: Dict[str, Tuple[int, int, int, int]] | None,
    rpeaks_map: Dict[str, List[int]] | None,
    intervals: Dict | None,
    out_path: str,
    highlight_lead: str = "II",
) -> str:
    """Desenha linhas verticais nos R e barras em onset/offset do QRS no lead destaque."""
    im = Image.open(image_path).convert("RGB")
    arr = np.asarray(im.convert("L"))
    bbox = find_content_bbox(arr)
    leads = segment_layout(arr, "3x4", bbox=bbox)
    lab2box = {d["lead"]: d["bbox"] for d in leads}
    if leads_boxes:
        lab2box.update(leads_boxes)
    dr = ImageDraw.Draw(im, "RGBA")

    # desenha R-peaks (todas as leads) se fornecidas no espaço da imagem (índices relativos ao crop da lead)
    if rpeaks_map:
        for lab, peaks in rpeaks_map.items():
            box = lab2box.get(lab)
            if not box:
                continue
            x0, y0, x1, y1 = box
            w = x1 - x0
            h = y1 - y0
            for p in peaks or []:
                x = (
                    x0 + int((p / max(1, w)) * w)
                    if isinstance(p, float) and 0 <= p <= 1
                    else (x0 + int(p))
                )
                dr.line([(x, y0), (x, y1)], fill=(0, 128, 255, 120), width=2)

    # barras no lead destaque a partir de intervals.per_beat.onsets/offsets (índices do traçado 1D)
    if intervals and highlight_lead in lab2box:
        per = intervals.get("per_beat") or {}
        ons = per.get("onsets") or []
        offs = per.get("offsets") or []
        x0, y0, x1, y1 = lab2box[highlight_lead]
        for a, b in zip(ons, offs):
            xa = x0 + int(a)
            xb = x0 + int(b)
            dr.rectangle([(xa, y0), (xb, y1)], outline=(255, 0, 0, 160))

    im.save(out_path)
    return out_path

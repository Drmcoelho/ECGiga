import numpy as np


def find_content_bbox(gray, tol=250):
    """Retorna bbox (x0,y0,x1,y1) da área não-branca (heurística)."""
    mask = gray < tol
    ys, xs = np.where(mask)
    if len(xs) == 0 or len(ys) == 0:
        h, w = gray.shape
        return (0, 0, w, h)
    return (int(xs.min()), int(ys.min()), int(xs.max() + 1), int(ys.max() + 1))


def segment_12leads_basic(gray, layout="3x4", bbox=None, margin=0.02):
    """
    Segmentação simplificada: divide retângulo de conteúdo em 3 linhas x 4 colunas.
    Retorna lista de dicts: {lead, bbox:(x0,y0,x1,y1)}
    """
    h, w = gray.shape
    if bbox is None:
        bbox = find_content_bbox(gray)
    x0, y0, x1, y1 = bbox
    W = x1 - x0
    H = y1 - y0
    rows, cols = 3, 4
    mx = int(margin * W)
    my = int(margin * H)
    labels = ["I", "II", "III", "aVR", "aVL", "aVF", "V1", "V2", "V3", "V4", "V5", "V6"]
    out = []
    k = 0
    for r in range(rows):
        for c in range(cols):
            cx0 = x0 + c * W // cols + mx
            cx1 = x0 + (c + 1) * W // cols - mx
            cy0 = y0 + r * H // rows + my
            cy1 = y0 + (r + 1) * H // rows - my
            out.append({"lead": labels[k], "bbox": (int(cx0), int(cy0), int(cx1), int(cy1))})
            k += 1
    return out

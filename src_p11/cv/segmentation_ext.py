

def _grid_boxes(bbox, rows, cols, margin=0.02):
    x0, y0, x1, y1 = bbox
    W = x1 - x0
    H = y1 - y0
    mx = int(margin * W)
    my = int(margin * H)
    boxes = []
    for r in range(rows):
        for c in range(cols):
            cx0 = x0 + c * W // cols + mx
            cx1 = x0 + (c + 1) * W // cols - mx
            cy0 = y0 + r * H // rows + my
            cy1 = y0 + (r + 1) * H // rows - my
            boxes.append((int(cx0), int(cy0), int(cx1), int(cy1)))
    return boxes


def segment_layout(gray, layout="3x4", bbox=None, margin=0.02):
    """
    Suporta: '3x4', '6x2', '3x4+rhythm' (lead II longo inferior).
    Retorna lista de dicts {lead, bbox}.
    """
    from .segmentation import find_content_bbox

    if bbox is None:
        bbox = find_content_bbox(gray)
    x0, y0, x1, y1 = bbox
    if layout == "3x4":
        labels = ["I", "II", "III", "aVR", "aVL", "aVF", "V1", "V2", "V3", "V4", "V5", "V6"]
        boxes = _grid_boxes(bbox, 3, 4, margin)
        return [{"lead": lab, "bbox": box} for lab, box in zip(labels, boxes)]
    elif layout == "6x2":
        # linha 1: I, II, III, aVR, aVL, aVF  |  linha 2: V1..V6
        top_h = (y1 - y0) // 2
        top_bbox = (x0, y0, x1, y0 + top_h)
        bot_bbox = (x0, y0 + top_h, x1, y1)
        labs_top = ["I", "II", "III", "aVR", "aVL", "aVF"]
        labs_bot = ["V1", "V2", "V3", "V4", "V5", "V6"]
        boxes = []
        boxes += _grid_boxes(top_bbox, 1, 6, margin)
        boxes += _grid_boxes(bot_bbox, 1, 6, margin)
        return [{"lead": lab, "bbox": box} for lab, box in zip(labs_top + labs_bot, boxes)]
    elif layout == "3x4+rhythm":
        # 3x4 clássico + tira longa (II) em faixa inferior de 15% da altura
        base_h = int((y1 - y0) * 0.85)
        base_bbox = (x0, y0, x1, y0 + base_h)
        rhythm_bbox = (x0, y0 + base_h, x1, y1)
        labels = ["I", "II", "III", "aVR", "aVL", "aVF", "V1", "V2", "V3", "V4", "V5", "V6"]
        boxes = _grid_boxes(base_bbox, 3, 4, margin)
        out = [{"lead": lab, "bbox": box} for lab, box in zip(labels, boxes)]
        out.append({"lead": "II_rhythm", "bbox": (x0, y0 + base_h, x1, y1)})
        return out
    else:
        raise ValueError(f"Layout não suportado: {layout}")

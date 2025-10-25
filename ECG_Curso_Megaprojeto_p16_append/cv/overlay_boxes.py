from __future__ import annotations

from PIL import Image, ImageDraw

COLORS = {
    "P": (35, 132, 255, 200),
    "PR": (111, 66, 193, 200),
    "QRS": (220, 53, 69, 200),
    "ST": (255, 193, 7, 210),
    "T": (40, 167, 69, 200),
    "U": (23, 162, 184, 200),
    "artifact": (108, 117, 125, 200),
    "other": (0, 0, 0, 160),
}


def draw_boxes(
    image_path: str, annotations_json: str, out_path: str, show_labels: bool = True
) -> str:
    import json

    im = Image.open(image_path).convert("RGBA")
    overlay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    dr = ImageDraw.Draw(overlay)
    ann = json.load(open(annotations_json, "r", encoding="utf-8"))
    for b in ann.get("boxes", []):
        x, y, w, h = int(b["x"]), int(b["y"]), int(b["w"]), int(b["h"])
        lab = b.get("label", "other")
        color = COLORS.get(lab, (0, 0, 0, 160))
        dr.rectangle([x, y, x + w, y + h], outline=color, width=2)
        dr.rectangle([x, y - 16, x + min(64, w), y], fill=color)
        if show_labels:
            dr.text((x + 3, y - 14), lab, fill=(255, 255, 255, 255))
    out = Image.alpha_composite(im, overlay).convert("RGB")
    out.save(out_path)
    return out_path

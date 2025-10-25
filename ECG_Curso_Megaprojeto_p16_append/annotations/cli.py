from __future__ import annotations

import json
from pathlib import Path

import typer

app = typer.Typer(help="Ferramentas de anotações (p14)")


def _load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def _iou(a, b):
    ax0, ay0, ax1, ay1 = a["x"], a["y"], a["x"] + a["w"], a["y"] + a["h"]
    bx0, by0, bx1, by1 = b["x"], b["y"], b["x"] + b["w"], b["y"] + b["h"]
    ix0, iy0 = max(ax0, bx0), max(ay0, by0)
    ix1, iy1 = min(ax1, bx1), min(ay1, by1)
    iw, ih = max(0, ix1 - ix0), max(0, iy1 - iy0)
    inter = iw * ih
    aarea = (ax1 - ax0) * (ay1 - ay0)
    barea = (bx1 - bx0) * (by1 - by0)
    union = aarea + barea - inter + 1e-9
    return inter / union


@app.command("validate")
def validate(
    annotations_json: str = typer.Argument(..., help="annotations.json"),
    schema_path: str = typer.Option("reporting/schema/annotation.schema.v0.1.json", "--schema"),
):
    """Valida um JSON de anotações contra o schema v0.1."""
    try:
        import jsonschema  # opcional, se não houver, cai em validação básica
    except Exception:
        jsonschema = None
    ann = _load(annotations_json)
    if jsonschema:
        schema = _load(schema_path)
        jsonschema.validate(ann, schema)
        print("✓ Válido contra o schema.")
    else:
        # validação mínima
        assert "boxes" in ann and isinstance(ann["boxes"], list), "boxes ausente"
        print("✓ Estrutura básica ok (jsonschema não instalado).")


@app.command("compare")
def compare(
    pred_json: str = typer.Argument(..., help="annotations.json do aluno"),
    gt_json: str = typer.Argument(..., help="gabarito annotations.json"),
    iou_thr: float = typer.Option(0.3, "--iou", help="limiar IoU para acerto"),
    out_json: str = typer.Option(None, "--out", help="salvar métricas/metching"),
):
    """Compara anotações com gabarito por label e IoU → precisão/recall/F1."""
    pred = _load(pred_json)
    gt = _load(gt_json)
    labels = ["P", "PR", "QRS", "ST", "T", "U", "artifact", "other"]
    report = {"iou_thr": iou_thr, "per_label": {}, "macro_F1": None}
    all_f1 = []
    for lab in labels:
        P = [b for b in pred.get("boxes", []) if b.get("label") == lab]
        G = [b for b in gt.get("boxes", []) if b.get("label") == lab]
        used = set()
        tp = 0
        fp = 0
        fn = 0
        for a in P:
            best = -1.0
            best_j = -1
            for j, b in enumerate(G):
                if j in used:
                    continue
                i = _iou(a, b)
                if i > best:
                    best = i
                    best_j = j
            if best >= iou_thr and best_j >= 0:
                tp += 1
                used.add(best_j)
            else:
                fp += 1
        fn = len(G) - len(used)
        prec = tp / (tp + fp + 1e-9)
        rec = tp / (tp + fn + 1e-9)
        f1 = (2 * prec * rec) / (prec + rec + 1e-9)
        report["per_label"][lab] = {
            "TP": tp,
            "FP": fp,
            "FN": fn,
            "precision": prec,
            "recall": rec,
            "F1": f1,
        }
        all_f1.append(f1)
    report["macro_F1"] = sum(all_f1) / len(all_f1) if all_f1 else 0.0
    if out_json:
        Path(out_json).parent.mkdir(parents=True, exist_ok=True)
        Path(out_json).write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"Relatório salvo em {out_json}")
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))


@app.command("overlay")
def overlay(
    image_path: str = typer.Argument(..., help="PNG/JPG do caso"),
    annotations_json: str = typer.Argument(..., help="annotations.json"),
    out_image: str = typer.Option("reports/overlays/annotations_overlay.png", "--out"),
):
    """Gera overlay colorido com caixas e rótulos."""
    from cv.overlay_boxes import draw_boxes

    Path(out_image).parent.mkdir(parents=True, exist_ok=True)
    p = draw_boxes(image_path, annotations_json, out_image, show_labels=True)
    print(f"Overlay salvo em {p}")

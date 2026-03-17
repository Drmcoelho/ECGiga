"""
case_player.scorer
==================
Scoring and evaluation utilities for ECG case annotations.

Provides IoU calculation, annotation scoring, and Portuguese-language
feedback generation.
"""

from __future__ import annotations

from typing import Any


# ------------------------------------------------------------------
#  IoU (Intersection over Union)
# ------------------------------------------------------------------

def _box_area(box: dict) -> float:
    """Area of an axis-aligned bounding box ``{x, y, w, h}``."""
    return max(0.0, box["w"]) * max(0.0, box["h"])


def _intersect_area(a: dict, b: dict) -> float:
    """Intersection area of two axis-aligned bounding boxes."""
    x_left = max(a["x"], b["x"])
    y_top = max(a["y"], b["y"])
    x_right = min(a["x"] + a["w"], b["x"] + b["w"])
    y_bottom = min(a["y"] + a["h"], b["y"] + b["h"])
    if x_right <= x_left or y_bottom <= y_top:
        return 0.0
    return (x_right - x_left) * (y_bottom - y_top)


def calculate_iou(pred_boxes: list[dict], gt_boxes: list[dict]) -> float:
    """Compute mean best-match IoU between *pred_boxes* and *gt_boxes*.

    Each box is a dict ``{"x": float, "y": float, "w": float, "h": float}``.

    For every predicted box we find the ground-truth box with the
    highest IoU and average those best-match values.  If either list
    is empty the result is ``0.0``.

    Parameters
    ----------
    pred_boxes:
        Student / predicted bounding boxes.
    gt_boxes:
        Ground-truth (answer key) bounding boxes.

    Returns
    -------
    float
        Mean best-match IoU in ``[0, 1]``.
    """
    if not pred_boxes or not gt_boxes:
        return 0.0

    best_ious: list[float] = []
    for pred in pred_boxes:
        best = 0.0
        for gt in gt_boxes:
            inter = _intersect_area(pred, gt)
            union = _box_area(pred) + _box_area(gt) - inter
            if union > 0:
                iou = inter / union
                if iou > best:
                    best = iou
            best_ious.append(best)
            best = max(best_ious)  # running best for this pred
        best_ious_final = best  # best IoU for this pred box
        # replace appended intermediates with the final best
        best_ious = best_ious[: len(best_ious) - len(gt_boxes)] + [best_ious_final]

    # Simplified: recalculate cleanly
    best_ious = []
    for pred in pred_boxes:
        best = 0.0
        for gt in gt_boxes:
            inter = _intersect_area(pred, gt)
            union = _box_area(pred) + _box_area(gt) - inter
            if union > 0:
                iou = inter / union
                if iou > best:
                    best = iou
        best_ious.append(best)

    return sum(best_ious) / len(best_ious)


# ------------------------------------------------------------------
#  Annotation scoring
# ------------------------------------------------------------------

_IOU_THRESHOLD = 0.5


def score_annotations(student: dict, answer_key: dict) -> dict:
    """Score student annotations against an answer key.

    Both *student* and *answer_key* map label names to lists of boxes::

        {"P_wave": [{"x":…, "y":…, "w":…, "h":…}, …], …}

    Parameters
    ----------
    student:
        Student annotations, ``{label: [box, …]}``.
    answer_key:
        Ground-truth annotations, ``{label: [box, …]}``.

    Returns
    -------
    dict
        ``{"total_score", "per_label_scores", "tp", "fp", "fn", "macro_f1"}``
    """
    all_labels = set(list(answer_key.keys()) + list(student.keys()))

    tp_total = 0
    fp_total = 0
    fn_total = 0
    per_label: dict[str, dict[str, Any]] = {}
    f1_scores: list[float] = []

    for label in sorted(all_labels):
        gt_boxes = answer_key.get(label, [])
        pred_boxes = student.get(label, [])

        # Match each prediction to the best GT via IoU
        matched_gt: set[int] = set()
        tp = 0
        fp = 0

        for pred in pred_boxes:
            best_iou = 0.0
            best_idx = -1
            for gi, gt in enumerate(gt_boxes):
                if gi in matched_gt:
                    continue
                inter = _intersect_area(pred, gt)
                union = _box_area(pred) + _box_area(gt) - inter
                if union > 0:
                    iou = inter / union
                    if iou > best_iou:
                        best_iou = iou
                        best_idx = gi
            if best_iou >= _IOU_THRESHOLD and best_idx >= 0:
                tp += 1
                matched_gt.add(best_idx)
            else:
                fp += 1

        fn = len(gt_boxes) - len(matched_gt)

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

        per_label[label] = {
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
        }
        f1_scores.append(f1)

        tp_total += tp
        fp_total += fp
        fn_total += fn

    macro_f1 = sum(f1_scores) / len(f1_scores) if f1_scores else 0.0

    # Total score: percentage of GT boxes correctly matched
    total_gt = tp_total + fn_total
    total_score = tp_total / total_gt if total_gt > 0 else 0.0

    return {
        "total_score": round(total_score, 4),
        "per_label_scores": per_label,
        "tp": tp_total,
        "fp": fp_total,
        "fn": fn_total,
        "macro_f1": round(macro_f1, 4),
    }


# ------------------------------------------------------------------
#  Feedback generation (Portuguese)
# ------------------------------------------------------------------

def generate_feedback(score: dict) -> str:
    """Generate human-readable feedback in Portuguese from a *score* dict.

    Parameters
    ----------
    score:
        As returned by :func:`score_annotations`.

    Returns
    -------
    str
        Multi-line feedback text.
    """
    lines: list[str] = []

    total = score.get("total_score", 0)
    macro_f1 = score.get("macro_f1", 0)
    tp = score.get("tp", 0)
    fp = score.get("fp", 0)
    fn = score.get("fn", 0)

    # Overall assessment
    if total >= 0.9:
        lines.append("Excelente! Voce identificou quase todas as estruturas corretamente.")
    elif total >= 0.7:
        lines.append("Bom trabalho! A maioria das anotacoes esta correta.")
    elif total >= 0.5:
        lines.append("Resultado razoavel. Ha espaco para melhoria em algumas anotacoes.")
    else:
        lines.append("Resultado abaixo do esperado. Revise o conteudo e tente novamente.")

    lines.append("")
    lines.append(f"Pontuacao geral: {total:.0%}")
    lines.append(f"F1 macro: {macro_f1:.2f}")
    lines.append(f"Verdadeiros positivos: {tp}  |  Falsos positivos: {fp}  |  Falsos negativos: {fn}")

    # Per-label breakdown
    per_label = score.get("per_label_scores", {})
    if per_label:
        lines.append("")
        lines.append("Detalhamento por estrutura:")
        for label, metrics in per_label.items():
            status = "OK" if metrics["f1"] >= 0.8 else "Revisar"
            lines.append(
                f"  - {label}: F1={metrics['f1']:.2f}, "
                f"Precisao={metrics['precision']:.2f}, "
                f"Recall={metrics['recall']:.2f} [{status}]"
            )

    # Specific tips
    lines.append("")
    if fp > tp * 0.5 and tp > 0:
        lines.append(
            "Dica: Voce marcou varias regioes incorretas (falsos positivos). "
            "Tente ser mais seletivo nas anotacoes."
        )
    if fn > tp and tp > 0:
        lines.append(
            "Dica: Algumas estruturas nao foram marcadas (falsos negativos). "
            "Revise o tracado com atencao."
        )
    if tp == 0:
        lines.append(
            "Nenhuma anotacao coincidiu com a resposta esperada. "
            "Revise a teoria e tente novamente."
        )

    return "\n".join(lines)

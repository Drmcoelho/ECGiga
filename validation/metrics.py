"""Clinical validation metrics for ECG analysis.

Provides standard diagnostic metrics (sensitivity, specificity, PPV, NPV, F1),
inter-rater agreement statistics (Cohen's and Fleiss' kappa), and
Bland-Altman analysis for method comparison.
"""

from __future__ import annotations

import math


def sensitivity(tp: int, fn: int) -> float:
    """Calculate sensitivity (true positive rate / recall).

    sensitivity = TP / (TP + FN)
    """
    denom = tp + fn
    if denom == 0:
        return 0.0
    return tp / denom


def specificity(tn: int, fp: int) -> float:
    """Calculate specificity (true negative rate).

    specificity = TN / (TN + FP)
    """
    denom = tn + fp
    if denom == 0:
        return 0.0
    return tn / denom


def ppv(tp: int, fp: int) -> float:
    """Calculate positive predictive value (precision).

    PPV = TP / (TP + FP)
    """
    denom = tp + fp
    if denom == 0:
        return 0.0
    return tp / denom


def npv(tn: int, fn: int) -> float:
    """Calculate negative predictive value.

    NPV = TN / (TN + FN)
    """
    denom = tn + fn
    if denom == 0:
        return 0.0
    return tn / denom


def f1_score(tp: int, fp: int, fn: int) -> float:
    """Calculate F1 score (harmonic mean of precision and recall).

    F1 = 2 * (precision * recall) / (precision + recall)
    """
    precision = ppv(tp, fp)
    recall = sensitivity(tp, fn)
    denom = precision + recall
    if denom == 0:
        return 0.0
    return 2.0 * precision * recall / denom


def cohen_kappa(matrix: list[list[int]]) -> float:
    """Calculate Cohen's kappa for inter-rater agreement (2 raters).

    Args:
        matrix: Square confusion matrix as list of lists.
                matrix[i][j] = number of items rated i by rater 1, j by rater 2.

    Returns:
        Cohen's kappa coefficient (-1 to 1).
    """
    n = len(matrix)
    if n == 0:
        return 0.0

    total = sum(sum(row) for row in matrix)
    if total == 0:
        return 0.0

    # Observed agreement
    po = sum(matrix[i][i] for i in range(n)) / total

    # Expected agreement by chance
    pe = 0.0
    for k in range(n):
        row_sum = sum(matrix[k])
        col_sum = sum(matrix[i][k] for i in range(n))
        pe += (row_sum * col_sum) / (total * total)

    if pe == 1.0:
        return 1.0

    return (po - pe) / (1.0 - pe)


def fleiss_kappa(ratings: list[list[int]]) -> float:
    """Calculate Fleiss' kappa for multiple raters.

    Args:
        ratings: Matrix where ratings[i][j] = number of raters who assigned
                 category j to subject i. Each row sums to the same n (number of raters).

    Returns:
        Fleiss' kappa coefficient.
    """
    if not ratings or not ratings[0]:
        return 0.0

    N = len(ratings)  # number of subjects
    k = len(ratings[0])  # number of categories
    n = sum(ratings[0])  # number of raters per subject

    if N == 0 or n <= 1:
        return 0.0

    # P_i for each subject
    P = []
    for i in range(N):
        row_sum = sum(r * r for r in ratings[i])
        P_i = (row_sum - n) / (n * (n - 1)) if n > 1 else 0.0
        P.append(P_i)

    P_bar = sum(P) / N

    # p_j: proportion of all assignments to category j
    p = []
    total_assignments = N * n
    for j in range(k):
        col_sum = sum(ratings[i][j] for i in range(N))
        p.append(col_sum / total_assignments)

    P_e_bar = sum(pj * pj for pj in p)

    if P_e_bar == 1.0:
        return 1.0

    return (P_bar - P_e_bar) / (1.0 - P_e_bar)


def bland_altman(measured: list[float], reference: list[float]) -> dict:
    """Perform Bland-Altman analysis for method comparison.

    Args:
        measured: Values from the method being evaluated
        reference: Values from the reference/gold standard method

    Returns:
        Dict with keys: mean_diff, std_diff, upper_loa, lower_loa,
        differences, means, n
    """
    if len(measured) != len(reference):
        raise ValueError("measured and reference must have the same length")

    n = len(measured)
    if n == 0:
        return {
            "mean_diff": 0.0,
            "std_diff": 0.0,
            "upper_loa": 0.0,
            "lower_loa": 0.0,
            "differences": [],
            "means": [],
            "n": 0,
        }

    differences = [m - r for m, r in zip(measured, reference)]
    means = [(m + r) / 2.0 for m, r in zip(measured, reference)]

    mean_diff = sum(differences) / n

    if n > 1:
        variance = sum((d - mean_diff) ** 2 for d in differences) / (n - 1)
        std_diff = math.sqrt(variance)
    else:
        std_diff = 0.0

    upper_loa = mean_diff + 1.96 * std_diff
    lower_loa = mean_diff - 1.96 * std_diff

    return {
        "mean_diff": mean_diff,
        "std_diff": std_diff,
        "upper_loa": upper_loa,
        "lower_loa": lower_loa,
        "differences": differences,
        "means": means,
        "n": n,
    }


def generate_validation_report(results: dict) -> str:
    """Generate a human-readable validation summary from results.

    Args:
        results: Dict with keys like tp, fp, fn, tn, and optionally
                 measured, reference for Bland-Altman.

    Returns:
        Formatted string report.
    """
    lines = []
    lines.append("=" * 60)
    lines.append("CLINICAL VALIDATION REPORT")
    lines.append("=" * 60)
    lines.append("")

    tp = results.get("tp", 0)
    fp = results.get("fp", 0)
    fn = results.get("fn", 0)
    tn = results.get("tn", 0)

    sens = sensitivity(tp, fn)
    spec = specificity(tn, fp)
    pos_pv = ppv(tp, fp)
    neg_pv = npv(tn, fn)
    f1 = f1_score(tp, fp, fn)

    lines.append("Confusion Matrix:")
    lines.append(f"  TP = {tp}, FP = {fp}")
    lines.append(f"  FN = {fn}, TN = {tn}")
    lines.append("")
    lines.append("Diagnostic Metrics:")
    lines.append(f"  Sensitivity (Recall): {sens:.4f}")
    lines.append(f"  Specificity:          {spec:.4f}")
    lines.append(f"  PPV (Precision):      {pos_pv:.4f}")
    lines.append(f"  NPV:                  {neg_pv:.4f}")
    lines.append(f"  F1 Score:             {f1:.4f}")
    lines.append("")

    # Bland-Altman if data present
    measured = results.get("measured")
    reference = results.get("reference")
    if measured and reference and len(measured) == len(reference):
        ba = bland_altman(measured, reference)
        lines.append("Bland-Altman Analysis:")
        lines.append(f"  N:                    {ba['n']}")
        lines.append(f"  Mean Difference:      {ba['mean_diff']:.4f}")
        lines.append(f"  SD of Differences:    {ba['std_diff']:.4f}")
        lines.append(f"  Upper LoA (+1.96 SD): {ba['upper_loa']:.4f}")
        lines.append(f"  Lower LoA (-1.96 SD): {ba['lower_loa']:.4f}")
        lines.append("")

    # Kappa if matrix present
    kappa_matrix = results.get("kappa_matrix")
    if kappa_matrix:
        kappa = cohen_kappa(kappa_matrix)
        lines.append("Inter-rater Agreement:")
        lines.append(f"  Cohen's Kappa:        {kappa:.4f}")
        if kappa < 0.0:
            interp = "Less than chance agreement"
        elif kappa < 0.21:
            interp = "Slight agreement"
        elif kappa < 0.41:
            interp = "Fair agreement"
        elif kappa < 0.61:
            interp = "Moderate agreement"
        elif kappa < 0.81:
            interp = "Substantial agreement"
        else:
            interp = "Almost perfect agreement"
        lines.append(f"  Interpretation:       {interp}")
        lines.append("")

    lines.append("=" * 60)
    return "\n".join(lines)

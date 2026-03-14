"""Clinical validation metrics for ECG analysis.

Provides standard diagnostic metrics (sensitivity, specificity, PPV, NPV, F1),
inter-rater agreement statistics (Cohen's and Fleiss' kappa),
Bland-Altman analysis for method comparison, and statistically rigorous
confidence intervals, likelihood ratios, diagnostic odds ratio, ROC/AUC,
and bootstrap confidence intervals for clinical validation.
"""

from __future__ import annotations

import math
import random


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


def _z_score(alpha: float) -> float:
    """Approximate the z-score for a given two-tailed alpha using the rational
    approximation from Abramowitz and Stegun (formula 26.2.23)."""
    p = 1.0 - alpha / 2.0
    # Rational approximation for the inverse normal CDF (Abramowitz & Stegun)
    t = math.sqrt(-2.0 * math.log(1.0 - p))
    c0, c1, c2 = 2.515517, 0.802853, 0.010328
    d1, d2, d3 = 1.432788, 0.189269, 0.001308
    z = t - (c0 + c1 * t + c2 * t * t) / (1.0 + d1 * t + d2 * t * t + d3 * t * t * t)
    return z


def confidence_interval_proportion(numerator: int, denominator: int, alpha: float = 0.05) -> tuple[float, float]:
    """Wilson score confidence interval for a proportion.

    Provides better coverage than the Wald interval, especially for
    proportions near 0 or 1 and small sample sizes.

    Args:
        numerator: Number of successes.
        denominator: Total number of trials.
        alpha: Significance level (default 0.05 for 95% CI).

    Returns:
        Tuple of (lower_bound, upper_bound) for the proportion.
    """
    if denominator == 0:
        return (0.0, 0.0)

    p_hat = numerator / denominator
    z = _z_score(alpha)
    z2 = z * z

    denom = 1.0 + z2 / denominator
    centre = p_hat + z2 / (2.0 * denominator)
    margin = z * math.sqrt((p_hat * (1.0 - p_hat) + z2 / (4.0 * denominator)) / denominator)

    lower = (centre - margin) / denom
    upper = (centre + margin) / denom

    # Clamp to [0, 1]
    lower = max(0.0, lower)
    upper = min(1.0, upper)

    return (lower, upper)


def likelihood_ratios(tp: int, fp: int, fn: int, tn: int) -> dict:
    """Calculate positive and negative likelihood ratios with confidence intervals.

    LR+ = sensitivity / (1 - specificity)
    LR- = (1 - sensitivity) / specificity

    Args:
        tp: True positives.
        fp: False positives.
        fn: False negatives.
        tn: True negatives.

    Returns:
        Dict with keys: lr_positive, lr_negative, lr_positive_ci, lr_negative_ci.
    """
    sens = sensitivity(tp, fn)
    spec = specificity(tn, fp)

    # LR+
    if (1.0 - spec) == 0.0:
        lr_pos = float("inf") if sens > 0.0 else 0.0
    else:
        lr_pos = sens / (1.0 - spec)

    # LR-
    if spec == 0.0:
        lr_neg = float("inf") if (1.0 - sens) > 0.0 else 0.0
    else:
        lr_neg = (1.0 - sens) / spec

    # CI for LR using the log method (Simel et al., 1991)
    lr_pos_ci = _lr_ci(tp, fp, fn, tn, positive=True)
    lr_neg_ci = _lr_ci(tp, fp, fn, tn, positive=False)

    return {
        "lr_positive": lr_pos,
        "lr_negative": lr_neg,
        "lr_positive_ci": lr_pos_ci,
        "lr_negative_ci": lr_neg_ci,
    }


def _lr_ci(tp: int, fp: int, fn: int, tn: int, positive: bool = True, alpha: float = 0.05) -> tuple[float, float]:
    """Confidence interval for a likelihood ratio using the log method."""
    z = _z_score(alpha)

    if positive:
        # LR+ = sens / (1 - spec) = (tp/(tp+fn)) / (fp/(fp+tn))
        if tp == 0 or fp == 0:
            return (0.0, float("inf"))
        lr = (tp / (tp + fn)) / (fp / (fp + tn))
        # Variance of ln(LR+)
        var_ln = (1.0 / tp) - (1.0 / (tp + fn)) + (1.0 / fp) - (1.0 / (fp + tn))
    else:
        # LR- = (1 - sens) / spec = (fn/(tp+fn)) / (tn/(fp+tn))
        if fn == 0 or tn == 0:
            return (0.0, float("inf"))
        lr = (fn / (tp + fn)) / (tn / (fp + tn))
        var_ln = (1.0 / fn) - (1.0 / (tp + fn)) + (1.0 / tn) - (1.0 / (fp + tn))

    if var_ln < 0:
        return (0.0, float("inf"))

    se_ln = math.sqrt(var_ln)
    ln_lr = math.log(lr)
    lower = math.exp(ln_lr - z * se_ln)
    upper = math.exp(ln_lr + z * se_ln)
    return (lower, upper)


def diagnostic_odds_ratio(tp: int, fp: int, fn: int, tn: int) -> dict:
    """Calculate diagnostic odds ratio with confidence interval.

    DOR = (TP * TN) / (FP * FN)

    The DOR is the ratio of the odds of a positive test result in a
    diseased individual to the odds of a positive test in a non-diseased
    individual (Glas et al., 2003).

    Args:
        tp: True positives.
        fp: False positives.
        fn: False negatives.
        tn: True negatives.

    Returns:
        Dict with keys: dor, ci_lower, ci_upper, ln_dor, se_ln_dor.
    """
    # Apply Haldane-Anscombe correction if any cell is zero
    if tp == 0 or fp == 0 or fn == 0 or tn == 0:
        a, b, c, d = tp + 0.5, fp + 0.5, fn + 0.5, tn + 0.5
    else:
        a, b, c, d = float(tp), float(fp), float(fn), float(tn)

    dor = (a * d) / (b * c)
    ln_dor = math.log(dor)
    se_ln_dor = math.sqrt(1.0 / a + 1.0 / b + 1.0 / c + 1.0 / d)

    z = _z_score(0.05)
    ci_lower = math.exp(ln_dor - z * se_ln_dor)
    ci_upper = math.exp(ln_dor + z * se_ln_dor)

    return {
        "dor": dor,
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
        "ln_dor": ln_dor,
        "se_ln_dor": se_ln_dor,
    }


def roc_auc(y_true: list[int], y_scores: list[float]) -> dict:
    """Compute ROC curve points and AUC using the trapezoidal rule.

    Args:
        y_true: Binary ground truth labels (0 or 1).
        y_scores: Predicted probabilities or scores.

    Returns:
        Dict with keys: fpr (list), tpr (list), thresholds (list), auc (float).
    """
    if len(y_true) != len(y_scores):
        raise ValueError("y_true and y_scores must have the same length")

    n = len(y_true)
    if n == 0:
        return {"fpr": [], "tpr": [], "thresholds": [], "auc": 0.0}

    total_pos = sum(y_true)
    total_neg = n - total_pos

    if total_pos == 0 or total_neg == 0:
        return {"fpr": [0.0, 1.0], "tpr": [0.0, 1.0], "thresholds": [float("inf"), float("-inf")], "auc": 0.5}

    # Sort by descending score
    paired = sorted(zip(y_scores, y_true), key=lambda x: -x[0])

    fpr_list = [0.0]
    tpr_list = [0.0]
    thresholds = [paired[0][0] + 1.0]  # threshold above max score

    tp_count = 0
    fp_count = 0

    i = 0
    while i < n:
        # Find all items with the same score
        current_score = paired[i][0]
        j = i
        while j < n and paired[j][0] == current_score:
            if paired[j][1] == 1:
                tp_count += 1
            else:
                fp_count += 1
            j += 1

        fpr_list.append(fp_count / total_neg)
        tpr_list.append(tp_count / total_pos)
        thresholds.append(current_score)
        i = j

    # Compute AUC using trapezoidal rule
    auc_val = 0.0
    for k in range(1, len(fpr_list)):
        dx = fpr_list[k] - fpr_list[k - 1]
        auc_val += dx * (tpr_list[k - 1] + tpr_list[k]) / 2.0

    return {
        "fpr": fpr_list,
        "tpr": tpr_list,
        "thresholds": thresholds,
        "auc": auc_val,
    }


def bootstrap_ci(metric_fn, data: dict, n_boot: int = 1000, alpha: float = 0.05, seed: int = 42) -> dict:
    """Bootstrap confidence interval for any diagnostic metric.

    Resamples the confusion matrix cells and computes the metric on each
    bootstrap replicate to estimate the sampling distribution.

    Args:
        metric_fn: A callable that takes (tp, fp, fn, tn) and returns a float.
        data: Dict with keys tp, fp, fn, tn.
        n_boot: Number of bootstrap replicates.
        alpha: Significance level (default 0.05 for 95% CI).
        seed: Random seed for reproducibility.

    Returns:
        Dict with keys: estimate, ci_lower, ci_upper, se, bootstrap_values.
    """
    tp, fp, fn, tn = data["tp"], data["fp"], data["fn"], data["tn"]
    total = tp + fp + fn + tn

    if total == 0:
        return {
            "estimate": 0.0,
            "ci_lower": 0.0,
            "ci_upper": 0.0,
            "se": 0.0,
            "bootstrap_values": [],
        }

    point_estimate = metric_fn(tp, fp, fn, tn)

    # Build a population vector: 0=TP, 1=FP, 2=FN, 3=TN
    population = [0] * tp + [1] * fp + [2] * fn + [3] * tn

    rng = random.Random(seed)
    boot_values = []

    for _ in range(n_boot):
        sample = rng.choices(population, k=total)
        b_tp = sample.count(0)
        b_fp = sample.count(1)
        b_fn = sample.count(2)
        b_tn = sample.count(3)
        try:
            val = metric_fn(b_tp, b_fp, b_fn, b_tn)
            if math.isfinite(val):
                boot_values.append(val)
        except (ZeroDivisionError, ValueError):
            continue

    if not boot_values:
        return {
            "estimate": point_estimate,
            "ci_lower": point_estimate,
            "ci_upper": point_estimate,
            "se": 0.0,
            "bootstrap_values": [],
        }

    boot_values.sort()
    n_valid = len(boot_values)

    lower_idx = int(math.floor((alpha / 2.0) * n_valid))
    upper_idx = int(math.floor((1.0 - alpha / 2.0) * n_valid)) - 1
    lower_idx = max(0, min(lower_idx, n_valid - 1))
    upper_idx = max(0, min(upper_idx, n_valid - 1))

    mean_boot = sum(boot_values) / n_valid
    variance = sum((v - mean_boot) ** 2 for v in boot_values) / max(n_valid - 1, 1)
    se = math.sqrt(variance)

    return {
        "estimate": point_estimate,
        "ci_lower": boot_values[lower_idx],
        "ci_upper": boot_values[upper_idx],
        "se": se,
        "bootstrap_values": boot_values,
    }


def _interpret_kappa(kappa: float) -> str:
    """Interpret kappa using Landis & Koch (1977) benchmarks."""
    if kappa < 0.0:
        return "Less than chance agreement"
    elif kappa < 0.21:
        return "Slight agreement"
    elif kappa < 0.41:
        return "Fair agreement"
    elif kappa < 0.61:
        return "Moderate agreement"
    elif kappa < 0.81:
        return "Substantial agreement"
    else:
        return "Almost perfect agreement"


def _interpret_dor(dor: float) -> str:
    """Interpret DOR using Hosmer-Lemeshow guidelines adapted for DOR."""
    if dor < 1.0:
        return "Test performs worse than chance"
    elif dor < 5.0:
        return "Negligible discriminatory power"
    elif dor < 25.0:
        return "Moderate discriminatory power"
    elif dor < 100.0:
        return "Good discriminatory power"
    else:
        return "Excellent discriminatory power"


def comprehensive_diagnostic_report(results: dict) -> str:
    """Generate a comprehensive clinical validation report with statistical rigor.

    Includes all basic metrics with Wilson score confidence intervals,
    likelihood ratios, diagnostic odds ratio, clinical interpretations
    with citations (Landis & Koch for kappa, Hosmer-Lemeshow for DOR),
    and optional sensitivity analysis across thresholds.

    Args:
        results: Dict with keys tp, fp, fn, tn, and optionally:
                 measured, reference (for Bland-Altman),
                 kappa_matrix (for Cohen's kappa),
                 y_true, y_scores (for ROC/AUC and threshold sensitivity analysis).

    Returns:
        Formatted string report.
    """
    lines = []
    lines.append("=" * 70)
    lines.append("COMPREHENSIVE CLINICAL VALIDATION REPORT")
    lines.append("=" * 70)
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

    sens_ci = confidence_interval_proportion(tp, tp + fn)
    spec_ci = confidence_interval_proportion(tn, tn + fp)
    ppv_ci = confidence_interval_proportion(tp, tp + fp)
    npv_ci = confidence_interval_proportion(tn, tn + fn)

    lines.append("Confusion Matrix:")
    lines.append(f"  TP = {tp}, FP = {fp}")
    lines.append(f"  FN = {fn}, TN = {tn}")
    lines.append(f"  Total = {tp + fp + fn + tn}")
    lines.append(f"  Prevalence = {(tp + fn) / max(tp + fp + fn + tn, 1):.4f}")
    lines.append("")

    lines.append("Diagnostic Metrics (95% Wilson Score CI):")
    lines.append(f"  Sensitivity (Recall): {sens:.4f}  [{sens_ci[0]:.4f}, {sens_ci[1]:.4f}]")
    lines.append(f"  Specificity:          {spec:.4f}  [{spec_ci[0]:.4f}, {spec_ci[1]:.4f}]")
    lines.append(f"  PPV (Precision):      {pos_pv:.4f}  [{ppv_ci[0]:.4f}, {ppv_ci[1]:.4f}]")
    lines.append(f"  NPV:                  {neg_pv:.4f}  [{npv_ci[0]:.4f}, {npv_ci[1]:.4f}]")
    lines.append(f"  F1 Score:             {f1:.4f}")
    lines.append("")

    # Likelihood ratios
    lr = likelihood_ratios(tp, fp, fn, tn)
    lines.append("Likelihood Ratios:")
    if math.isinf(lr["lr_positive"]):
        lines.append("  LR+:                  inf")
    else:
        lines.append(f"  LR+:                  {lr['lr_positive']:.4f}  [{lr['lr_positive_ci'][0]:.4f}, {lr['lr_positive_ci'][1]:.4f}]")
    if math.isinf(lr["lr_negative"]):
        lines.append("  LR-:                  inf")
    else:
        lines.append(f"  LR-:                  {lr['lr_negative']:.4f}  [{lr['lr_negative_ci'][0]:.4f}, {lr['lr_negative_ci'][1]:.4f}]")
    lines.append("")

    # DOR
    dor = diagnostic_odds_ratio(tp, fp, fn, tn)
    lines.append("Diagnostic Odds Ratio:")
    lines.append(f"  DOR:                  {dor['dor']:.4f}  [{dor['ci_lower']:.4f}, {dor['ci_upper']:.4f}]")
    lines.append(f"  Interpretation:       {_interpret_dor(dor['dor'])} (Hosmer-Lemeshow)")
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
        interp = _interpret_kappa(kappa)
        lines.append("Inter-rater Agreement:")
        lines.append(f"  Cohen's Kappa:        {kappa:.4f}")
        lines.append(f"  Interpretation:       {interp} (Landis & Koch, 1977)")
        lines.append("")

    # ROC/AUC if scores present
    y_true = results.get("y_true")
    y_scores = results.get("y_scores")
    if y_true and y_scores and len(y_true) == len(y_scores):
        roc = roc_auc(y_true, y_scores)
        lines.append("ROC Analysis:")
        lines.append(f"  AUC:                  {roc['auc']:.4f}")
        lines.append(f"  ROC Points:           {len(roc['fpr'])}")
        lines.append("")

        # Sensitivity analysis at different thresholds
        lines.append("Sensitivity Analysis (metrics at different thresholds):")
        lines.append(f"  {'Threshold':>10}  {'Sens':>8}  {'Spec':>8}  {'PPV':>8}  {'NPV':>8}  {'F1':>8}")
        lines.append(f"  {'-' * 58}")

        # Pick representative thresholds
        thresholds_to_try = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
        for thresh in thresholds_to_try:
            t_tp = sum(1 for yt, ys in zip(y_true, y_scores) if ys >= thresh and yt == 1)
            t_fp = sum(1 for yt, ys in zip(y_true, y_scores) if ys >= thresh and yt == 0)
            t_fn = sum(1 for yt, ys in zip(y_true, y_scores) if ys < thresh and yt == 1)
            t_tn = sum(1 for yt, ys in zip(y_true, y_scores) if ys < thresh and yt == 0)
            t_sens = sensitivity(t_tp, t_fn)
            t_spec = specificity(t_tn, t_fp)
            t_ppv = ppv(t_tp, t_fp)
            t_npv = npv(t_tn, t_fn)
            t_f1 = f1_score(t_tp, t_fp, t_fn)
            lines.append(f"  {thresh:>10.2f}  {t_sens:>8.4f}  {t_spec:>8.4f}  {t_ppv:>8.4f}  {t_npv:>8.4f}  {t_f1:>8.4f}")
        lines.append("")

    lines.append("=" * 70)
    return "\n".join(lines)


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

    # Likelihood ratios
    lr = likelihood_ratios(tp, fp, fn, tn)
    lines.append("Likelihood Ratios:")
    if math.isinf(lr["lr_positive"]):
        lines.append("  LR+:                  inf")
    else:
        lines.append(f"  LR+:                  {lr['lr_positive']:.4f}")
    if math.isinf(lr["lr_negative"]):
        lines.append("  LR-:                  inf")
    else:
        lines.append(f"  LR-:                  {lr['lr_negative']:.4f}")
    lines.append("")

    # Diagnostic odds ratio
    dor = diagnostic_odds_ratio(tp, fp, fn, tn)
    lines.append("Diagnostic Odds Ratio:")
    lines.append(f"  DOR:                  {dor['dor']:.4f}")
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

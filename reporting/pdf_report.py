"""PDF report generation for ECG analysis.

Uses matplotlib for layout and rendering. Produces a multi-page PDF with
patient info, measurements, flags, interpretation, and educational notes.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

from reporting.i18n import t


def _render_measurements_table(report: dict, language: str = "pt") -> plt.Figure:
    """Render a measurements table as a matplotlib Figure.

    Shows PR, QRS, QT, QTc, RR, heart rate, and frontal axis values
    with reference ranges.
    """
    iv = (report.get("intervals_refined") or report.get("intervals") or {}).get("median", {})
    axis = report.get("axis") or {}
    rr = iv.get("RR_s")
    hr = round(60.0 / rr) if rr and rr > 0 else None

    rows = [
        (t("heart_rate", language), f"{hr}" if hr else "N/A", "bpm", "60-100"),
        (t("pr_interval", language), f"{iv.get('PR_ms', 'N/A')}", "ms", "120-200"),
        (t("qrs_duration", language), f"{iv.get('QRS_ms', 'N/A')}", "ms", "60-120"),
        (t("qt_interval", language), f"{iv.get('QT_ms', 'N/A')}", "ms", "350-440"),
        (t("qtc_interval", language), f"{iv.get('QTc_B', 'N/A')}", "ms", "350-450"),
        (t("frontal_axis", language), f"{axis.get('angle_deg', 'N/A')}", t("degrees", language), "-30 to +90"),
    ]

    fig, ax = plt.subplots(figsize=(8.27, 4))
    ax.axis("off")

    col_labels = [
        t("measurements", language),
        "",  # value column
        "",  # unit column
        "Ref." if language == "en" else "Ref.",
    ]
    table_data = [[r[0], r[1], r[2], r[3]] for r in rows]

    table = ax.table(
        cellText=table_data,
        colLabels=col_labels,
        cellLoc="center",
        loc="center",
        colWidths=[0.35, 0.2, 0.15, 0.3],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 1.6)

    # Style header
    for j in range(4):
        cell = table[0, j]
        cell.set_facecolor("#2C5F8A")
        cell.set_text_props(color="white", fontweight="bold")

    # Alternate row colors
    for i in range(1, len(rows) + 1):
        color = "#F0F4F8" if i % 2 == 0 else "#FFFFFF"
        for j in range(4):
            table[i, j].set_facecolor(color)

    fig.tight_layout()
    return fig


def _render_interpretation(report: dict, language: str = "pt") -> str:
    """Build interpretation text from report data."""
    lines = []

    flags = report.get("flags", [])
    iv = (report.get("intervals_refined") or report.get("intervals") or {}).get("median", {})
    axis = report.get("axis") or {}

    # Heart rate interpretation
    rr = iv.get("RR_s")
    if rr and rr > 0:
        hr = 60.0 / rr
        if hr < 60:
            lines.append(t("sinus_bradycardia", language) + f" ({hr:.0f} bpm)")
        elif hr > 100:
            lines.append(t("sinus_tachycardia", language) + f" ({hr:.0f} bpm)")
        else:
            lines.append(t("sinus_rhythm", language) + f" ({hr:.0f} bpm)")

    # PR interpretation
    pr = iv.get("PR_ms")
    if pr is not None and pr > 200:
        lines.append(t("prolonged_pr", language))

    # QRS interpretation
    qrs = iv.get("QRS_ms")
    if qrs is not None and qrs >= 120:
        lines.append(t("wide_qrs", language))

    # QTc interpretation
    qtc = iv.get("QTc_B")
    if qtc is not None:
        if qtc > 450:
            lines.append(t("prolonged_qtc", language))
        elif qtc < 350:
            lines.append(t("short_qtc", language))

    # Axis interpretation
    angle = axis.get("angle_deg")
    if angle is not None:
        if -30 <= angle <= 90:
            lines.append(t("normal_axis", language))
        elif -90 <= angle < -30:
            lines.append(t("left_axis_deviation", language))
        elif 90 < angle <= 180:
            lines.append(t("right_axis_deviation", language))
        else:
            lines.append(t("extreme_axis", language))

    if not lines:
        lines.append(t("no_significant_flags", language))

    return "\n".join(lines)


def generate_pdf_report(
    report: dict,
    output_path: str,
    overlay_path: str | None = None,
    language: str = "pt",
) -> str:
    """Generate a multi-page PDF report from an ECG analysis report dict.

    Pages:
      1. Header with patient info and ECG image/overlay
      2. Measurements table (PR, QRS, QT, QTc, axis)
      3. Flags, interpretation, differential diagnosis
      4. Educational notes using camera analogy

    Args:
        report: ECG analysis report dict
        output_path: Path to save the PDF
        overlay_path: Optional path to ECG overlay image
        language: Language code ("pt" or "en")

    Returns:
        The output path string.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    meta = report.get("meta", {})
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    with PdfPages(output_path) as pdf:
        # ── Page 1: Header + ECG image ──────────────────────────
        fig1, ax1 = plt.subplots(figsize=(8.27, 11.69))
        ax1.axis("off")

        header_text = f"{t('report_title', language)}\n"
        header_text += f"{t('date', language)}: {now}\n"
        header_text += f"{t('generated_by', language)}\n"

        if meta:
            header_text += f"\nSource: {meta.get('src', 'N/A')}\n"
            header_text += f"Resolution: {meta.get('w', '?')}x{meta.get('h', '?')} px\n"
            header_text += f"Lead: {meta.get('lead_used', 'II')}\n"

        ax1.text(
            0.5, 0.95, t("report_title", language),
            transform=ax1.transAxes, fontsize=22, fontweight="bold",
            ha="center", va="top", color="#2C5F8A",
        )
        ax1.text(
            0.5, 0.88, f"{t('date', language)}: {now}  |  {t('generated_by', language)}",
            transform=ax1.transAxes, fontsize=10,
            ha="center", va="top", color="#666666",
        )

        # Patient info box
        info_lines = []
        if meta:
            info_lines.append(f"Source: {meta.get('src', 'N/A')}")
            info_lines.append(f"Resolution: {meta.get('w', '?')}x{meta.get('h', '?')} px")
            info_lines.append(f"Lead: {meta.get('lead_used', 'II')}")
        info_text = "\n".join(info_lines)
        ax1.text(
            0.05, 0.78, f"{t('patient_info', language)}:\n{info_text}",
            transform=ax1.transAxes, fontsize=10,
            va="top", family="monospace",
            bbox=dict(boxstyle="round,pad=0.5", facecolor="#F0F4F8", edgecolor="#CCCCCC"),
        )

        # ECG overlay image if available
        if overlay_path and Path(overlay_path).exists():
            try:
                img = plt.imread(overlay_path)
                ax_img = fig1.add_axes([0.05, 0.1, 0.9, 0.5])
                ax_img.imshow(img, aspect="auto")
                ax_img.axis("off")
            except Exception:
                ax1.text(
                    0.5, 0.4, "[ECG overlay image not available]",
                    transform=ax1.transAxes, fontsize=10, ha="center", color="#999999",
                )
        else:
            ax1.text(
                0.5, 0.4, "[ECG overlay image not provided]",
                transform=ax1.transAxes, fontsize=10, ha="center", color="#999999",
            )

        ax1.text(
            0.5, 0.02, f"{t('page', language)} 1 {t('of', language)} 4",
            transform=ax1.transAxes, fontsize=8, ha="center", color="#999999",
        )
        fig1.tight_layout()
        pdf.savefig(fig1)
        plt.close(fig1)

        # ── Page 2: Measurements table ──────────────────────────
        fig2 = _render_measurements_table(report, language)
        # Add title
        fig2.suptitle(t("measurements", language), fontsize=16, fontweight="bold", color="#2C5F8A", y=0.98)
        fig2.text(
            0.5, 0.02, f"{t('page', language)} 2 {t('of', language)} 4",
            fontsize=8, ha="center", color="#999999",
        )
        pdf.savefig(fig2)
        plt.close(fig2)

        # ── Page 3: Flags + Interpretation ──────────────────────
        fig3, ax3 = plt.subplots(figsize=(8.27, 11.69))
        ax3.axis("off")

        ax3.text(
            0.5, 0.95, f"{t('flags', language)} & {t('interpretation', language)}",
            transform=ax3.transAxes, fontsize=16, fontweight="bold",
            ha="center", va="top", color="#2C5F8A",
        )

        # Flags section
        flags = report.get("flags", [])
        flags_text = "\n".join(f"  - {f}" for f in flags) if flags else "  - " + t("no_significant_flags", language)
        ax3.text(
            0.05, 0.85, f"{t('flags', language)}:\n{flags_text}",
            transform=ax3.transAxes, fontsize=10, va="top",
            bbox=dict(boxstyle="round,pad=0.5", facecolor="#FFF8E1", edgecolor="#FFB300"),
        )

        # Interpretation section
        interp = _render_interpretation(report, language)
        ax3.text(
            0.05, 0.60, f"{t('interpretation', language)}:\n{interp}",
            transform=ax3.transAxes, fontsize=10, va="top",
            bbox=dict(boxstyle="round,pad=0.5", facecolor="#E8F5E9", edgecolor="#4CAF50"),
        )

        # Differential diagnosis
        diff_diag = t("differential_diagnosis", language)
        dd_lines = []
        iv = (report.get("intervals_refined") or report.get("intervals") or {}).get("median", {})
        qrs = iv.get("QRS_ms")
        if qrs is not None and qrs >= 120:
            dd_lines.append("- LBBB / RBBB")
            dd_lines.append("- Ventricular pre-excitation (WPW)")
        pr = iv.get("PR_ms")
        if pr is not None and pr > 200:
            dd_lines.append("- First degree AV block")
            dd_lines.append("- Medication effect (digoxin, beta-blockers)")
        qtc = iv.get("QTc_B")
        if qtc is not None and qtc > 450:
            dd_lines.append("- Congenital long QT syndrome")
            dd_lines.append("- Drug-induced QT prolongation")
        if not dd_lines:
            dd_lines.append("- No specific differential considerations")
        dd_text = "\n".join(dd_lines)

        ax3.text(
            0.05, 0.35, f"{diff_diag}:\n{dd_text}",
            transform=ax3.transAxes, fontsize=10, va="top",
            bbox=dict(boxstyle="round,pad=0.5", facecolor="#E3F2FD", edgecolor="#2196F3"),
        )

        ax3.text(
            0.5, 0.02, f"{t('page', language)} 3 {t('of', language)} 4",
            fontsize=8, ha="center", color="#999999", transform=ax3.transAxes,
        )
        fig3.tight_layout()
        pdf.savefig(fig3)
        plt.close(fig3)

        # ── Page 4: Educational notes (camera analogy) ──────────
        fig4, ax4 = plt.subplots(figsize=(8.27, 11.69))
        ax4.axis("off")

        ax4.text(
            0.5, 0.95, t("educational_notes", language),
            transform=ax4.transAxes, fontsize=16, fontweight="bold",
            ha="center", va="top", color="#2C5F8A",
        )

        ax4.text(
            0.5, 0.85, t("camera_analogy_title", language),
            transform=ax4.transAxes, fontsize=14, fontweight="bold",
            ha="center", va="top", color="#333333",
        )

        camera_text = t("camera_analogy_body", language)
        ax4.text(
            0.1, 0.75, camera_text,
            transform=ax4.transAxes, fontsize=11, va="top",
            wrap=True,
            bbox=dict(boxstyle="round,pad=0.8", facecolor="#F3E5F5", edgecolor="#9C27B0"),
        )

        # Additional educational content
        edu_extra = (
            "Key reference values:\n"
            "  PR interval: 120-200 ms\n"
            "  QRS duration: 60-120 ms\n"
            "  QT interval: 350-440 ms\n"
            "  QTc (Bazett): 350-450 ms\n"
            "  Frontal axis: -30 to +90 degrees\n"
            "  Heart rate: 60-100 bpm"
        )
        ax4.text(
            0.1, 0.45, edu_extra,
            transform=ax4.transAxes, fontsize=10, va="top",
            family="monospace",
            bbox=dict(boxstyle="round,pad=0.5", facecolor="#F0F4F8", edgecolor="#CCCCCC"),
        )

        ax4.text(
            0.5, 0.02, f"{t('page', language)} 4 {t('of', language)} 4",
            fontsize=8, ha="center", color="#999999", transform=ax4.transAxes,
        )
        fig4.tight_layout()
        pdf.savefig(fig4)
        plt.close(fig4)

    return output_path

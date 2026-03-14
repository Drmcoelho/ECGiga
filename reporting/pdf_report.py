"""PDF report generation for ECG analysis.

Uses matplotlib for layout and rendering. Produces a multi-page PDF with
patient info, measurements with abnormal value highlighting, flags,
interpretation, differential diagnosis, educational notes, and legal disclaimer.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

from reporting.i18n import t

# Reference ranges for highlighting (adult values)
_REFERENCE_RANGES = {
    "heart_rate": (60, 100),
    "pr_interval": (120, 200),
    "qrs_duration": (60, 120),
    "qt_interval": (350, 440),
    "qtc_interval": (350, 450),
    "frontal_axis": (-30, 90),
}

# Critical thresholds that warrant red highlighting
_CRITICAL_THRESHOLDS = {
    "heart_rate": (40, 150),      # Extreme brady/tachy
    "qrs_duration": (0, 160),     # Severe widening
    "qtc_interval": (300, 500),   # Extreme QT
}


def _classify_value(key: str, value: float) -> str:
    """Classify a measurement value as normal, abnormal, or critical."""
    crit = _CRITICAL_THRESHOLDS.get(key)
    if crit and (value < crit[0] or value > crit[1]):
        return "critical"
    ref = _REFERENCE_RANGES.get(key)
    if ref:
        if value < ref[0]:
            return "low"
        elif value > ref[1]:
            return "high"
    return "normal"


def _render_measurements_table(report: dict, language: str = "pt") -> plt.Figure:
    """Render a measurements table with abnormal value highlighting.

    Normal values: white background
    Abnormal values: yellow background
    Critical values: red background with bold text
    """
    iv = (report.get("intervals_refined") or report.get("intervals") or {}).get("median", {})
    axis = report.get("axis") or {}
    rr = iv.get("RR_s")
    hr = round(60.0 / rr) if rr and rr > 0 else None

    rows = [
        ("heart_rate", t("heart_rate", language), hr, "bpm", "60-100"),
        ("pr_interval", t("pr_interval", language), iv.get("PR_ms"), "ms", "120-200"),
        ("qrs_duration", t("qrs_duration", language), iv.get("QRS_ms"), "ms", "60-120"),
        ("qt_interval", t("qt_interval", language), iv.get("QT_ms"), "ms", "350-440"),
        ("qtc_interval", t("qtc_interval", language), iv.get("QTc_B"), "ms", "350-450"),
        ("frontal_axis", t("frontal_axis", language), axis.get("angle_deg"), t("degrees", language), "-30 to +90"),
    ]

    fig, ax = plt.subplots(figsize=(8.27, 5))
    ax.axis("off")

    col_labels = [
        t("measurements", language),
        "",       # value
        "",       # unit
        "Ref.",   # reference
        "",       # status
    ]

    table_data = []
    cell_colors = []

    for key, label, value, unit, ref_range in rows:
        val_str = f"{value}" if value is not None else "N/A"
        status = ""
        row_color = ["#FFFFFF"] * 5

        if value is not None:
            classification = _classify_value(key, value)
            if classification == "critical":
                status = t("critical", language)
                row_color = ["#FFCDD2", "#FFCDD2", "#FFCDD2", "#FFCDD2", "#FFCDD2"]
            elif classification in ("low", "high"):
                status = "↓" if classification == "low" else "↑"
                row_color = ["#FFF9C4", "#FFF9C4", "#FFF9C4", "#FFF9C4", "#FFF9C4"]
            else:
                status = "✓"

        table_data.append([label, val_str, unit, ref_range, status])
        cell_colors.append(row_color)

    table = ax.table(
        cellText=table_data,
        colLabels=col_labels,
        cellLoc="center",
        loc="center",
        colWidths=[0.30, 0.15, 0.10, 0.20, 0.10],
        cellColours=cell_colors,
    )
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 1.8)

    # Style header row
    for j in range(5):
        cell = table[0, j]
        cell.set_facecolor("#2C5F8A")
        cell.set_text_props(color="white", fontweight="bold")

    # Bold critical values
    for i, (key, label, value, unit, ref_range) in enumerate(rows):
        if value is not None and _classify_value(key, value) == "critical":
            for j in range(5):
                table[i + 1, j].set_text_props(fontweight="bold", color="#B71C1C")

    fig.tight_layout()
    return fig


def _render_interpretation(report: dict, language: str = "pt") -> str:
    """Build interpretation text from report data."""
    lines = []
    iv = (report.get("intervals_refined") or report.get("intervals") or {}).get("median", {})
    axis = report.get("axis") or {}

    # Heart rate
    rr = iv.get("RR_s")
    if rr and rr > 0:
        hr = 60.0 / rr
        if hr < 60:
            lines.append(t("sinus_bradycardia", language) + f" ({hr:.0f} bpm)")
        elif hr > 100:
            lines.append(t("sinus_tachycardia", language) + f" ({hr:.0f} bpm)")
        else:
            lines.append(t("sinus_rhythm", language) + f" ({hr:.0f} bpm)")

    # PR
    pr = iv.get("PR_ms")
    if pr is not None and pr > 200:
        lines.append(t("prolonged_pr", language))

    # QRS
    qrs = iv.get("QRS_ms")
    if qrs is not None and qrs >= 120:
        lines.append(t("wide_qrs", language))

    # QTc
    qtc = iv.get("QTc_B")
    if qtc is not None:
        if qtc > 450:
            lines.append(t("prolonged_qtc", language))
        elif qtc < 350:
            lines.append(t("short_qtc", language))

    # Axis
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
    patient_info: dict | None = None,
) -> str:
    """Generate a multi-page PDF report from an ECG analysis report dict.

    Pages:
      1. Header with patient demographics and ECG image
      2. Measurements table with abnormal value highlighting
      3. Flags, interpretation, differential diagnosis
      4. Educational notes + Legal disclaimer

    Args:
        report: ECG analysis report dict
        output_path: Path to save the PDF
        overlay_path: Optional path to ECG overlay image
        language: Language code ("pt" or "en")
        patient_info: Optional dict with patient demographics:
            name, dob, age, sex, medical_record, requesting_physician

    Returns:
        The output path string.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    meta = report.get("meta", {})
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    report_id = str(uuid.uuid4())[:12].upper()

    with PdfPages(output_path) as pdf:
        # Set PDF metadata
        d = pdf.infodict()
        d["Title"] = t("report_title", language)
        d["Author"] = "ECGiga"
        d["Subject"] = "ECG Analysis Report"
        d["CreationDate"] = datetime.now()

        # ── Page 1: Header + Patient Info + ECG image ─────────
        fig1, ax1 = plt.subplots(figsize=(8.27, 11.69))
        ax1.axis("off")

        # Title
        ax1.text(
            0.5, 0.96, t("report_title", language),
            transform=ax1.transAxes, fontsize=22, fontweight="bold",
            ha="center", va="top", color="#2C5F8A",
        )

        # Report metadata line
        ax1.text(
            0.5, 0.91,
            f"{t('date', language)}: {now}  |  "
            f"{t('report_id', language)}: {report_id}  |  "
            f"{t('generated_by', language)}",
            transform=ax1.transAxes, fontsize=9,
            ha="center", va="top", color="#666666",
        )

        # Patient demographics box
        patient = patient_info or {}
        demo_lines = [f"{t('patient_info', language)}:"]
        if patient.get("name"):
            demo_lines.append(f"  Nome: {patient['name']}")
        if patient.get("dob"):
            demo_lines.append(f"  Data de Nascimento: {patient['dob']}")
        if patient.get("age"):
            demo_lines.append(f"  Idade: {patient['age']}")
        if patient.get("sex"):
            demo_lines.append(f"  Sexo: {patient['sex']}")
        if patient.get("medical_record"):
            demo_lines.append(f"  Prontuário: {patient['medical_record']}")
        if patient.get("requesting_physician"):
            demo_lines.append(f"  Médico Solicitante: {patient['requesting_physician']}")
        if meta:
            demo_lines.append(f"  Source: {meta.get('src', 'N/A')}")
            demo_lines.append(f"  Resolution: {meta.get('w', '?')}x{meta.get('h', '?')} px")

        demo_text = "\n".join(demo_lines)
        ax1.text(
            0.05, 0.84, demo_text,
            transform=ax1.transAxes, fontsize=10,
            va="top", family="monospace",
            bbox=dict(boxstyle="round,pad=0.5", facecolor="#F0F4F8", edgecolor="#CCCCCC"),
        )

        # ECG overlay image
        if overlay_path and Path(overlay_path).exists():
            try:
                img = plt.imread(overlay_path)
                ax_img = fig1.add_axes([0.05, 0.1, 0.9, 0.45])
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
            0.5, 0.02, f"{t('page', language)} 1 {t('of', language)} 4  |  ID: {report_id}",
            transform=ax1.transAxes, fontsize=8, ha="center", color="#999999",
        )
        fig1.tight_layout()
        pdf.savefig(fig1)
        plt.close(fig1)

        # ── Page 2: Measurements table ────────────────────────
        fig2 = _render_measurements_table(report, language)
        fig2.suptitle(
            t("measurements", language),
            fontsize=16, fontweight="bold", color="#2C5F8A", y=0.98,
        )
        fig2.text(
            0.5, 0.02, f"{t('page', language)} 2 {t('of', language)} 4  |  ID: {report_id}",
            fontsize=8, ha="center", color="#999999",
        )
        pdf.savefig(fig2)
        plt.close(fig2)

        # ── Page 3: Flags + Interpretation + Differential ─────
        fig3, ax3 = plt.subplots(figsize=(8.27, 11.69))
        ax3.axis("off")

        ax3.text(
            0.5, 0.96, f"{t('flags', language)} & {t('interpretation', language)}",
            transform=ax3.transAxes, fontsize=16, fontweight="bold",
            ha="center", va="top", color="#2C5F8A",
        )

        # Flags
        flags = report.get("flags", [])
        flags_text = "\n".join(f"  • {f}" for f in flags) if flags else f"  • {t('no_significant_flags', language)}"
        ax3.text(
            0.05, 0.88, f"{t('flags', language)}:\n{flags_text}",
            transform=ax3.transAxes, fontsize=10, va="top",
            bbox=dict(boxstyle="round,pad=0.5", facecolor="#FFF8E1", edgecolor="#FFB300"),
        )

        # Interpretation
        interp = _render_interpretation(report, language)
        ax3.text(
            0.05, 0.62, f"{t('interpretation', language)}:\n{interp}",
            transform=ax3.transAxes, fontsize=10, va="top",
            bbox=dict(boxstyle="round,pad=0.5", facecolor="#E8F5E9", edgecolor="#4CAF50"),
        )

        # Differential diagnosis
        iv = (report.get("intervals_refined") or report.get("intervals") or {}).get("median", {})
        dd_lines = []
        qrs = iv.get("QRS_ms")
        if qrs is not None and qrs >= 120:
            dd_lines.append("• BRD / BRE (bloqueio de ramo)" if language == "pt" else "• RBBB / LBBB")
            dd_lines.append("• Pré-excitação ventricular (WPW)" if language == "pt" else "• Ventricular pre-excitation (WPW)")
        pr = iv.get("PR_ms")
        if pr is not None and pr > 200:
            dd_lines.append("• BAV 1º grau" if language == "pt" else "• First degree AV block")
            dd_lines.append("• Efeito medicamentoso (digital, betabloqueador)" if language == "pt" else "• Medication effect (digoxin, beta-blockers)")
        qtc = iv.get("QTc_B")
        if qtc is not None and qtc > 450:
            dd_lines.append("• Síndrome do QT longo" if language == "pt" else "• Long QT syndrome")
            dd_lines.append("• QT prolongado por drogas/eletrólitos" if language == "pt" else "• Drug-induced / electrolyte QT prolongation")
        if not dd_lines:
            dd_lines.append("• Sem considerações diferenciais específicas" if language == "pt" else "• No specific differential considerations")
        dd_text = "\n".join(dd_lines)

        ax3.text(
            0.05, 0.38, f"{t('differential_diagnosis', language)}:\n{dd_text}",
            transform=ax3.transAxes, fontsize=10, va="top",
            bbox=dict(boxstyle="round,pad=0.5", facecolor="#E3F2FD", edgecolor="#2196F3"),
        )

        ax3.text(
            0.5, 0.02, f"{t('page', language)} 3 {t('of', language)} 4  |  ID: {report_id}",
            fontsize=8, ha="center", color="#999999", transform=ax3.transAxes,
        )
        fig3.tight_layout()
        pdf.savefig(fig3)
        plt.close(fig3)

        # ── Page 4: Educational notes + Legal disclaimer ──────
        fig4, ax4 = plt.subplots(figsize=(8.27, 11.69))
        ax4.axis("off")

        ax4.text(
            0.5, 0.96, t("educational_notes", language),
            transform=ax4.transAxes, fontsize=16, fontweight="bold",
            ha="center", va="top", color="#2C5F8A",
        )

        # Camera analogy
        ax4.text(
            0.5, 0.88, t("camera_analogy_title", language),
            transform=ax4.transAxes, fontsize=14, fontweight="bold",
            ha="center", va="top", color="#333333",
        )

        camera_text = t("camera_analogy_body", language)
        ax4.text(
            0.1, 0.78, camera_text,
            transform=ax4.transAxes, fontsize=10, va="top",
            wrap=True,
            bbox=dict(boxstyle="round,pad=0.8", facecolor="#F3E5F5", edgecolor="#9C27B0"),
        )

        # Reference values
        edu_extra = (
            "Valores de referência (adulto):\n"
            "  Intervalo PR:    120-200 ms\n"
            "  Duração QRS:     60-120 ms\n"
            "  Intervalo QT:    350-440 ms\n"
            "  QTc (Bazett):    350-450 ms\n"
            "  Eixo frontal:    -30° a +90°\n"
            "  Freq. cardíaca:  60-100 bpm"
            if language == "pt" else
            "Reference values (adult):\n"
            "  PR Interval:     120-200 ms\n"
            "  QRS Duration:    60-120 ms\n"
            "  QT Interval:     350-440 ms\n"
            "  QTc (Bazett):    350-450 ms\n"
            "  Frontal Axis:    -30° to +90°\n"
            "  Heart Rate:      60-100 bpm"
        )
        ax4.text(
            0.1, 0.48, edu_extra,
            transform=ax4.transAxes, fontsize=10, va="top",
            family="monospace",
            bbox=dict(boxstyle="round,pad=0.5", facecolor="#F0F4F8", edgecolor="#CCCCCC"),
        )

        # Legal disclaimer
        ax4.text(
            0.1, 0.25, f"{t('disclaimer', language)}:",
            transform=ax4.transAxes, fontsize=12, fontweight="bold",
            va="top", color="#B71C1C",
        )
        ax4.text(
            0.1, 0.20, t("disclaimer_text", language),
            transform=ax4.transAxes, fontsize=9, va="top",
            wrap=True, style="italic",
            bbox=dict(boxstyle="round,pad=0.5", facecolor="#FFEBEE", edgecolor="#B71C1C"),
        )

        ax4.text(
            0.5, 0.02, f"{t('page', language)} 4 {t('of', language)} 4  |  ID: {report_id}",
            fontsize=8, ha="center", color="#999999", transform=ax4.transAxes,
        )
        fig4.tight_layout()
        pdf.savefig(fig4)
        plt.close(fig4)

    return output_path

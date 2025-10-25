"""
Markdown Exporter for ECG Reports

Converts ECG reports to Markdown format with human-readable content.
"""

from datetime import datetime
from typing import Any, Dict


def report_to_markdown(report: Dict[str, Any], include_plugins: bool = True) -> str:
    """
    Convert an ECG report to Markdown format.

    Args:
        report: ECG report dictionary
        include_plugins: Whether to include plugin summaries

    Returns:
        Markdown formatted string
    """
    lines = []

    # Title and metadata
    meta = report.get("meta", {})
    version = report.get("version", "unknown")

    lines.append("# ECG Report")
    lines.append("")
    lines.append(f"**Version:** {version}")

    if meta:
        lines.append(f"**Source:** {meta.get('src', 'unknown')}")
        if meta.get("w") and meta.get("h"):
            lines.append(f"**Resolution:** {meta.get('w')}×{meta.get('h')} px")
        if meta.get("lead_used"):
            lines.append(f"**Analysis Lead:** {meta.get('lead_used')}")
    lines.append("")

    # Capabilities
    capabilities = report.get("capabilities", [])
    if capabilities:
        lines.append("## Capabilities")
        for cap in capabilities:
            lines.append(f"- {cap}")
        lines.append("")

    # Flags
    flags = report.get("flags", [])
    if flags:
        lines.append("## Flags")
        lines.append("**Flags:** " + "; ".join(flags))
        lines.append("")

    # Key measures
    lines.append("## Key Measures")

    # Heart Rate
    measures = report.get("measures", {})
    intervals_refined = report.get("intervals_refined", {})

    if measures.get("fc_bpm") or measures.get("rr_ms"):
        hr = measures.get("fc_bpm") or (
            60000.0 / measures.get("rr_ms") if measures.get("rr_ms") else None
        )
        if hr:
            lines.append(f"**Heart Rate:** {hr:.1f} bpm")

    # QTc
    median = intervals_refined.get("median", {}) if intervals_refined else {}
    if median.get("QTc_B") or median.get("QTc_F"):
        qtc_b = median.get("QTc_B")
        qtc_f = median.get("QTc_F")
        qtc_parts = []
        if qtc_b:
            qtc_parts.append(f"Bazett: {qtc_b} ms")
        if qtc_f:
            qtc_parts.append(f"Fridericia: {qtc_f} ms")
        if qtc_parts:
            lines.append(f"**QTc:** {', '.join(qtc_parts)}")

    # QRS duration
    if median.get("QRS_ms"):
        lines.append(f"**QRS Duration:** {median.get('QRS_ms')} ms")

    # Cardiac axis
    axis = report.get("axis", {})
    if axis.get("angle_deg") is not None and axis.get("label"):
        lines.append(f"**Cardiac Axis:** {axis.get('label')} ({axis.get('angle_deg')}°)")

    lines.append("")

    # Plugin summaries (if requested and available)
    if include_plugins:
        plugins = report.get("plugins", {})
        if plugins:
            lines.append("## Plugin Analysis")
            for plugin_name, plugin_data in plugins.items():
                lines.append(f"### {plugin_name}")
                if isinstance(plugin_data, dict) and plugin_data.get("summary"):
                    lines.append(plugin_data["summary"])
                else:
                    lines.append(f"Analysis completed: {plugin_name}")
                lines.append("")

    # Generated timestamp
    lines.append("---")
    lines.append(f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")

    return "\n".join(lines)

from __future__ import annotations

import json
from pathlib import Path


def to_md(rep: dict) -> str:
    meta = rep.get("meta", {})
    ivm = (rep.get("intervals_refined") or {}).get("median") or {}
    ivr = (rep.get("intervals_refined") or {}).get("median_robust") or {}
    axis = rep.get("axis") or {}

    def fmt(m):
        return " | ".join(
            [
                f"PR {m.get('PR_ms')} ms",
                f"QRS {m.get('QRS_ms')} ms",
                f"QT {m.get('QT_ms')} ms",
                f"QTcB {m.get('QTc_B')}",
                f"QTcF {m.get('QTc_F')}",
            ]
        )

    lines = []
    lines.append(f"# Laudo ECG — {Path(meta.get('src','?')).name}")
    lines.append("")
    lines.append(f"- **Resolução**: {meta.get('w')}×{meta.get('h')} px")
    lines.append(f"- **Lead de análise**: {meta.get('lead_used','II')}")
    lines.append("")
    if ivm:
        lines.append("## Intervalos (mediana)")
        lines.append(fmt(ivm))
        lines.append("")
    if ivr:
        lines.append("## Intervalos (robusto — MAD)")
        lines.append(fmt(ivr))
        lines.append(
            f"- batimentos usados: {rep.get('intervals_refined',{}).get('beats_used')} / {rep.get('intervals_refined',{}).get('beats_total')}"
        )
        lines.append("")
    if axis:
        lines.append("## Eixo frontal")
        lines.append(f"- θ = **{axis.get('angle_deg')}°** — {axis.get('label')}")
        lines.append("")
    if rep.get("flags"):
        lines.append("## Flags")
        for f in rep["flags"]:
            lines.append(f"- {f}")
        lines.append("")
    lines.append("## JSON")
    lines.append("```json")
    lines.append(json.dumps(rep, ensure_ascii=False, indent=2))
    lines.append("```")
    return "\n".join(lines)


def to_html(md_text: str) -> str:
    # conversão mínima: troca cabeçalhos/itálicos/inline code, preserva blocos de código
    import re

    html_text = md_text
    html_text = re.sub(r"^# (.*)$", r"<h1>\\1</h1>", html_text, flags=re.MULTILINE)
    html_text = re.sub(r"^## (.*)$", r"<h2>\\1</h2>", html_text, flags=re.MULTILINE)
    html_text = re.sub(r"\\*\\*(.*?)\\*\\*", r"<strong>\\1</strong>", html_text)
    html_text = re.sub(r"`([^`]+)`", r"<code>\\1</code>", html_text)
    html_text = html_text.replace("\n", "<br/>\n")
    return f"<!doctype html><meta charset='utf-8'><style>body{{font-family:system-ui, -apple-system, Segoe UI, sans-serif; max-width: 920px; margin: 2rem auto; line-height:1.5}}</style>{html_text}"


def export(report_json: str, out_md: str = None, out_html: str = None) -> tuple[str, str]:
    rep = json.loads(Path(report_json).read_text(encoding="utf-8"))
    md = to_md(rep)
    if out_md:
        Path(out_md).write_text(md, encoding="utf-8")
    html = to_html(md)
    if out_html:
        Path(out_html).write_text(html, encoding="utf-8")
    return out_md, out_html


def _embed_base64_image(path: str) -> str:
    import base64
    import mimetypes

    data = Path(path).read_bytes()
    mime, _ = mimetypes.guess_type(path)
    mime = mime or "image/png"
    b64 = base64.b64encode(data).decode("ascii")
    return f"<img alt='overlay' style='max-width:100%;border:1px solid #ddd' src='data:{mime};base64,{b64}'/>"


def export(
    report_json: str, out_md: str = None, out_html: str = None, overlay_path: str = None
) -> tuple[str, str]:
    rep = json.loads(Path(report_json).read_text(encoding="utf-8"))
    md = to_md(rep)
    if out_md:
        Path(out_md).write_text(md, encoding="utf-8")
    html = to_html(md)
    if overlay_path and Path(overlay_path).exists():
        html += "<hr/>" + _embed_base64_image(overlay_path)
    if out_html:
        Path(out_html).write_text(html, encoding="utf-8")
    return out_md, out_html

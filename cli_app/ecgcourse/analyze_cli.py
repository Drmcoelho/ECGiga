"""ECG signal analysis and calculations CLI."""

from __future__ import annotations
import json
import math
import pathlib
import time
from typing import Optional, Tuple

import typer
from rich import print
from rich.panel import Panel

from .logging_utils import get_logger
from .config import CONFIG

logger = get_logger(__name__)

analyze_app = typer.Typer(help="ECG signal analysis and calculations")

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]


def axis_from_I_aVF(lead_i_mv: Optional[float], avf_mv: Optional[float]) -> Tuple[Optional[float], Optional[str]]:
    """Calculate cardiac axis from Lead I and aVF voltages.
    
    Args:
        lead_i_mv: QRS net voltage in Lead I (mV)
        avf_mv: QRS net voltage in aVF (mV)
        
    Returns:
        Tuple of (angle in degrees, descriptive label)
    """
    if lead_i_mv is None or avf_mv is None:
        return None, None
    
    angle = math.degrees(math.atan2(avf_mv, lead_i_mv))
    
    # Classification based on I/aVF polarity (robust approach)
    if lead_i_mv >= 0 and avf_mv >= 0:
        label = "Normal"
    elif lead_i_mv >= 0 and avf_mv < 0:
        label = "Desvio para a esquerda"
    elif lead_i_mv < 0 and avf_mv >= 0:
        label = "Desvio para a direita"
    else:
        label = "Desvio extremo (noroeste)"
    
    return angle, label


@analyze_app.command()
def values(
    path_or_none: Optional[str] = typer.Argument(None, help="Arquivo JSON opcional com valores"),
    pr: Optional[int] = typer.Option(None, "--pr", help="PR interval (ms)"),
    qrs: Optional[int] = typer.Option(None, "--qrs", help="QRS duration (ms)"),
    qt: Optional[int] = typer.Option(None, "--qt", help="QT interval (ms)"),
    rr: Optional[int] = typer.Option(None, "--rr", help="RR interval (ms)"),
    fc: Optional[float] = typer.Option(None, "--fc", help="Heart rate (bpm)"),
    lead_i: Optional[float] = typer.Option(None, "--lead-i", help="QRS net voltage in Lead I (mV)"),
    avf: Optional[float] = typer.Option(None, "--avf", help="QRS net voltage in aVF (mV)"),
    sexo: Optional[str] = typer.Option(None, "--sexo", help="Gender: M/F for QTc threshold"),
    report: bool = typer.Option(False, "--report", help="Save report to reports/"),
):
    """Analyze ECG values: calculate QTc, axis, and generate clinical flags."""
    logger.info("Analyzing ECG values")
    
    # Load data from JSON file if provided
    data = {}
    if path_or_none and path_or_none.lower().endswith(".json"):
        p = pathlib.Path(path_or_none)
        if not p.exists():
            typer.echo(f"Arquivo não encontrado: {p}", err=True)
            raise typer.Exit(code=2)
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
    
    # Override with CLI parameters
    for k, v in {
        "pr": pr, "qrs": qrs, "qt": qt, "rr": rr, 
        "fc": fc, "lead_i": lead_i, "avf": avf, "sexo": sexo
    }.items():
        if v is not None:
            data[k] = v
    
    # Validate required inputs
    if "rr" not in data and "fc" not in data:
        typer.echo("Informe RR (ms) ou FC (bpm).", err=True)
        raise typer.Exit(code=2)
    
    if "qt" not in data:
        typer.echo("Informe QT (ms) para cálculo de QTc.", err=True)
        raise typer.Exit(code=2)
    
    # Calculate derived values
    rr_ms = float(data["rr"]) if "rr" in data else 60000.0 / float(data["fc"])
    fc_bpm = 60000.0 / rr_ms
    qt_ms = float(data["qt"])
    pr_ms = float(data.get("pr")) if data.get("pr") is not None else None
    qrs_ms = float(data.get("qrs")) if data.get("qrs") is not None else None
    
    # QTc calculations
    qtc_bazett = qt_ms / ((rr_ms / 1000.0) ** 0.5)
    qtc_fridericia = qt_ms / ((rr_ms / 1000.0) ** (1.0 / 3.0))
    
    # Axis calculation
    lead_i_mv = float(data.get("lead_i")) if data.get("lead_i") is not None else None
    avf_mv = float(data.get("avf")) if data.get("avf") is not None else None
    angle, axis_label = axis_from_I_aVF(lead_i_mv, avf_mv)
    
    # Generate clinical flags
    flags = []
    
    # PR interval flags
    if pr_ms is not None:
        if pr_ms > 200:
            flags.append("PR > 200 ms: suspeita de BAV 1º")
        if pr_ms < 120 and (qrs_ms is None or qrs_ms < CONFIG.QRS_BORDERLINE_THRESHOLD_MS):
            flags.append("PR < 120 ms: considerar pré-excitação")
    
    # QRS duration flags
    if qrs_ms is not None:
        if qrs_ms >= CONFIG.QRS_WIDE_THRESHOLD_MS:
            flags.append("QRS ≥ 120 ms: sugere bloqueio de ramo completo/origem ventricular")
        elif CONFIG.QRS_BORDERLINE_THRESHOLD_MS <= qrs_ms < CONFIG.QRS_WIDE_THRESHOLD_MS:
            flags.append("QRS 110–119 ms: possível bloqueio de ramo incompleto")
    
    # QTc flags
    sexo_s = (data.get("sexo") or "").strip().upper()
    qtc_threshold = (
        CONFIG.QTC_MALE_THRESHOLD_MS if sexo_s == "M" else
        CONFIG.QTC_FEMALE_THRESHOLD_MS if sexo_s == "F" else
        CONFIG.QTC_DEFAULT_THRESHOLD_MS
    )
    
    if qtc_bazett >= qtc_threshold or qtc_fridericia >= qtc_threshold:
        flags.append(f"QTc prolongado (limiar {qtc_threshold} ms)")
    
    if qtc_bazett < CONFIG.QTC_SHORT_THRESHOLD_MS or qtc_fridericia < CONFIG.QTC_SHORT_THRESHOLD_MS:
        flags.append(f"QTc possivelmente curto (<{CONFIG.QTC_SHORT_THRESHOLD_MS} ms)")
    
    # Heart rate flags
    if fc_bpm < CONFIG.MIN_HR_BPM:
        flags.append(f"Bradicardia (FC < {CONFIG.MIN_HR_BPM} bpm)")
    elif fc_bpm > CONFIG.MAX_HR_BPM:
        flags.append(f"Taquicardia extrema (FC > {CONFIG.MAX_HR_BPM} bpm)")
    elif fc_bpm > 100:
        flags.append("Taquicardia (FC > 100 bpm)")
    elif fc_bpm < 60:
        flags.append("Bradicardia (FC < 60 bpm)")
    
    # Build output structure
    out = {
        "inputs": {
            "pr_ms": pr_ms,
            "qrs_ms": qrs_ms,
            "qt_ms": qt_ms,
            "rr_ms": rr_ms,
            "fc_bpm": fc_bpm,
            "lead_i_mv": lead_i_mv,
            "aVF_mv": avf_mv,
            "sexo": sexo_s or None,
        },
        "derived": {
            "QTc_Bazett_ms": round(qtc_bazett, 1),
            "QTc_Fridericia_ms": round(qtc_fridericia, 1),
            "axis_angle_deg": round(angle, 1) if angle is not None else None,
            "axis_label": axis_label,
        },
        "flags": flags,
        "notes": [
            "Bazett supercorrige em FC alta e subcorrige em FC baixa; Fridericia é alternativa mais estável.",
            "Classificação de eixo baseada em sinais de I/aVF e ângulo aproximado.",
            "Heurísticas são educacionais e não substituem avaliação clínica completa."
        ]
    }
    
    # Display results
    print(Panel.fit(
        f"[bold]FC:[/] {fc_bpm:.1f} bpm | "
        f"[bold]QTc (Bazett/Fridericia):[/] {out['derived']['QTc_Bazett_ms']:.1f}/"
        f"{out['derived']['QTc_Fridericia_ms']:.1f} ms"
    ))
    
    if axis_label:
        print(Panel.fit(f"[bold]Eixo:[/] {axis_label} ({out['derived']['axis_angle_deg']}° aprox)"))
    
    if flags:
        print(Panel.fit("[bold yellow]Flags:[/]\n- " + "\n- ".join(flags)))
    else:
        print(Panel.fit("[bold green]Sem flags relevantes pelos limiares configurados.[/]"))
    
    logger.debug(f"Analysis complete: {len(flags)} flags generated")
    
    # Save reports if requested
    if report:
        reports_dir = REPO_ROOT / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        ts = time.strftime("%Y%m%d-%H%M%S")
        
        # JSON report
        json_path = reports_dir / f"{ts}_analyze_values.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
        
        # Markdown report
        md_path = reports_dir / f"{ts}_analyze_values.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(f"# Relatório analyze values — {ts}\n\n")
            f.write(f"- FC: {fc_bpm:.1f} bpm\n")
            f.write(f"- QTc Bazett: {out['derived']['QTc_Bazett_ms']:.1f} ms\n")
            f.write(f"- QTc Fridericia: {out['derived']['QTc_Fridericia_ms']:.1f} ms\n")
            
            if axis_label:
                f.write(f"- Eixo: {axis_label} ({out['derived']['axis_angle_deg']}°)\n")
            
            if flags:
                f.write("\n## Flags\n")
                for flag in flags:
                    f.write(f"- {flag}\n")
        
        print(Panel.fit("[bold green]Relatórios salvos em reports/"))
        logger.info(f"Reports saved: {json_path}, {md_path}")


if __name__ == "__main__":
    analyze_app()
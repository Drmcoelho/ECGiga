
from __future__ import annotations
import json, sys, pathlib, time, random, math
import typer
from rich import print
from rich.panel import Panel
from rich.table import Table
from jsonschema import Draft202012Validator

app = typer.Typer(help="ECGCourse CLI — quizzes, análises e utilitários.")

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
SCHEMA_CANDIDATES = [
    REPO_ROOT / "quiz" / "schema" / "mcq.schema.json",
    REPO_ROOT / "cli_app" / "quiz" / "schema" / "mcq.schema.json",
]

def load_schema() -> dict:
    for p in SCHEMA_CANDIDATES:
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
    typer.echo("Schema mcq.schema.json não encontrado.", err=True)
    raise typer.Exit(code=2)

def validate_item(item: dict, schema: dict):
    Draft202012Validator(schema).validate(item)

def ask_item(item: dict) -> tuple[bool, int]:
    print(Panel.fit(f"[bold cyan]{item['topic']}[/] — dificuldade: {item['difficulty']}"))
    print(f"[bold]Q:[/] {item['stem']}\n")
    for i, opt in enumerate(item["options"]):
        print(f"  [bold]{chr(65+i)}[/]) {opt}")
    ans = input("\nSua resposta (A/B/C/D... ou 'q' para sair): ").strip().upper()
    if ans == 'Q':
        return None, None
    idx = ord(ans) - 65
    correct = idx == item["answer_index"]
    if correct:
        print(Panel.fit("[bold green]Correto![/]"))
    else:
        print(Panel.fit(f"[bold red]Incorreto[/] — correta: {chr(65+item['answer_index'])}"))
    print("\n[bold]Explicação:[/]")
    print(item["explanation"])
    return correct, idx

@app.command()
def quiz(
    action: str = typer.Argument(..., help="run|validate|bank"),
    path: str = typer.Argument(..., help="arquivo .json (run/validate) ou diretório (bank)"),
    report: bool = typer.Option(False, "--report", help="salva relatórios em reports/"),
    shuffle: bool = typer.Option(True, "--shuffle/--no-shuffle", help="embaralhar ordem no modo bank"),
    seed: int = typer.Option(0, "--seed", help="seed para reprodutibilidade (0 = auto)"),
):
    schema = load_schema()
    p = pathlib.Path(path)

    if action in ("run", "validate"):
        if not p.exists():
            typer.echo(f"Arquivo não encontrado: {p}", err=True); raise typer.Exit(code=2)
        with open(p, "r", encoding="utf-8") as f:
            item = json.load(f)
        if action == "validate":
            validate_item(item, schema); print(Panel.fit("[bold green]OK[/] — Schema válido.")); raise typer.Exit(code=0)
        validate_item(item, schema); ask_item(item); raise typer.Exit(code=0)

    if action == "bank":
        if not p.exists() or not p.is_dir():
            typer.echo(f"Diretório inválido: {p}", err=True); raise typer.Exit(code=2)
        items = []
        for fp in sorted(p.glob("*.json")):
            with open(fp, "r", encoding="utf-8") as f:
                it = json.load(f)
            validate_item(it, schema); it["_src"] = str(fp); items.append(it)
        if not items:
            typer.echo("Nenhum .json encontrado.", err=True); raise typer.Exit(code=2)
        if shuffle:
            r = random.Random(seed or time.time_ns()); r.shuffle(items)
        results = []
        for it in items:
            ans = ask_item(it)
            if ans == (None, None): break
            ok, chosen = ans
            results.append({"id": it["id"], "topic": it["topic"], "difficulty": it["difficulty"],
                            "correct": bool(ok), "chosen_index": chosen, "answer_index": it["answer_index"],
                            "src": it["_src"]})
            print("-"*60)
        if not results:
            print(Panel.fit("[bold yellow]Sem respostas registradas.[/]")); raise typer.Exit(code=0)
        total = len(results); acertos = sum(1 for r in results if r["correct"]); pct = 100.0*acertos/total
        tbl = Table(title="Resumo — Banco"); tbl.add_column("Total"); tbl.add_column("Acertos"); tbl.add_column("%")
        tbl.add_row(str(total), str(acertos), f"{pct:.1f}"); print(tbl)
        def agg(key):
            m = {}
            for r in results:
                k = r[key]; m.setdefault(k, {"n":0,"ok":0}); m[k]["n"] += 1; m[k]["ok"] += int(r["correct"])
            return {k: {"n":v["n"], "ok":v["ok"], "pct":(100.0*v["ok"]/v["n"])} for k,v in m.items()}
        by_topic = agg("topic"); by_diff = agg("difficulty")
        print(Panel.fit(f"[bold]Por tópico:[/] {by_topic}"))
        print(Panel.fit(f"[bold]Por dificuldade:[/] {by_diff}"))
        if report:
            reports_dir = (REPO_ROOT / "reports"); reports_dir.mkdir(parents=True, exist_ok=True)
            ts = time.strftime("%Y%m%d-%H%M%S")
            with open(reports_dir / f"{ts}_summary.json", "w", encoding="utf-8") as f:
                json.dump({"total": total, "correct": acertos, "pct": pct,
                           "by_topic": by_topic, "by_difficulty": by_diff, "results": results},
                          f, ensure_ascii=False, indent=2)
            with open(reports_dir / f"{ts}_summary.md", "w", encoding="utf-8") as f:
                f.write(f"# Relatório de Quiz — {ts}\n\n")
                f.write(f"- Total: {total}\n- Acertos: {acertos}\n- %: {pct:.1f}\n\n")
                f.write("## Por tópico\n\n")
                for k,v in by_topic.items():
                    f.write(f"- {k}: {v['ok']}/{v['n']} ({v['pct']:.1f}%)\n")
                f.write("\n## Por dificuldade\n\n")
                for k,v in by_diff.items():
                    f.write(f"- {k}: {v['ok']}/{v['n']} ({v['pct']:.1f}%)\n")
                f.write("\n## Itens incorretos\n\n")
                for r in results:
                    if not r["correct"]:
                        f.write(f"- {r['id']} [{r['topic']}/{r['difficulty']}] — src: {r['src']}\n")
            print(Panel.fit("[bold green]Relatórios salvos em reports/"))
        raise typer.Exit(code=0)

# Analyze subapp
analyze_app = typer.Typer(help="Análises de valores estruturados de ECG (p2).")

def axis_from_I_aVF(lead_i_mv, avf_mv):
    if lead_i_mv is None or avf_mv is None:
        return None, None
    angle = math.degrees(math.atan2(avf_mv, lead_i_mv))
    # Classificação baseada em sinais (robusta)
    if lead_i_mv >= 0 and avf_mv >= 0:
        label = "Normal"
    elif lead_i_mv >= 0 and avf_mv < 0:
        label = "Desvio para a esquerda"
    elif lead_i_mv < 0 and avf_mv >= 0:
        label = "Desvio para a direita"
    else:
        label = "Desvio extremo (noroeste)"
    return angle, label

@analyze_app.command("values")
def analyze_values(
    path_or_none: str = typer.Argument(None, help="Opcional: arquivo JSON com valores"),
    pr: int = typer.Option(None, "--pr", help="PR (ms)"),
    qrs: int = typer.Option(None, "--qrs", help="QRS (ms)"),
    qt: int = typer.Option(None, "--qt", help="QT (ms)"),
    rr: int = typer.Option(None, "--rr", help="RR (ms)"),
    fc: float = typer.Option(None, "--fc", help="Frequência cardíaca (bpm)"),
    lead_i: float = typer.Option(None, "--lead-i", help="QRS líquido em I (mV)"),
    avf: float = typer.Option(None, "--avf", help="QRS líquido em aVF (mV)"),
    sexo: str = typer.Option(None, "--sexo", help="M/F para limiar QTc"),
    report: bool = typer.Option(False, "--report", help="Salvar relatório em reports/"),
):
    data = {}
    if path_or_none and path_or_none.lower().endswith(".json"):
        p = pathlib.Path(path_or_none)
        if not p.exists():
            typer.echo(f"Arquivo não encontrado: {p}", err=True); raise typer.Exit(code=2)
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
    for k, v in {"pr":pr, "qrs":qrs, "qt":qt, "rr":rr, "fc":fc, "lead_i":lead_i, "avf":avf, "sexo":sexo}.items():
        if v is not None: data[k] = v

    if "rr" not in data and "fc" not in data:
        typer.echo("Informe RR (ms) ou FC (bpm).", err=True); raise typer.Exit(code=2)
    if "qt" not in data:
        typer.echo("Informe QT (ms) para cálculo de QTc.", err=True); raise typer.Exit(code=2)

    rr_ms = float(data["rr"]) if "rr" in data else 60000.0/float(data["fc"])
    fc_bpm = 60000.0/rr_ms
    qt_ms = float(data["qt"])
    pr_ms = float(data.get("pr")) if data.get("pr") is not None else None
    qrs_ms = float(data.get("qrs")) if data.get("qrs") is not None else None

    qtcb = qt_ms / ( (rr_ms/1000.0) ** 0.5 )
    qtcfr = qt_ms / ( (rr_ms/1000.0) ** (1.0/3.0) )

    lead_i_mv = float(data.get("lead_i")) if data.get("lead_i") is not None else None
    avf_mv = float(data.get("avf")) if data.get("avf") is not None else None
    angle, axis_label = axis_from_I_aVF(lead_i_mv, avf_mv)

    flags = []
    if pr_ms is not None:
        if pr_ms > 200: flags.append("PR > 200 ms: suspeita de BAV 1º")
        if pr_ms < 120 and (qrs_ms is None or qrs_ms < 120): flags.append("PR < 120 ms: considerar pré-excitação")
    if qrs_ms is not None:
        if qrs_ms >= 120: flags.append("QRS ≥ 120 ms: sugere bloqueio de ramo completo/origem ventricular")
        elif 110 <= qrs_ms < 120: flags.append("QRS 110–119 ms: possível bloqueio de ramo incompleto")
    sexo_s = (data.get("sexo") or "").strip().upper()
    limiar = 450 if sexo_s == "M" else (470 if sexo_s == "F" else 460)
    if qtcb >= limiar or qtcfr >= limiar:
        flags.append(f"QTc prolongado (limiar {limiar} ms)")
    if qtcb < 350 or qtcfr < 350:
        flags.append("QTc possivelmente curto (<350 ms)")

    out = {
        "inputs": {"pr_ms": pr_ms, "qrs_ms": qrs_ms, "qt_ms": qt_ms, "rr_ms": rr_ms, "fc_bpm": fc_bpm,
                   "lead_i_mv": lead_i_mv, "aVF_mv": avf_mv, "sexo": sexo_s or None},
        "derived": {"QTc_Bazett_ms": round(qtcb,1), "QTc_Fridericia_ms": round(qtcfr,1),
                    "axis_angle_deg": round(angle,1) if angle is not None else None,
                    "axis_label": axis_label},
        "flags": flags,
        "notes": [
            "Bazett supercorrige em FC alta e subcorrige em FC baixa; Fridericia é alternativa mais estável.",
            "Classificação de eixo baseada em sinais de I/aVF e ângulo aproximado.",
            "Heurísticas são educacionais e não substituem avaliação clínica completa."
        ]
    }

    print(Panel.fit(f"[bold]FC:[/] {fc_bpm:.1f} bpm | [bold]QTc (Bazett/Fridericia):[/] {out['derived']['QTc_Bazett_ms']:.1f}/{out['derived']['QTc_Fridericia_ms']:.1f} ms"))
    if axis_label:
        print(Panel.fit(f"[bold]Eixo:[/] {axis_label} ({out['derived']['axis_angle_deg']}° aprox)"))
    if flags:
        print(Panel.fit("[bold yellow]Flags:[/]\n- " + "\n- ".join(flags)))
    else:
        print(Panel.fit("[bold green]Sem flags relevantes pelos limiares configurados.[/]"))

    if report:
        reports_dir = (REPO_ROOT / "reports"); reports_dir.mkdir(parents=True, exist_ok=True)
        ts = time.strftime("%Y%m%d-%H%M%S")
        with open(reports_dir / f"{ts}_analyze_values.json", "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
        with open(reports_dir / f"{ts}_analyze_values.md", "w", encoding="utf-8") as f:
            f.write(f"# Relatório analyze values — {ts}\n\n")
            f.write(f"- FC: {fc_bpm:.1f} bpm\n")
            f.write(f"- QTc Bazett: {out['derived']['QTc_Bazett_ms']:.1f} ms\n")
            f.write(f"- QTc Fridericia: {out['derived']['QTc_Fridericia_ms']:.1f} ms\n")
            if axis_label:
                f.write(f"- Eixo: {axis_label} ({out['derived']['axis_angle_deg']}°)\n")
            if flags:
                f.write("\n## Flags\n")
                for fl in flags: f.write(f"- {fl}\n")
        print(Panel.fit("[bold green]Relatórios salvos em reports/"))

app.add_typer(analyze_app, name="analyze")

if __name__ == "__main__":
    app()

# --------------------------
# INGEST commands (p3)
# --------------------------
ingest_app = typer.Typer(help="Ingestão de ECG por imagem (PNG/JPG).")

def _axis_from_I_aVF(lead_i_mv, avf_mv):
    if lead_i_mv is None or avf_mv is None:
        return None, None
    angle = math.degrees(math.atan2(avf_mv, lead_i_mv))
    if lead_i_mv >= 0 and avf_mv >= 0: label = "Normal"
    elif lead_i_mv >= 0 and avf_mv < 0: label = "Desvio para a esquerda"
    elif lead_i_mv < 0 and avf_mv >= 0: label = "Desvio para a direita"
    else: label = "Desvio extremo (noroeste)"
    return angle, label

def _qtc(qt_ms: float, rr_ms: float):
    qb = qt_ms / ((rr_ms/1000.0)**0.5)
    qf = qt_ms / ((rr_ms/1000.0)**(1.0/3.0))
    return round(qb,1), round(qf,1)

@ingest_app.command("image")
def ingest_image(
    image_path: str = typer.Argument(..., help="Arquivo PNG/JPG/PDF(1ª pág.)"),
    meta: str = typer.Option(None, "--meta", help="Sidecar META JSON (se não usar <arquivo>.meta.json)"),
    sexo: str = typer.Option(None, "--sexo", help="M/F para limiar QTc"),
    report: bool = typer.Option(False, "--report", help="Salvar laudo conforme schema"),
):
    p = pathlib.Path(image_path)
    if not p.exists():
        typer.echo(f"Arquivo não encontrado: {p}", err=True); raise typer.Exit(code=2)

    # Sidecar META
    meta_path = pathlib.Path(meta) if meta else p.with_suffix(p.suffix + ".meta.json")
    meta_data = {}
    if meta_path.exists():
        try:
            meta_data = json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception as e:
            typer.echo(f"Falha lendo META: {meta_path} — {e}", err=True)

    # Estratégia p3: se META tiver medidas/params, usamos; senão, placeholder educativo.
    dpi = meta_data.get("dpi")
    mm_per_mV = meta_data.get("mm_per_mV")
    ms_per_div = meta_data.get("ms_per_div")
    layout = meta_data.get("leads_layout", "3x4")
    measures = meta_data.get("measures", {})

    # Derivados
    rr_ms = measures.get("rr_ms")
    fc_bpm = measures.get("fc_bpm") or (60000.0/rr_ms if rr_ms else None)
    qt_ms = measures.get("qt_ms")
    pr_ms = measures.get("pr_ms")
    qrs_ms = measures.get("qrs_ms")
    lead_i = measures.get("lead_i_mv")
    avf = measures.get("avf_mv")

    angle, axis_label = _axis_from_I_aVF(lead_i, avf) if (lead_i is not None and avf is not None) else (None, None)
    qb, qf = (None, None)
    if qt_ms and (rr_ms or fc_bpm):
        rr_calc = rr_ms if rr_ms else 60000.0/float(fc_bpm)
        qb, qf = _qtc(float(qt_ms), float(rr_calc))

    sexo_s = (sexo or meta_data.get("sexo") or "").strip().upper()
    limiar = 450 if sexo_s == "M" else (470 if sexo_s == "F" else 460)

    flags = []
    if pr_ms is not None and pr_ms > 200: flags.append("PR > 200 ms: suspeita de BAV 1º")
    if pr_ms is not None and pr_ms < 120 and (qrs_ms is None or qrs_ms < 120): flags.append("PR < 120 ms: considerar pré-excitação")
    if qrs_ms is not None:
        if qrs_ms >= 120: flags.append("QRS ≥ 120 ms: bloqueio de ramo completo/origem ventricular")
        elif 110 <= qrs_ms < 120: flags.append("QRS 110–119 ms: bloqueio de ramo incompleto")
    if (qb is not None and qb >= limiar) or (qf is not None and qf >= limiar):
        flags.append(f"QTc prolongado (limiar {limiar} ms)")
    if (qb is not None and qb < 350) or (qf is not None and qf < 350):
        flags.append("QTc possivelmente curto (<350 ms)")

    suggested = []
    if flags:
        if any("QTc prolongado" in f for f in flags):
            suggested.append("Investigar causas de QT prolongado (drogas, distúrbios eletrolíticos, canalopatias).")
        if any("PR > 200" in f for f in flags):
            suggested.append("Compatível com BAV de 1º grau em contexto clínico adequado.")
        if any("pré-excitação" in f for f in flags):
            suggested.append("Se houver delta/QRS largo, considerar WPW e ajuste de manejo em taquiarritmias.")
        if any("QRS ≥ 120" in f for f in flags):
            suggested.append("QRS largo: avaliar morfologia BRE/BRD, discordâncias e critérios de isquemia em bloqueios.")
    else:
        suggested.append("Sem flags críticas pelos limiares configurados; correlacionar clinicamente.")

    report_obj = {
        "meta": {
            "source_image": str(p),
            "sidecar_meta_used": bool(meta_data),
            "ingest_version": "p3-0.1",
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "notes": ["Este laudo segue schema v0.1 (p3)."]
        },
        "patient_info": {
            "id": meta_data.get("patient_id"),
            "age": meta_data.get("age"),
            "sex": sexo_s or None,
            "context": meta_data.get("context")
        },
        "acquisition": {
            "dpi": dpi, "mm_per_mV": mm_per_mV, "ms_per_div": ms_per_div, "leads_layout": layout
        },
        "measures": {
            "pr_ms": pr_ms, "qrs_ms": qrs_ms, "qt_ms": qt_ms, "rr_ms": rr_ms,
            "fc_bpm": fc_bpm, "axis_angle_deg": angle, "axis_label": axis_label
        },
        "flags": flags,
        "suggested_interpretations": suggested,
        "version": "0.1.0"
    }

    # Resumo
    print(Panel.fit("[bold]Ingestão de imagem — resumo[/]"))
    print(f"Arquivo: {p.name}")
    if meta_data: print("META: encontrado e aplicado.")
    if fc_bpm: print(f"FC: {fc_bpm:.1f} bpm")
    if qt_ms: print(f"QT: {qt_ms} ms | QTc (B/F): {qb}/{qf} ms")
    if axis_label: print(f"Eixo: {axis_label} ({angle:.1f}° aprox)")
    if flags: print("Flags: " + "; ".join(flags))

    # Salvar relatórios
    if report:
        reports_dir = (REPO_ROOT / "reports"); reports_dir.mkdir(parents=True, exist_ok=True)
        ts = time.strftime("%Y%m%d-%H%M%S")
        with open(reports_dir / f"{ts}_ecg_report.json", "w", encoding="utf-8") as f:
            json.dump(report_obj, f, ensure_ascii=False, indent=2)
        with open(reports_dir / f"{ts}_ecg_report.md", "w", encoding="utf-8") as f:
            f.write(f"# Laudo ECG (ingest image) — {ts}\\n\\n")
            f.write(f"- Arquivo: {p.name}\\n")
            if fc_bpm: f.write(f"- FC: {fc_bpm:.1f} bpm\\n")
            if qt_ms: f.write(f"- QT: {qt_ms} ms | QTc (B/F): {qb}/{qf} ms\\n")
            if axis_label: f.write(f"- Eixo: {axis_label} ({angle:.1f}°)\\n")
            if flags:\n                f.write("\\n## Flags\\n"); [f.write(f"- {fl}\\n") for fl in flags]\n            if suggested:\n                f.write("\\n## Sugestões/Observações\\n"); [f.write(f"- {s}\\n") for s in suggested]\n        print(Panel.fit("[bold green]Laudos salvos em reports/"))

app.add_typer(ingest_app, name="ingest")

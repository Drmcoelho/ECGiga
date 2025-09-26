
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
    auto_grid: bool = typer.Option(False, "--auto-grid", help="Tentar calibrar grade e segmentar 12D"),
    deskew: bool = typer.Option(False, "--deskew", help="Estimar rotação e deskew antes de processar"),
    normalize: bool = typer.Option(False, "--normalize", help="Normalizar escala para px/mm ~10"),
    schema_v2: bool = typer.Option(True, "--schema-v2/--schema-v1", help="Emitir laudo no schema v0.2"),
    auto_leads: bool = typer.Option(False, "--auto-leads", help="Detectar layout e rótulos automaticamente"),
    rpeaks_lead: str = typer.Option(None, "--rpeaks-lead", help="Derivação para FC (ex.: II, V2)"),
    schema_v3: bool = typer.Option(True, "--schema-v3/--schema-v2-off", help="Emitir laudo no schema v0.3"),
    rpeaks_robust: bool = typer.Option(False, "--rpeaks-robust", help="Usar detecção robusta de R-peaks (Pan‑Tompkins-like)"),
    intervals: bool = typer.Option(False, "--intervals", help="Estimar PR/QRS/QT/QTc a partir do traçado"),
    schema_v4: bool = typer.Option(True, "--schema-v4/--schema-v3-off", help="Emitir laudo no schema v0.4"),
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
    auto_grid: bool = typer.Option(False, "--auto-grid", help="Tentar calibrar grade e segmentar 12D"),
    deskew: bool = typer.Option(False, "--deskew", help="Estimar rotação e deskew antes de processar"),
    normalize: bool = typer.Option(False, "--normalize", help="Normalizar escala para px/mm ~10"),
    schema_v2: bool = typer.Option(True, "--schema-v2/--schema-v1", help="Emitir laudo no schema v0.2"),
    auto_leads: bool = typer.Option(False, "--auto-leads", help="Detectar layout e rótulos automaticamente"),
    rpeaks_lead: str = typer.Option(None, "--rpeaks-lead", help="Derivação para FC (ex.: II, V2)"),
    schema_v3: bool = typer.Option(True, "--schema-v3/--schema-v2-off", help="Emitir laudo no schema v0.3"),
    rpeaks_robust: bool = typer.Option(False, "--rpeaks-robust", help="Usar detecção robusta de R-peaks (Pan‑Tompkins-like)"),
    intervals: bool = typer.Option(False, "--intervals", help="Estimar PR/QRS/QT/QTc a partir do traçado"),
    schema_v4: bool = typer.Option(True, "--schema-v4/--schema-v3-off", help="Emitir laudo no schema v0.4"),
    report: bool = typer.Option(False, "--report", help="Salvar laudo conforme schema"),
):
    p = pathlib.Path(image_path)
    if not p.exists():
        typer.echo(f"Arquivo não encontrado: {p}", err=True); raise typer.Exit(code=2)

    # Sidecar META
    meta_path = pathlib.Path(meta) if meta else p.with_suffix(p.suffix + ".meta.json")
    # Pré-processamento opcional: deskew + normalize (aplicados sequencialmente sobre arquivo temporário em memória)
    from PIL import Image
    _img = Image.open(_buf).convert("RGB")
    if deskew:
        from cv.deskew import estimate_rotation_angle, rotate_image
        _info = estimate_rotation_angle(_img, search_deg=6.0, step=0.5)
        _img = rotate_image(_img, _info['angle_deg'])
    if normalize:
        from cv.normalize import normalize_scale
        _img, _scale, _pxmm = normalize_scale(_img, target_px_per_mm=10.0)
    # Substitui path por buffer em memória para etapas seguintes que leem a imagem
    import io as _io
    _buf = _io.BytesIO()
    _img.save(_buf, format="PNG")
    _buf.seek(0)
    
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
    # Auto grid/segmentation if requested or if no calibration present
    seg = None
    grid = None
    layout_det = None
    lead_labels = None
    rpeaks_out = None
    intervals_out = None


    if auto_grid:
        try:
            from PIL import Image
            import numpy as _np
            from cv.grid_detect import estimate_grid_period_px
            from cv.segmentation import segment_12leads_basic, find_content_bbox
            arr = _np.asarray(Image.open(_buf).convert("RGB"))
            grid = estimate_grid_period_px(arr)
            gray = _np.asarray(Image.open(_buf).convert("L"))
            bbox = find_content_bbox(gray)
            seg_leads = segment_12leads_basic(gray, bbox=bbox)
            seg = {"content_bbox": bbox, "leads": seg_leads}
        if auto_leads:
            from cv.lead_ocr import choose_layout
            cand = {"3x4":[d["bbox"] for d in seg_leads]}
            layout_det = choose_layout(_np.asarray(Image.open(p).convert("L")), {"3x4":[d["bbox"] for d in seg_leads]})
            lead_labels = layout_det.get("labels")
        if rpeaks_lead:
            from cv.rpeaks_from_image import extract_trace_centerline, smooth_signal, detect_rpeaks_from_trace, estimate_px_per_sec
            # procura bbox do lead requisitado
            _lab2box = {d["lead"]: d["bbox"] for d in seg_leads}
            if rpeaks_lead in _lab2box:
                _x0,_y0,_x1,_y1 = _lab2box[rpeaks_lead]
                _gray = _np.asarray(Image.open(p).convert("L"))
                _crop = _gray[_y0:_y1, _x0:_x1]
                _trace = smooth_signal(extract_trace_centerline(_crop, band=0.8), win=11)
                _pxmm = (grid.get("px_small_x") if grid else None) or (grid.get("px_small_y") if grid else None)
                _pxsec = estimate_px_per_sec(_pxmm, 25.0) or 250.0
                rpeaks_out = detect_rpeaks_from_trace(_trace, px_per_sec=_pxsec, zthr=2.0)
                if rpeaks_robust:
                    from cv.rpeaks_robust import pan_tompkins_like
                    _rob = pan_tompkins_like(_trace, _pxsec)
                    rpeaks_out = {"peaks_idx": _rob["peaks_idx"], "method": "pan_tompkins_like"}
                if intervals:
                    from cv.intervals import intervals_from_trace
                    intervals_out = intervals_from_trace(_trace, rpeaks_out.get("peaks_idx") or [], _pxsec)

                rpeaks_out["lead_used"] = rpeaks_lead
        
        except Exception as e:
            typer.echo(f"Auto-grid falhou: {e}", err=True)
    

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
            "dpi": dpi, "mm_per_mV": mm_per_mV, "ms_per_div": ms_per_div, "leads_layout": layout,
            "px_per_mm_x": (grid.get("px_small_x") if grid else None),
            "px_per_mm_y": (grid.get("px_small_y") if grid else None),
            "px_small_grid": (grid.get("px_small_x") if grid else None),
            "px_big_grid": (grid.get("px_big_x") if grid else None),
            "grid_confidence": (grid.get("confidence") if grid else None)
        },
        "measures": {
            "pr_ms": pr_ms, "qrs_ms": qrs_ms, "qt_ms": qt_ms, "rr_ms": rr_ms,
            "fc_bpm": fc_bpm, "axis_angle_deg": angle, "axis_label": axis_label
        },
        "flags": flags,
        "suggested_interpretations": suggested,
        "segmentation": (seg if seg else None),
        "layout_detection": (layout_det if auto_leads else None),
        "rpeaks": (rpeaks_out if rpeaks_lead else None),
        "intervals": (intervals_out if intervals else None),
        "version": ("0.4.0" if schema_v4 else ("0.3.0" if schema_v3 else ("0.2.0" if schema_v2 else "0.1.0")))
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


# --------------------------
# ASSETS commands (p3c)
# --------------------------
assets_app = typer.Typer(help="Automação de assets (download, verificação de licenças, pré-processamento).")

def _import_scripts():
    import sys as _sys, pathlib as _pl
    p = REPO_ROOT / "scripts" / "python"
    if str(p) not in _sys.path:
        _sys.path.append(str(p))

@assets_app.command("download")
def assets_download():
    """Baixa imagens do manifesto para assets/raw/images/"""
    _import_scripts()
    from download_assets import main as _main
    _main()

@assets_app.command("verify")
def assets_verify(manifest_in: str = typer.Option("assets/manifest/ecg_images.v1.jsonl", "--in"),
                  manifest_out: str = typer.Option(None, "--out")):
    """Verifica licenças/autor e gera ecg_images.verified.jsonl + créditos."""
    _import_scripts()
    from verify_licenses import main as _main
    _main(manifest_in, manifest_out)

@assets_app.command("preprocess")
def assets_preprocess():
    """Gera derivados WEBP/AVIF e manifesto ecg_images.derived.json."""
    _import_scripts()
    from preprocess_images import main as _main
    _main()

app.add_typer(assets_app, name="assets")


# --------------------------
# CV commands (p4)
# --------------------------
cv_app = typer.Typer(help="Visão computacional (grade + segmentação 12D).")

def _open_image_to_array(path: pathlib.Path):
    from PIL import Image
    import numpy as np
    img = Image.open(path).convert("RGB")
    return np.asarray(img)

@cv_app.command("calibrate")
def cv_calibrate(image_path: str = typer.Argument(..., help="PNG/JPG"),
                 dump_json: bool = typer.Option(False, "--json", help="Imprime JSON com calibração")):
    """Detecta período de grade (px) e estima px/mm grande/pequena."""
    import json as _json
    import numpy as _np
    from cv.grid_detect import estimate_grid_period_px
    arr = _open_image_to_array(pathlib.Path(image_path))
    info = estimate_grid_period_px(arr)
    # Heurística: px_small ≈ período; px_big ≈ 5*px_small; px/mm ≈ px_small (se small=1mm)
    px_small = float(info.get("px_small_x") or info.get("px_small_y") or 0.0)
    px_big = float(info.get("px_big_x") or info.get("px_big_y") or 0.0)
    out = {
        "px_small_grid": px_small,
        "px_big_grid": px_big,
        "px_per_mm_x": px_small or None,
        "px_per_mm_y": px_small or None,
        "grid_confidence": info.get("confidence", 0.0),
    }
    if dump_json:
        print(_json.dumps(out, ensure_ascii=False, indent=2))
    else:
        print(Panel.fit(f"[bold]Grid (px):[/] small≈{px_small:.1f}, big≈{px_big:.1f} | conf {out['grid_confidence']:.2f}"))
    return out

@cv_app.command("segment")
def cv_segment(image_path: str = typer.Argument(..., help="PNG/JPG"),
               layout: str = typer.Option("3x4", "--layout", help="Layout esperado"),
               dump_json: bool = typer.Option(False, "--json", help="Imprime JSON com caixas")):
    """Segmenta a área útil em 12 caixas para as derivações (básico)."""
    import json as _json
    import numpy as _np
    from PIL import Image
    from cv.segmentation import segment_12leads_basic, find_content_bbox
    gray = _np.asarray(Image.open(image_path).convert("L"))
    bbox = find_content_bbox(gray)
    leads = segment_12leads_basic(gray, layout=layout, bbox=bbox)
    out = {"content_bbox": bbox, "leads": leads}
    if dump_json:
        print(_json.dumps(out, ensure_ascii=False, indent=2))
    else:
        print(Panel.fit(f"[bold]Content bbox:[/] {bbox} — {len(leads)} leads geradas."))
    return out

app.add_typer(cv_app, name="cv")


@cv_app.command("deskew")
def cv_deskew(image_path: str = typer.Argument(..., help="PNG/JPG"),
              save: str = typer.Option(None, "--save", help="Salvar imagem deskew"),
              search_deg: float = typer.Option(6.0, "--range", help="Ângulo máximo (+/-)")):
    """Estima rotação e aplica deskew (busca bruta)."""
    from PIL import Image
    from cv.deskew import estimate_rotation_angle, rotate_image
    p = pathlib.Path(image_path)
    img = Image.open(_buf).convert("RGB")
    info = estimate_rotation_angle(img, search_deg=search_deg, step=0.5)
    print(f"Ângulo estimado: {info['angle_deg']:.2f}° (score {info['score']:.3f} vs {info['score0']:.3f})")
    if save:
        out = rotate_image(img, info['angle_deg'])
        out.save(save)
        print(f"Imagem salva: {save}")

@cv_app.command("normalize")
def cv_normalize(image_path: str = typer.Argument(..., help="PNG/JPG"),
                 target_pxmm: float = typer.Option(10.0, "--pxmm", help="px por mm alvo"),
                 save: str = typer.Option(None, "--save", help="Salvar imagem normalizada")):
    """Normaliza escala para atingir px/mm alvo (sem upscaling >2x)."""
    from PIL import Image
    from cv.normalize import normalize_scale
    p = pathlib.Path(image_path)
    img = Image.open(_buf).convert("RGB")
    im1, scale, pxmm = normalize_scale(img, target_px_per_mm=target_pxmm)
    print(f"px/mm estimado: {pxmm} | scale aplicado: {scale:.3f}")
    if save:
        im1.save(save)
        print(f"Imagem salva: {save}")

@cv_app.command("layout-seg")
def cv_layout_seg(image_path: str = typer.Argument(..., help="PNG/JPG"),
                  layout: str = typer.Option("3x4", "--layout", help="3x4 | 6x2 | 3x4+rhythm"),
                  dump_json: bool = typer.Option(False, "--json", help="Imprime JSON com caixas")):
    """Segmenta conforme layout escolhido (3x4, 6x2 ou 3x4+rhythm)."""
    import json as _json, numpy as _np
    from PIL import Image
    from cv.segmentation_ext import segment_layout
    gray = _np.asarray(Image.open(image_path).convert("L"))
    seg = segment_layout(gray, layout=layout)
    if dump_json:
        print(_json.dumps({"leads": seg}, ensure_ascii=False, indent=2))
    else:
        print(f"{len(seg)} caixas geradas para layout {layout}.")


@cv_app.command("detect-layout")
def cv_detect_layout(image_path: str = typer.Argument(..., help="PNG/JPG"),
                     layout_hint: str = typer.Option(None, "--hint", help="3x4|6x2|3x4+rhythm"),
                     dump_json: bool = typer.Option(False, "--json")):
    """Detecta layout (3x4/6x2/3x4+ritmo) por rótulos dentro das caixas candidatas."""
    import json as _json, numpy as _np
    from PIL import Image
    from cv.segmentation import find_content_bbox
    from cv.segmentation_ext import segment_layout
    from cv.lead_ocr import choose_layout
    gray = _np.asarray(Image.open(image_path).convert("L"))
    bbox = find_content_bbox(gray)
    candidates = {
        "3x4": segment_layout(gray, "3x4", bbox=bbox),
        "6x2": segment_layout(gray, "6x2", bbox=bbox),
        "3x4+rhythm": segment_layout(gray, "3x4+rhythm", bbox=bbox),
    }
    best = choose_layout(gray, {k:[d["bbox"] for d in v] for k,v in candidates.items()})
    out = {"layout": best["layout"] or "unknown", "score": best["score"], "labels": best["labels"], "content_bbox": bbox}
    if dump_json:
        print(_json.dumps(out, ensure_ascii=False, indent=2))
    else:
        print(f"Layout: {out['layout']} (score {out['score']:.2f})")
    return out

@cv_app.command("detect-leads")
def cv_detect_leads(image_path: str = typer.Argument(..., help="PNG/JPG"),
                    layout: str = typer.Option("3x4", "--layout"),
                    dump_json: bool = typer.Option(False, "--json")):
    """Detecta rótulos por caixa para um layout escolhido, retornando {lead,label,score}."""
    import json as _json, numpy as _np
    from PIL import Image
    from cv.segmentation import find_content_bbox
    from cv.segmentation_ext import segment_layout
    from cv.lead_ocr import detect_labels_per_box
    gray = _np.asarray(Image.open(image_path).convert("L"))
    bbox = find_content_bbox(gray)
    boxes = [d["bbox"] for d in segment_layout(gray, layout, bbox=bbox)]
    det = detect_labels_per_box(gray, boxes)
    if dump_json:
        print(_json.dumps(det, ensure_ascii=False, indent=2))
    else:
        ok = sum(1 for d in det if d.get("label"))
        print(f"Rótulos detectados em {ok}/{len(det)} caixas.")
    return det

@cv_app.command("rpeaks")
def cv_rpeaks(image_path: str = typer.Argument(..., help="PNG/JPG"),
              layout: str = typer.Option("3x4", "--layout"),
              lead: str = typer.Option("II", "--lead", help="Lead alvo para FC (ex.: II, V2, V5)"),
              speed_mm_s: float = typer.Option(25.0, "--speed", help="Velocidade mm/s"),
              zthr: float = typer.Option(2.0, "--zthr", help="Limiar z-score p/ picos"),
              dump_json: bool = typer.Option(False, "--json")):
    """Extrai traçado 1D da caixa da derivação alvo e estima R-peaks/FC."""
    import json as _json, numpy as _np
    from PIL import Image
    from cv.segmentation import find_content_bbox
    from cv.segmentation_ext import segment_layout
    from cv.grid_detect import estimate_grid_period_px
    from cv.rpeaks_from_image import extract_trace_centerline, smooth_signal, detect_rpeaks_from_trace, estimate_px_per_sec
    gray = _np.asarray(Image.open(image_path).convert("L"))
    bbox = find_content_bbox(gray)
    seg = segment_layout(gray, layout, bbox=bbox)
    # Seleciona caixa pela label esperada
    label2idx = {d["lead"]: i for i,d in enumerate(seg)}
    if lead not in label2idx:
        raise typer.Exit(code=2)
    x0,y0,x1,y1 = seg[label2idx[lead]]["bbox"]
    crop = gray[y0:y1, x0:x1]
    trace = extract_trace_centerline(crop, band=0.8)
    trace = smooth_signal(trace, win=11)
    grid = estimate_grid_period_px(_np.asarray(Image.open(image_path).convert("RGB")))
    pxmm = grid.get("px_small_x") or grid.get("px_small_y")
    pxsec = estimate_px_per_sec(pxmm, speed_mm_per_sec=speed_mm_s)
    res = detect_rpeaks_from_trace(trace, px_per_sec=pxsec or 250.0, zthr=zthr)
    out = {"lead_used": lead, **res}
    if dump_json:
        print(_json.dumps(out, ensure_ascii=False, indent=2))
    else:
        print(f"Lead {lead}: HR média {res['hr_bpm_mean']:.1f} bpm (picos {len(res['peaks_idx'])})" if res['hr_bpm_mean'] else f"Lead {lead}: insuficiente para FC.")
    return out


@cv_app.command("rpeaks-robust")
def cv_rpeaks_robust(image_path: str = typer.Argument(..., help="PNG/JPG"),
                     layout: str = typer.Option("3x4", "--layout"),
                     lead: str = typer.Option("II", "--lead"),
                     speed_mm_s: float = typer.Option(25.0, "--speed"),
                     dump_json: bool = typer.Option(False, "--json")):
    """Detecção robusta de R-peaks (Pan‑Tompkins-like) a partir da imagem recortada da derivação alvo."""
    import json as _json, numpy as _np
    from PIL import Image
    from cv.segmentation import find_content_bbox
    from cv.segmentation_ext import segment_layout
    from cv.grid_detect import estimate_grid_period_px
    from cv.rpeaks_from_image import extract_trace_centerline, smooth_signal, estimate_px_per_sec
    from cv.rpeaks_robust import pan_tompkins_like
    gray = _np.asarray(Image.open(image_path).convert("L"))
    bbox = find_content_bbox(gray)
    seg = segment_layout(gray, layout, bbox=bbox)
    lab2box = {d["lead"]: d["bbox"] for d in seg}
    if lead not in lab2box: raise typer.Exit(code=2)
    x0,y0,x1,y1 = lab2box[lead]
    crop = gray[y0:y1, x0:x1]
    trace = smooth_signal(extract_trace_centerline(crop), win=11)
    pxmm = (estimate_grid_period_px(_np.asarray(Image.open(image_path).convert("RGB"))).get("px_small_x")
            or estimate_grid_period_px(_np.asarray(Image.open(image_path).convert("RGB"))).get("px_small_y"))
    pxsec = estimate_px_per_sec(pxmm, speed_mm_per_sec=speed_mm_s) or 250.0
    res = pan_tompkins_like(trace, pxsec)
    out = {"lead_used": lead, **{k:v for k,v in res.items() if k!='signals'}}
    if dump_json: print(_json.dumps(out, ensure_ascii=False, indent=2))
    else: print(f"Lead {lead}: {len(out['peaks_idx'])} picos detectados | fs≈{pxsec:.1f} px/s")
    return out

@cv_app.command("intervals")
def cv_intervals(image_path: str = typer.Argument(..., help="PNG/JPG"),
                 layout: str = typer.Option("3x4", "--layout"),
                 lead: str = typer.Option("II", "--lead"),
                 speed_mm_s: float = typer.Option(25.0, "--speed"),
                 dump_json: bool = typer.Option(False, "--json")):
    """Onsets/offsets de QRS e estimativas de PR/QRS/QT/QTc a partir de R-peaks robustos."""
    import json as _json, numpy as _np
    from PIL import Image
    from cv.segmentation import find_content_bbox
    from cv.segmentation_ext import segment_layout
    from cv.grid_detect import estimate_grid_period_px
    from cv.rpeaks_from_image import extract_trace_centerline, smooth_signal, estimate_px_per_sec
    from cv.rpeaks_robust import pan_tompkins_like
    from cv.intervals import intervals_from_trace
    gray = _np.asarray(Image.open(image_path).convert("L"))
    bbox = find_content_bbox(gray)
    seg = segment_layout(gray, layout, bbox=bbox)
    lab2box = {d["lead"]: d["bbox"] for d in seg}
    if lead not in lab2box: raise typer.Exit(code=2)
    x0,y0,x1,y1 = lab2box[lead]
    crop = gray[y0:y1, x0:x1]
    trace = smooth_signal(extract_trace_centerline(crop), win=11)
    pxmm = (estimate_grid_period_px(_np.asarray(Image.open(image_path).convert("RGB"))).get("px_small_x")
            or estimate_grid_period_px(_np.asarray(Image.open(image_path).convert("RGB"))).get("px_small_y"))
    pxsec = estimate_px_per_sec(pxmm, speed_mm_per_sec=speed_mm_s) or 250.0
    rdet = pan_tompkins_like(trace, pxsec)
    iv = intervals_from_trace(trace, rdet["peaks_idx"], pxsec)
    out = {"lead_used": lead, "rpeaks": {"peaks_idx": rdet["peaks_idx"]}, "intervals": iv}
    if dump_json: print(_json.dumps(out, ensure_ascii=False, indent=2))
    else: 
        m = iv["median"]
        print(f"PR {m.get('PR_ms')} ms | QRS {m.get('QRS_ms')} ms | QT {m.get('QT_ms')} ms | QTcB {m.get('QTc_B')} ms | QTcF {m.get('QTc_F')} ms")
    return out


quiz_app = typer.Typer(help="Geração de quizzes MCQ a partir de laudos.")

@quiz_app.command("build")
def quiz_build(report_json: str = typer.Argument(..., help="Arquivo de laudo JSON"),
               out_json: str = typer.Option(None, "--out", help="Arquivo de saída (JSON)")):
    """Gera MCQs automaticamente com base em PR/QRS/QT/QTc/HR do laudo."""
    import json as _json
    from quiz.generate_quiz import quiz_from_report
    with open(report_json,"r",encoding="utf-8") as f:
        rep = _json.load(f)
    q = quiz_from_report(rep)
    if out_json:
        with open(out_json,"w",encoding="utf-8") as f: _json.dump(q,f,ensure_ascii=False,indent=2)
        print(f"Quiz salvo em {out_json}")
    else:
        print(_json.dumps(q, ensure_ascii=False, indent=2))

app.add_typer(quiz_app, name="quiz")

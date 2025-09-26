
from __future__ import annotations
import json, glob
from pathlib import Path
from typing import List, Dict

TEMPLATE = """<!doctype html>
<meta charset="utf-8">
<title>ECGiga — Relatório de Desempenho</title>
<style>
body{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;background:#f8fafc;margin:0}
header{background:#111;color:#fff;padding:14px 18px}
main{padding:16px;max-width:980px;margin:0 auto}
.card{background:#fff;border:1px solid #e5e7eb;border-radius:12px;padding:14px;margin:12px 0}
table{width:100%;border-collapse:collapse}
th,td{border-bottom:1px solid #e5e7eb;padding:8px;text-align:left}
.badge{display:inline-block;background:#eef;border:1px solid #99c;border-radius:4px;padding:1px 6px;margin-left:6px;font-size:12px}
</style>
<header><h3>ECGiga — Relatório de Desempenho</h3></header>
<main>
  <div class="card">
    <h4>Resumo</h4>
    <p>Arquivos analisados: {nfiles}</p>
    <p>Macro-F1 médio: <b>{macro_mean:.2f}</b></p>
  </div>
  <div class="card">
    <h4>Detalhes por arquivo</h4>
    <table>
      <thead><tr><th>Arquivo</th><th>Macro-F1</th><th>Observações</th></tr></thead>
      <tbody>
      {rows}
      </tbody>
    </table>
  </div>
  <div class="card">
    <h4>Recomendações</h4>
    <ul>
      <li>Baixa F1 em <b>ST/T</b> → estudar <i>ST–T Lab</i> (isquemia/eletrolíticos).</li>
      <li>Baixa F1 em <b>QRS</b> → revisar <i>Conduction Lab</i> (PR/QRS, BRD/BRE) e <i>AP Lab</i> (fase 0).</li>
      <li>Baixa F1 em <b>P/PR</b> → reforçar marcapasso sinusal e atraso AV (AP Lab + Conduction Lab).</li>
    </ul>
  </div>
</main>
"""

def render(perf_files: List[Path], out_html: Path) -> str:
    rows = []
    macros = []
    for p in perf_files:
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
            mf = float(d.get("macro_F1") or 0.0); macros.append(mf)
            note = []
            per = d.get("per_label") or {}
            for lab in ("ST","T","QRS","P","PR"):
                item = per.get(lab)
                if item and float(item.get("F1",0)) < 0.5:
                    note.append(f"{lab}↓")
            rows.append(f"<tr><td>{p.name}</td><td>{mf:.2f}</td><td>{', '.join(note) or '-'}</td></tr>")
        except Exception:
            rows.append(f"<tr><td>{p.name}</td><td>-</td><td>erro ao ler</td></tr>")
    macro_mean = sum(macros)/len(macros) if macros else 0.0
    html = TEMPLATE.format(nfiles=len(perf_files), macro_mean=macro_mean, rows="\\n".join(rows))
    out_html.parent.mkdir(parents=True, exist_ok=True)
    out_html.write_text(html, encoding="utf-8")
    return str(out_html)

def build_report(input_glob: str, out_html: str) -> str:
    files = [Path(p) for p in glob.glob(input_glob)]
    return render(files, Path(out_html))

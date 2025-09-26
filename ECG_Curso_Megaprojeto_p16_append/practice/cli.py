
from __future__ import annotations
import json, random
from pathlib import Path
import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

app = typer.Typer(help="Prática e Quiz (p13)")
console = Console()

def _load_json(p: Path):
    return json.loads(Path(p).read_text(encoding='utf-8'))

@app.command("build")
def build_practice(reports_dir: str = typer.Argument("reports", help="Pasta com *.report.json"),
                   out_dir: str = typer.Argument("web_app/case_player/cases")):
    """Gera casos estáticos (JSON) a partir de laudos para o Case Player."""
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    rep_dir = Path(reports_dir)
    items = []
    for p in rep_dir.glob("*.json"):
        try:
            rep = _load_json(p)
            meta = rep.get("meta",{})
            item = {"name": Path(meta.get("src", p.name)).stem,
                    "report": rep}
            (out / f"{item['name']}.json").write_text(json.dumps(item, ensure_ascii=False, indent=2), encoding='utf-8')
            items.append(item["name"])
        except Exception as e:
            console.print(f"[red]Falha em {p}: {e}[/red]")
    (out / "_index.json").write_text(json.dumps({"cases": items}, ensure_ascii=False, indent=2), encoding='utf-8')
    console.print(Panel.fit(f"Gerados {len(items)} casos em {out}"))

@app.command("serve")
def serve_case_player(port: int = typer.Option(8013, "--port")):
    """Serve o Case Player (estático) localmente."""
    import http.server, socketserver, os
    os.chdir("web_app/case_player")
    Handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", port), Handler) as httpd:
        console.print(f"[green]Case Player em http://127.0.0.1:{port}[/green]")
        httpd.serve_forever()

@app.command("quiz")
def run_quiz(quiz_json: str = typer.Argument(..., help="Arquivo quiz *.json"),
             n: int = typer.Option(8, "--n"),
             shuffle: bool = typer.Option(True, "--shuffle/--no-shuffle")):
    """Executa um MCQ no terminal com feedback imediato e score final."""
    data = _load_json(quiz_json)
    qs = list(data.get("questions", []))[:n]
    if shuffle:
        random.shuffle(qs)
    score=0
    for i,q in enumerate(qs,1):
        console.rule(f"[bold]Q{i}[/bold]")
        console.print(Markdown(q.get("prompt","(sem enunciado)")))
        ch = q.get("choices", [])
        if shuffle: random.shuffle(ch)
        tbl = Table(show_header=True, header_style="bold")
        tbl.add_column("#"); tbl.add_column("Alternativa")
        for j,c in enumerate(ch):
            tbl.add_row(chr(65+j), c["text"])
        console.print(tbl)
        ans = console.input("[cyan]Sua resposta (A,B,C,...)>[/cyan] ").strip().upper()[:1]
        idx = ord(ans)-65 if ans else -1
        ok = (0<=idx<len(ch)) and bool(ch[idx].get("is_correct"))
        exp = ch[idx].get("explanation") if (0<=idx<len(ch)) else "Sem explicação."
        if ok:
            score += 1
            console.print(Panel.fit("[green]Correto![/green]\\n"+exp))
        else:
            # destaque correta
            corr = next((c for c in ch if c.get("is_correct")), None)
            corr_txt = corr.get("text") if corr else "(?)"
            console.print(Panel.fit(f"[red]Incorreto.[/red]\\nCorreta: [bold]{corr_txt}[/bold]\\n{exp}"))
    console.rule("[bold]Resultado[/bold]")
    console.print(f"Score: {score}/{len(qs)}  ({(100.0*score/len(qs)):.0f}%)")

"""Quiz management and interactive learning CLI."""

from __future__ import annotations
import json
import pathlib
import time
import random
from typing import Tuple, Optional

import typer
from rich import print
from rich.panel import Panel
from rich.table import Table
from jsonschema import Draft202012Validator

from .logging_utils import get_logger

logger = get_logger(__name__)

quiz_app = typer.Typer(help="Quiz management and interactive learning")

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
SCHEMA_CANDIDATES = [
    REPO_ROOT / "quiz" / "schema" / "mcq.schema.json",
    REPO_ROOT / "cli_app" / "quiz" / "schema" / "mcq.schema.json",
]


def load_schema() -> dict:
    """Load MCQ schema from available locations."""
    for p in SCHEMA_CANDIDATES:
        if p.exists():
            logger.debug(f"Loading schema from {p}")
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
    typer.echo("Schema mcq.schema.json não encontrado.", err=True)
    raise typer.Exit(code=2)


def validate_item(item: dict, schema: dict):
    """Validate quiz item against schema."""
    Draft202012Validator(schema).validate(item)


def ask_item(item: dict) -> Optional[Tuple[bool, int]]:
    """Present quiz item to user and collect response.
    
    Returns:
        Tuple of (correct, chosen_index) or None if user quits
    """
    print(Panel.fit(f"[bold cyan]{item['topic']}[/] — dificuldade: {item['difficulty']}"))
    print(f"[bold]Q:[/] {item['stem']}\n")
    
    for i, opt in enumerate(item["options"]):
        print(f"  [bold]{chr(65+i)}[/]) {opt}")
    
    ans = input("\nSua resposta (A/B/C/D... ou 'q' para sair): ").strip().upper()
    if ans == 'Q':
        return None
    
    try:
        idx = ord(ans) - 65
        if idx < 0 or idx >= len(item["options"]):
            print("[bold red]Resposta inválida![/]")
            return ask_item(item)  # Ask again
    except (ValueError, TypeError):
        print("[bold red]Resposta inválida![/]")
        return ask_item(item)  # Ask again
    
    correct = idx == item["answer_index"]
    if correct:
        print(Panel.fit("[bold green]Correto![/]"))
    else:
        print(Panel.fit(f"[bold red]Incorreto[/] — correta: {chr(65+item['answer_index'])}"))
    
    print("\n[bold]Explicação:[/]")
    print(item["explanation"])
    return correct, idx


@quiz_app.command()
def run(
    path: str = typer.Argument(..., help="Arquivo .json do quiz"),
):
    """Run a single quiz item."""
    logger.info(f"Running quiz from {path}")
    schema = load_schema()
    p = pathlib.Path(path)
    
    if not p.exists():
        typer.echo(f"Arquivo não encontrado: {p}", err=True)
        raise typer.Exit(code=2)
    
    with open(p, "r", encoding="utf-8") as f:
        item = json.load(f)
    
    validate_item(item, schema)
    ask_item(item)


@quiz_app.command()
def validate(
    path: str = typer.Argument(..., help="Arquivo .json para validar"),
):
    """Validate a quiz item against schema."""
    logger.info(f"Validating quiz item {path}")
    schema = load_schema()
    p = pathlib.Path(path)
    
    if not p.exists():
        typer.echo(f"Arquivo não encontrado: {p}", err=True)
        raise typer.Exit(code=2)
    
    with open(p, "r", encoding="utf-8") as f:
        item = json.load(f)
    
    validate_item(item, schema)
    print(Panel.fit("[bold green]OK[/] — Schema válido."))


@quiz_app.command()
def bank(
    path: str = typer.Argument(..., help="Diretório com arquivos .json do banco"),
    report: bool = typer.Option(False, "--report", help="Salvar relatórios em reports/"),
    shuffle: bool = typer.Option(True, "--shuffle/--no-shuffle", help="Embaralhar ordem"),
    seed: int = typer.Option(0, "--seed", help="Seed para reprodutibilidade (0 = auto)"),
):
    """Run quiz bank session with multiple items."""
    logger.info(f"Running quiz bank from {path}")
    schema = load_schema()
    p = pathlib.Path(path)
    
    if not p.exists() or not p.is_dir():
        typer.echo(f"Diretório inválido: {p}", err=True)
        raise typer.Exit(code=2)
    
    # Load all quiz items
    items = []
    for fp in sorted(p.glob("*.json")):
        try:
            with open(fp, "r", encoding="utf-8") as f:
                it = json.load(f)
            validate_item(it, schema)
            it["_src"] = str(fp)
            items.append(it)
        except Exception as e:
            logger.warning(f"Skipping invalid file {fp}: {e}")
    
    if not items:
        typer.echo("Nenhum .json válido encontrado.", err=True)
        raise typer.Exit(code=2)
    
    logger.info(f"Loaded {len(items)} quiz items")
    
    # Shuffle if requested
    if shuffle:
        r = random.Random(seed or time.time_ns())
        r.shuffle(items)
        logger.debug("Items shuffled")
    
    # Interactive session
    results = []
    for it in items:
        ans = ask_item(it)
        if ans is None:
            break
        
        ok, chosen = ans
        results.append({
            "id": it["id"],
            "topic": it["topic"], 
            "difficulty": it["difficulty"],
            "correct": bool(ok),
            "chosen_index": chosen,
            "answer_index": it["answer_index"],
            "src": it["_src"]
        })
        print("-" * 60)
    
    if not results:
        print(Panel.fit("[bold yellow]Sem respostas registradas.[/]"))
        return
    
    # Calculate statistics
    total = len(results)
    acertos = sum(1 for r in results if r["correct"])
    pct = 100.0 * acertos / total
    
    # Display summary table
    tbl = Table(title="Resumo — Banco")
    tbl.add_column("Total")
    tbl.add_column("Acertos")
    tbl.add_column("%")
    tbl.add_row(str(total), str(acertos), f"{pct:.1f}")
    print(tbl)
    
    # Aggregate by topic and difficulty
    def agg(key):
        m = {}
        for r in results:
            k = r[key]
            m.setdefault(k, {"n": 0, "ok": 0})
            m[k]["n"] += 1
            m[k]["ok"] += int(r["correct"])
        return {k: {"n": v["n"], "ok": v["ok"], "pct": (100.0 * v["ok"] / v["n"])} for k, v in m.items()}
    
    by_topic = agg("topic")
    by_diff = agg("difficulty")
    
    print(Panel.fit(f"[bold]Por tópico:[/] {by_topic}"))
    print(Panel.fit(f"[bold]Por dificuldade:[/] {by_diff}"))
    
    # Save reports if requested
    if report:
        reports_dir = REPO_ROOT / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        ts = time.strftime("%Y%m%d-%H%M%S")
        
        # JSON report
        with open(reports_dir / f"{ts}_quiz_summary.json", "w", encoding="utf-8") as f:
            json.dump({
                "total": total,
                "correct": acertos,
                "pct": pct,
                "by_topic": by_topic,
                "by_difficulty": by_diff,
                "results": results
            }, f, ensure_ascii=False, indent=2)
        
        # Markdown report
        with open(reports_dir / f"{ts}_quiz_summary.md", "w", encoding="utf-8") as f:
            f.write(f"# Relatório de Quiz — {ts}\n\n")
            f.write(f"- Total: {total}\n- Acertos: {acertos}\n- %: {pct:.1f}\n\n")
            f.write("## Por tópico\n\n")
            for k, v in by_topic.items():
                f.write(f"- {k}: {v['ok']}/{v['n']} ({v['pct']:.1f}%)\n")
            f.write("\n## Por dificuldade\n\n")
            for k, v in by_diff.items():
                f.write(f"- {k}: {v['ok']}/{v['n']} ({v['pct']:.1f}%)\n")
            f.write("\n## Itens incorretos\n\n")
            for r in results:
                if not r["correct"]:
                    f.write(f"- {r['id']} [{r['topic']}/{r['difficulty']}] — src: {r['src']}\n")
        
        print(Panel.fit("[bold green]Relatórios salvos em reports/"))
        logger.info(f"Reports saved to {reports_dir}")


if __name__ == "__main__":
    quiz_app()
"""
mega.cli — Interface de linha de comando (CLI) do MEGA.

Comandos principais:
    mega init      — Cria estrutura de directórios e configuração inicial
    mega ingest    — Valida e carrega conteúdo de um módulo
    mega deploy    — Constrói site estático / mostra instruções de deploy
    mega status    — Mostra estado actual do projecto

⚠ AVISO EDUCACIONAL: Este software é destinado exclusivamente a fins
educacionais e de pesquisa. Não deve ser utilizado para diagnóstico
clínico real. Sempre consulte um profissional de saúde qualificado.
"""

from __future__ import annotations

import pathlib
import sys

import typer
from rich import print as rprint
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from mega import __version__
from mega.config import DEFAULT_CONFIG_NAME, MegaConfig, find_config, load_or_default
from mega.deploy import build_site, github_pages_instructions, render_instructions
from mega.ingest import ingest_module

app = typer.Typer(
    name="mega",
    help=(
        "MEGA CLI — Módulo Educacional Gerador Avançado.\n\n"
        "Ferramenta para criação, validação e publicação de conteúdo "
        "educacional de ECG do projecto ECGiga.\n\n"
        "⚠ Conteúdo exclusivamente educacional — não substitui avaliação clínica."
    ),
    no_args_is_help=True,
)

console = Console()

DISCLAIMER = (
    "[yellow bold]⚠ AVISO EDUCACIONAL:[/] Este conteúdo é exclusivamente "
    "educacional e de pesquisa. Não substitui orientação médica profissional."
)

# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _resolve_root() -> pathlib.Path:
    """Resolve o directório raiz do projecto (onde está mega.yaml ou cwd)."""
    cfg_path = find_config()
    if cfg_path is not None:
        return cfg_path.parent
    return pathlib.Path.cwd().resolve()


def _print_banner() -> None:
    """Imprime o banner do MEGA CLI."""
    rprint(
        Panel.fit(
            f"[bold cyan]MEGA CLI[/] v{__version__} — "
            "[bold]M[/]ódulo [bold]E[/]ducacional [bold]G[/]erador [bold]A[/]vançado\n"
            f"{DISCLAIMER}",
            border_style="cyan",
        )
    )


# ------------------------------------------------------------------
# mega init
# ------------------------------------------------------------------

@app.command()
def init(
    directory: str = typer.Argument(
        ".",
        help="Directório onde criar o projecto (padrão: directório actual).",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Sobrescrever configuração existente.",
    ),
) -> None:
    """Cria a estrutura de directórios e configuração inicial do projecto MEGA."""
    _print_banner()
    root = pathlib.Path(directory).resolve()

    config_path = root / DEFAULT_CONFIG_NAME
    if config_path.exists() and not force:
        rprint(
            f"[red]Erro:[/] Configuração já existe em {config_path}.\n"
            "Use --force para sobrescrever."
        )
        raise typer.Exit(code=1)

    # Criar configuração padrão
    config = MegaConfig.default(root)
    config.save(config_path)
    rprint(f"[green]✓[/] Configuração criada: {config_path}")

    # Criar estrutura de directórios
    modules_dir = root / config.diretorio_modulos
    dirs_to_create = [
        modules_dir,
        modules_dir / "01_fundamentos",
        modules_dir / "01_fundamentos" / "aulas",
        modules_dir / "01_fundamentos" / "quizzes",
        modules_dir / "02_ritmo_cardiaco",
        modules_dir / "02_ritmo_cardiaco" / "aulas",
        modules_dir / "02_ritmo_cardiaco" / "quizzes",
    ]

    for d in dirs_to_create:
        d.mkdir(parents=True, exist_ok=True)
        rprint(f"[green]✓[/] Directório criado: {d.relative_to(root)}")

    # Criar ficheiro de exemplo (aula)
    example_lesson = modules_dir / "01_fundamentos" / "aulas" / "01_introducao.md"
    if not example_lesson.exists():
        example_lesson.write_text(
            "# Introdução à Eletrocardiografia\n"
            "\n"
            "> **Aviso Educacional:** Este conteúdo é exclusivamente educacional "
            "e não substitui avaliação clínica profissional.\n"
            "\n"
            "## O que é o ECG?\n"
            "\n"
            "O eletrocardiograma (ECG) é um exame que regista a actividade "
            "eléctrica do coração ao longo do tempo, captada por eléctrodos "
            "colocados na superfície do corpo.\n"
            "\n"
            "## Derivações\n"
            "\n"
            "O ECG padrão utiliza 12 derivações:\n"
            "\n"
            "- **Bipolares (I, II, III)** — Diferença de potencial entre dois membros\n"
            "- **Unipolares aumentadas (aVR, aVL, aVF)** — Potencial de um membro\n"
            "- **Precordiais (V1–V6)** — Eléctrodos no tórax\n"
            "\n"
            "## Objectivos de Aprendizagem\n"
            "\n"
            "- Compreender o princípio básico do ECG\n"
            "- Identificar as 12 derivações padrão\n"
            "- Reconhecer os componentes da onda cardíaca (P, QRS, T)\n",
            encoding="utf-8",
        )
        rprint(f"[green]✓[/] Aula de exemplo criada: {example_lesson.relative_to(root)}")

    # Criar ficheiro de exemplo (quiz)
    example_quiz = modules_dir / "01_fundamentos" / "quizzes" / "01_introducao_quiz.json"
    if not example_quiz.exists():
        import json

        quiz_data = {
            "modulo": "01_fundamentos",
            "titulo": "Quiz — Introdução ao ECG",
            "aviso": (
                "Este quiz é exclusivamente educacional. "
                "Não substitui avaliação clínica."
            ),
            "questions": [
                {
                    "stem": "Quantas derivações possui o ECG padrão?",
                    "topic": "derivacoes",
                    "difficulty": 1,
                    "options": ["6 derivações", "10 derivações", "12 derivações", "15 derivações"],
                    "answer_index": 2,
                    "explanation": (
                        "O ECG padrão utiliza 12 derivações: "
                        "3 bipolares (I, II, III), 3 unipolares aumentadas "
                        "(aVR, aVL, aVF) e 6 precordiais (V1-V6)."
                    ),
                },
                {
                    "stem": "Qual componente do ECG representa a despolarização ventricular?",
                    "topic": "ondas",
                    "difficulty": 1,
                    "options": [
                        "Onda P",
                        "Complexo QRS",
                        "Onda T",
                        "Segmento ST",
                    ],
                    "answer_index": 1,
                    "explanation": (
                        "O complexo QRS representa a despolarização dos ventrículos. "
                        "A onda P representa a despolarização atrial e a onda T "
                        "representa a repolarização ventricular."
                    ),
                },
            ],
        }
        example_quiz.write_text(
            json.dumps(quiz_data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        rprint(f"[green]✓[/] Quiz de exemplo criado: {example_quiz.relative_to(root)}")

    rprint()
    rprint(
        Panel.fit(
            "[bold green]Projecto MEGA inicializado com sucesso![/]\n\n"
            "Próximos passos:\n"
            "  1. Edite [cyan]mega.yaml[/] com as configurações do seu projecto\n"
            "  2. Adicione aulas (.md) e quizzes (.json) em [cyan]content/modules/[/]\n"
            "  3. Execute [cyan]mega ingest <módulo>[/] para validar o conteúdo\n"
            "  4. Execute [cyan]mega deploy --build[/] para gerar o site\n"
            f"\n{DISCLAIMER}",
            title="[bold]Sucesso[/]",
            border_style="green",
        )
    )


# ------------------------------------------------------------------
# mega ingest
# ------------------------------------------------------------------

@app.command()
def ingest(
    module_path: str = typer.Argument(
        ...,
        help="Caminho para o directório do módulo a ingerir.",
    ),
) -> None:
    """Valida e carrega conteúdo de um módulo educacional."""
    _print_banner()

    path = pathlib.Path(module_path).resolve()
    if not path.is_dir():
        rprint(f"[red]Erro:[/] Directório não encontrado: {path}")
        raise typer.Exit(code=1)

    rprint(f"[cyan]Ingerindo módulo:[/] {path}\n")

    report = ingest_module(path)

    # Tabela de aulas
    if report.lessons:
        lesson_table = Table(title="Aulas Encontradas", show_lines=True)
        lesson_table.add_column("Ficheiro", style="cyan")
        lesson_table.add_column("Título", style="bold")
        lesson_table.add_column("Palavras", justify="right")
        lesson_table.add_column("Headings", justify="right")
        lesson_table.add_column("Disclaimer", justify="center")

        for lesson in report.lessons:
            disclaimer_icon = "[green]Sim[/]" if lesson.has_disclaimer else "[red]Não[/]"
            lesson_table.add_row(
                lesson.path.name,
                lesson.titulo,
                str(lesson.num_words),
                str(lesson.num_headings),
                disclaimer_icon,
            )
        console.print(lesson_table)
        rprint()

    # Tabela de quizzes
    if report.quizzes:
        quiz_table = Table(title="Quizzes Encontrados", show_lines=True)
        quiz_table.add_column("Ficheiro", style="cyan")
        quiz_table.add_column("Questões", justify="right")
        quiz_table.add_column("Tópicos")
        quiz_table.add_column("Válido", justify="center")

        for quiz in report.quizzes:
            valid_icon = "[green]Sim[/]" if quiz.valid else "[red]Não[/]"
            quiz_table.add_row(
                quiz.path.name,
                str(quiz.num_questions),
                ", ".join(quiz.topics) if quiz.topics else "—",
                valid_icon,
            )
        console.print(quiz_table)
        rprint()

    # Resumo
    summary_parts = [
        f"[bold]Aulas:[/] {report.total_lessons}",
        f"[bold]Quizzes:[/] {report.total_quizzes}",
        f"[bold]Questões:[/] {report.total_questions}",
        f"[bold]Palavras:[/] {report.total_words:,}",
    ]
    rprint(Panel.fit("\n".join(summary_parts), title="Resumo", border_style="blue"))

    # Avisos
    if report.warnings:
        rprint()
        rprint("[yellow bold]Avisos:[/]")
        for w in report.warnings:
            rprint(f"  [yellow]![/] {w}")
        rprint()

    if report.is_valid:
        rprint("[green bold]Módulo válido e pronto para deploy.[/]")
    else:
        rprint("[red bold]Módulo contém problemas. Corrija os avisos acima.[/]")
        raise typer.Exit(code=1)


# ------------------------------------------------------------------
# mega deploy
# ------------------------------------------------------------------

@app.command()
def deploy(
    build: bool = typer.Option(
        False,
        "--build",
        "-b",
        help="Construir o site estático.",
    ),
    target: str = typer.Option(
        "github-pages",
        "--target",
        "-t",
        help="Destino do deploy: 'github-pages' ou 'render'.",
    ),
) -> None:
    """Constrói o site estático e/ou mostra instruções de deploy."""
    _print_banner()
    root = _resolve_root()

    if build:
        rprint("[cyan]Construindo site estático...[/]\n")
        result = build_site(root)

        if result.warnings:
            rprint("[yellow bold]Avisos durante o build:[/]")
            for w in result.warnings:
                rprint(f"  [yellow]![/] {w}")
            rprint()

        rprint(
            Panel.fit(
                f"[bold]Módulos processados:[/] {result.modules_processed}\n"
                f"[bold]Páginas geradas:[/] {result.pages_generated}\n"
                f"[bold]Directório de saída:[/] {result.output_dir}",
                title="Build Completo" if result.success else "Build com Avisos",
                border_style="green" if result.success else "yellow",
            )
        )
        rprint()

    # Instruções de deploy
    if target.lower() in ("github-pages", "gh-pages", "github"):
        rprint(github_pages_instructions(root))
    elif target.lower() == "render":
        rprint(render_instructions())
    else:
        rprint(f"[red]Erro:[/] Destino desconhecido: '{target}'.")
        rprint("Destinos disponíveis: github-pages, render")
        raise typer.Exit(code=1)


# ------------------------------------------------------------------
# mega status
# ------------------------------------------------------------------

@app.command()
def status() -> None:
    """Mostra o estado actual do projecto MEGA."""
    _print_banner()
    root = _resolve_root()
    config = load_or_default(root)

    # Informações do projecto
    proj_table = Table(title="Informações do Projecto", show_lines=True)
    proj_table.add_column("Campo", style="bold")
    proj_table.add_column("Valor")

    cfg_path = find_config(root)
    proj_table.add_row("Configuração", str(cfg_path) if cfg_path else "[yellow]Não encontrada[/]")
    proj_table.add_row("Nome", config.projeto_nome)
    proj_table.add_row("Versão", config.projeto_versao)
    proj_table.add_row("Idioma", config.projeto_idioma)
    proj_table.add_row("Destino de Deploy", config.destino_publicacao)
    proj_table.add_row("Dir. Módulos", config.diretorio_modulos)
    proj_table.add_row("Dir. Saída", config.diretorio_saida)
    console.print(proj_table)
    rprint()

    # Módulos encontrados
    modules_dir = root / config.diretorio_modulos
    if not modules_dir.is_dir():
        rprint(
            "[yellow]Directório de módulos não encontrado.[/] "
            "Execute [cyan]mega init[/] para criar a estrutura."
        )
        return

    module_dirs = sorted([d for d in modules_dir.iterdir() if d.is_dir()])

    if not module_dirs:
        rprint(
            "[yellow]Nenhum módulo encontrado.[/] "
            f"Crie directórios em [cyan]{modules_dir.relative_to(root)}[/]."
        )
        return

    mod_table = Table(title="Módulos de Conteúdo", show_lines=True)
    mod_table.add_column("Módulo", style="cyan")
    mod_table.add_column("Aulas", justify="right")
    mod_table.add_column("Quizzes", justify="right")
    mod_table.add_column("Questões", justify="right")
    mod_table.add_column("Palavras", justify="right")
    mod_table.add_column("Estado", justify="center")

    total_lessons = 0
    total_quizzes = 0
    total_questions = 0
    total_words = 0

    for mdir in module_dirs:
        report = ingest_module(mdir)
        total_lessons += report.total_lessons
        total_quizzes += report.total_quizzes
        total_questions += report.total_questions
        total_words += report.total_words

        status_icon = "[green]OK[/]" if report.is_valid else "[red]Problemas[/]"
        mod_table.add_row(
            mdir.name,
            str(report.total_lessons),
            str(report.total_quizzes),
            str(report.total_questions),
            f"{report.total_words:,}",
            status_icon,
        )

    console.print(mod_table)
    rprint()

    # Totais
    rprint(
        Panel.fit(
            f"[bold]Total de módulos:[/] {len(module_dirs)}\n"
            f"[bold]Total de aulas:[/] {total_lessons}\n"
            f"[bold]Total de quizzes:[/] {total_quizzes}\n"
            f"[bold]Total de questões:[/] {total_questions}\n"
            f"[bold]Total de palavras:[/] {total_words:,}",
            title="Resumo Geral",
            border_style="blue",
        )
    )

    # Verificar site gerado
    site_dir = root / config.diretorio_saida
    if site_dir.is_dir():
        html_files = list(site_dir.glob("*.html"))
        rprint(f"\n[green]Site gerado:[/] {site_dir} ({len(html_files)} página(s))")
    else:
        rprint(
            "\n[yellow]Site ainda não gerado.[/] "
            "Execute [cyan]mega deploy --build[/] para gerar."
        )


# ------------------------------------------------------------------
# Entry-point
# ------------------------------------------------------------------

if __name__ == "__main__":
    app()

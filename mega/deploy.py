"""
mega.deploy — Utilidades de publicação (deploy) do conteúdo educacional.

Suporta geração de site estático para GitHub Pages e instruções para Render.

⚠ AVISO EDUCACIONAL: Todo o conteúdo gerado é destinado exclusivamente
a fins educacionais. Não substitui orientação médica profissional.
"""

from __future__ import annotations

import datetime
import json
import pathlib
import shutil
from dataclasses import dataclass, field
from typing import Any

from mega.config import MegaConfig, load_or_default
from mega.ingest import ingest_module, ModuleReport


# ------------------------------------------------------------------
# Resultado do build
# ------------------------------------------------------------------

@dataclass
class BuildResult:
    """Resultado do processo de construção do site."""

    output_dir: pathlib.Path
    pages_generated: int = 0
    modules_processed: int = 0
    warnings: list[str] = field(default_factory=list)
    success: bool = True


# ------------------------------------------------------------------
# Geração HTML simples
# ------------------------------------------------------------------

_HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 900px;
            margin: 0 auto;
            padding: 2rem;
            line-height: 1.6;
            color: #333;
            background: #fafafa;
        }}
        h1 {{ color: #1a5276; border-bottom: 3px solid #2ecc71; padding-bottom: 0.5rem; }}
        h2 {{ color: #2c3e50; }}
        .disclaimer {{
            background: #ffeaa7;
            border-left: 4px solid #fdcb6e;
            padding: 1rem;
            margin: 1rem 0;
            font-size: 0.9rem;
        }}
        .module-card {{
            background: white;
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 1.5rem;
            margin: 1rem 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}
        .stats {{ color: #666; font-size: 0.9rem; }}
        nav {{ background: #1a5276; padding: 1rem 2rem; margin: -2rem -2rem 2rem; }}
        nav a {{ color: white; text-decoration: none; margin-right: 1.5rem; }}
        footer {{
            margin-top: 3rem;
            padding-top: 1rem;
            border-top: 1px solid #ddd;
            font-size: 0.85rem;
            color: #888;
        }}
    </style>
</head>
<body>
    <nav>
        <a href="index.html"><strong>ECGiga Curso</strong></a>
        <a href="index.html">Início</a>
    </nav>
    <div class="disclaimer">
        <strong>Aviso Educacional:</strong> Este conteúdo é exclusivamente educacional
        e de pesquisa. Não deve ser utilizado para diagnóstico clínico.
        Consulte sempre um profissional de saúde qualificado.
    </div>
    {content}
    <footer>
        <p>Gerado por MEGA CLI — ECGiga Megaprojeto &copy; {year}</p>
        <p>Conteúdo exclusivamente educacional. Não substitui avaliação médica.</p>
    </footer>
</body>
</html>
"""


def _render_html(title: str, content: str) -> str:
    """Renderiza conteúdo dentro do template HTML base."""
    return _HTML_TEMPLATE.format(
        title=title,
        content=content,
        year=datetime.datetime.now().year,
    )


def _md_to_simple_html(text: str) -> str:
    """
    Conversor Markdown extremamente simplificado (sem dependências externas).
    Converte headings, parágrafos e listas básicas.
    """
    import re

    lines = text.strip().splitlines()
    html_parts: list[str] = []
    in_list = False

    for line in lines:
        stripped = line.strip()

        # Headings
        heading_match = re.match(r"^(#{1,6})\s+(.+)$", stripped)
        if heading_match:
            if in_list:
                html_parts.append("</ul>")
                in_list = False
            level = len(heading_match.group(1))
            html_parts.append(f"<h{level}>{heading_match.group(2)}</h{level}>")
            continue

        # Listas
        if stripped.startswith(("- ", "* ", "+ ")):
            if not in_list:
                html_parts.append("<ul>")
                in_list = True
            html_parts.append(f"  <li>{stripped[2:]}</li>")
            continue

        # Linha em branco
        if not stripped:
            if in_list:
                html_parts.append("</ul>")
                in_list = False
            continue

        # Parágrafo
        if in_list:
            html_parts.append("</ul>")
            in_list = False
        # Bold
        stripped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", stripped)
        # Italic
        stripped = re.sub(r"\*(.+?)\*", r"<em>\1</em>", stripped)
        html_parts.append(f"<p>{stripped}</p>")

    if in_list:
        html_parts.append("</ul>")

    return "\n".join(html_parts)


# ------------------------------------------------------------------
# Build do site
# ------------------------------------------------------------------

def build_site(root: pathlib.Path | None = None, config: MegaConfig | None = None) -> BuildResult:
    """
    Constrói o site estático a partir dos módulos de conteúdo.

    Gera ficheiros HTML no directório de saída definido na configuração.
    """
    root = pathlib.Path(root or pathlib.Path.cwd()).resolve()
    if config is None:
        config = load_or_default(root)

    output_dir = root / config.diretorio_saida
    modules_dir = root / config.diretorio_modulos

    result = BuildResult(output_dir=output_dir)

    # Limpar e criar directório de saída
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Recolher módulos
    module_dirs: list[pathlib.Path] = []
    if modules_dir.is_dir():
        module_dirs = sorted(
            [d for d in modules_dir.iterdir() if d.is_dir()],
        )

    if not module_dirs:
        result.warnings.append(
            f"Nenhum módulo encontrado em {modules_dir}. "
            "Use 'mega init' para criar a estrutura de directórios."
        )

    # Processar cada módulo
    module_summaries: list[dict[str, Any]] = []
    for mdir in module_dirs:
        report = ingest_module(mdir)
        result.modules_processed += 1
        result.warnings.extend(report.warnings)

        # Gerar páginas para as aulas
        for lesson in report.lessons:
            md_text = lesson.path.read_text(encoding="utf-8")
            lesson_html = _md_to_simple_html(md_text)
            page_html = _render_html(lesson.titulo, lesson_html)
            page_name = f"{mdir.name}_{lesson.path.stem}.html"
            (output_dir / page_name).write_text(page_html, encoding="utf-8")
            result.pages_generated += 1

        module_summaries.append({
            "nome": mdir.name,
            "aulas": report.total_lessons,
            "quizzes": report.total_quizzes,
            "questoes": report.total_questions,
            "palavras": report.total_words,
        })

    # Página índice
    index_content = f"<h1>{config.projeto_nome}</h1>\n"
    index_content += f"<p>{config.projeto_descricao}</p>\n"

    if module_summaries:
        index_content += "<h2>Módulos Disponíveis</h2>\n"
        for ms in module_summaries:
            index_content += f"""
            <div class="module-card">
                <h3>{ms['nome']}</h3>
                <p class="stats">
                    {ms['aulas']} aula(s) | {ms['quizzes']} quiz(zes) |
                    {ms['questoes']} questão(ões) | {ms['palavras']} palavras
                </p>
            </div>
            """
    else:
        index_content += (
            "<p><em>Nenhum módulo disponível ainda. "
            "Crie módulos em content/modules/ e execute 'mega deploy'.</em></p>"
        )

    index_html = _render_html(config.projeto_nome, index_content)
    (output_dir / "index.html").write_text(index_html, encoding="utf-8")
    result.pages_generated += 1

    return result


# ------------------------------------------------------------------
# Instruções de deploy
# ------------------------------------------------------------------

def github_pages_instructions(root: pathlib.Path | None = None) -> str:
    """Devolve instruções formatadas para publicação via GitHub Pages."""
    root = root or pathlib.Path.cwd()
    config = load_or_default(root)
    output_dir = config.diretorio_saida

    return f"""\
=== Instruções para Deploy no GitHub Pages ===

1. Execute o build do site:
   mega deploy --build

2. O site será gerado em: {output_dir}/

3. Configure o GitHub Pages:
   a) Vá a Settings > Pages no seu repositório
   b) Seleccione "Deploy from a branch"
   c) Escolha a branch principal e a pasta /{output_dir}
   — OU —
   d) Use GitHub Actions com o workflow abaixo

4. Workflow sugerido (.github/workflows/deploy.yml):

   name: Deploy MEGA Site
   on:
     push:
       branches: [main]
   jobs:
     deploy:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v4
         - uses: actions/setup-python@v5
           with:
             python-version: '3.11'
         - run: pip install -e .
         - run: mega deploy --build
         - uses: actions/upload-pages-artifact@v3
           with:
             path: {output_dir}
         - uses: actions/deploy-pages@v4

AVISO: Todo o conteúdo publicado é exclusivamente educacional.
"""


def render_instructions() -> str:
    """Devolve instruções formatadas para deploy no Render."""
    return """\
=== Instruções para Deploy no Render ===

1. Crie uma conta em https://render.com (se necessário).

2. Crie um novo "Static Site":
   a) Conecte o seu repositório GitHub
   b) Configure:
      - Build command: pip install -e . && mega deploy --build
      - Publish directory: _site

3. O render.yaml já está configurado no projecto.
   O Render detectará automaticamente as configurações.

4. Para deploy automático, ative "Auto-Deploy" nas configurações.

AVISO: Todo o conteúdo publicado é exclusivamente educacional.
Não substitui avaliação médica profissional.
"""

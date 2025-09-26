
from __future__ import annotations
import json, base64, mimetypes
from pathlib import Path
import typer

app = typer.Typer(help="Renderização de quiz (HTML) — p15")

def _embed_img(path: Path) -> str:
    if not path.exists():
        return ""
    data = path.read_bytes()
    mime,_ = mimetypes.guess_type(path.name)
    b64 = base64.b64encode(data).decode("ascii")
    return f"data:{mime or 'image/png'};base64,{b64}"

@app.command("render-html")
def render_html(quiz_json: str = typer.Argument(..., help="Quiz .json"),
                out_html: str = typer.Argument("quiz_rendered.html", help="Saída HTML única"),
                base_dir: str = typer.Option(".", "--base", help="Base p/ resolver paths de imagens")):
    q = json.loads(Path(quiz_json).read_text(encoding="utf-8"))
    base = Path(base_dir)
    # inlining de imagens
    for qu in q.get("questions", []):
        img = qu.get("image")
        if img:
            p = base / img
            qu["image"] = _embed_img(p)
    # HTML simples com script do quiz_html incorporado
    html = Path("web_app/quiz_html/quiz.html").read_text(encoding="utf-8")
    # injeta dados direto (auto-render sem input file)
    inject = f"<script>const __AUTO_DATA__ = {json.dumps(q, ensure_ascii=False)};(()=>{{" \
             f"const f=()=>{{const d=__AUTO_DATA__; document.querySelector('#root').innerHTML='';" \
             f"document.querySelector('#file').style.display='none'; renderQuiz(d);}};" \
             f"window.addEventListener('load', f);}})();</script>"
    html = html.replace("</script>", inject + "\\n</script>", 1)
    Path(out_html).write_text(html, encoding="utf-8")
    print(f"Quiz HTML gerado em {out_html}")

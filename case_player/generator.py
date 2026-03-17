"""
case_player.generator
=====================
Generate interactive ECG cases from structured reports.

Each case bundles an ECG image, clinical context, annotation regions,
and multiple-choice / free-text questions so a student can practise
reading ECGs in a self-contained player.
"""

from __future__ import annotations

import hashlib
import html as _html
import json
import os
from typing import Any


# ------------------------------------------------------------------
#  Defaults
# ------------------------------------------------------------------

_DIFFICULTY_LEVELS = ("easy", "medium", "hard")

_DEFAULT_QUESTIONS: dict[str, list[dict]] = {
    "easy": [
        {
            "id": "q1",
            "type": "multiple_choice",
            "text": "Qual e o ritmo predominante neste ECG?",
            "options": [
                "Ritmo sinusal",
                "Fibrilacao atrial",
                "Flutter atrial",
                "Taquicardia ventricular",
            ],
            "correct": 0,
        },
    ],
    "medium": [
        {
            "id": "q1",
            "type": "multiple_choice",
            "text": "Qual e o ritmo predominante neste ECG?",
            "options": [
                "Ritmo sinusal",
                "Fibrilacao atrial",
                "Flutter atrial",
                "Taquicardia ventricular",
            ],
            "correct": 0,
        },
        {
            "id": "q2",
            "type": "annotation",
            "text": "Marque a onda P em qualquer derivacao.",
        },
    ],
    "hard": [
        {
            "id": "q1",
            "type": "multiple_choice",
            "text": "Qual e o ritmo predominante neste ECG?",
            "options": [
                "Ritmo sinusal",
                "Fibrilacao atrial",
                "Flutter atrial",
                "Taquicardia ventricular",
            ],
            "correct": 0,
        },
        {
            "id": "q2",
            "type": "annotation",
            "text": "Marque a onda P em qualquer derivacao.",
        },
        {
            "id": "q3",
            "type": "free_text",
            "text": "Descreva o eixo eletrico e justifique.",
        },
    ],
}


# ------------------------------------------------------------------
#  Helpers
# ------------------------------------------------------------------

def _make_id(report: dict) -> str:
    """Deterministic short id derived from the report content."""
    blob = json.dumps(report, sort_keys=True, ensure_ascii=False).encode()
    return hashlib.sha256(blob).hexdigest()[:12]


def _extract_annotations(report: dict) -> list[dict]:
    """Pull annotation hints from a report (if present)."""
    annotations: list[dict] = []
    if "annotations" in report:
        return report["annotations"]
    # Build lightweight annotations from report fields when available
    for key in ("p_wave", "qrs_complex", "t_wave", "st_segment"):
        if key in report:
            annotations.append({
                "label": key,
                "description": str(report[key]),
            })
    return annotations


# ------------------------------------------------------------------
#  Public API
# ------------------------------------------------------------------

def generate_case(
    report: dict,
    image_path: str | None = None,
    difficulty: str = "medium",
) -> dict:
    """Create an interactive case dict from an ECG *report*.

    Parameters
    ----------
    report:
        Structured ECG report dictionary.  Expected keys include
        ``"diagnosis"`` or ``"conclusion"`` and optional wave-level
        entries (``p_wave``, ``qrs_complex``, etc.).
    image_path:
        Optional path/URL to the ECG image.
    difficulty:
        One of ``"easy"``, ``"medium"``, ``"hard"``.

    Returns
    -------
    dict
        A case dictionary ready for the case player.
    """
    if difficulty not in _DIFFICULTY_LEVELS:
        raise ValueError(
            f"difficulty must be one of {_DIFFICULTY_LEVELS!r}, got {difficulty!r}"
        )

    case_id = _make_id(report)

    # Title — use diagnosis / conclusion / fallback
    title = (
        report.get("diagnosis")
        or report.get("conclusion")
        or report.get("title")
        or f"Caso ECG {case_id[:6]}"
    )

    description = report.get("description", report.get("clinical_history", ""))

    annotations = _extract_annotations(report)

    # Build answer key from report
    answer_key: dict[str, Any] = {}
    if annotations:
        answer_key["annotations"] = annotations
    # Attach any known correct answers from the report
    if "rhythm" in report:
        answer_key["rhythm"] = report["rhythm"]
    if "axis" in report:
        answer_key["axis"] = report["axis"]

    # Pick question set
    questions = list(report.get("questions", _DEFAULT_QUESTIONS.get(difficulty, [])))

    return {
        "id": case_id,
        "title": title,
        "description": description,
        "image_url": image_path or "",
        "report": report,
        "annotations": annotations,
        "questions": questions,
        "answer_key": answer_key,
        "difficulty": difficulty,
    }


def generate_case_index(cases: list[dict], out_path: str) -> str:
    """Write an ``index.json`` listing all cases.

    Parameters
    ----------
    cases:
        List of case dicts (as returned by :func:`generate_case`).
    out_path:
        Directory or file path.  If *out_path* is a directory the file
        is written as ``<out_path>/index.json``; otherwise it is used
        as-is.

    Returns
    -------
    str
        Absolute path of the written file.
    """
    if os.path.isdir(out_path):
        filepath = os.path.join(out_path, "index.json")
    else:
        filepath = out_path
        parent = os.path.dirname(filepath)
        if parent:
            os.makedirs(parent, exist_ok=True)

    index_entries = []
    for case in cases:
        index_entries.append({
            "id": case["id"],
            "title": case["title"],
            "difficulty": case["difficulty"],
            "image_url": case.get("image_url", ""),
            "num_questions": len(case.get("questions", [])),
        })

    payload = {
        "version": 1,
        "count": len(index_entries),
        "cases": index_entries,
    }

    with open(filepath, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)

    return os.path.abspath(filepath)


def case_to_html(case: dict) -> str:
    """Render a single *case* as a self-contained HTML page.

    The output can be opened directly in a browser and works offline
    (no server required).
    """
    title = _html.escape(case.get("title", "ECG Case"))
    description = _html.escape(case.get("description", ""))
    difficulty = _html.escape(case.get("difficulty", "medium"))
    image_url = _html.escape(case.get("image_url", ""))

    questions_json = json.dumps(case.get("questions", []), ensure_ascii=False)
    answer_key_json = json.dumps(case.get("answer_key", {}), ensure_ascii=False)
    annotations_json = json.dumps(case.get("annotations", []), ensure_ascii=False)

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} — ECGiga</title>
<style>
  body {{ font-family: system-ui, sans-serif; margin: 0; padding: 16px;
         background: #f8f9fa; color: #202124; }}
  h1 {{ color: #1a73e8; font-size: 1.4rem; }}
  .badge {{ display: inline-block; padding: 2px 10px; border-radius: 12px;
            font-size: 0.8rem; font-weight: 600; background: #d2e3fc;
            color: #1a73e8; margin-left: 8px; }}
  .desc {{ color: #5f6368; margin-bottom: 16px; }}
  .ecg-img {{ max-width: 100%; border: 1px solid #dadce0; border-radius: 8px; }}
  .question {{ background: #fff; border: 1px solid #dadce0; border-radius: 8px;
               padding: 16px; margin-bottom: 12px; }}
  .question h3 {{ margin-top: 0; font-size: 1rem; }}
  .options label {{ display: block; padding: 6px 0; cursor: pointer; }}
  .btn {{ min-height: 44px; padding: 8px 20px; background: #1a73e8;
          color: #fff; border: none; border-radius: 4px; cursor: pointer;
          font-size: 0.95rem; }}
  .btn:hover {{ background: #1558b0; }}
  #result {{ margin-top: 16px; padding: 16px; border-radius: 8px;
             display: none; }}
  #result.correct {{ background: #e6f4ea; color: #137333; display: block; }}
  #result.partial {{ background: #fef7e0; color: #e37400; display: block; }}
  @media (prefers-color-scheme: dark) {{
    body {{ background: #121212; color: #e8eaed; }}
    .question {{ background: #1e1e1e; border-color: #3c4043; }}
    h1 {{ color: #8ab4f8; }}
    .badge {{ background: #1e3a5f; color: #8ab4f8; }}
    .desc {{ color: #9aa0a6; }}
  }}
</style>
</head>
<body>
  <h1>{title}<span class="badge">{difficulty}</span></h1>
  <p class="desc">{description}</p>
  {"<img class='ecg-img' src='" + image_url + "' alt='ECG'>" if image_url else ""}
  <div id="questions"></div>
  <button class="btn" onclick="checkAnswers()">Verificar Respostas</button>
  <div id="result"></div>
  <script>
    var questions = {questions_json};
    var answerKey = {answer_key_json};
    var annotations = {annotations_json};
    var container = document.getElementById('questions');
    questions.forEach(function(q, i) {{
      var div = document.createElement('div');
      div.className = 'question';
      var h = '<h3>' + q.text + '</h3>';
      if (q.type === 'multiple_choice' && q.options) {{
        h += '<div class="options">';
        q.options.forEach(function(opt, j) {{
          h += '<label><input type="radio" name="q' + i + '" value="' + j + '"> ' + opt + '</label>';
        }});
        h += '</div>';
      }} else if (q.type === 'free_text') {{
        h += '<textarea rows="3" style="width:100%" id="ft' + i + '"></textarea>';
      }} else {{
        h += '<p><em>Use o player de anotacoes para responder.</em></p>';
      }}
      div.innerHTML = h;
      container.appendChild(div);
    }});
    function checkAnswers() {{
      var correct = 0, total = 0;
      questions.forEach(function(q, i) {{
        if (q.type === 'multiple_choice') {{
          total++;
          var sel = document.querySelector('input[name="q' + i + '"]:checked');
          if (sel && parseInt(sel.value) === q.correct) correct++;
        }}
      }});
      var res = document.getElementById('result');
      if (total === 0) {{
        res.className = 'partial';
        res.style.display = 'block';
        res.textContent = 'Nenhuma questao de multipla escolha para corrigir.';
      }} else if (correct === total) {{
        res.className = 'correct';
        res.textContent = 'Parabens! Voce acertou ' + correct + '/' + total + '.';
      }} else {{
        res.className = 'partial';
        res.style.display = 'block';
        res.textContent = 'Voce acertou ' + correct + '/' + total + '. Revise e tente novamente.';
      }}
    }}
  </script>
</body>
</html>"""

"""
mega.ingest — Ingestão e validação de conteúdo educacional.

Lê ficheiros Markdown (aulas) e JSON (quizzes) de um directório de módulo,
valida a estrutura mínima e devolve um resumo do conteúdo encontrado.

⚠ AVISO EDUCACIONAL: O conteúdo ingerido é exclusivamente educacional.
Não deve ser interpretado como orientação clínica.
"""

from __future__ import annotations

import json
import pathlib
import re
from dataclasses import dataclass, field
from typing import Any


# ------------------------------------------------------------------
# Resultado da ingestão
# ------------------------------------------------------------------

@dataclass
class LessonInfo:
    """Metadados de uma aula Markdown."""

    path: pathlib.Path
    titulo: str
    num_headings: int
    num_paragraphs: int
    num_words: int
    has_disclaimer: bool


@dataclass
class QuizInfo:
    """Metadados de um ficheiro de quiz JSON."""

    path: pathlib.Path
    num_questions: int
    topics: list[str]
    valid: bool
    errors: list[str] = field(default_factory=list)


@dataclass
class ModuleReport:
    """Relatório completo da ingestão de um módulo."""

    module_path: pathlib.Path
    lessons: list[LessonInfo] = field(default_factory=list)
    quizzes: list[QuizInfo] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def total_lessons(self) -> int:
        return len(self.lessons)

    @property
    def total_quizzes(self) -> int:
        return len(self.quizzes)

    @property
    def total_questions(self) -> int:
        return sum(q.num_questions for q in self.quizzes)

    @property
    def total_words(self) -> int:
        return sum(l.num_words for l in self.lessons)

    @property
    def is_valid(self) -> bool:
        return len(self.warnings) == 0 and all(q.valid for q in self.quizzes)


# ------------------------------------------------------------------
# Parsing de Markdown
# ------------------------------------------------------------------

_HEADING_RE = re.compile(r"^#{1,6}\s+", re.MULTILINE)
_DISCLAIMER_KEYWORDS = [
    "educacional", "educativo", "não substitui", "aviso",
    "fins didáticos", "não clínico", "consulte um profissional",
]


def _parse_lesson(path: pathlib.Path) -> LessonInfo:
    """Analisa um ficheiro Markdown e extrai metadados."""
    text = path.read_text(encoding="utf-8")
    lines = text.strip().splitlines()

    # Título: primeiro heading de nível 1, ou nome do ficheiro
    titulo = path.stem.replace("_", " ").replace("-", " ").title()
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("# ") and not stripped.startswith("## "):
            titulo = stripped.lstrip("# ").strip()
            break

    headings = len(_HEADING_RE.findall(text))
    paragraphs = len([l for l in text.split("\n\n") if l.strip()])
    words = len(text.split())
    text_lower = text.lower()
    has_disclaimer = any(kw in text_lower for kw in _DISCLAIMER_KEYWORDS)

    return LessonInfo(
        path=path,
        titulo=titulo,
        num_headings=headings,
        num_paragraphs=paragraphs,
        num_words=words,
        has_disclaimer=has_disclaimer,
    )


# ------------------------------------------------------------------
# Parsing de Quiz JSON
# ------------------------------------------------------------------

REQUIRED_QUESTION_KEYS = {"stem", "options", "answer_index"}


def _validate_quiz(data: Any) -> tuple[bool, list[str]]:
    """Valida a estrutura de um quiz JSON. Retorna (valid, errors)."""
    errors: list[str] = []

    if not isinstance(data, dict):
        return False, ["Quiz deve ser um objeto JSON (dict)."]

    questions = data.get("questions", [])
    if not isinstance(questions, list):
        return False, ["Campo 'questions' deve ser uma lista."]

    if len(questions) == 0:
        errors.append("Quiz não contém nenhuma questão.")

    for i, q in enumerate(questions):
        if not isinstance(q, dict):
            errors.append(f"Questão {i + 1}: deve ser um objeto.")
            continue
        missing = REQUIRED_QUESTION_KEYS - set(q.keys())
        if missing:
            errors.append(f"Questão {i + 1}: campos obrigatórios em falta: {missing}")
        if isinstance(q.get("options"), list):
            if len(q["options"]) < 2:
                errors.append(f"Questão {i + 1}: deve ter pelo menos 2 opções.")
            ai = q.get("answer_index")
            if isinstance(ai, int) and (ai < 0 or ai >= len(q["options"])):
                errors.append(f"Questão {i + 1}: answer_index fora do intervalo.")

    return len(errors) == 0, errors


def _parse_quiz(path: pathlib.Path) -> QuizInfo:
    """Analisa um ficheiro de quiz JSON e extrai metadados."""
    errors: list[str] = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return QuizInfo(
            path=path,
            num_questions=0,
            topics=[],
            valid=False,
            errors=[f"JSON inválido: {exc}"],
        )

    valid, validation_errors = _validate_quiz(data)
    errors.extend(validation_errors)

    questions = data.get("questions", []) if isinstance(data, dict) else []
    topics_set: set[str] = set()
    for q in questions:
        if isinstance(q, dict) and "topic" in q:
            topics_set.add(q["topic"])

    return QuizInfo(
        path=path,
        num_questions=len(questions) if isinstance(questions, list) else 0,
        topics=sorted(topics_set),
        valid=valid,
        errors=errors,
    )


# ------------------------------------------------------------------
# Ingestão de módulo
# ------------------------------------------------------------------

def ingest_module(
    module_path: pathlib.Path,
    lesson_exts: list[str] | None = None,
    quiz_exts: list[str] | None = None,
) -> ModuleReport:
    """
    Realiza a ingestão completa de um directório de módulo.

    Procura recursivamente por ficheiros de aula (.md) e quiz (.json),
    valida cada um e devolve um *ModuleReport* com o resumo.
    """
    module_path = pathlib.Path(module_path).resolve()
    lesson_exts = lesson_exts or [".md"]
    quiz_exts = quiz_exts or [".json"]
    report = ModuleReport(module_path=module_path)

    if not module_path.is_dir():
        report.warnings.append(f"Directório não encontrado: {module_path}")
        return report

    # Procurar ficheiros
    all_files = sorted(module_path.rglob("*"))

    lesson_files = [f for f in all_files if f.is_file() and f.suffix.lower() in lesson_exts]
    quiz_files = [f for f in all_files if f.is_file() and f.suffix.lower() in quiz_exts]

    if not lesson_files and not quiz_files:
        report.warnings.append(
            f"Nenhum conteúdo encontrado em {module_path}. "
            "Esperados ficheiros .md (aulas) e/ou .json (quizzes)."
        )
        return report

    # Processar aulas
    for lf in lesson_files:
        try:
            info = _parse_lesson(lf)
            report.lessons.append(info)
            if not info.has_disclaimer:
                report.warnings.append(
                    f"Aula '{info.titulo}' ({lf.name}): sem aviso educacional. "
                    "Recomenda-se incluir disclaimer em todo conteúdo."
                )
        except Exception as exc:
            report.warnings.append(f"Erro ao processar aula {lf.name}: {exc}")

    # Processar quizzes
    for qf in quiz_files:
        try:
            info = _parse_quiz(qf)
            report.quizzes.append(info)
            if not info.valid:
                for err in info.errors:
                    report.warnings.append(f"Quiz {qf.name}: {err}")
        except Exception as exc:
            report.warnings.append(f"Erro ao processar quiz {qf.name}: {exc}")

    return report

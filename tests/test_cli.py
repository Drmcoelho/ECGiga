"""Tests for interactive CLI helpers."""

import pytest
import typer

from cli_app.ecgcourse.cli import ask_item, analyze_values


def test_ask_item_reprompts_on_blank(monkeypatch):
    answers = iter(["", "A"])
    item = {
        "topic": "ECG",
        "difficulty": "easy",
        "stem": "Qual alternativa?",
        "options": ["A", "B"],
        "answer_index": 0,
        "explanation": "Porque sim.",
    }
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    ok, idx = ask_item(item)
    assert ok is True
    assert idx == 0


def test_analyze_values_rejects_zero_rr():
    with pytest.raises(typer.Exit) as exc:
        analyze_values(path_or_none=None, rr=0, qt=380)
    assert exc.value.exit_code == 2


def test_analyze_values_rejects_zero_fc():
    with pytest.raises(typer.Exit) as exc:
        analyze_values(path_or_none=None, rr=None, fc=0, qt=380)
    assert exc.value.exit_code == 2

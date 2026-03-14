"""Tests for reporting.export and reporting.validate_light modules."""

import json
import pathlib

from reporting.export import to_md, to_html, export
from reporting.validate_light import validate_light


def test_to_md(sample_report):
    md = to_md(sample_report)
    assert isinstance(md, str)
    assert "# Laudo ECG" in md
    assert "Intervalos" in md


def test_to_html(sample_report):
    md = to_md(sample_report)
    html = to_html(md)
    assert isinstance(html, str)
    assert "<!doctype html>" in html


def test_export_files(tmp_path, sample_report):
    # Write report to temp JSON
    report_path = tmp_path / "report.json"
    report_path.write_text(json.dumps(sample_report), encoding="utf-8")
    md_path = str(tmp_path / "report.md")
    html_path = str(tmp_path / "report.html")
    export(str(report_path), out_md=md_path, out_html=html_path)
    assert pathlib.Path(md_path).exists()
    assert pathlib.Path(html_path).exists()
    assert len(pathlib.Path(md_path).read_text()) > 0
    assert len(pathlib.Path(html_path).read_text()) > 0


def test_validate_light_valid(sample_report):
    errs = validate_light(sample_report)
    assert errs == []


def test_validate_light_missing_meta():
    rep = {"version": "0.5.0"}
    errs = validate_light(rep)
    assert any("meta" in e for e in errs)


def test_validate_light_missing_version():
    rep = {"meta": {}}
    errs = validate_light(rep)
    assert any("version" in e for e in errs)


def test_validate_light_bad_axis():
    rep = {
        "meta": {},
        "version": "0.5.0",
        "axis": {"angle_deg": "not_a_number"},
    }
    errs = validate_light(rep)
    assert any("angle_deg" in e for e in errs)

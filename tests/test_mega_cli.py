"""Tests para o MEGA CLI — comandos init, ingest, deploy e status."""

from __future__ import annotations

import json
import pathlib

import pytest
import yaml
from typer.testing import CliRunner

from mega.cli import app
from mega.config import DEFAULT_CONFIG_NAME, MegaConfig, find_config, load_or_default
from mega.ingest import (
    ModuleReport,
    _parse_lesson,
    _parse_quiz,
    _validate_quiz,
    ingest_module,
)
from mega.deploy import BuildResult, build_site

runner = CliRunner()


# =====================================================================
# mega.config tests
# =====================================================================


class TestMegaConfig:
    """Testes para o módulo de configuração."""

    def test_default_config(self):
        cfg = MegaConfig.default()
        assert cfg.projeto_nome == "Curso ECG — Megaprojeto"
        assert cfg.projeto_idioma == "pt-BR"
        assert ".md" in cfg.formatos_aula
        assert ".json" in cfg.formatos_quiz

    def test_save_and_load(self, tmp_path):
        cfg = MegaConfig.default(tmp_path)
        saved_path = cfg.save()
        assert saved_path.exists()

        loaded = MegaConfig.load(saved_path)
        assert loaded.projeto_nome == cfg.projeto_nome
        assert loaded.projeto_versao == cfg.projeto_versao
        assert loaded.diretorio_modulos == cfg.diretorio_modulos

    def test_to_dict_roundtrip(self):
        cfg = MegaConfig.default()
        d = cfg.to_dict()
        restored = MegaConfig.from_dict(d)
        assert restored.projeto_nome == cfg.projeto_nome
        assert restored.destino_publicacao == cfg.destino_publicacao

    def test_load_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            MegaConfig.load(tmp_path / "inexistente.yaml")

    def test_find_config_none_when_absent(self, tmp_path):
        result = find_config(tmp_path)
        assert result is None

    def test_find_config_when_present(self, tmp_path):
        cfg_file = tmp_path / DEFAULT_CONFIG_NAME
        cfg_file.write_text("projeto:\n  nome: Teste\n", encoding="utf-8")
        result = find_config(tmp_path)
        assert result is not None
        assert result.name == DEFAULT_CONFIG_NAME

    def test_load_or_default_without_file(self, tmp_path):
        cfg = load_or_default(tmp_path)
        assert cfg.projeto_nome == "Curso ECG — Megaprojeto"

    def test_from_dict_with_partial_data(self):
        data = {"projeto": {"nome": "Meu Curso"}}
        cfg = MegaConfig.from_dict(data)
        assert cfg.projeto_nome == "Meu Curso"
        assert cfg.projeto_idioma == "pt-BR"  # default


# =====================================================================
# mega.ingest tests
# =====================================================================


class TestIngestLesson:
    """Testes para parsing de aulas Markdown."""

    def test_parse_simple_lesson(self, tmp_path):
        md_file = tmp_path / "aula.md"
        md_file.write_text(
            "# Minha Aula\n\n"
            "Conteúdo sobre ECG.\n\n"
            "## Secção 1\n\n"
            "Texto da secção.\n",
            encoding="utf-8",
        )
        info = _parse_lesson(md_file)
        assert info.titulo == "Minha Aula"
        assert info.num_headings == 2
        assert info.num_words > 0
        assert info.has_disclaimer is False

    def test_parse_lesson_with_disclaimer(self, tmp_path):
        md_file = tmp_path / "aula_aviso.md"
        md_file.write_text(
            "# Aula com Aviso\n\n"
            "**Aviso educacional:** conteúdo exclusivamente educacional.\n\n"
            "## Conteúdo\n\nTexto.\n",
            encoding="utf-8",
        )
        info = _parse_lesson(md_file)
        assert info.has_disclaimer is True

    def test_parse_lesson_without_heading(self, tmp_path):
        md_file = tmp_path / "sem_titulo.md"
        md_file.write_text("Apenas texto sem heading.\n", encoding="utf-8")
        info = _parse_lesson(md_file)
        # Título derivado do nome do ficheiro
        assert "Sem Titulo" in info.titulo


class TestIngestQuiz:
    """Testes para parsing de quizzes JSON."""

    def test_valid_quiz(self, tmp_path):
        quiz_file = tmp_path / "quiz.json"
        quiz_data = {
            "questions": [
                {
                    "stem": "Pergunta?",
                    "topic": "ecg",
                    "options": ["A", "B", "C", "D"],
                    "answer_index": 0,
                    "explanation": "Explicação.",
                },
            ],
        }
        quiz_file.write_text(json.dumps(quiz_data), encoding="utf-8")
        info = _parse_quiz(quiz_file)
        assert info.valid is True
        assert info.num_questions == 1
        assert "ecg" in info.topics

    def test_invalid_json(self, tmp_path):
        quiz_file = tmp_path / "bad.json"
        quiz_file.write_text("{invalid json", encoding="utf-8")
        info = _parse_quiz(quiz_file)
        assert info.valid is False
        assert len(info.errors) > 0

    def test_quiz_missing_required_fields(self, tmp_path):
        quiz_file = tmp_path / "missing.json"
        quiz_data = {"questions": [{"stem": "Só stem"}]}
        quiz_file.write_text(json.dumps(quiz_data), encoding="utf-8")
        info = _parse_quiz(quiz_file)
        assert info.valid is False

    def test_quiz_answer_index_out_of_range(self, tmp_path):
        quiz_file = tmp_path / "oor.json"
        quiz_data = {
            "questions": [
                {
                    "stem": "Pergunta?",
                    "options": ["A", "B"],
                    "answer_index": 5,
                },
            ],
        }
        quiz_file.write_text(json.dumps(quiz_data), encoding="utf-8")
        info = _parse_quiz(quiz_file)
        assert info.valid is False

    def test_validate_quiz_not_dict(self):
        valid, errors = _validate_quiz([1, 2, 3])
        assert valid is False

    def test_validate_quiz_empty_questions(self):
        valid, errors = _validate_quiz({"questions": []})
        assert valid is False
        assert any("nenhuma" in e.lower() for e in errors)


class TestIngestModule:
    """Testes para a ingestão completa de um módulo."""

    def test_ingest_empty_dir(self, tmp_path):
        module_dir = tmp_path / "modulo_vazio"
        module_dir.mkdir()
        report = ingest_module(module_dir)
        assert report.total_lessons == 0
        assert report.total_quizzes == 0
        assert len(report.warnings) > 0

    def test_ingest_missing_dir(self, tmp_path):
        report = ingest_module(tmp_path / "nao_existe")
        assert not report.is_valid
        assert len(report.warnings) > 0

    def test_ingest_full_module(self, tmp_path):
        module_dir = tmp_path / "modulo_completo"
        aulas_dir = module_dir / "aulas"
        quizzes_dir = module_dir / "quizzes"
        aulas_dir.mkdir(parents=True)
        quizzes_dir.mkdir(parents=True)

        # Criar aula com disclaimer
        (aulas_dir / "aula1.md").write_text(
            "# Aula 1\n\nConteúdo educacional.\n\n"
            "Aviso: este material não substitui avaliação clínica.\n",
            encoding="utf-8",
        )

        # Criar quiz válido
        quiz_data = {
            "questions": [
                {
                    "stem": "Q1?",
                    "topic": "basico",
                    "options": ["A", "B", "C"],
                    "answer_index": 1,
                    "explanation": "B é correcto.",
                },
                {
                    "stem": "Q2?",
                    "topic": "avancado",
                    "options": ["X", "Y"],
                    "answer_index": 0,
                    "explanation": "X é correcto.",
                },
            ],
        }
        (quizzes_dir / "quiz1.json").write_text(
            json.dumps(quiz_data, ensure_ascii=False), encoding="utf-8"
        )

        report = ingest_module(module_dir)
        assert report.total_lessons == 1
        assert report.total_quizzes == 1
        assert report.total_questions == 2
        assert report.total_words > 0
        assert report.is_valid


# =====================================================================
# mega.deploy tests
# =====================================================================


class TestDeploy:
    """Testes para o módulo de deploy."""

    def test_build_empty_project(self, tmp_path):
        config = MegaConfig.default(tmp_path)
        config.save()
        modules_dir = tmp_path / config.diretorio_modulos
        modules_dir.mkdir(parents=True, exist_ok=True)

        result = build_site(tmp_path, config)
        assert isinstance(result, BuildResult)
        assert result.pages_generated >= 1  # pelo menos index.html
        assert (result.output_dir / "index.html").exists()

    def test_build_with_content(self, tmp_path):
        config = MegaConfig.default(tmp_path)
        config.save()
        module_dir = tmp_path / config.diretorio_modulos / "mod1" / "aulas"
        module_dir.mkdir(parents=True)
        (module_dir / "aula1.md").write_text(
            "# Aula de Teste\n\nConteúdo educacional.\n",
            encoding="utf-8",
        )

        result = build_site(tmp_path, config)
        assert result.modules_processed == 1
        assert result.pages_generated >= 2  # index + aula

    def test_build_output_is_html(self, tmp_path):
        config = MegaConfig.default(tmp_path)
        config.save()
        modules_dir = tmp_path / config.diretorio_modulos
        modules_dir.mkdir(parents=True, exist_ok=True)

        result = build_site(tmp_path, config)
        index = (result.output_dir / "index.html").read_text(encoding="utf-8")
        assert "<!DOCTYPE html>" in index
        assert "educacional" in index.lower()


# =====================================================================
# CLI command tests (via Typer runner)
# =====================================================================


class TestCLIInit:
    """Testes para o comando 'mega init'."""

    def test_init_creates_structure(self, tmp_path):
        result = runner.invoke(app, ["init", str(tmp_path)])
        assert result.exit_code == 0
        assert (tmp_path / DEFAULT_CONFIG_NAME).exists()
        # Verifica que a configuração YAML é válida
        with open(tmp_path / DEFAULT_CONFIG_NAME, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert "projeto" in data
        assert "conteudo" in data

    def test_init_creates_example_content(self, tmp_path):
        result = runner.invoke(app, ["init", str(tmp_path)])
        assert result.exit_code == 0
        modules_dir = tmp_path / "content" / "modules"
        assert modules_dir.is_dir()
        # Verifica que existem ficheiros de exemplo
        md_files = list(modules_dir.rglob("*.md"))
        json_files = list(modules_dir.rglob("*.json"))
        assert len(md_files) >= 1
        assert len(json_files) >= 1

    def test_init_refuses_overwrite_without_force(self, tmp_path):
        runner.invoke(app, ["init", str(tmp_path)])
        result = runner.invoke(app, ["init", str(tmp_path)])
        assert result.exit_code == 1

    def test_init_force_overwrites(self, tmp_path):
        runner.invoke(app, ["init", str(tmp_path)])
        result = runner.invoke(app, ["init", str(tmp_path), "--force"])
        assert result.exit_code == 0


class TestCLIIngest:
    """Testes para o comando 'mega ingest'."""

    def test_ingest_missing_dir(self, tmp_path):
        result = runner.invoke(app, ["ingest", str(tmp_path / "nao_existe")])
        assert result.exit_code == 1
        assert "não encontrado" in result.output.lower() or "erro" in result.output.lower()

    def test_ingest_valid_module(self, tmp_path):
        # Preparar módulo com conteúdo válido
        aulas = tmp_path / "aulas"
        quizzes = tmp_path / "quizzes"
        aulas.mkdir()
        quizzes.mkdir()

        (aulas / "aula.md").write_text(
            "# Teste\n\nConteúdo educacional. Não substitui avaliação clínica.\n",
            encoding="utf-8",
        )
        quiz = {
            "questions": [
                {
                    "stem": "Pergunta?",
                    "options": ["A", "B"],
                    "answer_index": 0,
                    "explanation": "A.",
                    "topic": "teste",
                },
            ],
        }
        (quizzes / "quiz.json").write_text(
            json.dumps(quiz, ensure_ascii=False), encoding="utf-8"
        )

        result = runner.invoke(app, ["ingest", str(tmp_path)])
        assert result.exit_code == 0
        assert "aula" in result.output.lower() or "resumo" in result.output.lower()

    def test_ingest_empty_module_warns(self, tmp_path):
        module_dir = tmp_path / "vazio"
        module_dir.mkdir()
        result = runner.invoke(app, ["ingest", str(module_dir)])
        # Empty module results in warnings and non-zero exit
        assert result.exit_code == 1


class TestCLIDeploy:
    """Testes para o comando 'mega deploy'."""

    def test_deploy_instructions_github(self, tmp_path):
        # Inicializar projecto primeiro
        runner.invoke(app, ["init", str(tmp_path)])
        import os

        orig = os.getcwd()
        os.chdir(tmp_path)
        try:
            result = runner.invoke(app, ["deploy", "--target", "github-pages"])
            assert result.exit_code == 0
            assert "github" in result.output.lower()
        finally:
            os.chdir(orig)

    def test_deploy_instructions_render(self, tmp_path):
        runner.invoke(app, ["init", str(tmp_path)])
        import os

        orig = os.getcwd()
        os.chdir(tmp_path)
        try:
            result = runner.invoke(app, ["deploy", "--target", "render"])
            assert result.exit_code == 0
            assert "render" in result.output.lower()
        finally:
            os.chdir(orig)

    def test_deploy_build(self, tmp_path):
        runner.invoke(app, ["init", str(tmp_path)])
        import os

        orig = os.getcwd()
        os.chdir(tmp_path)
        try:
            result = runner.invoke(app, ["deploy", "--build"])
            assert result.exit_code == 0
            assert (tmp_path / "_site" / "index.html").exists()
        finally:
            os.chdir(orig)

    def test_deploy_unknown_target(self, tmp_path):
        runner.invoke(app, ["init", str(tmp_path)])
        import os

        orig = os.getcwd()
        os.chdir(tmp_path)
        try:
            result = runner.invoke(app, ["deploy", "--target", "desconhecido"])
            assert result.exit_code == 1
        finally:
            os.chdir(orig)


class TestCLIStatus:
    """Testes para o comando 'mega status'."""

    def test_status_initialized_project(self, tmp_path):
        runner.invoke(app, ["init", str(tmp_path)])
        import os

        orig = os.getcwd()
        os.chdir(tmp_path)
        try:
            result = runner.invoke(app, ["status"])
            assert result.exit_code == 0
            assert "projecto" in result.output.lower() or "módulo" in result.output.lower()
        finally:
            os.chdir(orig)

    def test_status_no_config(self, tmp_path):
        import os

        orig = os.getcwd()
        os.chdir(tmp_path)
        try:
            result = runner.invoke(app, ["status"])
            assert result.exit_code == 0
        finally:
            os.chdir(orig)

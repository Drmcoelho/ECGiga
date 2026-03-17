"""
Testes para o pipeline de fine-tuning (mega.training).

Cobre: construção de datasets a partir de quizzes reais,
métricas de avaliação e validação de checklists médicos.
"""

from __future__ import annotations

import json
import math
import pathlib
import tempfile

import pytest

from mega.training.dataset import DatasetBuilder, TrainingExample
from mega.training.evaluate import (
    evaluate_medical_checklist,
    evaluate_perplexity,
    generate_evaluation_report,
)
from mega.training.checklist import (
    ECG_CHECKLIST,
    get_all_categories,
    get_checklist_by_category,
    get_mandatory_items,
)
from mega.training.lora import LoRATrainer

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
QUIZ_BANK = REPO_ROOT / "quiz" / "bank"


# ========================================================================
# DatasetBuilder — quizzes
# ========================================================================


class TestDatasetBuilderQuizzes:
    """Testa build_from_quizzes com o banco real de quizzes."""

    def test_build_from_quiz_bank(self):
        """Carrega todos os quizzes do banco e gera exemplos."""
        builder = DatasetBuilder()
        examples = builder.build_from_quizzes(QUIZ_BANK)
        # O banco tem pelo menos ~200 arquivos JSON → pelo menos 200 exemplos
        assert len(examples) >= 100, (
            f"Esperava >= 100 exemplos, obteve {len(examples)}"
        )

    def test_quiz_example_fields(self):
        """Cada exemplo gerado possui instruction, input, output."""
        builder = DatasetBuilder()
        examples = builder.build_from_quizzes(QUIZ_BANK)
        for ex in examples[:20]:
            assert ex.instruction, "instruction vazio"
            assert ex.input, "input vazio"
            assert ex.output, "output vazio"

    def test_quiz_example_has_metadata(self):
        """Exemplos possuem metadados (topic, difficulty, type)."""
        builder = DatasetBuilder()
        examples = builder.build_from_quizzes(QUIZ_BANK)
        for ex in examples[:20]:
            assert "type" in ex.metadata
            assert ex.metadata["type"] in (
                "quiz_resposta_direta",
                "quiz_analise_alternativas",
            )

    def test_quiz_generates_two_example_types(self):
        """Cada quiz gera exemplos de resposta direta e análise."""
        builder = DatasetBuilder()
        examples = builder.build_from_quizzes(QUIZ_BANK)
        types = {ex.metadata["type"] for ex in examples}
        assert "quiz_resposta_direta" in types
        assert "quiz_analise_alternativas" in types

    def test_build_from_single_quiz_file(self):
        """Testa com o arquivo exemplo_arrtimias.json."""
        single = QUIZ_BANK / "exemplo_arrtimias.json"
        assert single.exists(), f"{single} não encontrado"

        builder = DatasetBuilder()
        # Usar o diretório pai com rglob captura o arquivo
        # Para testar um único arquivo, criamos um dir temporário
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = pathlib.Path(tmpdir)
            (tmp / "test.json").write_text(
                single.read_text(encoding="utf-8"), encoding="utf-8"
            )
            examples = builder.build_from_quizzes(tmp)
            assert len(examples) == 2  # resposta direta + análise

    def test_quiz_output_contains_correct_answer(self):
        """A saída contém a resposta correta do quiz."""
        single = QUIZ_BANK / "exemplo_arrtimias.json"
        data = json.loads(single.read_text(encoding="utf-8"))
        correct = data["options"][data["answer_index"]]

        builder = DatasetBuilder()
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = pathlib.Path(tmpdir)
            (tmp / "test.json").write_text(
                single.read_text(encoding="utf-8"), encoding="utf-8"
            )
            examples = builder.build_from_quizzes(tmp)
            direct = [
                e for e in examples
                if e.metadata.get("type") == "quiz_resposta_direta"
            ]
            assert len(direct) == 1
            assert correct in direct[0].output

    def test_build_quiz_nonexistent_dir(self):
        """Diretório inexistente levanta FileNotFoundError."""
        builder = DatasetBuilder()
        with pytest.raises(FileNotFoundError):
            builder.build_from_quizzes("/tmp/nao_existe_xyz_123")

    def test_build_quiz_skips_invalid_json(self):
        """Arquivos JSON inválidos são ignorados sem erro."""
        builder = DatasetBuilder()
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = pathlib.Path(tmpdir)
            # Arquivo inválido
            (tmp / "bad.json").write_text("{invalid json", encoding="utf-8")
            # Arquivo válido
            valid = {
                "id": "test_01",
                "topic": "Teste",
                "difficulty": "easy",
                "stem": "Pergunta teste?",
                "options": ["A", "B", "C", "D"],
                "answer_index": 0,
                "explanation": "Explicação teste.",
            }
            (tmp / "good.json").write_text(
                json.dumps(valid, ensure_ascii=False), encoding="utf-8"
            )
            examples = builder.build_from_quizzes(tmp)
            assert len(examples) == 2  # resposta + análise do arquivo válido


# ========================================================================
# DatasetBuilder — quality / dedup / export
# ========================================================================


class TestDatasetQuality:
    """Testa filtro de qualidade, deduplicação e exportação."""

    def _make_builder_with_examples(self) -> DatasetBuilder:
        builder = DatasetBuilder()
        builder.examples = [
            TrainingExample(
                instruction="Instrução 1",
                input="Entrada 1",
                output="Saída completa com conteúdo suficiente para passar o filtro.",
                metadata={"type": "test"},
            ),
            TrainingExample(
                instruction="Instrução 2",
                input="Entrada 2",
                output="Curto",  # < 20 chars → removido
                metadata={"type": "test"},
            ),
            TrainingExample(
                instruction="",  # vazio → removido
                input="Entrada 3",
                output="Saída válida com conteúdo suficiente.",
                metadata={"type": "test"},
            ),
            # Duplicata da primeira
            TrainingExample(
                instruction="Instrução 1",
                input="Entrada 1",
                output="Saída completa com conteúdo suficiente para passar o filtro.",
                metadata={"type": "test"},
            ),
        ]
        return builder

    def test_filter_quality(self):
        builder = self._make_builder_with_examples()
        removed = builder.filter_quality(min_output_length=20)
        assert removed == 2  # "Curto" e instrução vazia
        assert len(builder.examples) == 2

    def test_deduplicate(self):
        builder = self._make_builder_with_examples()
        builder.filter_quality(min_output_length=20)
        removed = builder.deduplicate()
        assert removed == 1
        assert len(builder.examples) == 1

    def test_export_jsonl(self):
        builder = self._make_builder_with_examples()
        builder.filter_quality()
        builder.deduplicate()

        with tempfile.TemporaryDirectory() as tmpdir:
            path = pathlib.Path(tmpdir) / "dataset.jsonl"
            count = builder.export_jsonl(path)
            assert count == 1
            assert path.exists()

            # Verificar formato JSONL
            lines = path.read_text(encoding="utf-8").strip().split("\n")
            assert len(lines) == 1
            data = json.loads(lines[0])
            assert "instruction" in data
            assert "input" in data
            assert "output" in data

    def test_export_from_real_quizzes(self):
        """Exporta dataset real e verifica JSONL válido."""
        builder = DatasetBuilder()
        builder.build_from_quizzes(QUIZ_BANK)
        builder.filter_quality()
        builder.deduplicate()

        with tempfile.TemporaryDirectory() as tmpdir:
            path = pathlib.Path(tmpdir) / "ecg_dataset.jsonl"
            count = builder.export_jsonl(path)
            assert count > 50

            # Cada linha deve ser JSON válido
            with open(path, encoding="utf-8") as f:
                for i, line in enumerate(f):
                    data = json.loads(line)
                    assert "instruction" in data
                    assert "input" in data
                    assert "output" in data

    def test_stats(self):
        builder = DatasetBuilder()
        builder.build_from_quizzes(QUIZ_BANK)
        stats = builder.stats()
        assert stats["total"] > 0
        assert "por_tipo" in stats
        assert "por_topico" in stats


# ========================================================================
# DatasetBuilder — casos clínicos e aulas
# ========================================================================


class TestDatasetBuilderCasesAndLessons:
    """Testa build_from_cases e build_from_lessons com dados sintéticos."""

    def test_build_from_cases(self):
        builder = DatasetBuilder()
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = pathlib.Path(tmpdir)
            case = {
                "patient": "Homem, 65 anos",
                "history": "Dor torácica há 2 horas, sudorese",
                "ecg_findings": "Supra de ST em V1-V4, infra em DII, DIII, aVF",
                "diagnosis": "IAM anterior com supra de ST",
                "management": "Cineangiocoronariografia de urgência",
            }
            (tmp / "caso1.json").write_text(
                json.dumps(case, ensure_ascii=False), encoding="utf-8"
            )
            examples = builder.build_from_cases(tmp)
            assert len(examples) == 1
            assert "IAM anterior" in examples[0].output
            assert examples[0].metadata["type"] == "caso_clinico"

    def test_build_from_cases_skips_incomplete(self):
        builder = DatasetBuilder()
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = pathlib.Path(tmpdir)
            # Caso sem diagnóstico → deve ser ignorado
            case = {
                "patient": "Mulher, 45 anos",
                "history": "Palpitações",
                "ecg_findings": "",
                "diagnosis": "",
            }
            (tmp / "incompleto.json").write_text(
                json.dumps(case, ensure_ascii=False), encoding="utf-8"
            )
            examples = builder.build_from_cases(tmp)
            assert len(examples) == 0

    def test_build_from_lessons(self):
        builder = DatasetBuilder()
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = pathlib.Path(tmpdir)
            lesson = {
                "title": "Eixo Elétrico Cardíaco",
                "content": "O eixo elétrico representa a direção média da despolarização ventricular.",
                "key_points": [
                    "Eixo normal: entre -30 e +90 graus",
                    "DI positivo e aVF positivo indicam eixo normal",
                    "Desvio para a esquerda sugere BDAS ou HVE",
                ],
            }
            (tmp / "aula1.json").write_text(
                json.dumps(lesson, ensure_ascii=False), encoding="utf-8"
            )
            examples = builder.build_from_lessons(tmp)
            # 1 resumo + 3 pontos-chave = 4
            assert len(examples) == 4
            types = {ex.metadata["type"] for ex in examples}
            assert "aula_resumo" in types
            assert "aula_ponto_chave" in types

    def test_cases_nonexistent_dir(self):
        builder = DatasetBuilder()
        with pytest.raises(FileNotFoundError):
            builder.build_from_cases("/tmp/nao_existe_xyz_456")

    def test_lessons_nonexistent_dir(self):
        builder = DatasetBuilder()
        with pytest.raises(FileNotFoundError):
            builder.build_from_lessons("/tmp/nao_existe_xyz_789")


# ========================================================================
# Avaliação — Perplexidade
# ========================================================================


class TestEvaluatePerplexity:
    """Testa o cálculo de perplexidade."""

    def test_perplexity_from_log_probs(self):
        """Calcula perplexidade a partir de log-probabilidades."""
        log_probs = [-1.0, -2.0, -1.5, -1.0]
        result = evaluate_perplexity(log_probs, [])
        assert "perplexity" in result
        assert "avg_loss" in result
        assert result["num_examples"] == 4
        # avg_neg_log_prob = (1 + 2 + 1.5 + 1) / 4 = 1.375
        # ppl = exp(1.375) ≈ 3.955
        assert 3.0 < result["perplexity"] < 5.0

    def test_perplexity_empty_list(self):
        result = evaluate_perplexity([], [])
        assert result["perplexity"] == float("inf")
        assert result["num_examples"] == 0

    def test_perplexity_perfect_predictions(self):
        """Log-probs de 0 → perplexidade 1."""
        log_probs = [0.0, 0.0, 0.0]
        result = evaluate_perplexity(log_probs, [])
        assert abs(result["perplexity"] - 1.0) < 0.01

    def test_perplexity_high_loss(self):
        """Log-probs muito negativos → alta perplexidade (com cap)."""
        log_probs = [-50.0, -60.0, -70.0]
        result = evaluate_perplexity(log_probs, [])
        assert result["perplexity"] > 1.0


# ========================================================================
# Avaliação — Checklist médico
# ========================================================================


class TestEvaluateMedicalChecklist:
    """Testa avaliação de respostas contra checklist médico."""

    def test_checklist_full_match(self):
        """Resposta contendo todas as palavras-chave → score alto."""
        checklist = [
            {
                "id": "test_01",
                "categoria": "Ritmo",
                "descricao": "Ritmo sinusal",
                "palavras_chave": ["ritmo sinusal"],
                "obrigatorio": True,
            },
            {
                "id": "test_02",
                "categoria": "Frequência",
                "descricao": "FC",
                "palavras_chave": ["frequência cardíaca", "bpm"],
                "obrigatorio": True,
            },
        ]
        responses = [
            "O ECG mostra ritmo sinusal com frequência cardíaca de 72 bpm."
        ]
        result = evaluate_medical_checklist(responses, checklist)
        assert result["score"] == 1.0
        assert result["taxa_aprovacao"] == 100.0
        assert result["aprovacao_geral"] is True
        assert len(result["aprovados"]) == 2

    def test_checklist_partial_match(self):
        """Resposta parcial → score intermediário."""
        checklist = [
            {
                "id": "t1",
                "categoria": "Ritmo",
                "descricao": "Ritmo",
                "palavras_chave": ["ritmo sinusal"],
                "obrigatorio": True,
            },
            {
                "id": "t2",
                "categoria": "Eixo",
                "descricao": "Eixo",
                "palavras_chave": ["eixo elétrico"],
                "obrigatorio": False,
            },
        ]
        responses = ["Ritmo sinusal normal."]
        result = evaluate_medical_checklist(responses, checklist)
        assert result["score"] == 0.5
        assert len(result["aprovados"]) == 1
        assert len(result["reprovados"]) == 1

    def test_checklist_mandatory_failed(self):
        """Falha em item obrigatório → aprovacao_geral False."""
        checklist = [
            {
                "id": "t1",
                "categoria": "Ritmo",
                "descricao": "Ritmo",
                "palavras_chave": ["fibrilação atrial"],
                "obrigatorio": True,
            },
        ]
        responses = ["ECG normal, sem alterações."]
        result = evaluate_medical_checklist(responses, checklist)
        assert result["aprovacao_geral"] is False
        assert result["itens_obrigatorios_reprovados"] == 1

    def test_checklist_empty_responses(self):
        result = evaluate_medical_checklist([], ECG_CHECKLIST)
        assert result["score"] == 0.0
        assert result["itens_avaliados"] == 0

    def test_checklist_with_ecg_checklist(self):
        """Testa com o ECG_CHECKLIST real usando resposta rica."""
        response = (
            "O ECG mostra ritmo sinusal com frequência cardíaca de 80 bpm. "
            "O eixo elétrico está normal. O intervalo PR mede 160 ms (normal). "
            "A duração do QRS é de 90 ms. O intervalo QTc é de 420 ms. "
            "Não há supradesnivelamento ou infradesnivelamento do segmento ST. "
            "A onda T está normal em todas as derivações."
        )
        result = evaluate_medical_checklist([response], ECG_CHECKLIST)
        # Uma resposta completa deve acertar pelo menos os itens obrigatórios
        assert result["score"] > 0.2
        assert result["total_itens"] == len(ECG_CHECKLIST)


# ========================================================================
# Relatório de avaliação
# ========================================================================


class TestEvaluationReport:
    """Testa geração de relatório em português."""

    def test_report_with_perplexity(self):
        results = {
            "perplexity": 3.5,
            "avg_loss": 1.25,
            "num_examples": 100,
        }
        report = generate_evaluation_report(results)
        assert "RELATÓRIO DE AVALIAÇÃO" in report
        assert "Perplexidade" in report
        assert "3.5" in report

    def test_report_with_checklist(self):
        results = {
            "score": 0.8,
            "taxa_aprovacao": 80.0,
            "total_itens": 5,
            "itens_avaliados": 5,
            "aprovados": [
                {"categoria": "Ritmo", "descricao": "Sinusal", "obrigatorio": True}
            ],
            "reprovados": [
                {"categoria": "Eixo", "descricao": "Eixo", "obrigatorio": False}
            ],
            "itens_obrigatorios_reprovados": 0,
            "aprovacao_geral": True,
        }
        report = generate_evaluation_report(results)
        assert "Checklist" in report
        assert "80.0%" in report
        assert "APROVADO" in report

    def test_report_failed_status(self):
        results = {
            "score": 0.2,
            "taxa_aprovacao": 20.0,
            "total_itens": 5,
            "itens_avaliados": 5,
            "aprovados": [],
            "reprovados": [
                {"categoria": "Ritmo", "descricao": "Sinusal", "obrigatorio": True}
            ],
            "itens_obrigatorios_reprovados": 1,
            "aprovacao_geral": False,
        }
        report = generate_evaluation_report(results)
        assert "REPROVADO" in report
        assert "ATENÇÃO" in report


# ========================================================================
# Checklist
# ========================================================================


class TestChecklist:
    """Testa o checklist médico de ECG."""

    def test_checklist_has_at_least_20_items(self):
        assert len(ECG_CHECKLIST) >= 20, (
            f"Checklist deve ter >= 20 itens, tem {len(ECG_CHECKLIST)}"
        )

    def test_checklist_has_25_items(self):
        assert len(ECG_CHECKLIST) == 25

    def test_checklist_item_structure(self):
        """Cada item tem os campos necessários."""
        required_fields = {"id", "categoria", "descricao", "palavras_chave", "obrigatorio"}
        for item in ECG_CHECKLIST:
            missing = required_fields - set(item.keys())
            assert not missing, f"Item {item.get('id')} falta campos: {missing}"

    def test_checklist_ids_unique(self):
        ids = [item["id"] for item in ECG_CHECKLIST]
        assert len(ids) == len(set(ids)), "IDs do checklist devem ser únicos"

    def test_checklist_categories(self):
        categories = get_all_categories()
        assert "Ritmo" in categories
        assert "Frequência" in categories
        assert "Eixo" in categories
        assert "Intervalos" in categories
        assert "Morfologia" in categories

    def test_get_checklist_by_category(self):
        ritmo = get_checklist_by_category("Ritmo")
        assert len(ritmo) >= 2
        for item in ritmo:
            assert item["categoria"] == "Ritmo"

    def test_get_mandatory_items(self):
        mandatory = get_mandatory_items()
        assert len(mandatory) >= 5
        for item in mandatory:
            assert item["obrigatorio"] is True

    def test_checklist_keywords_not_empty(self):
        """Cada item deve ter pelo menos uma palavra-chave."""
        for item in ECG_CHECKLIST:
            assert len(item["palavras_chave"]) > 0, (
                f"Item {item['id']} sem palavras-chave"
            )

    def test_ecg_core_areas_covered(self):
        """Checklist cobre as áreas essenciais de interpretação de ECG."""
        categories = get_all_categories()
        essential = ["Ritmo", "Frequência", "Eixo", "Intervalos", "Morfologia", "Segmento ST"]
        for area in essential:
            assert area in categories, f"Área essencial '{area}' não coberta"


# ========================================================================
# LoRATrainer
# ========================================================================


class TestLoRATrainer:
    """Testa a configuração do LoRATrainer (sem treinamento real)."""

    def test_default_config(self):
        trainer = LoRATrainer()
        config = trainer.prepare_config()
        assert config["lora"]["r"] == 16
        assert config["lora"]["lora_alpha"] == 32
        assert config["training"]["num_train_epochs"] == 3
        assert config["project"] == "ECGiga-LoRA"

    def test_custom_config(self):
        trainer = LoRATrainer(
            model_name="test-model",
            rank=8,
            alpha=16,
            epochs=5,
            batch_size=8,
            learning_rate=1e-4,
        )
        config = trainer.prepare_config()
        assert config["model_name_or_path"] == "test-model"
        assert config["lora"]["r"] == 8
        assert config["lora"]["lora_alpha"] == 16
        assert config["training"]["num_train_epochs"] == 5
        assert config["training"]["per_device_train_batch_size"] == 8
        assert config["training"]["learning_rate"] == 1e-4

    def test_save_config(self):
        trainer = LoRATrainer()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = pathlib.Path(tmpdir) / "config.json"
            trainer.save_config(path)
            assert path.exists()
            config = json.loads(path.read_text(encoding="utf-8"))
            assert "lora" in config
            assert "training" in config

    def test_train_missing_dataset(self):
        trainer = LoRATrainer()
        with pytest.raises(FileNotFoundError):
            trainer.train("/tmp/nao_existe_dataset.jsonl")

    def test_train_returns_instructions_when_deps_missing(self):
        """Sem torch/transformers instalados, retorna instruções."""
        trainer = LoRATrainer()
        with tempfile.TemporaryDirectory() as tmpdir:
            dataset = pathlib.Path(tmpdir) / "test.jsonl"
            dataset.write_text(
                '{"instruction":"a","input":"b","output":"c"}\n',
                encoding="utf-8",
            )
            result = trainer.train(dataset)
            # Em ambiente de teste sem GPU, deve retornar instruções
            # ou resultado de treinamento se deps estiverem disponíveis
            assert "status" in result

    def test_export_adapter_creates_config(self):
        trainer = LoRATrainer()
        with tempfile.TemporaryDirectory() as tmpdir:
            # Simular output_dir
            trainer.output_dir = str(pathlib.Path(tmpdir) / "src")
            pathlib.Path(trainer.output_dir).mkdir()

            export_dir = pathlib.Path(tmpdir) / "export"
            result = trainer.export_adapter(export_dir)
            assert export_dir.exists()
            assert "training_config.json" in result["arquivos_exportados"]
            config_file = export_dir / "training_config.json"
            assert config_file.exists()


# ========================================================================
# TrainingExample
# ========================================================================


class TestTrainingExample:
    """Testa a dataclass TrainingExample."""

    def test_to_dict(self):
        ex = TrainingExample(
            instruction="Instrução",
            input="Entrada",
            output="Saída",
            metadata={"type": "test"},
        )
        d = ex.to_dict()
        assert d["instruction"] == "Instrução"
        assert d["input"] == "Entrada"
        assert d["output"] == "Saída"
        assert d["metadata"]["type"] == "test"

    def test_content_hash_deterministic(self):
        ex1 = TrainingExample(instruction="A", input="B", output="C")
        ex2 = TrainingExample(instruction="A", input="B", output="C")
        assert ex1.content_hash() == ex2.content_hash()

    def test_content_hash_differs(self):
        ex1 = TrainingExample(instruction="A", input="B", output="C")
        ex2 = TrainingExample(instruction="A", input="B", output="D")
        assert ex1.content_hash() != ex2.content_hash()

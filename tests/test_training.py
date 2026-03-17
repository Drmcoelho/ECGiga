"""Tests for LoRA fine-tuning pipeline."""

from pathlib import Path


def test_dataset_builder_collects_from_bank():
    from training.lora_pipeline import DatasetBuilder
    builder = DatasetBuilder(content_dir="content/modules")
    pairs = builder.collect_qa_pairs()
    # Should find questions from quiz/bank at minimum
    assert len(pairs) > 0
    assert "instruction" in pairs[0]
    assert "response" in pairs[0]


def test_dataset_builder_export_jsonl(tmp_path):
    from training.lora_pipeline import DatasetBuilder
    builder = DatasetBuilder()
    out = str(tmp_path / "train.jsonl")
    count = builder.export_jsonl(output_path=out)
    assert count > 0
    assert Path(out).exists()
    # Verify JSONL format
    import json
    lines = Path(out).read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == count
    first = json.loads(lines[0])
    assert "instruction" in first


def test_dataset_builder_split():
    from training.lora_pipeline import DatasetBuilder
    builder = DatasetBuilder()
    split = builder.split_dataset(train_ratio=0.8)
    assert split["total"] > 0
    assert len(split["train"]) + len(split["eval"]) == split["total"]


def test_lora_pipeline_scaffold(tmp_path):
    from training.lora_pipeline import LoRAPipeline
    pipeline = LoRAPipeline(base_model="test-model")
    n = pipeline.prepare_dataset()
    assert n > 0

    config = pipeline.train(output_dir=str(tmp_path / "model"))
    assert config["status"] == "scaffold_only"
    assert Path(tmp_path / "model" / "training_config.json").exists()


def test_lora_pipeline_evaluate():
    from training.lora_pipeline import LoRAPipeline
    pipeline = LoRAPipeline()
    result = pipeline.evaluate()
    assert result["status"] == "scaffold_only"

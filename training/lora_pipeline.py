"""Educational fine-tuning pipeline for ECG interpretation models.

Scaffolds a LoRA training pipeline for open-source models (e.g., Mistral 7B)
using didactic question-reasoning-answer datasets from the ECG course.

Usage:
    from training.lora_pipeline import LoRAPipeline
    pipeline = LoRAPipeline(base_model="mistralai/Mistral-7B-v0.1")
    pipeline.prepare_dataset("content/modules/")
    pipeline.train(output_dir="models/ecg-lora")
    pipeline.evaluate()
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Optional


class DatasetBuilder:
    """Builds training datasets from ECG course content."""

    def __init__(self, content_dir: str = "content/modules"):
        self.content_dir = Path(content_dir)

    def collect_qa_pairs(self) -> list[dict]:
        """Collect question-answer pairs from quiz banks."""
        pairs = []
        for json_file in self.content_dir.rglob("*.json"):
            try:
                data = json.loads(json_file.read_text(encoding="utf-8"))
                if isinstance(data, dict) and "questions" in data:
                    for q in data["questions"]:
                        pairs.append(self._qa_from_mcq(q))
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and "stem" in item:
                            pairs.append(self._qa_from_mcq(item))
            except (json.JSONDecodeError, OSError):
                continue

        # Also collect from quiz/bank
        bank = Path("quiz/bank")
        if bank.exists():
            for json_file in bank.rglob("*.json"):
                try:
                    data = json.loads(json_file.read_text(encoding="utf-8"))
                    if isinstance(data, dict) and "stem" in data:
                        pairs.append(self._qa_from_mcq(data))
                except (json.JSONDecodeError, OSError):
                    continue

        return pairs

    def _qa_from_mcq(self, mcq: dict) -> dict:
        """Convert MCQ to instruction-response format for training."""
        options = mcq.get("options", [])
        answer_idx = mcq.get("answer_index", 0)
        correct = options[answer_idx] if answer_idx < len(options) else ""

        options_text = "\n".join(f"{chr(65+i)}) {opt}" for i, opt in enumerate(options))

        return {
            "instruction": f"{mcq.get('stem', '')}\n\n{options_text}",
            "response": f"A resposta correta é {chr(65+answer_idx)}) {correct}.\n\nExplicação: {mcq.get('explanation', '')}",
            "topic": mcq.get("topic", "ECG"),
            "difficulty": mcq.get("difficulty", "medium"),
            "source_id": mcq.get("id", "unknown"),
        }

    def export_jsonl(self, output_path: str = "training/data/ecg_train.jsonl") -> int:
        """Export dataset as JSONL for training."""
        pairs = self.collect_qa_pairs()
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            for pair in pairs:
                f.write(json.dumps(pair, ensure_ascii=False) + "\n")
        return len(pairs)

    def split_dataset(self, train_ratio: float = 0.85) -> dict:
        """Split into train/eval sets."""
        import random
        pairs = self.collect_qa_pairs()
        random.shuffle(pairs)
        split_idx = int(len(pairs) * train_ratio)
        return {
            "train": pairs[:split_idx],
            "eval": pairs[split_idx:],
            "total": len(pairs),
        }


class LoRAPipeline:
    """LoRA fine-tuning pipeline for ECG educational models.

    Requires: transformers, peft, datasets, bitsandbytes (not in base deps).
    Install with: pip install transformers peft datasets bitsandbytes accelerate
    """

    def __init__(self, base_model: str = "mistralai/Mistral-7B-v0.1",
                 lora_r: int = 16, lora_alpha: int = 32,
                 lora_dropout: float = 0.05):
        self.base_model = base_model
        self.lora_r = lora_r
        self.lora_alpha = lora_alpha
        self.lora_dropout = lora_dropout
        self._dataset: Optional[list] = None

    def prepare_dataset(self, content_dir: str = "content/modules") -> int:
        """Prepare training dataset from course content."""
        builder = DatasetBuilder(content_dir)
        self._dataset = builder.collect_qa_pairs()
        return len(self._dataset)

    def train(self, output_dir: str = "models/ecg-lora",
              epochs: int = 3, batch_size: int = 4,
              learning_rate: float = 2e-4) -> dict:
        """Train LoRA adapter. Requires GPU and transformers ecosystem."""
        if not self._dataset:
            raise RuntimeError("Call prepare_dataset() first")

        # This is a scaffold — actual training requires GPU + HF libs
        config = {
            "base_model": self.base_model,
            "lora_r": self.lora_r,
            "lora_alpha": self.lora_alpha,
            "lora_dropout": self.lora_dropout,
            "epochs": epochs,
            "batch_size": batch_size,
            "learning_rate": learning_rate,
            "dataset_size": len(self._dataset),
            "output_dir": output_dir,
            "status": "scaffold_only",
            "note": "Actual training requires: pip install transformers peft datasets bitsandbytes accelerate",
        }

        Path(output_dir).mkdir(parents=True, exist_ok=True)
        Path(output_dir, "training_config.json").write_text(
            json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        return config

    def evaluate(self, eval_data: Optional[list] = None) -> dict:
        """Evaluate model on held-out data."""
        return {
            "status": "scaffold_only",
            "note": "Evaluation requires trained adapter and transformers",
            "metrics": {
                "perplexity": None,
                "accuracy": None,
                "medical_checklist_score": None,
            },
        }

"""
mega.training — Pipeline de fine-tuning para o projeto ECGiga.

Fornece ferramentas para:
  - Construção de datasets a partir do banco de quizzes, casos clínicos e aulas
  - Treinamento LoRA (Low-Rank Adaptation)
  - Avaliação de qualidade e acurácia médica

Referência: GitHub issue #23
"""

from mega.training.dataset import DatasetBuilder
from mega.training.lora import LoRATrainer
from mega.training.evaluate import (
    evaluate_perplexity,
    evaluate_medical_checklist,
    generate_evaluation_report,
)
from mega.training.checklist import ECG_CHECKLIST

__all__ = [
    "DatasetBuilder",
    "LoRATrainer",
    "evaluate_perplexity",
    "evaluate_medical_checklist",
    "generate_evaluation_report",
    "ECG_CHECKLIST",
]

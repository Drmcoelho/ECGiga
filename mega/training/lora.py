"""
mega.training.lora — Wrapper para treinamento LoRA.

Fornece a classe LoRATrainer que gera configurações, inicia treinamento
e exporta adaptadores LoRA para modelos de linguagem.
"""

from __future__ import annotations

import json
import logging
import pathlib
import shutil
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class LoRATrainer:
    """Gerencia o treinamento LoRA para fine-tuning de modelos de ECG.

    Parameters
    ----------
    model_name : str
        Nome ou caminho do modelo base (ex.: "meta-llama/Llama-2-7b-hf").
    rank : int
        Rank da decomposição LoRA (padrão: 16).
    alpha : int
        Fator de escala alpha do LoRA (padrão: 32).
    epochs : int
        Número de épocas de treinamento (padrão: 3).
    batch_size : int
        Tamanho do batch (padrão: 4).
    learning_rate : float
        Taxa de aprendizado (padrão: 2e-4).
    target_modules : list[str]
        Módulos alvo para LoRA (padrão: q_proj, v_proj).
    output_dir : str
        Diretório de saída para checkpoints.
    max_seq_length : int
        Comprimento máximo de sequência (padrão: 2048).
    warmup_steps : int
        Número de passos de aquecimento (padrão: 100).
    gradient_accumulation_steps : int
        Passos de acumulação de gradiente (padrão: 4).
    """

    model_name: str = "meta-llama/Llama-2-7b-hf"
    rank: int = 16
    alpha: int = 32
    epochs: int = 3
    batch_size: int = 4
    learning_rate: float = 2e-4
    target_modules: list[str] = field(
        default_factory=lambda: ["q_proj", "v_proj"]
    )
    output_dir: str = "./lora_output"
    max_seq_length: int = 2048
    warmup_steps: int = 100
    gradient_accumulation_steps: int = 4

    def prepare_config(self) -> Dict[str, Any]:
        """Gera o dicionário de configuração para treinamento LoRA.

        Retorna um dict compatível com frameworks como Axolotl,
        LLaMA-Factory ou PEFT/transformers.

        Returns
        -------
        dict
            Configuração completa de treinamento.
        """
        config = {
            # Modelo
            "model_name_or_path": self.model_name,
            "model_type": "AutoModelForCausalLM",
            # LoRA
            "lora": {
                "r": self.rank,
                "lora_alpha": self.alpha,
                "target_modules": self.target_modules,
                "lora_dropout": 0.05,
                "bias": "none",
                "task_type": "CAUSAL_LM",
            },
            # Treinamento
            "training": {
                "num_train_epochs": self.epochs,
                "per_device_train_batch_size": self.batch_size,
                "learning_rate": self.learning_rate,
                "warmup_steps": self.warmup_steps,
                "gradient_accumulation_steps": self.gradient_accumulation_steps,
                "max_seq_length": self.max_seq_length,
                "fp16": True,
                "logging_steps": 10,
                "save_strategy": "epoch",
                "evaluation_strategy": "epoch",
                "output_dir": self.output_dir,
                "report_to": "none",
            },
            # Otimizador
            "optimizer": {
                "type": "adamw_torch",
                "weight_decay": 0.01,
            },
            # Dataset
            "dataset": {
                "format": "instruction",
                "field_instruction": "instruction",
                "field_input": "input",
                "field_output": "output",
            },
            # Metadados
            "project": "ECGiga-LoRA",
            "description": "Fine-tuning LoRA para interpretação de ECG em português",
        }

        logger.info(
            "Configuração LoRA preparada: rank=%d, alpha=%d, lr=%.1e, epochs=%d",
            self.rank,
            self.alpha,
            self.learning_rate,
            self.epochs,
        )
        return config

    def save_config(self, path: str | pathlib.Path) -> None:
        """Salva a configuração de treinamento em arquivo JSON.

        Parameters
        ----------
        path : str | pathlib.Path
            Caminho do arquivo de saída.
        """
        config = self.prepare_config()
        out = pathlib.Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        logger.info("Configuração salva em %s", out)

    def train(self, dataset_path: str | pathlib.Path) -> Dict[str, Any]:
        """Executa o treinamento LoRA.

        Tenta usar PEFT/transformers se disponíveis. Caso contrário,
        retorna instruções para instalação das dependências.

        Parameters
        ----------
        dataset_path : str | pathlib.Path
            Caminho para o arquivo JSONL de treinamento.

        Returns
        -------
        dict
            Resultado do treinamento ou instruções de instalação.
        """
        dataset_path = pathlib.Path(dataset_path)
        if not dataset_path.exists():
            raise FileNotFoundError(
                f"Dataset não encontrado: {dataset_path}"
            )

        # Verificar dependências
        missing = self._check_dependencies()
        if missing:
            instructions = self._install_instructions(missing)
            logger.warning(
                "Dependências ausentes para treinamento: %s", ", ".join(missing)
            )
            return {
                "status": "dependencias_ausentes",
                "dependencias_faltantes": missing,
                "instrucoes": instructions,
                "config": self.prepare_config(),
                "dataset_path": str(dataset_path),
            }

        # Se dependências estiverem presentes, executar treinamento
        return self._run_training(dataset_path)

    def _check_dependencies(self) -> list[str]:
        """Verifica se as dependências de treinamento estão instaladas."""
        missing = []
        for pkg in ["torch", "transformers", "peft", "datasets", "trl"]:
            try:
                __import__(pkg)
            except ImportError:
                missing.append(pkg)
        return missing

    def _install_instructions(self, missing: list[str]) -> str:
        """Gera instruções de instalação para dependências faltantes."""
        packages = " ".join(missing)
        return (
            f"Para executar o treinamento LoRA, instale as dependências:\n\n"
            f"  pip install {packages}\n\n"
            f"Ou instale todas de uma vez:\n\n"
            f"  pip install torch transformers peft datasets trl "
            f"accelerate bitsandbytes\n\n"
            f"Alternativamente, use a configuração gerada com:\n"
            f"  trainer.save_config('config.json')\n\n"
            f"E execute com frameworks como Axolotl ou LLaMA-Factory."
        )

    def _run_training(self, dataset_path: pathlib.Path) -> Dict[str, Any]:
        """Executa o treinamento com PEFT/transformers.

        Este método só é chamado quando todas as dependências estão
        disponíveis.
        """
        import torch  # noqa: F811
        from datasets import load_dataset
        from peft import LoraConfig, get_peft_model
        from transformers import (
            AutoModelForCausalLM,
            AutoTokenizer,
            TrainingArguments,
        )
        from trl import SFTTrainer

        config = self.prepare_config()

        logger.info("Carregando modelo: %s", self.model_name)
        tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            torch_dtype=torch.float16,
            device_map="auto",
        )

        lora_config = LoraConfig(
            r=self.rank,
            lora_alpha=self.alpha,
            target_modules=self.target_modules,
            lora_dropout=0.05,
            bias="none",
            task_type="CAUSAL_LM",
        )

        model = get_peft_model(model, lora_config)

        dataset = load_dataset("json", data_files=str(dataset_path), split="train")

        def format_example(example):
            text = (
                f"### Instrução:\n{example['instruction']}\n\n"
                f"### Entrada:\n{example['input']}\n\n"
                f"### Resposta:\n{example['output']}"
            )
            return {"text": text}

        dataset = dataset.map(format_example)

        training_args = TrainingArguments(
            output_dir=self.output_dir,
            num_train_epochs=self.epochs,
            per_device_train_batch_size=self.batch_size,
            learning_rate=self.learning_rate,
            warmup_steps=self.warmup_steps,
            gradient_accumulation_steps=self.gradient_accumulation_steps,
            fp16=True,
            logging_steps=10,
            save_strategy="epoch",
            report_to="none",
        )

        trainer = SFTTrainer(
            model=model,
            tokenizer=tokenizer,
            train_dataset=dataset,
            args=training_args,
            max_seq_length=self.max_seq_length,
        )

        logger.info("Iniciando treinamento LoRA...")
        train_result = trainer.train()

        model.save_pretrained(self.output_dir)
        tokenizer.save_pretrained(self.output_dir)

        logger.info("Treinamento concluído. Adaptador salvo em %s", self.output_dir)
        return {
            "status": "concluido",
            "output_dir": self.output_dir,
            "train_loss": train_result.training_loss,
            "epochs": self.epochs,
            "config": config,
        }

    def export_adapter(self, output_dir: str | pathlib.Path) -> Dict[str, Any]:
        """Exporta o adaptador LoRA treinado para um diretório.

        Copia os arquivos do adaptador (adapter_config.json,
        adapter_model.bin) para o diretório de destino.

        Parameters
        ----------
        output_dir : str | pathlib.Path
            Diretório de destino para o adaptador.

        Returns
        -------
        dict
            Informações sobre a exportação.
        """
        src = pathlib.Path(self.output_dir)
        dst = pathlib.Path(output_dir)
        dst.mkdir(parents=True, exist_ok=True)

        adapter_files = [
            "adapter_config.json",
            "adapter_model.bin",
            "adapter_model.safetensors",
        ]

        exported = []
        for fname in adapter_files:
            src_file = src / fname
            if src_file.exists():
                shutil.copy2(src_file, dst / fname)
                exported.append(fname)

        # Sempre exportar a configuração de treinamento
        config_path = dst / "training_config.json"
        config_path.write_text(
            json.dumps(self.prepare_config(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        exported.append("training_config.json")

        result = {
            "output_dir": str(dst),
            "arquivos_exportados": exported,
            "modelo_base": self.model_name,
            "lora_rank": self.rank,
            "lora_alpha": self.alpha,
        }

        logger.info("Adaptador exportado para %s: %s", dst, exported)
        return result

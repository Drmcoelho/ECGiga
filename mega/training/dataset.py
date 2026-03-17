"""
mega.training.dataset — Construção de datasets para fine-tuning.

Converte quizzes, casos clínicos e aulas do ECGiga em formato JSONL
compatível com LoRA fine-tuning (instrução / entrada / saída).
"""

from __future__ import annotations

import hashlib
import json
import logging
import pathlib
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tipos de exemplo
# ---------------------------------------------------------------------------

@dataclass
class TrainingExample:
    """Um exemplo de treinamento no formato instrução/entrada/saída."""

    instruction: str
    input: str
    output: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "instruction": self.instruction,
            "input": self.input,
            "output": self.output,
            "metadata": self.metadata,
        }

    def content_hash(self) -> str:
        """Hash determinístico para deduplicação."""
        raw = f"{self.instruction}|{self.input}|{self.output}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# DatasetBuilder
# ---------------------------------------------------------------------------

class DatasetBuilder:
    """Constrói datasets de treinamento a partir de fontes do ECGiga."""

    def __init__(self) -> None:
        self.examples: List[TrainingExample] = []

    # -- Quiz ---------------------------------------------------------------

    def build_from_quizzes(self, quiz_dir: str | pathlib.Path) -> List[TrainingExample]:
        """Converte arquivos JSON de quiz em exemplos de treinamento.

        Cada quiz JSON segue o schema:
            id, topic, difficulty, stem, options, answer_index, explanation

        Gera dois tipos de exemplo por quiz:
          1. Resposta direta (qual é a resposta correta + explicação)
          2. Explicação didática (por que as alternativas erradas estão erradas)

        Parameters
        ----------
        quiz_dir : str | pathlib.Path
            Diretório raiz do banco de quizzes (pode conter subpastas).

        Returns
        -------
        list[TrainingExample]
            Exemplos gerados nesta chamada.
        """
        quiz_path = pathlib.Path(quiz_dir)
        if not quiz_path.exists():
            raise FileNotFoundError(f"Diretório de quizzes não encontrado: {quiz_path}")

        new_examples: List[TrainingExample] = []
        json_files = sorted(quiz_path.rglob("*.json"))

        for fpath in json_files:
            try:
                data = json.loads(fpath.read_text(encoding="utf-8"))
                examples = self._quiz_to_examples(data, source=str(fpath))
                new_examples.extend(examples)
            except (json.JSONDecodeError, KeyError, IndexError) as exc:
                logger.warning("Erro ao processar %s: %s", fpath, exc)
                continue

        self.examples.extend(new_examples)
        logger.info(
            "Quiz: %d arquivos processados, %d exemplos gerados",
            len(json_files),
            len(new_examples),
        )
        return new_examples

    def _quiz_to_examples(
        self, data: Dict[str, Any], source: str = ""
    ) -> List[TrainingExample]:
        """Converte um único quiz JSON em exemplos de treinamento."""
        examples: List[TrainingExample] = []

        stem = data["stem"]
        options = data["options"]
        answer_idx = data["answer_index"]
        correct = options[answer_idx]
        explanation = data.get("explanation", "")
        topic = data.get("topic", "ECG")
        difficulty = data.get("difficulty", "medium")
        quiz_id = data.get("id", "")

        # Formata as opções como texto
        options_text = "\n".join(
            f"  {chr(65 + i)}) {opt}" for i, opt in enumerate(options)
        )

        # Exemplo 1: Resposta direta
        instruction = (
            "Você é um especialista em eletrocardiografia. "
            "Responda a questão de múltipla escolha sobre ECG, "
            "indicando a alternativa correta e explicando o raciocínio."
        )
        input_text = f"Pergunta: {stem}\n\nAlternativas:\n{options_text}"
        answer_letter = chr(65 + answer_idx)
        output_text = (
            f"Resposta correta: {answer_letter}) {correct}\n\n"
            f"Explicação: {explanation}"
        )

        examples.append(
            TrainingExample(
                instruction=instruction,
                input=input_text,
                output=output_text,
                metadata={
                    "source": source,
                    "quiz_id": quiz_id,
                    "topic": topic,
                    "difficulty": difficulty,
                    "type": "quiz_resposta_direta",
                },
            )
        )

        # Exemplo 2: Análise de alternativas incorretas
        wrong_options = [
            (chr(65 + i), opt)
            for i, opt in enumerate(options)
            if i != answer_idx
        ]
        if wrong_options and explanation:
            instruction2 = (
                "Você é um professor de eletrocardiografia. "
                "Explique por que a alternativa correta é a melhor "
                "resposta e por que as outras estão erradas."
            )
            wrong_text = "\n".join(
                f"  - {letter}) {opt}" for letter, opt in wrong_options
            )
            output2 = (
                f"A alternativa correta é {answer_letter}) {correct}.\n\n"
                f"Explicação: {explanation}\n\n"
                f"As seguintes alternativas estão incorretas:\n{wrong_text}\n\n"
                f"Cada uma delas não corresponde ao achado descrito na questão."
            )
            examples.append(
                TrainingExample(
                    instruction=instruction2,
                    input=input_text,
                    output=output2,
                    metadata={
                        "source": source,
                        "quiz_id": quiz_id,
                        "topic": topic,
                        "difficulty": difficulty,
                        "type": "quiz_analise_alternativas",
                    },
                )
            )

        return examples

    # -- Casos clínicos -----------------------------------------------------

    def build_from_cases(self, cases_dir: str | pathlib.Path) -> List[TrainingExample]:
        """Converte casos clínicos em exemplos de treinamento.

        Espera arquivos JSON com schema:
            patient, history, ecg_findings, diagnosis, management

        Parameters
        ----------
        cases_dir : str | pathlib.Path
            Diretório contendo JSONs de casos clínicos.

        Returns
        -------
        list[TrainingExample]
            Exemplos gerados.
        """
        cases_path = pathlib.Path(cases_dir)
        if not cases_path.exists():
            raise FileNotFoundError(
                f"Diretório de casos clínicos não encontrado: {cases_path}"
            )

        new_examples: List[TrainingExample] = []
        json_files = sorted(cases_path.rglob("*.json"))

        for fpath in json_files:
            try:
                data = json.loads(fpath.read_text(encoding="utf-8"))
                examples = self._case_to_examples(data, source=str(fpath))
                new_examples.extend(examples)
            except (json.JSONDecodeError, KeyError) as exc:
                logger.warning("Erro ao processar caso %s: %s", fpath, exc)
                continue

        self.examples.extend(new_examples)
        logger.info(
            "Casos: %d arquivos processados, %d exemplos gerados",
            len(json_files),
            len(new_examples),
        )
        return new_examples

    def _case_to_examples(
        self, data: Dict[str, Any], source: str = ""
    ) -> List[TrainingExample]:
        """Converte um caso clínico em exemplos de treinamento."""
        examples: List[TrainingExample] = []

        patient = data.get("patient", "Paciente não identificado")
        history = data.get("history", "")
        ecg_findings = data.get("ecg_findings", "")
        diagnosis = data.get("diagnosis", "")
        management = data.get("management", "")

        if not (history and ecg_findings and diagnosis):
            return examples

        # Exemplo: Diagnóstico a partir do ECG
        instruction = (
            "Você é um cardiologista experiente. "
            "Com base na história clínica e nos achados do ECG, "
            "forneça o diagnóstico e a conduta."
        )
        input_text = (
            f"Paciente: {patient}\n"
            f"História: {history}\n"
            f"Achados no ECG: {ecg_findings}"
        )
        output_text = f"Diagnóstico: {diagnosis}"
        if management:
            output_text += f"\n\nConduta: {management}"

        examples.append(
            TrainingExample(
                instruction=instruction,
                input=input_text,
                output=output_text,
                metadata={
                    "source": source,
                    "type": "caso_clinico",
                },
            )
        )

        return examples

    # -- Aulas / Lições -----------------------------------------------------

    def build_from_lessons(
        self, lessons_dir: str | pathlib.Path
    ) -> List[TrainingExample]:
        """Converte conteúdo de aulas em pares de pergunta-resposta.

        Espera arquivos JSON com schema:
            title, content, key_points (list of str)

        Gera perguntas didáticas a partir dos pontos-chave.

        Parameters
        ----------
        lessons_dir : str | pathlib.Path
            Diretório contendo JSONs de aulas.

        Returns
        -------
        list[TrainingExample]
            Exemplos gerados.
        """
        lessons_path = pathlib.Path(lessons_dir)
        if not lessons_path.exists():
            raise FileNotFoundError(
                f"Diretório de aulas não encontrado: {lessons_path}"
            )

        new_examples: List[TrainingExample] = []
        json_files = sorted(lessons_path.rglob("*.json"))

        for fpath in json_files:
            try:
                data = json.loads(fpath.read_text(encoding="utf-8"))
                examples = self._lesson_to_examples(data, source=str(fpath))
                new_examples.extend(examples)
            except (json.JSONDecodeError, KeyError) as exc:
                logger.warning("Erro ao processar aula %s: %s", fpath, exc)
                continue

        self.examples.extend(new_examples)
        logger.info(
            "Aulas: %d arquivos processados, %d exemplos gerados",
            len(json_files),
            len(new_examples),
        )
        return new_examples

    def _lesson_to_examples(
        self, data: Dict[str, Any], source: str = ""
    ) -> List[TrainingExample]:
        """Converte uma aula em exemplos de pergunta-resposta."""
        examples: List[TrainingExample] = []

        title = data.get("title", "")
        content = data.get("content", "")
        key_points = data.get("key_points", [])

        if not title or not content:
            return examples

        # Exemplo: Resumo da aula
        instruction = (
            "Você é um professor de eletrocardiografia. "
            "Resuma o conteúdo da aula a seguir, destacando os pontos principais."
        )
        input_text = f"Aula: {title}\n\n{content}"
        if key_points:
            points_text = "\n".join(f"  - {p}" for p in key_points)
            output_text = (
                f"Resumo da aula '{title}':\n\n"
                f"Pontos-chave:\n{points_text}"
            )
        else:
            output_text = f"Resumo da aula '{title}':\n\n{content[:500]}"

        examples.append(
            TrainingExample(
                instruction=instruction,
                input=input_text,
                output=output_text,
                metadata={
                    "source": source,
                    "type": "aula_resumo",
                    "title": title,
                },
            )
        )

        # Exemplo por ponto-chave
        for i, point in enumerate(key_points):
            if len(point.strip()) < 10:
                continue
            instruction_kp = (
                "Você é um especialista em ECG. "
                "Explique o seguinte conceito de eletrocardiografia."
            )
            examples.append(
                TrainingExample(
                    instruction=instruction_kp,
                    input=f"Conceito: {point}",
                    output=(
                        f"No contexto de '{title}': {point}\n\n"
                        f"Este é um ponto importante na interpretação "
                        f"de eletrocardiogramas."
                    ),
                    metadata={
                        "source": source,
                        "type": "aula_ponto_chave",
                        "title": title,
                        "key_point_index": i,
                    },
                )
            )

        return examples

    # -- Filtros e exportação ------------------------------------------------

    def filter_quality(self, min_output_length: int = 20) -> int:
        """Remove exemplos de baixa qualidade.

        Critérios:
          - output com menos de min_output_length caracteres
          - instruction ou input vazios
          - campos com conteúdo muito repetitivo

        Returns
        -------
        int
            Número de exemplos removidos.
        """
        before = len(self.examples)
        filtered: List[TrainingExample] = []

        for ex in self.examples:
            # Campos não podem ser vazios
            if not ex.instruction.strip() or not ex.input.strip():
                continue
            # Output mínimo
            if len(ex.output.strip()) < min_output_length:
                continue
            # Verificar repetição excessiva (mesmo caractere > 80%)
            if ex.output.strip():
                most_common_ratio = max(
                    ex.output.count(c) for c in set(ex.output)
                ) / len(ex.output)
                if most_common_ratio > 0.8:
                    continue

            filtered.append(ex)

        self.examples = filtered
        removed = before - len(self.examples)
        logger.info("Filtro de qualidade: %d exemplos removidos", removed)
        return removed

    def deduplicate(self) -> int:
        """Remove exemplos duplicados baseado em hash de conteúdo.

        Returns
        -------
        int
            Número de duplicatas removidas.
        """
        before = len(self.examples)
        seen: set[str] = set()
        unique: List[TrainingExample] = []

        for ex in self.examples:
            h = ex.content_hash()
            if h not in seen:
                seen.add(h)
                unique.append(ex)

        self.examples = unique
        removed = before - len(self.examples)
        logger.info("Deduplicação: %d duplicatas removidas", removed)
        return removed

    def export_jsonl(self, output_path: str | pathlib.Path) -> int:
        """Exporta exemplos para arquivo JSONL.

        O formato é compatível com frameworks de fine-tuning LoRA
        (ex.: Axolotl, LLaMA-Factory, etc.).

        Parameters
        ----------
        output_path : str | pathlib.Path
            Caminho do arquivo JSONL de saída.

        Returns
        -------
        int
            Número de exemplos exportados.
        """
        output = pathlib.Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        with output.open("w", encoding="utf-8") as f:
            for ex in self.examples:
                line = json.dumps(ex.to_dict(), ensure_ascii=False)
                f.write(line + "\n")

        logger.info("Exportado %d exemplos para %s", len(self.examples), output)
        return len(self.examples)

    def stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do dataset atual."""
        if not self.examples:
            return {"total": 0, "por_tipo": {}, "por_dificuldade": {}, "por_topico": {}}

        by_type: Dict[str, int] = {}
        by_difficulty: Dict[str, int] = {}
        by_topic: Dict[str, int] = {}

        for ex in self.examples:
            t = ex.metadata.get("type", "desconhecido")
            by_type[t] = by_type.get(t, 0) + 1

            d = ex.metadata.get("difficulty", "")
            if d:
                by_difficulty[d] = by_difficulty.get(d, 0) + 1

            topic = ex.metadata.get("topic", "")
            if topic:
                by_topic[topic] = by_topic.get(topic, 0) + 1

        return {
            "total": len(self.examples),
            "por_tipo": by_type,
            "por_dificuldade": by_difficulty,
            "por_topico": by_topic,
        }

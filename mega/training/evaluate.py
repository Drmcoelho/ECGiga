"""
mega.training.evaluate — Utilitários de avaliação para fine-tuning.

Fornece métricas de perplexidade, verificação de acurácia médica
via checklist, e geração de relatórios de avaliação em português.
"""

from __future__ import annotations

import logging
import math
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence

logger = logging.getLogger(__name__)


def evaluate_perplexity(
    model: Any,
    dataset: List[Dict[str, str]],
    tokenizer: Any = None,
    max_length: int = 2048,
) -> Dict[str, float]:
    """Calcula a perplexidade do modelo em um dataset.

    Funciona com modelos HuggingFace (transformers) ou aceita
    listas de log-probabilidades pré-calculadas.

    Parameters
    ----------
    model : Any
        Modelo HuggingFace ou lista de float (log-probs por exemplo).
    dataset : list[dict]
        Lista de exemplos com campos 'instruction', 'input', 'output',
        ou lista de floats representando log-probabilidades.
    tokenizer : Any, optional
        Tokenizer HuggingFace (necessário se model for um modelo real).
    max_length : int
        Comprimento máximo de sequência.

    Returns
    -------
    dict
        Dicionário com 'perplexity', 'avg_loss', 'num_examples'.
    """
    # Se receber log-probabilidades diretamente (para testes / avaliação offline)
    if isinstance(model, (list, tuple)):
        log_probs = model
        if not log_probs:
            return {"perplexity": float("inf"), "avg_loss": float("inf"), "num_examples": 0}
        avg_neg_log_prob = -sum(log_probs) / len(log_probs)
        ppl = math.exp(min(avg_neg_log_prob, 100))  # cap para evitar overflow
        return {
            "perplexity": round(ppl, 4),
            "avg_loss": round(avg_neg_log_prob, 4),
            "num_examples": len(log_probs),
        }

    # Treinamento com modelo HuggingFace real
    try:
        import torch
        from torch.utils.data import DataLoader
    except ImportError:
        logger.warning("PyTorch não disponível. Retornando perplexidade estimada.")
        return {
            "perplexity": float("nan"),
            "avg_loss": float("nan"),
            "num_examples": len(dataset),
            "nota": "PyTorch não instalado — instale com: pip install torch",
        }

    model.eval()
    total_loss = 0.0
    total_tokens = 0

    with torch.no_grad():
        for example in dataset:
            text = (
                f"### Instrução:\n{example.get('instruction', '')}\n\n"
                f"### Entrada:\n{example.get('input', '')}\n\n"
                f"### Resposta:\n{example.get('output', '')}"
            )
            inputs = tokenizer(
                text,
                return_tensors="pt",
                truncation=True,
                max_length=max_length,
            ).to(model.device)

            outputs = model(**inputs, labels=inputs["input_ids"])
            total_loss += outputs.loss.item() * inputs["input_ids"].shape[1]
            total_tokens += inputs["input_ids"].shape[1]

    avg_loss = total_loss / max(total_tokens, 1)
    ppl = math.exp(min(avg_loss, 100))

    return {
        "perplexity": round(ppl, 4),
        "avg_loss": round(avg_loss, 4),
        "num_examples": len(dataset),
    }


def evaluate_medical_checklist(
    responses: List[str],
    checklist: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Avalia respostas do modelo contra um checklist de acurácia médica.

    Cada item do checklist deve ter:
      - id: identificador único
      - categoria: categoria do item (ex.: "ritmo", "frequência")
      - descricao: descrição do critério
      - palavras_chave: lista de termos que devem aparecer na resposta
      - obrigatorio: bool indicando se o item é obrigatório

    Parameters
    ----------
    responses : list[str]
        Lista de respostas geradas pelo modelo.
    checklist : list[dict]
        Lista de itens do checklist médico.

    Returns
    -------
    dict
        Resultado da avaliação com score, itens aprovados/reprovados.
    """
    if not responses:
        return {
            "score": 0.0,
            "total_itens": len(checklist),
            "itens_avaliados": 0,
            "aprovados": [],
            "reprovados": [],
            "taxa_aprovacao": 0.0,
        }

    # Concatenar todas as respostas para busca
    all_text = " ".join(responses).lower()

    approved: List[Dict[str, Any]] = []
    failed: List[Dict[str, Any]] = []

    for item in checklist:
        item_id = item.get("id", "?")
        keywords = item.get("palavras_chave", [])
        required = item.get("obrigatorio", False)
        description = item.get("descricao", "")
        category = item.get("categoria", "")

        # Verificar se pelo menos uma palavra-chave está presente
        found_keywords = []
        for kw in keywords:
            # Busca case-insensitive com suporte a acentos
            if kw.lower() in all_text:
                found_keywords.append(kw)

        passed = len(found_keywords) > 0 if keywords else False

        result_item = {
            "id": item_id,
            "categoria": category,
            "descricao": description,
            "obrigatorio": required,
            "aprovado": passed,
            "palavras_encontradas": found_keywords,
            "palavras_esperadas": keywords,
        }

        if passed:
            approved.append(result_item)
        else:
            failed.append(result_item)

    total = len(checklist)
    score = len(approved) / max(total, 1)

    # Verificar itens obrigatórios
    mandatory_failed = [
        item for item in failed if item.get("obrigatorio", False)
    ]

    return {
        "score": round(score, 4),
        "total_itens": total,
        "itens_avaliados": total,
        "aprovados": approved,
        "reprovados": failed,
        "taxa_aprovacao": round(score * 100, 2),
        "itens_obrigatorios_reprovados": len(mandatory_failed),
        "aprovacao_geral": len(mandatory_failed) == 0,
    }


def generate_evaluation_report(results: Dict[str, Any]) -> str:
    """Gera um relatório formatado de avaliação em português.

    Parameters
    ----------
    results : dict
        Resultados da avaliação (de evaluate_perplexity e/ou
        evaluate_medical_checklist).

    Returns
    -------
    str
        Relatório formatado em texto.
    """
    lines: List[str] = []
    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    lines.append("=" * 60)
    lines.append("  RELATÓRIO DE AVALIAÇÃO — ECGiga Fine-Tuning")
    lines.append(f"  Data: {timestamp}")
    lines.append("=" * 60)
    lines.append("")

    # Perplexidade
    if "perplexity" in results:
        lines.append("--- Perplexidade ---")
        ppl = results["perplexity"]
        avg_loss = results.get("avg_loss", "N/A")
        n_examples = results.get("num_examples", "N/A")
        lines.append(f"  Perplexidade:      {ppl}")
        lines.append(f"  Loss médio:        {avg_loss}")
        lines.append(f"  Exemplos avaliados: {n_examples}")
        lines.append("")

    # Checklist médico
    if "score" in results:
        lines.append("--- Checklist de Acurácia Médica ---")
        lines.append(f"  Score:             {results['score']:.2%}")
        lines.append(f"  Taxa de aprovação: {results.get('taxa_aprovacao', 0):.1f}%")
        lines.append(
            f"  Itens avaliados:   {results.get('itens_avaliados', 0)} "
            f"de {results.get('total_itens', 0)}"
        )
        lines.append("")

        approved = results.get("aprovados", [])
        if approved:
            lines.append("  Itens APROVADOS:")
            for item in approved:
                cat = item.get("categoria", "")
                desc = item.get("descricao", "")
                req = " [OBRIGATÓRIO]" if item.get("obrigatorio") else ""
                lines.append(f"    [OK] {cat}: {desc}{req}")
            lines.append("")

        failed = results.get("reprovados", [])
        if failed:
            lines.append("  Itens REPROVADOS:")
            for item in failed:
                cat = item.get("categoria", "")
                desc = item.get("descricao", "")
                req = " [OBRIGATÓRIO]" if item.get("obrigatorio") else ""
                lines.append(f"    [X]  {cat}: {desc}{req}")
            lines.append("")

        mandatory_failed = results.get("itens_obrigatorios_reprovados", 0)
        if mandatory_failed > 0:
            lines.append(
                f"  ATENÇÃO: {mandatory_failed} item(ns) obrigatório(s) "
                f"não foram atendidos."
            )
            lines.append("")

        overall = results.get("aprovacao_geral", False)
        status = "APROVADO" if overall else "REPROVADO"
        lines.append(f"  Status geral: {status}")
        lines.append("")

    lines.append("=" * 60)
    lines.append("  Fim do relatório")
    lines.append("=" * 60)

    return "\n".join(lines)

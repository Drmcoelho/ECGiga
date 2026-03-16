"""
Orquestrador Multi-LLM para geração de casos clínicos de ECG.

Pipeline: draft (local/offline) -> refine (cloud) -> verify (regras)

Funcionalidades:
- Suporte a múltiplos backends com fallback gracioso
- Cache de resultados para evitar chamadas redundantes
- Verificação factual automática
- Geração funciona mesmo sem conexão (modo offline)

Refs: GitHub issue #20
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from typing import Any

from .backends import (
    LLMBackend,
    OllamaBackend,
    GeminiBackend,
    OpenAIBackend,
    OfflineBackend,
)
from .verify import CaseVerifier, DISCLAIMER_PT

logger = logging.getLogger(__name__)


class CaseOrchestrator:
    """Orquestrador multi-LLM para geração de casos clínicos de ECG.

    Implementa um pipeline de três estágios:
    1. **Draft** — Rascunho inicial usando backend local (Ollama) ou offline
    2. **Refine** — Refinamento usando backend cloud (Gemini/OpenAI) se disponível
    3. **Verify** — Verificação factual usando regras determinísticas

    Parameters
    ----------
    draft_backend : LLMBackend | None
        Backend para rascunho. Se None, tenta Ollama, depois offline.
    refine_backend : LLMBackend | None
        Backend para refinamento. Se None, tenta Gemini, depois OpenAI.
    enable_cache : bool
        Habilitar cache de resultados (padrão: True).
    cache_ttl : int
        Tempo de vida do cache em segundos (padrão: 3600 = 1 hora).
    strict_verify : bool
        Modo estrito de verificação (padrão: False).
    """

    def __init__(
        self,
        draft_backend: LLMBackend | None = None,
        refine_backend: LLMBackend | None = None,
        enable_cache: bool = True,
        cache_ttl: int = 3600,
        strict_verify: bool = False,
    ) -> None:
        self._offline = OfflineBackend()
        self._draft_backend = draft_backend
        self._refine_backend = refine_backend
        self._verifier = CaseVerifier(strict=strict_verify)
        self._enable_cache = enable_cache
        self._cache_ttl = cache_ttl
        self._cache: dict[str, dict[str, Any]] = {}

        # Inicializar backends padrão se não fornecidos
        if self._draft_backend is None:
            self._draft_backend = self._init_draft_backend()
        if self._refine_backend is None:
            self._refine_backend = self._init_refine_backend()

    def _init_draft_backend(self) -> LLMBackend:
        """Tenta inicializar o melhor backend disponível para draft."""
        ollama = OllamaBackend()
        if ollama.is_available():
            logger.info("Usando Ollama/Mistral como backend de draft")
            return ollama
        logger.info("Ollama não disponível — usando backend offline para draft")
        return self._offline

    def _init_refine_backend(self) -> LLMBackend | None:
        """Tenta inicializar o melhor backend disponível para refinamento."""
        gemini = GeminiBackend()
        if gemini.is_available():
            logger.info("Usando Gemini como backend de refinamento")
            return gemini

        openai = OpenAIBackend()
        if openai.is_available():
            logger.info("Usando OpenAI como backend de refinamento")
            return openai

        logger.info("Nenhum backend cloud disponível — refinamento será offline")
        return None

    # ------------------------------------------------------------------
    # Cache
    # ------------------------------------------------------------------

    def _cache_key(self, topic: str, difficulty: str, language: str) -> str:
        """Gera chave de cache para os parâmetros."""
        raw = f"{topic}|{difficulty}|{language}"
        return hashlib.md5(raw.encode()).hexdigest()

    def _get_cached(self, key: str) -> dict[str, Any] | None:
        """Retorna resultado do cache se válido."""
        if not self._enable_cache:
            return None
        entry = self._cache.get(key)
        if entry is None:
            return None
        if time.time() - entry.get("_timestamp", 0) > self._cache_ttl:
            del self._cache[key]
            return None
        return entry

    def _set_cache(self, key: str, result: dict[str, Any]) -> None:
        """Armazena resultado no cache."""
        if not self._enable_cache:
            return
        result_copy = dict(result)
        result_copy["_timestamp"] = time.time()
        self._cache[key] = result_copy

    def clear_cache(self) -> None:
        """Limpa todo o cache."""
        self._cache.clear()

    # ------------------------------------------------------------------
    # Pipeline principal
    # ------------------------------------------------------------------

    def draft_case(
        self,
        topic: str,
        difficulty: str = "medium",
        language: str = "pt",
    ) -> dict[str, Any]:
        """Gera um caso clínico completo usando o pipeline draft-refine-verify.

        Parameters
        ----------
        topic : str
            Tópico do caso (ex. "STEMI", "Fibrilação Atrial", "Bradicardia").
        difficulty : str
            Nível de dificuldade: "easy", "medium", "hard".
        language : str
            Idioma do caso (padrão: "pt" — Português do Brasil).

        Returns
        -------
        dict
            Caso clínico completo com chaves:
            - Todos os campos do caso clínico
            - ``pipeline`` (dict): metadados do pipeline executado
            - ``verification`` (dict): resultado da verificação
            - ``disclaimer`` (str): disclaimer obrigatório
        """
        # Verificar cache
        cache_key = self._cache_key(topic, difficulty, language)
        cached = self._get_cached(cache_key)
        if cached is not None:
            logger.info("Caso retornado do cache para topic=%s", topic)
            cached_copy = dict(cached)
            cached_copy.pop("_timestamp", None)
            cached_copy.setdefault("pipeline", {})["from_cache"] = True
            return cached_copy

        pipeline_info: dict[str, Any] = {
            "draft_backend": "none",
            "refine_backend": "none",
            "from_cache": False,
        }

        # Etapa 1: Draft
        case = self._stage_draft(topic, difficulty, language, pipeline_info)

        # Etapa 2: Refine
        case = self._stage_refine(case, pipeline_info)

        # Etapa 3: Verify
        verification = self._stage_verify(case)

        # Montar resultado final
        result = dict(case)
        result["pipeline"] = pipeline_info
        result["verification"] = {
            "valid": verification["valid"],
            "score": verification["score"],
            "errors": verification["errors"],
            "warnings": verification["warnings"],
        }
        result["disclaimer"] = DISCLAIMER_PT

        # Cachear
        self._set_cache(cache_key, result)

        return result

    def _stage_draft(
        self,
        topic: str,
        difficulty: str,
        language: str,
        pipeline_info: dict[str, Any],
    ) -> dict[str, Any]:
        """Etapa 1: Gerar rascunho do caso."""
        backend = self._draft_backend or self._offline

        try:
            case = backend.generate_case(topic, difficulty, language)
            pipeline_info["draft_backend"] = backend.name
            logger.info("Draft gerado com backend: %s", backend.name)
            return case
        except Exception as exc:
            logger.warning(
                "Falha no draft com %s: %s — usando fallback offline",
                backend.name,
                exc,
            )

        # Fallback para offline
        case = self._offline.generate_case(topic, difficulty, language)
        pipeline_info["draft_backend"] = "offline (fallback)"
        return case

    def _stage_refine(
        self,
        case: dict[str, Any],
        pipeline_info: dict[str, Any],
    ) -> dict[str, Any]:
        """Etapa 2: Refinar caso usando backend cloud."""
        if self._refine_backend is None:
            pipeline_info["refine_backend"] = "none"
            return case

        if not self._refine_backend.is_available():
            pipeline_info["refine_backend"] = "unavailable"
            # Tentar refinamento offline
            refined = self._offline.refine_case(case)
            pipeline_info["refine_backend"] = "offline (fallback)"
            return refined

        try:
            refined = self._refine_backend.refine_case(case)
            pipeline_info["refine_backend"] = self._refine_backend.name
            logger.info("Caso refinado com backend: %s", self._refine_backend.name)
            return refined
        except Exception as exc:
            logger.warning(
                "Falha no refinamento com %s: %s — mantendo draft original",
                self._refine_backend.name,
                exc,
            )
            # Tentar refinamento offline como fallback
            try:
                refined = self._offline.refine_case(case)
                pipeline_info["refine_backend"] = "offline (fallback)"
                return refined
            except Exception:
                pipeline_info["refine_backend"] = "failed"
                return case

    def _stage_verify(self, case: dict[str, Any]) -> dict[str, Any]:
        """Etapa 3: Verificar caso com regras determinísticas."""
        return self._verifier.verify(case)

    # ------------------------------------------------------------------
    # Métodos auxiliares
    # ------------------------------------------------------------------

    def draft_case_offline(
        self,
        topic: str,
        difficulty: str = "medium",
        language: str = "pt",
    ) -> dict[str, Any]:
        """Gera caso usando apenas o backend offline (sem APIs).

        Parameters
        ----------
        topic : str
            Tópico do caso.
        difficulty : str
            Dificuldade.
        language : str
            Idioma.

        Returns
        -------
        dict
            Caso clínico com verificação.
        """
        case = self._offline.generate_case(topic, difficulty, language)
        case = self._offline.refine_case(case)
        verification = self._verifier.verify(case)

        result = dict(case)
        result["pipeline"] = {
            "draft_backend": "offline",
            "refine_backend": "offline",
            "from_cache": False,
        }
        result["verification"] = {
            "valid": verification["valid"],
            "score": verification["score"],
            "errors": verification["errors"],
            "warnings": verification["warnings"],
        }
        result["disclaimer"] = DISCLAIMER_PT
        return result

    def get_available_backends(self) -> dict[str, bool]:
        """Retorna status de disponibilidade de cada backend.

        Returns
        -------
        dict[str, bool]
            Mapeamento de nome do backend para disponibilidade.
        """
        return {
            "ollama": OllamaBackend().is_available(),
            "gemini": GeminiBackend().is_available(),
            "openai": OpenAIBackend().is_available(),
            "offline": True,
        }

    def list_topics(self) -> list[str]:
        """Retorna tópicos disponíveis nos templates.

        Returns
        -------
        list[str]
            Lista de tópicos.
        """
        from .templates import list_topics
        return list_topics()

    @property
    def cache_size(self) -> int:
        """Número de entradas no cache."""
        return len(self._cache)

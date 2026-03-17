"""
Multi-LLM orchestrator for clinical ECG case generation.

Supports multiple backends (local Ollama/Mistral, Gemini, OpenAI, offline)
with a draft-refine-verify pipeline and graceful fallback.

Refs: GitHub issue #20
"""

from __future__ import annotations

from .orchestrator import CaseOrchestrator
from .backends import (
    OllamaBackend,
    GeminiBackend,
    OpenAIBackend,
    OfflineBackend,
)
from .verify import CaseVerifier
from .templates import TEMPLATES, get_template

__all__ = [
    "CaseOrchestrator",
    "OllamaBackend",
    "GeminiBackend",
    "OpenAIBackend",
    "OfflineBackend",
    "CaseVerifier",
    "TEMPLATES",
    "get_template",
]

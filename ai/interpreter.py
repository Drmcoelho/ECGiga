"""
LLM-powered ECG interpreter with multiple backend support.

Phase 22 (p22) - AI/LLM integration for differential diagnosis.
Supports Anthropic (Claude), OpenAI, and an offline rule-based fallback.
"""

from __future__ import annotations

import json
import os
from typing import Any

from .prompts import (
    SYSTEM_PROMPT_INTERPRETER,
    CAMERA_ANALOGY_CONTEXT,
    build_interpretation_prompt,
    build_differential_prompt,
)
from .offline_rules import interpret_report as offline_interpret
from .offline_rules import generate_differential as offline_differential


class ECGInterpreter:
    """Main LLM-powered ECG interpreter.

    Supports multiple backends:
    - ``"anthropic"`` (default): Uses the Anthropic / Claude API.
    - ``"openai"``: Uses the OpenAI API.
    - ``"offline"``: Rule-based interpretation, no API required.

    Parameters
    ----------
    backend : str
        One of ``"anthropic"``, ``"openai"``, ``"offline"``.
    model : str
        Model identifier for the chosen backend.
    api_key : str | None
        API key. If ``None``, will try to read from the appropriate
        environment variable (``ANTHROPIC_API_KEY`` or ``OPENAI_API_KEY``).
    """

    def __init__(
        self,
        backend: str = "anthropic",
        model: str = "claude-sonnet-4-20250514",
        api_key: str | None = None,
    ) -> None:
        self.backend = backend.lower()
        self.model = model
        self.api_key = api_key
        self._conversation_history: list[dict[str, str]] = []

        # Resolve API key from environment if not provided
        if self.api_key is None:
            if self.backend == "anthropic":
                self.api_key = os.environ.get("ANTHROPIC_API_KEY")
            elif self.backend == "openai":
                self.api_key = os.environ.get("OPENAI_API_KEY")

    def interpret(self, report: dict) -> dict:
        """Full interpretation of an ECG report.

        Parameters
        ----------
        report : dict
            ECG report dictionary (ECGiga schema).

        Returns
        -------
        dict
            ``{"interpretation": str, "differentials": list, "recommendations": list, "confidence": str}``
        """
        if self.backend == "offline":
            return self._call_offline_interpret(report)

        prompt = build_interpretation_prompt(report)
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT_INTERPRETER},
            {"role": "user", "content": prompt},
        ]

        try:
            response = self._dispatch(messages)
            return self._parse_interpretation_response(response)
        except Exception as e:
            # Fallback to offline on any API error
            result = offline_interpret(report)
            result["interpretation"] += (
                f"\n\n[Nota: Interpretação offline utilizada devido a erro na API: {e}]"
            )
            return result

    def differential_diagnosis(self, findings: list[str]) -> dict:
        """Generate differential diagnosis from ECG findings.

        Parameters
        ----------
        findings : list[str]
            List of ECG findings/abnormalities.

        Returns
        -------
        dict
            ``{"differentials": list[dict], "reasoning": str}``
        """
        if self.backend == "offline":
            diffs = offline_differential(findings)
            return {
                "differentials": diffs,
                "reasoning": "Diagnóstico diferencial gerado por regras offline.",
            }

        prompt = build_differential_prompt(findings)
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT_INTERPRETER},
            {"role": "user", "content": prompt},
        ]

        try:
            response = self._dispatch(messages)
            return {
                "differentials": self._parse_differential_response(response),
                "reasoning": response,
            }
        except Exception as e:
            diffs = offline_differential(findings)
            return {
                "differentials": diffs,
                "reasoning": f"Diagnóstico diferencial offline (erro na API: {e}).",
            }

    def explain_with_cameras(self, report: dict) -> str:
        """Explain the ECG using camera analogies.

        Parameters
        ----------
        report : dict
            ECG report dictionary.

        Returns
        -------
        str
            Human-friendly explanation using camera analogies.
        """
        if self.backend == "offline":
            return self._offline_camera_explanation(report)

        prompt = build_interpretation_prompt(report)
        camera_prompt = (
            f"{CAMERA_ANALOGY_CONTEXT}\n\n"
            f"{prompt}\n\n"
            "Por favor, explique este ECG usando EXCLUSIVAMENTE analogias com "
            "câmera fotográfica. Torne a explicação acessível para leigos."
        )
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT_INTERPRETER},
            {"role": "user", "content": camera_prompt},
        ]

        try:
            return self._dispatch(messages)
        except Exception as e:
            explanation = self._offline_camera_explanation(report)
            return explanation + f"\n\n[Nota: Explicação offline devido a erro na API: {e}]"

    # ------------------------------------------------------------------
    # Backend dispatch
    # ------------------------------------------------------------------

    def _dispatch(self, messages: list[dict[str, str]]) -> str:
        """Route to the appropriate backend."""
        if self.backend == "anthropic":
            return self._call_anthropic(messages)
        elif self.backend == "openai":
            return self._call_openai(messages)
        elif self.backend == "offline":
            # Extract user message for offline processing
            user_msg = next((m["content"] for m in messages if m["role"] == "user"), "")
            return self._call_offline(user_msg)
        else:
            raise ValueError(f"Backend desconhecido: {self.backend}")

    def _call_anthropic(self, messages: list[dict[str, str]]) -> str:
        """Call the Anthropic (Claude) API.

        Parameters
        ----------
        messages : list[dict]
            List of message dicts with ``"role"`` and ``"content"`` keys.

        Returns
        -------
        str
            The model's response text.

        Raises
        ------
        RuntimeError
            If the API key is missing or the API call fails.
        """
        if not self.api_key:
            raise RuntimeError(
                "Chave de API Anthropic não configurada. "
                "Defina a variável de ambiente ANTHROPIC_API_KEY ou passe api_key ao construtor. "
                "Para uso sem API, use backend='offline'."
            )

        try:
            import anthropic
        except ImportError:
            raise RuntimeError(
                "Pacote 'anthropic' não instalado. "
                "Instale com: pip install anthropic"
            )

        client = anthropic.Anthropic(api_key=self.api_key)

        # Separate system prompt from messages
        system_text = ""
        user_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_text = msg["content"]
            else:
                user_messages.append(msg)

        response = client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=system_text,
            messages=user_messages,
        )

        return response.content[0].text

    def _call_openai(self, messages: list[dict[str, str]]) -> str:
        """Call the OpenAI API (optional backend).

        Parameters
        ----------
        messages : list[dict]
            List of message dicts with ``"role"`` and ``"content"`` keys.

        Returns
        -------
        str
            The model's response text.

        Raises
        ------
        RuntimeError
            If the API key is missing or the API call fails.
        """
        if not self.api_key:
            raise RuntimeError(
                "Chave de API OpenAI não configurada. "
                "Defina a variável de ambiente OPENAI_API_KEY ou passe api_key ao construtor. "
                "Para uso sem API, use backend='offline'."
            )

        try:
            import openai
        except ImportError:
            raise RuntimeError(
                "Pacote 'openai' não instalado. "
                "Instale com: pip install openai"
            )

        client = openai.OpenAI(api_key=self.api_key)
        response = client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=4096,
        )

        return response.choices[0].message.content

    def _call_offline(self, prompt: str) -> str:
        """Offline fallback with rule-based interpretation.

        Parameters
        ----------
        prompt : str
            The user prompt text (used for context but the offline engine
            works primarily from structured data).

        Returns
        -------
        str
            A basic interpretation string.
        """
        return (
            "Modo offline ativo — sem acesso a API de LLM.\n"
            "Use o método interpret() com um relatório estruturado para obter "
            "uma interpretação completa baseada em regras.\n\n"
            f"Prompt recebido (primeiros 200 caracteres):\n{prompt[:200]}..."
        )

    # ------------------------------------------------------------------
    # Offline helpers
    # ------------------------------------------------------------------

    def _call_offline_interpret(self, report: dict) -> dict:
        """Run the offline rule-based interpretation."""
        return offline_interpret(report)

    def _offline_camera_explanation(self, report: dict) -> str:
        """Generate a camera-analogy explanation using offline rules."""
        result = offline_interpret(report)
        parts = [
            "## Explicação do ECG com Analogias de Câmera\n",
            "Imagine que o coração é fotografado por múltiplas câmeras posicionadas "
            "ao seu redor. Cada derivação do ECG é uma dessas câmeras.\n",
        ]

        # Extract camera notes from interpretation
        interp = result["interpretation"]
        if "Analogias com Câmera" in interp:
            camera_section = interp.split("### Analogias com Câmera")[1]
            parts.append(camera_section.strip())
        else:
            parts.append(
                "Todas as câmeras estão funcionando corretamente — cada uma captura "
                "a atividade elétrica exatamente como esperado."
            )

        if result["differentials"]:
            parts.append("\n### O que isso pode significar")
            for d in result["differentials"]:
                parts.append(f"- {d}")

        return "\n".join(parts)

    # ------------------------------------------------------------------
    # Response parsing helpers
    # ------------------------------------------------------------------

    def _parse_interpretation_response(self, response: str) -> dict:
        """Parse a free-text LLM response into the structured format."""
        # Try to extract structured data; fall back to raw text
        interpretation = response
        differentials: list[str] = []
        recommendations: list[str] = []
        confidence = "moderada"

        lines = response.split("\n")
        current_section = "interpretation"

        for line in lines:
            ll = line.lower().strip()
            if any(kw in ll for kw in ("diagnóstico", "diferencial", "differential")):
                current_section = "differentials"
                continue
            if any(kw in ll for kw in ("recomendaç", "recommendation")):
                current_section = "recommendations"
                continue
            if "confiança" in ll or "confidence" in ll:
                if "alta" in ll or "high" in ll:
                    confidence = "alta"
                elif "baixa" in ll or "low" in ll:
                    confidence = "baixa"
                else:
                    confidence = "moderada"
                continue

            stripped = line.strip().lstrip("-•*").strip()
            if stripped:
                if current_section == "differentials":
                    differentials.append(stripped)
                elif current_section == "recommendations":
                    recommendations.append(stripped)

        return {
            "interpretation": interpretation,
            "differentials": differentials or ["Consultar texto da interpretação acima."],
            "recommendations": recommendations or ["Correlacionar com quadro clínico."],
            "confidence": confidence,
        }

    def _parse_differential_response(self, response: str) -> list[dict]:
        """Parse differential diagnosis response into structured list."""
        results: list[dict] = []
        lines = response.split("\n")

        for line in lines:
            stripped = line.strip().lstrip("-•*0123456789.)").strip()
            if stripped and len(stripped) > 10:
                results.append({
                    "diagnosis": stripped[:200],
                    "support": "",
                    "camera_analogy": "",
                })

        return results or [{"diagnosis": response[:300], "support": "", "camera_analogy": ""}]

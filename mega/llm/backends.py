"""
Implementações de backends LLM para geração de casos clínicos de ECG.

Backends disponíveis:
- OllamaBackend  — Mistral local via API do Ollama
- GeminiBackend  — Google Gemini API
- OpenAIBackend  — OpenAI API (GPT-4 / GPT-3.5)
- OfflineBackend — Geração baseada em templates (sem dependências externas)

Refs: GitHub issue #20
"""

from __future__ import annotations

import json
import logging
import os
import random
import re
from abc import ABC, abstractmethod
from typing import Any

from .templates import TEMPLATES, get_template

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Prompt base para geração de casos clínicos
# ---------------------------------------------------------------------------

CASE_GENERATION_PROMPT = """\
Você é um especialista em cardiologia e eletrocardiografia, criando casos \
clínicos educacionais de ECG em Português do Brasil.

Gere um caso clínico completo sobre o tópico: {topic}
Dificuldade: {difficulty}
Idioma: {language}

O caso deve conter OBRIGATORIAMENTE:
1. "titulo": Título descritivo do caso
2. "historia": História clínica detalhada (idade, sexo, sintomas, antecedentes, exame físico)
3. "achados_ecg": Dicionário com achados eletrocardiográficos estruturados:
   - "ritmo": descrição do ritmo
   - "fc_bpm": frequência cardíaca (número)
   - "eixo": eixo elétrico
   - "pr_ms": intervalo PR em ms (número ou null)
   - "qrs_ms": duração do QRS em ms (número)
   - "qtc_ms": QTc em ms (número ou null)
   - "st_segment": alterações do segmento ST
   - "ondas_t": descrição das ondas T
   - "outras": outros achados relevantes
4. "diagnostico": Diagnóstico eletrocardiográfico principal
5. "perguntas": Lista com pelo menos 3 perguntas para o aluno
6. "explicacao": Explicação detalhada do caso com raciocínio clínico

Responda APENAS com JSON válido, sem texto adicional.
"""

REFINE_PROMPT = """\
Você é um revisor médico especializado em cardiologia. Revise o seguinte caso \
clínico de ECG e melhore-o:

{case_json}

Instruções de revisão:
1. Verifique a coerência dos achados com o diagnóstico
2. Melhore a história clínica se necessário
3. Garanta que os valores numéricos estão fisiologicamente corretos
4. Adicione detalhes clínicos relevantes se estiverem faltando
5. Melhore as perguntas para serem mais didáticas
6. Enriqueça a explicação com referências a diretrizes quando possível

Responda APENAS com o JSON revisado e melhorado, sem texto adicional.
"""


# ---------------------------------------------------------------------------
# Classe base abstrata
# ---------------------------------------------------------------------------

class LLMBackend(ABC):
    """Interface abstrata para backends LLM."""

    name: str = "base"

    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Envia prompt ao LLM e retorna texto de resposta.

        Parameters
        ----------
        prompt : str
            Prompt a enviar.

        Returns
        -------
        str
            Resposta do modelo.

        Raises
        ------
        ConnectionError
            Se o backend não estiver disponível.
        """

    @abstractmethod
    def is_available(self) -> bool:
        """Verifica se o backend está disponível.

        Returns
        -------
        bool
            True se o backend pode ser utilizado.
        """

    def generate_case(
        self,
        topic: str,
        difficulty: str = "medium",
        language: str = "pt",
    ) -> dict[str, Any]:
        """Gera um caso clínico como dicionário.

        Parameters
        ----------
        topic : str
            Tópico do caso (ex. "STEMI", "Fibrilação Atrial").
        difficulty : str
            Nível de dificuldade: "easy", "medium", "hard".
        language : str
            Idioma do caso (padrão: "pt" — Português).

        Returns
        -------
        dict
            Caso clínico estruturado.
        """
        prompt = CASE_GENERATION_PROMPT.format(
            topic=topic,
            difficulty=difficulty,
            language=language,
        )
        raw = self.generate(prompt)
        return self._parse_json_response(raw)

    def refine_case(self, case: dict[str, Any]) -> dict[str, Any]:
        """Refina um caso clínico existente.

        Parameters
        ----------
        case : dict
            Caso clínico a refinar.

        Returns
        -------
        dict
            Caso refinado.
        """
        case_json = json.dumps(case, ensure_ascii=False, indent=2)
        prompt = REFINE_PROMPT.format(case_json=case_json)
        raw = self.generate(prompt)
        refined = self._parse_json_response(raw)
        # Preservar campos originais se refinamento falhar parcialmente
        for key in case:
            if key not in refined:
                refined[key] = case[key]
        return refined

    @staticmethod
    def _parse_json_response(text: str) -> dict[str, Any]:
        """Tenta extrair JSON válido da resposta do LLM.

        Parameters
        ----------
        text : str
            Texto da resposta que pode conter JSON embutido.

        Returns
        -------
        dict
            Dicionário parseado.

        Raises
        ------
        ValueError
            Se não for possível extrair JSON válido.
        """
        # Tentar parse direto
        text = text.strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Tentar extrair bloco JSON de markdown
        json_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1).strip())
            except json.JSONDecodeError:
                pass

        # Tentar encontrar { ... } no texto
        brace_match = re.search(r"\{.*\}", text, re.DOTALL)
        if brace_match:
            try:
                return json.loads(brace_match.group(0))
            except json.JSONDecodeError:
                pass

        raise ValueError(f"Não foi possível extrair JSON válido da resposta do LLM: {text[:200]}...")


# ---------------------------------------------------------------------------
# OllamaBackend — Mistral local via Ollama
# ---------------------------------------------------------------------------

class OllamaBackend(LLMBackend):
    """Backend local usando Ollama com modelo Mistral.

    Parameters
    ----------
    model : str
        Nome do modelo no Ollama (padrão: "mistral").
    base_url : str
        URL base da API do Ollama (padrão: "http://localhost:11434").
    timeout : int
        Timeout em segundos para requisições.
    """

    name = "ollama"

    def __init__(
        self,
        model: str = "mistral",
        base_url: str | None = None,
        timeout: int = 120,
    ) -> None:
        self.model = model
        self.base_url = base_url or os.environ.get(
            "OLLAMA_BASE_URL", "http://localhost:11434"
        )
        self.timeout = timeout

    def is_available(self) -> bool:
        """Verifica se Ollama está rodando localmente."""
        try:
            import urllib.request
            req = urllib.request.Request(
                f"{self.base_url}/api/tags",
                method="GET",
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read())
                models = [m.get("name", "") for m in data.get("models", [])]
                return any(self.model in m for m in models)
        except Exception:
            return False

    def generate(self, prompt: str) -> str:
        """Gera texto usando Ollama API."""
        import urllib.request

        payload = json.dumps({
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "num_predict": 4096,
            },
        }).encode("utf-8")

        req = urllib.request.Request(
            f"{self.base_url}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read())
                return data.get("response", "")
        except Exception as exc:
            raise ConnectionError(
                f"Erro ao conectar ao Ollama em {self.base_url}: {exc}"
            ) from exc


# ---------------------------------------------------------------------------
# GeminiBackend — Google Gemini API
# ---------------------------------------------------------------------------

class GeminiBackend(LLMBackend):
    """Backend usando Google Gemini API.

    Parameters
    ----------
    api_key : str | None
        Chave de API do Google Gemini. Se None, busca em GEMINI_API_KEY.
    model : str
        Modelo a usar (padrão: "gemini-pro").
    """

    name = "gemini"

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gemini-pro",
    ) -> None:
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY", "")
        self.model = model
        self._base_url = "https://generativelanguage.googleapis.com/v1beta"

    def is_available(self) -> bool:
        """Verifica se a API key está configurada."""
        return bool(self.api_key)

    def generate(self, prompt: str) -> str:
        """Gera texto usando Gemini API."""
        if not self.api_key:
            raise ConnectionError("GEMINI_API_KEY não configurada")

        import urllib.request

        url = (
            f"{self._base_url}/models/{self.model}:generateContent"
            f"?key={self.api_key}"
        )

        payload = json.dumps({
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 4096,
            },
        }).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read())
                candidates = data.get("candidates", [])
                if candidates:
                    content = candidates[0].get("content", {})
                    parts = content.get("parts", [])
                    if parts:
                        return parts[0].get("text", "")
                return ""
        except Exception as exc:
            raise ConnectionError(
                f"Erro ao conectar à API Gemini: {exc}"
            ) from exc


# ---------------------------------------------------------------------------
# OpenAIBackend — OpenAI API
# ---------------------------------------------------------------------------

class OpenAIBackend(LLMBackend):
    """Backend usando OpenAI API (GPT-4 / GPT-3.5).

    Parameters
    ----------
    api_key : str | None
        Chave de API da OpenAI. Se None, busca em OPENAI_API_KEY.
    model : str
        Modelo a usar (padrão: "gpt-4").
    """

    name = "openai"

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gpt-4",
    ) -> None:
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.model = model

    def is_available(self) -> bool:
        """Verifica se a API key está configurada."""
        return bool(self.api_key)

    def generate(self, prompt: str) -> str:
        """Gera texto usando OpenAI API."""
        if not self.api_key:
            raise ConnectionError("OPENAI_API_KEY não configurada")

        import urllib.request

        url = "https://api.openai.com/v1/chat/completions"

        payload = json.dumps({
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Você é um especialista em cardiologia e ECG. "
                        "Responda sempre em Português do Brasil."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.7,
            "max_tokens": 4096,
        }).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read())
                choices = data.get("choices", [])
                if choices:
                    return choices[0].get("message", {}).get("content", "")
                return ""
        except Exception as exc:
            raise ConnectionError(
                f"Erro ao conectar à API OpenAI: {exc}"
            ) from exc


# ---------------------------------------------------------------------------
# OfflineBackend — Template-based, sem dependências externas
# ---------------------------------------------------------------------------

class OfflineBackend(LLMBackend):
    """Backend offline baseado em templates pré-definidos.

    Sempre funciona, sem necessidade de API keys ou serviços externos.
    Utiliza os templates de ``templates.py`` para gerar casos, com
    variações aleatórias para diversidade.
    """

    name = "offline"

    def __init__(self) -> None:
        self._variation_names_m = [
            "João", "Pedro", "Carlos", "Antônio", "Francisco",
            "José", "Marcos", "Paulo", "Rafael", "Lucas",
        ]
        self._variation_names_f = [
            "Maria", "Ana", "Joana", "Fernanda", "Beatriz",
            "Carla", "Lúcia", "Patrícia", "Sandra", "Teresa",
        ]

    def is_available(self) -> bool:
        """Sempre disponível."""
        return True

    def generate(self, prompt: str) -> str:
        """Retorna JSON de um template como string.

        O prompt é analisado para extrair tópico e dificuldade.
        """
        topic, difficulty = self._extract_topic_difficulty(prompt)
        case = self.generate_case(topic, difficulty)
        return json.dumps(case, ensure_ascii=False, indent=2)

    def generate_case(
        self,
        topic: str,
        difficulty: str = "medium",
        language: str = "pt",
    ) -> dict[str, Any]:
        """Gera caso a partir de templates com variações.

        Parameters
        ----------
        topic : str
            Tópico do caso (busca parcial nos templates).
        difficulty : str
            Dificuldade desejada.
        language : str
            Idioma (ignorado — sempre português).

        Returns
        -------
        dict
            Caso clínico estruturado.
        """
        template = get_template(topic=topic, difficulty=difficulty)
        case = self._apply_variations(dict(template))
        case["backend"] = "offline"
        case["topico"] = template.get("topico", topic)
        case["dificuldade"] = template.get("dificuldade", difficulty)
        return case

    def refine_case(self, case: dict[str, Any]) -> dict[str, Any]:
        """No modo offline, o refinamento é um pass-through.

        Adiciona pequenas melhorias textuais se possível.
        """
        refined = dict(case)
        # Garantir que campos essenciais existem
        if "explicacao" in refined and isinstance(refined["explicacao"], str):
            if "diretriz" not in refined["explicacao"].lower():
                refined["explicacao"] += (
                    " Sempre consultar as diretrizes vigentes da Sociedade "
                    "Brasileira de Cardiologia (SBC) e do American Heart "
                    "Association (AHA) para condutas atualizadas."
                )
        return refined

    def _apply_variations(self, case: dict[str, Any]) -> dict[str, Any]:
        """Aplica variações aleatórias a um template para diversidade."""
        result = dict(case)

        historia = result.get("historia", "")
        if isinstance(historia, str):
            # Variar ligeiramente a idade (+-5 anos)
            age_match = re.search(r"(\d+)\s*anos", historia)
            if age_match:
                original_age = int(age_match.group(1))
                new_age = max(18, original_age + random.randint(-5, 5))
                historia = historia.replace(
                    f"{original_age} anos", f"{new_age} anos", 1
                )

            # Variar PA ligeiramente
            pa_match = re.search(r"PA\s+(\d+)/(\d+)", historia)
            if pa_match:
                sys = int(pa_match.group(1)) + random.randint(-10, 10)
                dia = int(pa_match.group(2)) + random.randint(-5, 5)
                sys = max(80, min(220, sys))
                dia = max(40, min(130, dia))
                historia = historia.replace(
                    pa_match.group(0), f"PA {sys}/{dia}", 1
                )

            result["historia"] = historia

        # Variar ligeiramente FC
        achados = result.get("achados_ecg", {})
        if isinstance(achados, dict) and "fc_bpm" in achados:
            fc = achados["fc_bpm"]
            if isinstance(fc, (int, float)):
                achados["fc_bpm"] = max(20, int(fc + random.randint(-5, 5)))
                result["achados_ecg"] = achados

        return result

    @staticmethod
    def _extract_topic_difficulty(prompt: str) -> tuple[str, str]:
        """Extrai tópico e dificuldade do prompt."""
        topic = ""
        difficulty = "medium"

        # Extrair tópico
        topic_match = re.search(
            r"(?:tópico|topic|sobre)[:\s]+(.+?)(?:\n|$)", prompt, re.IGNORECASE
        )
        if topic_match:
            topic = topic_match.group(1).strip()

        # Extrair dificuldade
        diff_match = re.search(
            r"(?:dificuldade|difficulty)[:\s]+(easy|medium|hard|fácil|médio|difícil)",
            prompt,
            re.IGNORECASE,
        )
        if diff_match:
            d = diff_match.group(1).lower()
            diff_map = {"fácil": "easy", "médio": "medium", "difícil": "hard"}
            difficulty = diff_map.get(d, d)

        return topic, difficulty

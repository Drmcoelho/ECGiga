"""Multi-LLM orchestrator for clinical case generation.

Integrates local (Ollama/Mistral) and cloud (Gemini, GPT) models
for generating progressive clinical cases and layered explanations.
Priority: local model for drafts, cloud for refinement.
"""

from __future__ import annotations
import json
import hashlib
from pathlib import Path
from typing import Optional


class LLMConfig:
    """Configuration for an LLM provider."""
    def __init__(self, provider: str, model: str, api_key: Optional[str] = None,
                 base_url: Optional[str] = None, timeout: int = 30):
        self.provider = provider  # "ollama", "gemini", "openai"
        self.model = model
        self.api_key = api_key
        self.base_url = base_url or self._default_url()
        self.timeout = timeout

    def _default_url(self) -> str:
        defaults = {
            "ollama": "http://localhost:11434",
            "gemini": "https://generativelanguage.googleapis.com",
            "openai": "https://api.openai.com",
        }
        return defaults.get(self.provider, "")


class ResponseCache:
    """Simple file-based cache for LLM responses."""
    def __init__(self, cache_dir: str = ".llm_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _key(self, prompt: str, provider: str, model: str) -> str:
        content = f"{provider}:{model}:{prompt}"
        return hashlib.sha256(content.encode()).hexdigest()

    def get(self, prompt: str, provider: str, model: str) -> Optional[str]:
        path = self.cache_dir / f"{self._key(prompt, provider, model)}.json"
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            return data.get("response")
        return None

    def set(self, prompt: str, provider: str, model: str, response: str) -> None:
        path = self.cache_dir / f"{self._key(prompt, provider, model)}.json"
        path.write_text(json.dumps({
            "provider": provider, "model": model,
            "prompt_hash": self._key(prompt, provider, model),
            "response": response,
        }, ensure_ascii=False, indent=2), encoding="utf-8")


class LLMOrchestrator:
    """Multi-LLM orchestrator with priority: local > cloud.

    Flow:
    1. Local model (Ollama/Mistral) generates draft
    2. Cloud model (Gemini or GPT) refines if available
    3. Results cached for efficiency
    4. All outputs include educational disclaimers
    """

    DISCLAIMER = (
        "\u26a0\ufe0f AVISO: Este conte\u00fado foi gerado por intelig\u00eancia artificial "
        "para fins exclusivamente educacionais. N\u00e3o substitui avalia\u00e7\u00e3o "
        "cl\u00ednica profissional. Sempre correlacione com fontes m\u00e9dicas validadas."
    )

    def __init__(self, configs: Optional[list[LLMConfig]] = None,
                 cache_dir: str = ".llm_cache"):
        self.configs = configs or []
        self.cache = ResponseCache(cache_dir)
        self._providers: dict[str, LLMConfig] = {}
        for cfg in self.configs:
            self._providers[cfg.provider] = cfg

    def add_provider(self, config: LLMConfig) -> None:
        self.configs.append(config)
        self._providers[config.provider] = config

    def _call_ollama(self, prompt: str, config: LLMConfig) -> str:
        import requests
        resp = requests.post(
            f"{config.base_url}/api/generate",
            json={"model": config.model, "prompt": prompt, "stream": False},
            timeout=config.timeout,
        )
        resp.raise_for_status()
        return resp.json().get("response", "")

    def _call_openai(self, prompt: str, config: LLMConfig) -> str:
        import requests
        resp = requests.post(
            f"{config.base_url}/v1/chat/completions",
            headers={"Authorization": f"Bearer {config.api_key}"},
            json={
                "model": config.model,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=config.timeout,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

    def _call_gemini(self, prompt: str, config: LLMConfig) -> str:
        import requests
        resp = requests.post(
            f"{config.base_url}/v1/models/{config.model}:generateContent",
            params={"key": config.api_key},
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=config.timeout,
        )
        resp.raise_for_status()
        return resp.json()["candidates"][0]["content"]["parts"][0]["text"]

    def _call(self, prompt: str, config: LLMConfig) -> str:
        cached = self.cache.get(prompt, config.provider, config.model)
        if cached:
            return cached

        callers = {
            "ollama": self._call_ollama,
            "openai": self._call_openai,
            "gemini": self._call_gemini,
        }
        caller = callers.get(config.provider)
        if not caller:
            raise ValueError(f"Provider desconhecido: {config.provider}")

        response = caller(prompt, config)
        self.cache.set(prompt, config.provider, config.model, response)
        return response

    def generate(self, prompt: str, refine: bool = True) -> dict:
        """Generate response with local-first, cloud-refinement strategy."""
        result = {
            "draft": None,
            "refined": None,
            "provider_draft": None,
            "provider_refined": None,
            "disclaimer": self.DISCLAIMER,
        }

        # Priority order: ollama (local) > gemini > openai
        priority = ["ollama", "gemini", "openai"]

        for provider in priority:
            if provider in self._providers:
                try:
                    draft = self._call(prompt, self._providers[provider])
                    result["draft"] = draft
                    result["provider_draft"] = provider
                    break
                except Exception:
                    continue

        if not result["draft"]:
            result["draft"] = "[Nenhum provedor LLM dispon\u00edvel. Configure Ollama local ou chaves de API.]"
            return result

        if refine and result["provider_draft"] == "ollama":
            refine_prompt = (
                f"Revise e melhore o seguinte texto m\u00e9dico educacional, "
                f"corrigindo imprecis\u00f5es e melhorando clareza:\n\n{result['draft']}"
            )
            for provider in ["gemini", "openai"]:
                if provider in self._providers:
                    try:
                        refined = self._call(refine_prompt, self._providers[provider])
                        result["refined"] = refined
                        result["provider_refined"] = provider
                        break
                    except Exception:
                        continue

        return result

    def draft_case(self, topic: str, difficulty: str = "medium",
                   n_phases: int = 4) -> dict:
        """Generate a progressive clinical case."""
        prompt = f"""Gere um caso cl\u00ednico progressivo sobre ECG com as seguintes especifica\u00e7\u00f5es:

Tema: {topic}
Dificuldade: {difficulty}
Fases: {n_phases}

O caso deve ter:
1. Contexto cl\u00ednico (idade, sexo, queixa principal)
2. Fases progressivas com:
   - Instru\u00e7\u00e3o para o aluno
   - Resposta esperada
   - Dicas (hints)
3. Interpreta\u00e7\u00e3o final
4. Pontos de aprendizado

Formato: JSON v\u00e1lido com campos: id, title, difficulty, context, phases[], final_interpretation, learning_points[]

IMPORTANTE: Conte\u00fado exclusivamente educacional. Incluir disclaimer."""

        result = self.generate(prompt, refine=True)

        # Try to parse as JSON
        draft = result.get("refined") or result.get("draft", "")
        try:
            # Extract JSON from response if wrapped in text
            import re
            json_match = re.search(r'\{[\s\S]*\}', draft)
            if json_match:
                case = json.loads(json_match.group())
                case["_meta"] = {
                    "generated_by": result.get("provider_draft"),
                    "refined_by": result.get("provider_refined"),
                    "disclaimer": self.DISCLAIMER,
                }
                return case
        except (json.JSONDecodeError, AttributeError):
            pass

        return {
            "raw_text": draft,
            "_meta": {
                "generated_by": result.get("provider_draft"),
                "refined_by": result.get("provider_refined"),
                "disclaimer": self.DISCLAIMER,
                "parse_error": "Could not parse as JSON",
            },
        }

    def available_providers(self) -> list[str]:
        """List configured providers."""
        available = []
        for provider, config in self._providers.items():
            if provider == "ollama":
                try:
                    import requests
                    resp = requests.get(f"{config.base_url}/api/tags", timeout=3)
                    if resp.ok:
                        available.append(f"ollama ({config.model})")
                except Exception:
                    pass
            else:
                if config.api_key:
                    available.append(f"{provider} ({config.model})")
        return available

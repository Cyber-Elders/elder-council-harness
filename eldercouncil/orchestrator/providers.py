# SPDX-License-Identifier: Apache-2.0
"""
BYO-LLM providers — credentials read from the environment, never shipped.

  Anthropic   -> ANTHROPIC_API_KEY        (model tags like claude-opus-4-8)
  OpenRouter  -> OPENROUTER_API_KEY        (any openrouter model id)
  Ollama      -> OLLAMA_HOST (default http://localhost:11434)  (local, keyless)

`select_client(model)` routes a model tag to a provider by simple prefix rules.
Each client raises a clear error if its credential is missing.
"""

from __future__ import annotations

import os


class ProviderError(RuntimeError):
    pass


class AnthropicClient:
    name = "anthropic"

    def query(self, model: str, system: str, prompt: str) -> str:
        key = os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise ProviderError("ANTHROPIC_API_KEY not set")
        try:
            import anthropic
        except ImportError as exc:  # pragma: no cover
            raise ProviderError("install eldercouncil[orchestrator] for the anthropic SDK") from exc
        client = anthropic.Anthropic(api_key=key)
        msg = client.messages.create(
            model=model, max_tokens=1024, system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(getattr(b, "text", "") for b in msg.content)


class OpenRouterClient:
    name = "openrouter"

    def query(self, model: str, system: str, prompt: str) -> str:
        key = os.environ.get("OPENROUTER_API_KEY")
        if not key:
            raise ProviderError("OPENROUTER_API_KEY not set")
        import httpx
        r = httpx.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}"},
            json={"model": model, "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}]},
            timeout=120,
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]


class OllamaClient:
    name = "ollama"

    def query(self, model: str, system: str, prompt: str) -> str:
        import httpx
        host = os.environ.get("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
        r = httpx.post(
            f"{host}/api/chat",
            json={"model": model, "stream": False, "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}]},
            timeout=300,
        )
        r.raise_for_status()
        return r.json()["message"]["content"]


def select_client(model: str):
    """Route a model tag to a provider. `inherit`/unpinned -> the default provider
    chain (Anthropic if keyed, else Ollama local)."""
    m = (model or "").lower()
    if m.startswith("claude") or m.startswith("anthropic"):
        return AnthropicClient()
    if "/" in m or m.startswith("openrouter"):
        return OpenRouterClient()
    if m in ("", "inherit") or m.startswith("ollama"):
        return AnthropicClient() if os.environ.get("ANTHROPIC_API_KEY") else OllamaClient()
    # bare local-style tags (e.g. gemma:27b) -> Ollama
    return OllamaClient()

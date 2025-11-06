"""Abstractions and implementations for supported LLM providers."""
from __future__ import annotations

import importlib
import json
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional, Protocol


class LLMProvider(Protocol):
    """Protocol for text generation providers."""

    model: str

    def generate(self, prompt: str, **options: Any) -> str:
        """Generate a completion from the provider."""


@dataclass
class ProviderConfig:
    """Configuration options shared by providers."""

    model: str
    api_key: Optional[str] = None
    temperature: float = 0.2
    max_tokens: int = 1024
    extra: Dict[str, Any] | None = None


class OpenAIProvider:
    """Implementation of :class:`LLMProvider` for OpenAI chat models."""

    def __init__(self, config: ProviderConfig):
        self.model = config.model
        self.temperature = config.temperature
        self.max_tokens = config.max_tokens
        api_key = config.api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY or pass api_key.")

        client_module = importlib.import_module("openai")
        client_module.api_key = api_key  # type: ignore[attr-defined]
        self._client = client_module

    def generate(self, prompt: str, **options: Any) -> str:
        params = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": options.get("system_prompt", "You are a helpful assistant.")},
                {"role": "user", "content": prompt},
            ],
            "temperature": options.get("temperature", self.temperature),
            "max_tokens": options.get("max_tokens", self.max_tokens),
        }
        response = self._client.ChatCompletion.create(**params)
        message = response["choices"][0]["message"]["content"]
        return str(message).strip()


class AnthropicProvider:
    """Implementation of :class:`LLMProvider` for Anthropic Claude models."""

    def __init__(self, config: ProviderConfig):
        self.model = config.model
        self.temperature = config.temperature
        self.max_tokens = config.max_tokens
        api_key = config.api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "Anthropic API key is required. Set ANTHROPIC_API_KEY or pass api_key explicitly."
            )

        module = importlib.import_module("anthropic")
        self._client = module.Client(api_key=api_key)

    def generate(self, prompt: str, **options: Any) -> str:
        params = {
            "model": self.model,
            "max_tokens": options.get("max_tokens", self.max_tokens),
            "temperature": options.get("temperature", self.temperature),
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": options.get("system_prompt", "You are a helpful assistant.")},
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
        }
        result = self._client.messages.create(**params)
        if not result.content:
            return ""
        return "\n".join(block.text for block in result.content if getattr(block, "text", ""))


class OllamaProvider:
    """Implementation of :class:`LLMProvider` for local Ollama models."""

    def __init__(self, config: ProviderConfig):
        self.model = config.model
        self.temperature = config.temperature
        self.max_tokens = config.max_tokens
        module = importlib.import_module("ollama")
        self._client = module.Client()
        self._options = config.extra or {}

    def generate(self, prompt: str, **options: Any) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "options": {"temperature": options.get("temperature", self.temperature), **self._options},
        }
        response = self._client.generate(**payload)
        if isinstance(response, dict) and "response" in response:
            return str(response["response"]).strip()
        if isinstance(response, str):
            return response.strip()
        return json.dumps(response)


def create_provider(name: str, model: Optional[str] = None, **kwargs: Any) -> LLMProvider:
    """Factory function for creating providers by name."""

    normalized = name.lower()
    if normalized == "openai":
        if not model:
            model = "gpt-3.5-turbo"
        return OpenAIProvider(ProviderConfig(model=model, **kwargs))
    if normalized == "anthropic":
        if not model:
            model = "claude-3-sonnet-20240229"
        return AnthropicProvider(ProviderConfig(model=model, **kwargs))
    if normalized == "ollama":
        if not model:
            model = "llama2"
        return OllamaProvider(ProviderConfig(model=model, extra=kwargs.pop("options", None), **kwargs))

    raise ValueError(f"Unsupported provider: {name}")


__all__ = [
    "LLMProvider",
    "ProviderConfig",
    "OpenAIProvider",
    "AnthropicProvider",
    "OllamaProvider",
    "create_provider",
]

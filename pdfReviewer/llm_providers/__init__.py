import os

from .anthropic import AnthropicProvider
from .base import LLMProvider, ProviderError
from .gemini import GeminiProvider
from .openai import OpenAIProvider

_PROVIDERS = {
    "anthropic": AnthropicProvider,
    "openai": OpenAIProvider,
    "gemini": GeminiProvider,
}


def get_provider() -> LLMProvider:
    """Instantiate the provider set by PROVIDER in .env (default: anthropic)."""
    name = os.getenv("PROVIDER", "anthropic").strip().lower()
    cls = _PROVIDERS.get(name)
    if cls is None:
        raise ValueError(
            f"Unknown PROVIDER '{name}'. Supported values: {' | '.join(_PROVIDERS)}"
        )
    return cls()


__all__ = ["get_provider", "LLMProvider", "ProviderError"]

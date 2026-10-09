"""
Factory for instantiating LLM providers based on configuration.
"""

from typing import Optional
from panel_review.config import PanelConfig, ProviderConfig
from panel_review.providers.base import LLMProvider
from panel_review.providers.openai_provider import OpenAIProvider
from panel_review.providers.anthropic_provider import AnthropicProvider
from panel_review.providers.gemini_provider import GeminiProvider
from panel_review.providers.ollama_provider import OllamaProvider
from panel_review.providers.mock_provider import MockProvider


class ProviderFactory:
    @staticmethod
    def create(
        provider_name: str,
        config: PanelConfig,
        model_override: Optional[str] = None,
    ) -> LLMProvider:
        prov_name = config.default_provider if provider_name in ("default", "") else provider_name
        prov_cfg = config.get_provider_config(prov_name)
        model = model_override if (model_override and model_override != "default") else prov_cfg.model

        key = prov_cfg.api_key
        base_url = prov_cfg.base_url
        temp = prov_cfg.temperature
        max_tokens = prov_cfg.max_tokens

        prov_lower = prov_name.lower()
        if prov_lower == "openai":
            return OpenAIProvider(
                model=model,
                api_key=key,
                base_url=base_url,
                temperature=temp,
                max_tokens=max_tokens,
            )
        elif prov_lower == "anthropic":
            return AnthropicProvider(
                model=model,
                api_key=key,
                base_url=base_url,
                temperature=temp,
                max_tokens=max_tokens,
            )
        elif prov_lower == "gemini":
            return GeminiProvider(
                model=model,
                api_key=key,
                base_url=base_url,
                temperature=temp,
                max_tokens=max_tokens,
            )
        elif prov_lower == "ollama":
            return OllamaProvider(
                model=model,
                base_url=base_url,
                temperature=temp,
                max_tokens=max_tokens,
            )
        elif prov_lower == "custom":
            # Uses OpenAI-compatible interface for custom endpoints (vLLM, Groq, Together, etc.)
            return OpenAIProvider(
                model=model,
                api_key=key or "custom-key",
                base_url=base_url or "http://localhost:8000/v1",
                temperature=temp,
                max_tokens=max_tokens,
            )
        elif prov_lower == "mock":
            return MockProvider(
                model=model,
                temperature=temp,
                max_tokens=max_tokens,
            )
        else:
            # Fallback to Mock if unrecognized provider
            return MockProvider(model=model)

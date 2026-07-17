from __future__ import annotations

from fastapi import HTTPException, status

from app.ai.providers.base import AIProvider
from app.ai.providers.http import AnthropicProvider, GeminiProvider, OpenAICompatibleProvider
from app.core.config import Settings, get_settings


def get_ai_provider(settings: Settings | None = None) -> AIProvider:
    """Create the active AI provider from environment settings."""
    resolved = settings or get_settings()
    provider = resolved.ai_provider.lower()

    if provider == "openai":
        return OpenAICompatibleProvider(
            provider_name="openai",
            api_key=resolved.openai_api_key,
            base_url="https://api.openai.com/v1",
        )
    if provider == "openrouter":
        return OpenAICompatibleProvider(
            provider_name="openrouter",
            api_key=resolved.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1",
        )
    if provider == "gemini":
        return GeminiProvider(api_key=resolved.gemini_api_key)
    if provider == "anthropic":
        return AnthropicProvider(api_key=resolved.anthropic_api_key)

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Unsupported AI provider: {resolved.ai_provider}",
    )

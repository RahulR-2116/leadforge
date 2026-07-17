from __future__ import annotations

import httpx
from fastapi import HTTPException, status

from app.ai.models.core import AIRequest, AIResponse
from app.ai.providers.base import AIProvider


class OpenAICompatibleProvider(AIProvider):
    """Provider for OpenAI-compatible chat completion APIs."""

    def __init__(self, *, provider_name: str, api_key: str | None, base_url: str) -> None:
        self._provider_name = provider_name
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")

    async def generate(self, request: AIRequest) -> AIResponse:
        """Generate text through a chat completions endpoint."""
        if not self._api_key:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"{self._provider_name} API key is not configured",
            )

        payload = {
            "model": request.model,
            "messages": [message.__dict__ for message in request.messages],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
        }
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{self._base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self._api_key}"},
                json=payload,
            )
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        return AIResponse(content=content, provider=self._provider_name, model=request.model)


class GeminiProvider(AIProvider):
    """Provider for Google Gemini generateContent API."""

    def __init__(self, *, api_key: str | None) -> None:
        self._api_key = api_key

    async def generate(self, request: AIRequest) -> AIResponse:
        """Generate text through Gemini."""
        if not self._api_key:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Gemini API key is not configured",
            )

        prompt = "\n\n".join(f"{message.role}: {message.content}" for message in request.messages)
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{request.model}:generateContent",
                params={"key": self._api_key},
                json={"contents": [{"parts": [{"text": prompt}]}]},
            )
        response.raise_for_status()
        data = response.json()
        content = data["candidates"][0]["content"]["parts"][0]["text"]
        return AIResponse(content=content, provider="gemini", model=request.model)


class AnthropicProvider(AIProvider):
    """Provider for Anthropic Messages API."""

    def __init__(self, *, api_key: str | None) -> None:
        self._api_key = api_key

    async def generate(self, request: AIRequest) -> AIResponse:
        """Generate text through Anthropic."""
        if not self._api_key:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Anthropic API key is not configured",
            )

        system = "\n\n".join(
            message.content for message in request.messages if message.role == "system"
        )
        messages = [
            {"role": message.role, "content": message.content}
            for message in request.messages
            if message.role != "system"
        ]
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self._api_key,
                    "anthropic-version": "2023-06-01",
                },
                json={
                    "model": request.model,
                    "system": system,
                    "messages": messages,
                    "temperature": request.temperature,
                    "max_tokens": request.max_tokens,
                },
            )
        response.raise_for_status()
        data = response.json()
        content = data["content"][0]["text"]
        return AIResponse(content=content, provider="anthropic", model=request.model)

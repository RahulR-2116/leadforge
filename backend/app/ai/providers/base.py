from __future__ import annotations

from abc import ABC, abstractmethod

from app.ai.models.core import AIRequest, AIResponse


class AIProvider(ABC):
    """Abstract interface implemented by all AI providers."""

    @abstractmethod
    async def generate(self, request: AIRequest) -> AIResponse:
        """Generate text for a provider-neutral request."""

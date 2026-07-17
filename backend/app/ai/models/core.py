from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ChatMessage:
    """Provider-neutral chat message."""

    role: str
    content: str


@dataclass(frozen=True)
class AIRequest:
    """Provider-neutral AI generation request."""

    messages: list[ChatMessage]
    model: str
    temperature: float
    max_tokens: int


@dataclass(frozen=True)
class AIResponse:
    """Provider-neutral AI generation response."""

    content: str
    provider: str
    model: str

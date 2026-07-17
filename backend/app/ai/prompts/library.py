from __future__ import annotations

import json
from pathlib import Path

DEFAULT_PROMPTS: dict[str, str] = {
    "whatsapp": "Write a short, conversational WhatsApp outreach message under 120 words.",
    "email": "Write a cold email with a subject, body, and clear CTA.",
    "follow_up": "Write a professional follow-up based on CRM status and context.",
    "audit": "Create a practical website audit or no-website opportunity report.",
    "proposal": "Create a professional website proposal with all required sections.",
    "summary": "Summarize this lead with objections, services, pricing strategy, and upsells.",
    "objection": "Generate three professional replies to the customer objection.",
    "conversation": "Generate a contextual reply using the prior conversation.",
    "demo_content": "Generate safe demo website content. Never fabricate factual claims.",
}


class PromptLibrary:
    """File-backed editable prompt template library."""

    def __init__(self, path: Path | None = None) -> None:
        self._path = path or Path("data") / "prompts.json"

    def list_prompts(self) -> dict[str, str]:
        """Return all prompt templates."""
        prompts = DEFAULT_PROMPTS.copy()
        if self._path.exists():
            prompts.update(json.loads(self._path.read_text(encoding="utf-8")))
        return prompts

    def update_prompt(self, key: str, template: str) -> dict[str, str]:
        """Update one prompt template."""
        prompts = self.list_prompts()
        prompts[key] = template
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(prompts, indent=2), encoding="utf-8")
        return prompts


prompt_library = PromptLibrary()

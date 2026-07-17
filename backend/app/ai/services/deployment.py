from __future__ import annotations

import base64
from dataclasses import dataclass
from pathlib import Path

import httpx

from app.core.config import Settings, get_settings


@dataclass(frozen=True)
class DeploymentResult:
    """Deployment result."""

    url: str
    status: str


class VercelDeploymentAdapter:
    """Deploy generated static demo sites to Vercel when configured."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    async def deploy(self, *, project_name: str, html_path: Path) -> DeploymentResult:
        """Deploy a single static HTML file to Vercel or return local URL when unconfigured."""
        if not self._settings.vercel_token:
            relative = html_path.as_posix().replace("generated/", "")
            return DeploymentResult(
                url=f"{self._settings.public_backend_url}/generated/{relative}",
                status="generated",
            )

        encoded = base64.b64encode(html_path.read_bytes()).decode("ascii")
        payload = {
            "name": project_name,
            "files": [{"file": "index.html", "data": encoded, "encoding": "base64"}],
            "projectSettings": {"framework": None},
        }
        params = (
            {"teamId": self._settings.vercel_team_id} if self._settings.vercel_team_id else None
        )
        async with httpx.AsyncClient(timeout=90) as client:
            response = await client.post(
                "https://api.vercel.com/v13/deployments",
                params=params,
                headers={"Authorization": f"Bearer {self._settings.vercel_token}"},
                json=payload,
            )
        response.raise_for_status()
        data = response.json()
        return DeploymentResult(url=f"https://{data['url']}", status="deployed")

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class HealthCheck(BaseModel):
    """Health response for service and database status."""

    service: str
    status: str
    environment: str
    database: str

    model_config = ConfigDict(from_attributes=True)

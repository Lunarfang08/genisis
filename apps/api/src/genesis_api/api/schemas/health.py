from typing import Literal

from pydantic import BaseModel, Field


class LivenessResponse(BaseModel):
    status: Literal["ok"] = "ok"
    service: Literal["genesis-api"] = "genesis-api"
    version: str


class DependencyStatus(BaseModel):
    status: Literal["ok", "degraded"]
    latency_ms: float = Field(serialization_alias="latencyMs", ge=0.0)
    detail: str | None = None


class ReadinessResponse(BaseModel):
    status: Literal["ok", "degraded"]
    service: Literal["genesis-api"] = "genesis-api"
    version: str
    dependencies: dict[str, DependencyStatus]

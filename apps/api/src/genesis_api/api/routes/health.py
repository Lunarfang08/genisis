import asyncio
from collections.abc import Awaitable, Callable
from time import perf_counter

from fastapi import APIRouter, Request, Response, status

from genesis_api import __version__
from genesis_api.api.schemas.health import (
    DependencyStatus,
    LivenessResponse,
    ReadinessResponse,
)

router = APIRouter(prefix="/health", tags=["health"])


async def _check(
    operation: Callable[[], Awaitable[None]],
    timeout_seconds: float,
) -> DependencyStatus:
    started_at = perf_counter()
    try:
        async with asyncio.timeout(timeout_seconds):
            await operation()
    except Exception as error:
        # A readiness probe must isolate dependency-specific failures. Returning
        # the exception type is sufficient diagnostics without leaking details.
        return DependencyStatus(
            status="degraded",
            latency_ms=(perf_counter() - started_at) * 1_000,
            detail=type(error).__name__,
        )

    return DependencyStatus(
        status="ok",
        latency_ms=(perf_counter() - started_at) * 1_000,
    )


@router.get("/live", response_model=LivenessResponse)
async def liveness() -> LivenessResponse:
    return LivenessResponse(version=__version__)


@router.get("/ready", response_model=ReadinessResponse)
async def readiness(request: Request, response: Response) -> ReadinessResponse:
    settings = request.app.state.settings
    database, redis = await asyncio.gather(
        _check(request.app.state.database.ping, settings.health_timeout_seconds),
        _check(request.app.state.redis.ping, settings.health_timeout_seconds),
    )
    overall_status = "ok" if database.status == "ok" and redis.status == "ok" else "degraded"

    if overall_status == "degraded":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return ReadinessResponse(
        status=overall_status,
        version=__version__,
        dependencies={"database": database, "redis": redis},
    )

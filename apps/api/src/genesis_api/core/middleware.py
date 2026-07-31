import logging
from collections.abc import Awaitable, Callable
from time import perf_counter
from uuid import UUID, uuid4

from fastapi import FastAPI, Request, Response

from genesis_api.api.errors import ApiError

logger = logging.getLogger("genesis_api.requests")


def _request_id(candidate: str | None) -> str:
    if candidate is None:
        return str(uuid4())
    try:
        return str(UUID(candidate))
    except ValueError:
        return str(uuid4())


def register_request_middleware(app: FastAPI) -> None:
    @app.middleware("http")
    async def request_context(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        started_at = perf_counter()
        request_id = _request_id(request.headers.get("x-request-id"))
        content_length = request.headers.get("content-length")
        if (
            content_length
            and int(content_length) > request.app.state.settings.request_size_limit_bytes
        ):
            raise ApiError(
                413,
                "Payload too large",
                "The request body exceeds the configured limit.",
                "request_too_large",
            )
        response: Response

        try:
            response = await call_next(request)
        except Exception:
            logger.exception(
                "request_failed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                },
            )
            raise

        duration_ms = (perf_counter() - started_at) * 1_000
        response.headers["x-request-id"] = request_id
        response.headers["x-content-type-options"] = "nosniff"
        response.headers["x-frame-options"] = "DENY"
        response.headers["referrer-policy"] = "strict-origin-when-cross-origin"
        response.headers["permissions-policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["content-security-policy"] = (
            "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
        )
        if request.app.state.settings.is_production:
            response.headers["strict-transport-security"] = "max-age=31536000; includeSubDomains"
        logger.info(
            "request_completed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
            },
        )
        return response

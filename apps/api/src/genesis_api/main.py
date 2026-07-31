from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from genesis_api import __version__
from genesis_api.api.errors import register_error_handlers
from genesis_api.api.router import api_router
from genesis_api.core.lifespan import lifespan
from genesis_api.core.logging import configure_logging
from genesis_api.core.middleware import register_request_middleware
from genesis_api.core.settings import get_settings

settings = get_settings()
configure_logging(settings.log_level)

app = FastAPI(
    title="GENESIS API",
    summary="API gateway for the artificial civilization simulator",
    version=__version__,
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID", "X-CSRF-Token"],
)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.trusted_hosts)
register_error_handlers(app)
register_request_middleware(app)
app.include_router(api_router, prefix=settings.api_prefix)


@app.get("/", include_in_schema=False)
async def root() -> dict[str, str]:
    return {
        "name": "GENESIS API",
        "version": __version__,
        "docs": "/docs" if not settings.is_production else "disabled",
    }

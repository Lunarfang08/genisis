import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from genesis_api.api.streaming import StreamHub
from genesis_api.core.settings import get_settings
from genesis_api.db.base import Base
from genesis_api.db.manager import DatabaseManager
from genesis_api.integrations.redis import RedisManager

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    app.state.settings = settings
    app.state.database = DatabaseManager(settings.database_url)
    app.state.redis = RedisManager(settings.redis_url)
    app.state.stream_hub = StreamHub()

    if settings.environment == "test":
        await app.state.database.create_schema(Base)

    logger.info("application_started", extra={"environment": settings.environment})
    try:
        yield
    finally:
        await app.state.redis.close()
        await app.state.database.close()
        logger.info("application_stopped")

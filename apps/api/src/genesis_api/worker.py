import asyncio
import logging
import signal
from contextlib import suppress

from genesis_api.core.logging import configure_logging
from genesis_api.core.settings import get_settings
from genesis_api.db.manager import DatabaseManager
from genesis_api.integrations.redis import RedisManager
from genesis_api.services.worker import SimulationWorker

logger = logging.getLogger(__name__)


async def run() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    database = DatabaseManager(settings.database_url)
    redis = RedisManager(settings.redis_url)
    worker = SimulationWorker(redis, settings)
    stopping = asyncio.Event()
    loop = asyncio.get_running_loop()
    for name in ("SIGINT", "SIGTERM"):
        if hasattr(signal, name):
            loop.add_signal_handler(getattr(signal, name), stopping.set)
    logger.info("worker_started")
    try:
        while not stopping.is_set():
            async for session in database.session():
                processed, published = await worker.process_batch(session)
            if processed or published:
                logger.info("worker_batch", extra={"commands": processed, "outbox": published})
            with suppress(TimeoutError):
                await asyncio.wait_for(stopping.wait(), timeout=1.0)
    finally:
        await redis.close()
        await database.close()
        logger.info("worker_stopped")


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()

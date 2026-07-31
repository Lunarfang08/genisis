import json
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from genesis_api.core.settings import Settings
from genesis_api.db.models import SimulationCommand, SimulationOutbox, WorldSettings
from genesis_api.integrations.redis import RedisManager
from genesis_api.services.narratives import NarrativeService
from genesis_api.services.simulation_runtime import PersistentSimulationRuntime


class SimulationWorker:
    """Idempotent command/outbox worker suitable for a separately scaled process."""

    def __init__(self, redis: RedisManager, settings: Settings) -> None:
        self.redis = redis
        self.worker_id = str(uuid4())
        self.runtime = PersistentSimulationRuntime()
        self.narratives = NarrativeService(settings)

    async def process_batch(self, session: AsyncSession, *, limit: int = 100) -> tuple[int, int]:
        commands = (
            await session.scalars(
                select(SimulationCommand)
                .where(SimulationCommand.processed_at.is_(None))
                .order_by(SimulationCommand.world_id, SimulationCommand.sequence)
                .with_for_update(skip_locked=True)
                .limit(limit)
            )
        ).all()
        processed = 0
        for command in commands:
            lease = await self.redis.acquire_lease(
                f"genesis:simulation-lease:{command.world_id}", self.worker_id, 30
            )
            if not lease:
                continue
            if command.command_type == "step":
                await self.runtime.tick(session, command.world_id, single_step=True)
            elif command.command_type == "reset":
                await self.runtime.reset(session, command.world_id)
            command.processed_at = datetime.now(UTC)
            processed += 1
        await session.commit()

        await self.narratives.annotate_next(session)

        active_worlds = (
            await session.scalars(
                select(WorldSettings.world_id)
                .where(WorldSettings.is_paused.is_(False), WorldSettings.rng_state.is_not(None))
                .order_by(WorldSettings.world_id)
                .limit(100)
            )
        ).all()
        for world_id in active_worlds:
            lease = await self.redis.acquire_lease(
                f"genesis:simulation-lease:{world_id}", self.worker_id, 30
            )
            if not lease:
                continue
            await self.runtime.tick(session, world_id)
            await session.commit()

        pending = (
            await session.scalars(
                select(SimulationOutbox)
                .where(SimulationOutbox.published_at.is_(None))
                .order_by(SimulationOutbox.created_at)
                .with_for_update(skip_locked=True)
                .limit(limit)
            )
        ).all()
        published = 0
        for item in pending:
            try:
                await self.redis.publish(
                    f"genesis:world:{item.world_id}:{item.channel}",
                    json.dumps(item.payload, separators=(",", ":")),
                )
            except Exception:
                item.attempts += 1
                continue
            item.attempts += 1
            item.published_at = datetime.now(UTC)
            published += 1
        await session.commit()
        return processed, published

from dataclasses import dataclass
from datetime import date
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from genesis_api.db.models import SimulationEvent, SimulationOutbox, World


@dataclass(frozen=True, slots=True)
class CommittedEvent:
    simulation_date: date
    category: str
    event_type: str
    payload: dict[str, Any]
    engine_version: str
    schema_version: int = 1
    actor_citizen_id: UUID | None = None
    target_citizen_id: UUID | None = None
    city_id: UUID | None = None
    causation_id: UUID | None = None
    correlation_id: UUID | None = None
    severity: str = "info"
    importance: int = 0


class EventRepository:
    """Persists ordered events and outbox rows in the caller's transaction."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def append(
        self, world_id: UUID, events: tuple[CommittedEvent, ...]
    ) -> tuple[SimulationEvent, ...]:
        if not events:
            return ()
        await self._session.execute(select(World.id).where(World.id == world_id).with_for_update())
        latest = (
            await self._session.scalar(
                select(func.max(SimulationEvent.sequence)).where(
                    SimulationEvent.world_id == world_id
                )
            )
            or 0
        )
        persisted: list[SimulationEvent] = []
        for offset, draft in enumerate(events, start=1):
            correlation_id = draft.correlation_id or uuid4()
            event = SimulationEvent(
                world_id=world_id,
                sequence=latest + offset,
                simulation_date=draft.simulation_date,
                category=draft.category,
                event_type=draft.event_type,
                schema_version=draft.schema_version,
                engine_version=draft.engine_version,
                actor_citizen_id=draft.actor_citizen_id,
                target_citizen_id=draft.target_citizen_id,
                city_id=draft.city_id,
                causation_id=draft.causation_id,
                correlation_id=correlation_id,
                severity=draft.severity,
                importance=draft.importance,
                payload=draft.payload,
            )
            self._session.add(event)
            await self._session.flush()
            self._session.add(
                SimulationOutbox(
                    world_id=world_id,
                    event_id=event.id,
                    channel=draft.category,
                    payload={
                        "id": str(event.id),
                        "sequence": event.sequence,
                        "simulation_date": event.simulation_date.isoformat(),
                        "category": event.category,
                        "event_type": event.event_type,
                        "importance": event.importance,
                        "payload": event.payload,
                    },
                )
            )
            persisted.append(event)
        return tuple(persisted)

from datetime import date
from decimal import Decimal
from typing import Any, cast
from uuid import UUID

from genesis_simulation.engine import SimulationEngine
from genesis_simulation.model import (
    CitizenState,
    DomainEvent,
    EngineCommand,
    EngineConfig,
    EngineResult,
    SimulationSnapshot,
    WorldState,
)
from genesis_simulation.randomness import state_from_json, state_to_json
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from genesis_api.db.models import (
    Citizen,
    Government,
    Occupation,
    SimulationEvent,
    WorldMetric,
    WorldSettings,
)
from genesis_api.db.models import (
    SimulationSnapshot as PersistedSnapshot,
)
from genesis_api.repositories.history import CommittedEvent, EventRepository


class PersistentSimulationRuntime:
    """Hydrates, advances, and atomically persists one deterministic world."""

    async def load(
        self, session: AsyncSession, world_id: UUID, *, days_per_tick: int | None = None
    ) -> SimulationEngine:
        settings = await session.scalar(
            select(WorldSettings).where(WorldSettings.world_id == world_id).with_for_update()
        )
        if settings is None or settings.rng_state is None:
            raise ValueError("world is not initialized")
        citizens = (
            await session.scalars(
                select(Citizen).where(Citizen.world_id == world_id).order_by(Citizen.id)
            )
        ).all()
        occupations = {
            item.id: item.name
            for item in (
                await session.scalars(select(Occupation).where(Occupation.world_id == world_id))
            ).all()
        }
        government = await session.scalar(
            select(Government).where(Government.world_id == world_id, Government.scope == "world")
        )
        state = WorldState(
            world_id=str(world_id),
            seed=settings.seed,
            simulation_date=settings.simulation_date,
            citizens={
                str(item.id): CitizenState(
                    id=str(item.id),
                    birth_date=item.birth_date,
                    lifecycle_status=item.lifecycle_status,
                    health=item.health,
                    happiness=item.happiness,
                    employment_status=item.employment_status,
                    occupation=(
                        occupations.get(item.occupation_id) if item.occupation_id else None
                    ),
                    income_minor=item.income_minor,
                    wealth_minor=item.wealth_minor,
                    relationship_strength=50,
                )
                for item in citizens
            },
            tick=settings.simulation_tick,
            event_sequence=settings.event_sequence,
            paused=settings.is_paused,
            speed=settings.tick_rate,
            treasury_minor=government.treasury_minor if government else 0,
            social_cohesion=settings.social_cohesion,
            environmental_quality=settings.environmental_quality,
            rng_state=state_from_json(cast(list[object], settings.rng_state)),
        )
        return SimulationEngine(
            state,
            config=EngineConfig(days_per_tick=days_per_tick or settings.tick_rate),
        )

    async def tick(
        self, session: AsyncSession, world_id: UUID, *, single_step: bool = False
    ) -> EngineResult:
        engine = await self.load(session, world_id, days_per_tick=1 if single_step else None)
        result = engine.apply(EngineCommand.step() if single_step else EngineCommand.tick())
        if result.advanced:
            await self.persist(session, world_id, result, engine)
        return result

    async def reset(self, session: AsyncSession, world_id: UUID) -> EngineResult:
        engine = await self.load(session, world_id)
        stored = await session.scalar(
            select(PersistedSnapshot)
            .where(PersistedSnapshot.world_id == world_id, PersistedSnapshot.event_sequence == 0)
            .order_by(PersistedSnapshot.created_at)
            .limit(1)
        )
        if stored is None:
            raise ValueError("initial snapshot is missing")
        manifest = tuple(cast(list[str], stored.rng_state["system_manifest"]))
        snapshot = SimulationSnapshot(
            world_id=str(world_id),
            tick=cast(int, stored.state["tick"]),
            event_sequence=cast(int, stored.state["event_sequence"]),
            engine_version=stored.engine_version,
            rng_algorithm=cast(str, stored.rng_state["algorithm"]),
            rng_version=cast(int, stored.rng_state["version"]),
            system_manifest=manifest,
            state=stored.state,
            checksum=stored.checksum,
        )
        engine.restore(snapshot)
        result = engine.apply(EngineCommand.pause())
        await self.persist(session, world_id, result, engine, add_engine_events=False)
        await EventRepository(session).append(
            world_id,
            (
                CommittedEvent(
                    simulation_date=result.state.simulation_date,
                    category="history",
                    event_type="world.reset_to_seed",
                    payload={"seed": result.state.seed},
                    engine_version=engine.config.engine_version,
                    severity="notice",
                    importance=80,
                ),
            ),
        )
        return result

    async def persist(
        self,
        session: AsyncSession,
        world_id: UUID,
        result: EngineResult,
        engine: SimulationEngine,
        *,
        add_engine_events: bool = True,
    ) -> None:
        settings = await session.scalar(
            select(WorldSettings).where(WorldSettings.world_id == world_id).with_for_update()
        )
        if settings is None:
            raise ValueError("world settings are missing")
        citizens = {
            str(item.id): item
            for item in (
                await session.scalars(select(Citizen).where(Citizen.world_id == world_id))
            ).all()
        }
        general_worker = await session.scalar(
            select(Occupation).where(
                Occupation.world_id == world_id, Occupation.name == "General Worker"
            )
        )
        for citizen_id, state in result.state.citizens.items():
            item = citizens[citizen_id]
            item.lifecycle_status = state.lifecycle_status
            item.health = state.health
            item.happiness = state.happiness
            item.employment_status = state.employment_status
            item.income_minor = state.income_minor
            item.wealth_minor = state.wealth_minor
            if state.occupation == "general_worker" and general_worker is not None:
                item.occupation_id = general_worker.id

        settings.simulation_date = result.state.simulation_date
        settings.simulation_tick = result.state.tick
        settings.event_sequence = result.state.event_sequence
        settings.is_paused = result.state.paused
        settings.tick_rate = result.state.speed
        settings.rng_state = cast(list[Any], state_to_json(result.state.rng_state))
        settings.social_cohesion = result.state.social_cohesion
        settings.environmental_quality = result.state.environmental_quality
        government = await session.scalar(
            select(Government).where(Government.world_id == world_id, Government.scope == "world")
        )
        if government is not None:
            government.treasury_minor = result.state.treasury_minor

        drafts = tuple(self._event(event) for event in result.events) if add_engine_events else ()
        persisted = await EventRepository(session).append(world_id, drafts)
        if result.state.simulation_date.day == 1 and result.advanced:
            summary = await EventRepository(session).append(
                world_id,
                (
                    CommittedEvent(
                        simulation_date=result.state.simulation_date,
                        category="history",
                        event_type="world.monthly_summary_committed",
                        payload={
                            "population": len(result.state.citizens),
                            "treasury_minor": result.state.treasury_minor,
                            "social_cohesion": result.state.social_cohesion,
                            "environmental_quality": result.state.environmental_quality,
                        },
                        engine_version=engine.config.engine_version,
                        severity="notice",
                        importance=85,
                    ),
                ),
            )
            persisted = (*persisted, *summary)

        metric_values: dict[str, tuple[int | float, str]] = {
            item.name: (item.value, item.unit) for item in result.metrics
        }
        metric_values.update(
            {
                "gdp_minor": (
                    sum(item.income_minor for item in result.state.citizens.values()),
                    "minor_units",
                ),
                "government_approval": (
                    round(
                        (
                            result.state.social_cohesion
                            + sum(item.happiness for item in result.state.citizens.values())
                            / max(1, len(result.state.citizens))
                        )
                        / 2
                    ),
                    "score",
                ),
                "environmental_risk": (100 - result.state.environmental_quality, "score"),
                "crime_rate": (
                    max(0, round((50 - result.state.social_cohesion) / 5)),
                    "per_1000",
                ),
            }
        )
        for name, (value, unit) in metric_values.items():
            await self._upsert_metric(
                session,
                world_id,
                result.state.simulation_date,
                name,
                Decimal(str(value)),
                unit,
                result.state.tick,
            )

        if result.snapshot is not None:
            latest_database_sequence = (
                persisted[-1].sequence
                if persisted
                else (
                    await session.scalar(
                        select(func.max(SimulationEvent.sequence)).where(
                            SimulationEvent.world_id == world_id
                        )
                    )
                    or 0
                )
            )
            snapshot = result.snapshot
            session.add(
                PersistedSnapshot(
                    world_id=world_id,
                    event_sequence=latest_database_sequence,
                    simulation_date=result.state.simulation_date,
                    schema_version=1,
                    engine_version=snapshot.engine_version,
                    rng_state={
                        "algorithm": snapshot.rng_algorithm,
                        "version": snapshot.rng_version,
                        "system_manifest": list(snapshot.system_manifest),
                    },
                    state=snapshot.state,
                    checksum=snapshot.checksum,
                )
            )

    @staticmethod
    def _event(event: DomainEvent) -> CommittedEvent:
        return CommittedEvent(
            simulation_date=event.simulation_date,
            category=event.category,
            event_type=event.event_type,
            payload=cast(dict[str, Any], event.payload),
            engine_version=event.engine_version,
            schema_version=event.schema_version,
            actor_citizen_id=UUID(event.actor_id) if event.actor_id else None,
            target_citizen_id=UUID(event.target_id) if event.target_id else None,
            severity=event.severity,
            importance=event.importance,
        )

    @staticmethod
    async def _upsert_metric(
        session: AsyncSession,
        world_id: UUID,
        simulation_date: date,
        name: str,
        value: Decimal,
        unit: str,
        tick: int,
    ) -> None:
        metric = await session.scalar(
            select(WorldMetric).where(
                WorldMetric.world_id == world_id,
                WorldMetric.simulation_date == simulation_date,
                WorldMetric.name == name,
                WorldMetric.scope == "world",
                WorldMetric.entity_id == world_id,
            )
        )
        if metric is None:
            session.add(
                WorldMetric(
                    world_id=world_id,
                    simulation_date=simulation_date,
                    name=name,
                    scope="world",
                    entity_id=world_id,
                    value=value,
                    unit=unit,
                    labels={"tick": tick},
                )
            )
        else:
            metric.value = value
            metric.unit = unit
            metric.labels = {"tick": tick}

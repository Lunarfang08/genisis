import asyncio
import json
from collections.abc import AsyncIterator
from datetime import date
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Header, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import func, or_, select
from sqlalchemy.orm import selectinload

from genesis_api.api.dependencies import CsrfProtected, CurrentUser, SessionDep
from genesis_api.api.errors import ApiError
from genesis_api.api.schemas.simulation import (
    AIActivityResponse,
    CitizenProfileResponse,
    ControlRequest,
    ControlResponse,
    EventListResponse,
    EventResponse,
    GovernmentResponse,
    MemoryResponse,
    RelationshipResponse,
    ReplayStatusResponse,
    SnapshotResponse,
    WorldDashboardResponse,
)
from genesis_api.api.streaming import LiveUpdate
from genesis_api.db.models import (
    AIUsage,
    Business,
    Citizen,
    CitizenRelationship,
    Government,
    SimulationCommand,
    SimulationEvent,
    SimulationSnapshot,
    User,
    World,
    WorldMetric,
    WorldSettings,
)

router = APIRouter(prefix="/worlds/{world_id}", tags=["simulation"])


async def _owned_world(world_id: UUID, user: User, session: SessionDep) -> World:
    world = await session.scalar(
        select(World)
        .options(selectinload(World.settings))
        .where(World.id == world_id, World.owner_id == user.id)
    )
    if world is None:
        raise ApiError(404, "Not found", "The world does not exist.", "world_not_found")
    return world


def _event_response(event: SimulationEvent) -> EventResponse:
    return EventResponse.model_validate(event)


@router.get("/timeline", response_model=EventListResponse)
async def timeline(
    world_id: UUID,
    user: CurrentUser,
    session: SessionDep,
    citizen_id: UUID | None = None,
    city_id: UUID | None = None,
    category: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    minimum_importance: Annotated[int, Query(ge=0, le=100)] = 0,
    after_sequence: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> EventListResponse:
    await _owned_world(world_id, user, session)
    statement = select(SimulationEvent).where(
        SimulationEvent.world_id == world_id,
        SimulationEvent.sequence > after_sequence,
        SimulationEvent.importance >= minimum_importance,
    )
    if citizen_id is not None:
        statement = statement.where(
            or_(
                SimulationEvent.actor_citizen_id == citizen_id,
                SimulationEvent.target_citizen_id == citizen_id,
            )
        )
    if city_id is not None:
        statement = statement.where(SimulationEvent.city_id == city_id)
    if category is not None:
        statement = statement.where(SimulationEvent.category == category)
    if date_from is not None:
        statement = statement.where(SimulationEvent.simulation_date >= date_from)
    if date_to is not None:
        statement = statement.where(SimulationEvent.simulation_date <= date_to)
    events = (
        await session.scalars(statement.order_by(SimulationEvent.sequence).limit(limit))
    ).all()
    return EventListResponse(
        items=[_event_response(event) for event in events],
        next_sequence=events[-1].sequence if len(events) == limit else None,
    )


@router.get("/important-events", response_model=EventListResponse)
async def important_events(
    world_id: UUID,
    user: CurrentUser,
    session: SessionDep,
    after_sequence: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> EventListResponse:
    return await timeline(
        world_id,
        user,
        session,
        minimum_importance=75,
        after_sequence=after_sequence,
        limit=limit,
    )


@router.get("/snapshots", response_model=list[SnapshotResponse])
async def snapshots(
    world_id: UUID, user: CurrentUser, session: SessionDep
) -> list[SnapshotResponse]:
    await _owned_world(world_id, user, session)
    items = (
        await session.scalars(
            select(SimulationSnapshot)
            .where(SimulationSnapshot.world_id == world_id)
            .order_by(SimulationSnapshot.event_sequence.desc())
            .limit(100)
        )
    ).all()
    return [SnapshotResponse.model_validate(item) for item in items]


@router.get("/replay-status", response_model=ReplayStatusResponse)
async def replay_status(
    world_id: UUID, user: CurrentUser, session: SessionDep
) -> ReplayStatusResponse:
    await _owned_world(world_id, user, session)
    latest_event = (
        await session.scalar(
            select(func.max(SimulationEvent.sequence)).where(SimulationEvent.world_id == world_id)
        )
        or 0
    )
    snapshot = await session.scalar(
        select(SimulationSnapshot)
        .where(SimulationSnapshot.world_id == world_id)
        .order_by(SimulationSnapshot.event_sequence.desc())
        .limit(1)
    )
    snapshot_sequence = snapshot.event_sequence if snapshot else None
    return ReplayStatusResponse(
        world_id=world_id,
        latest_event_sequence=latest_event,
        latest_snapshot_sequence=snapshot_sequence,
        replay_event_count=latest_event - (snapshot_sequence or 0),
        compatible=snapshot is None or bool(snapshot.engine_version),
    )


@router.get("/citizens/{citizen_id}", response_model=CitizenProfileResponse)
async def citizen_profile(
    world_id: UUID,
    citizen_id: UUID,
    user: CurrentUser,
    session: SessionDep,
) -> CitizenProfileResponse:
    world = await _owned_world(world_id, user, session)
    citizen = await session.scalar(
        select(Citizen)
        .options(
            selectinload(Citizen.skills),
            selectinload(Citizen.beliefs),
            selectinload(Citizen.goals),
            selectinload(Citizen.memories),
        )
        .where(Citizen.id == citizen_id, Citizen.world_id == world_id)
    )
    if citizen is None:
        raise ApiError(404, "Not found", "The citizen does not exist.", "citizen_not_found")
    events = (
        await session.scalars(
            select(SimulationEvent)
            .where(
                SimulationEvent.world_id == world_id,
                or_(
                    SimulationEvent.actor_citizen_id == citizen_id,
                    SimulationEvent.target_citizen_id == citizen_id,
                ),
                SimulationEvent.importance >= 50,
            )
            .order_by(SimulationEvent.sequence.desc())
            .limit(20)
        )
    ).all()
    return CitizenProfileResponse(
        id=citizen.id,
        full_name=citizen.full_name,
        age=citizen.age_on(world.settings.simulation_date),
        lifecycle_status=citizen.lifecycle_status,
        education_level=citizen.education_level,
        employment_status=citizen.employment_status,
        household_id=citizen.household_id,
        employer_business_id=citizen.employer_business_id,
        income_minor=citizen.income_minor,
        wealth_minor=citizen.wealth_minor,
        health=citizen.health,
        happiness=citizen.happiness,
        reputation=citizen.reputation,
        personality={
            "openness": citizen.openness,
            "conscientiousness": citizen.conscientiousness,
            "extraversion": citizen.extraversion,
            "agreeableness": citizen.agreeableness,
            "neuroticism": citizen.neuroticism,
        },
        skills={item.name: item.proficiency for item in citizen.skills},
        beliefs={
            item.topic: {"position": item.position, "conviction": item.conviction}
            for item in citizen.beliefs
        },
        goals=[
            {
                "title": item.title,
                "status": item.status,
                "priority": item.priority,
                "target_date": item.target_date.isoformat() if item.target_date else None,
            }
            for item in citizen.goals
        ],
        memories=[
            MemoryResponse.model_validate(item)
            for item in sorted(
                citizen.memories,
                key=lambda memory: (memory.importance, memory.recall_score),
                reverse=True,
            )[:20]
        ],
        major_events=[_event_response(event) for event in events],
    )


@router.get("/citizens/{citizen_id}/history", response_model=EventListResponse)
async def citizen_history(
    world_id: UUID,
    citizen_id: UUID,
    user: CurrentUser,
    session: SessionDep,
    after_sequence: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> EventListResponse:
    return await timeline(
        world_id,
        user,
        session,
        citizen_id=citizen_id,
        after_sequence=after_sequence,
        limit=limit,
    )


@router.get(
    "/citizens/{citizen_id}/relationships",
    response_model=list[RelationshipResponse],
)
async def citizen_relationships(
    world_id: UUID,
    citizen_id: UUID,
    user: CurrentUser,
    session: SessionDep,
) -> list[RelationshipResponse]:
    await _owned_world(world_id, user, session)
    items = (
        await session.scalars(
            select(CitizenRelationship)
            .where(
                CitizenRelationship.world_id == world_id,
                CitizenRelationship.source_citizen_id == citizen_id,
            )
            .order_by(
                CitizenRelationship.is_active.desc(),
                CitizenRelationship.strength.desc(),
            )
        )
    ).all()
    return [RelationshipResponse.model_validate(item) for item in items]


@router.get("/dashboard", response_model=WorldDashboardResponse)
async def dashboard(
    world_id: UUID, user: CurrentUser, session: SessionDep
) -> WorldDashboardResponse:
    await _owned_world(world_id, user, session)
    citizens = (await session.scalars(select(Citizen).where(Citizen.world_id == world_id))).all()
    population = len(citizens)
    employed = sum(item.employment_status in {"employed", "self_employed"} for item in citizens)
    businesses = (
        await session.scalar(
            select(func.count())
            .select_from(Business)
            .where(Business.world_id == world_id, Business.is_active.is_(True))
        )
        or 0
    )
    government = await session.scalar(
        select(Government).where(Government.world_id == world_id, Government.scope == "world")
    )
    latest_date = await session.scalar(
        select(func.max(WorldMetric.simulation_date)).where(WorldMetric.world_id == world_id)
    )
    metric_rows = (
        (
            await session.scalars(
                select(WorldMetric).where(
                    WorldMetric.world_id == world_id,
                    WorldMetric.simulation_date == latest_date,
                    WorldMetric.scope == "world",
                )
            )
        ).all()
        if latest_date
        else []
    )
    return WorldDashboardResponse(
        population=population,
        employed=employed,
        unemployed=max(0, population - employed),
        average_income_minor=(
            sum(item.income_minor for item in citizens) // population if population else 0
        ),
        total_wealth_minor=sum(item.wealth_minor for item in citizens),
        average_health=(sum(item.health for item in citizens) / population if population else 0.0),
        average_happiness=(
            sum(item.happiness for item in citizens) / population if population else 0.0
        ),
        active_businesses=businesses,
        treasury_minor=government.treasury_minor if government else 0,
        latest_metrics={item.name: float(item.value) for item in metric_rows},
    )


@router.get("/government", response_model=GovernmentResponse)
async def government(world_id: UUID, user: CurrentUser, session: SessionDep) -> GovernmentResponse:
    await _owned_world(world_id, user, session)
    item = await session.scalar(
        select(Government)
        .options(selectinload(Government.laws))
        .where(Government.world_id == world_id, Government.scope == "world")
    )
    if item is None:
        raise ApiError(
            404, "Not found", "The world government is not initialized.", "government_not_found"
        )
    return GovernmentResponse(
        id=item.id,
        name=item.name,
        government_type=item.government_type,
        leader_citizen_id=item.leader_citizen_id,
        treasury_minor=item.treasury_minor,
        term_started_on=item.term_started_on,
        term_ends_on=item.term_ends_on,
        laws=[
            {
                "code": law.code,
                "title": law.title,
                "status": law.status,
                "enacted_on": law.enacted_on,
            }
            for law in item.laws
        ],
    )


@router.get("/ai/activity", response_model=AIActivityResponse)
async def ai_activity(world_id: UUID, user: CurrentUser, session: SessionDep) -> AIActivityResponse:
    await _owned_world(world_id, user, session)
    items = (await session.scalars(select(AIUsage).where(AIUsage.world_id == world_id))).all()
    providers: dict[str, int] = {}
    for item in items:
        providers[item.provider] = providers.get(item.provider, 0) + 1
    return AIActivityResponse(
        calls=len(items),
        cache_hits=sum(item.cache_hit for item in items),
        failures=sum(not item.succeeded for item in items),
        input_tokens=sum(item.input_tokens for item in items),
        output_tokens=sum(item.output_tokens for item in items),
        estimated_cost_micros=sum(item.estimated_cost_micros for item in items),
        providers=providers,
    )


@router.post("/controls", response_model=ControlResponse, status_code=202)
async def control(
    world_id: UUID,
    payload: ControlRequest,
    request: Request,
    user: CurrentUser,
    session: SessionDep,
    _csrf: CsrfProtected,
) -> ControlResponse:
    await _owned_world(world_id, user, session)
    settings = await session.scalar(
        select(WorldSettings).where(WorldSettings.world_id == world_id).with_for_update()
    )
    if settings is None:
        raise ApiError(
            409,
            "World not initialized",
            "The world has no simulation settings.",
            "world_not_initialized",
        )
    latest = (
        await session.scalar(
            select(func.max(SimulationCommand.sequence)).where(
                SimulationCommand.world_id == world_id
            )
        )
        or 0
    )
    command = SimulationCommand(
        world_id=world_id,
        sequence=latest + 1,
        command_type=payload.command,
        payload=payload.model_dump(mode="json", exclude_none=True),
    )
    if payload.command in {"start", "resume"}:
        settings.is_paused = False
    elif payload.command == "pause":
        settings.is_paused = True
    elif payload.command == "set_speed" and payload.speed is not None:
        settings.tick_rate = payload.speed
    session.add(command)
    await session.commit()
    update = LiveUpdate(
        sequence=command.sequence,
        channel="status",
        data={
            "command": payload.command,
            "is_paused": settings.is_paused,
            "speed": settings.tick_rate,
            "correlation_id": str(command.correlation_id),
        },
    )
    request.app.state.stream_hub.publish(str(world_id), update)
    return ControlResponse(
        id=command.id,
        sequence=command.sequence,
        command=command.command_type,
        accepted=True,
        is_paused=settings.is_paused,
        speed=settings.tick_rate,
        correlation_id=command.correlation_id,
    )


@router.get("/stream")
async def stream(
    world_id: UUID,
    request: Request,
    user: CurrentUser,
    session: SessionDep,
    channels: Annotated[str, Query()] = "status,events,metrics",
    last_event_id: Annotated[str | None, Header(alias="Last-Event-ID")] = None,
) -> StreamingResponse:
    await _owned_world(world_id, user, session)
    try:
        resume_sequence = max(0, int(last_event_id or "0"))
    except ValueError as exc:
        raise ApiError(
            400, "Invalid request", "Last-Event-ID must be an integer.", "invalid_event_id"
        ) from exc
    selected_channels = frozenset(
        channel.strip()
        for channel in channels.split(",")
        if channel.strip()
        in {"status", "events", "metrics", "citizens", "government", "economy", "ai"}
    )
    if not selected_channels:
        raise ApiError(422, "Invalid request", "No valid channels selected.", "invalid_channels")
    backlog = (
        await session.scalars(
            select(SimulationEvent)
            .where(
                SimulationEvent.world_id == world_id,
                SimulationEvent.sequence > resume_sequence,
            )
            .order_by(SimulationEvent.sequence)
            .limit(500)
        )
    ).all()
    client_id = str(uuid4())
    queue = request.app.state.stream_hub.subscribe(client_id, str(world_id), selected_channels)

    async def event_source() -> AsyncIterator[str]:
        try:
            for event in backlog:
                data = _event_response(event).model_dump(mode="json")
                yield (
                    f"id: {event.sequence}\nevent: events\n"
                    f"data: {json.dumps(data, separators=(',', ':'))}\n\n"
                )
            while not await request.is_disconnected():
                try:
                    update = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield (
                        f"id: {update.sequence}\nevent: {update.channel}\n"
                        f"data: {json.dumps(update.data, separators=(',', ':'))}\n\n"
                    )
                except TimeoutError:
                    yield ": heartbeat\n\n"
        finally:
            request.app.state.stream_hub.unsubscribe(client_id)

    return StreamingResponse(
        event_source(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
        },
    )

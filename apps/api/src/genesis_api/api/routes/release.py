import csv
import io
import json
from collections import Counter
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Query, Request
from fastapi.responses import PlainTextResponse, Response
from sqlalchemy import func, select

from genesis_api.api.dependencies import CurrentUser, SessionDep
from genesis_api.api.errors import ApiError
from genesis_api.api.schemas.release import (
    AdminOverview,
    AnalyticsResponse,
    CapacityProjection,
    CityMapPoint,
    CompareRequest,
    CompareResponse,
    EntityCompareResponse,
    MapLandmark,
    MetricPoint,
    MetricSeries,
    RegionMapItem,
    ScenarioTemplate,
    WorldMapResponse,
)
from genesis_api.db.models import (
    AIUsage,
    Business,
    Citizen,
    City,
    Government,
    Law,
    Region,
    SimulationCommand,
    SimulationEvent,
    SimulationOutbox,
    SimulationSnapshot,
    World,
    WorldMetric,
    WorldSettings,
)

router = APIRouter(tags=["release"])

SCENARIOS = (
    ScenarioTemplate(
        key="balanced",
        name="Balanced Society",
        description="Stable baseline with moderate pressures.",
        settings={
            "economic_difficulty": 50,
            "resource_abundance": 50,
            "disaster_frequency": 20,
            "social_volatility": 30,
        },
    ),
    ScenarioTemplate(
        key="economic_crisis",
        name="Economic Crisis",
        description="Low liquidity and severe market pressure.",
        settings={
            "economic_difficulty": 90,
            "resource_abundance": 35,
            "disaster_frequency": 20,
            "social_volatility": 65,
        },
    ),
    ScenarioTemplate(
        key="rapid_growth",
        name="Rapid Growth",
        description="Abundant resources and accelerating population.",
        settings={
            "economic_difficulty": 30,
            "resource_abundance": 85,
            "disaster_frequency": 15,
            "social_volatility": 35,
        },
    ),
    ScenarioTemplate(
        key="resource_scarcity",
        name="Resource Scarcity",
        description="Institutions adapt to constrained resources.",
        settings={
            "economic_difficulty": 75,
            "resource_abundance": 10,
            "disaster_frequency": 35,
            "social_volatility": 55,
        },
    ),
    ScenarioTemplate(
        key="political_instability",
        name="Political Instability",
        description="High civic volatility tests government legitimacy.",
        settings={
            "economic_difficulty": 60,
            "resource_abundance": 45,
            "disaster_frequency": 25,
            "social_volatility": 95,
        },
    ),
    ScenarioTemplate(
        key="disaster_prone",
        name="Disaster-Prone World",
        description="Frequent environmental incidents stress recovery.",
        settings={
            "economic_difficulty": 65,
            "resource_abundance": 40,
            "disaster_frequency": 95,
            "social_volatility": 60,
        },
    ),
    ScenarioTemplate(
        key="high_technology",
        name="High-Technology Society",
        description="Advanced infrastructure with strong productivity.",
        settings={
            "economic_difficulty": 35,
            "resource_abundance": 70,
            "disaster_frequency": 20,
            "social_volatility": 25,
        },
    ),
)


async def _owned_world(world_id: UUID, owner_id: UUID, session: SessionDep) -> World:
    world = await session.scalar(
        select(World).where(World.id == world_id, World.owner_id == owner_id)
    )
    if world is None:
        raise ApiError(404, "Not found", "The world does not exist.", "world_not_found")
    return world


@router.get("/world-scenarios", response_model=list[ScenarioTemplate])
async def scenario_templates(_user: CurrentUser) -> tuple[ScenarioTemplate, ...]:
    return SCENARIOS


@router.get("/capacity-projection", response_model=CapacityProjection)
async def capacity_projection(
    _user: CurrentUser,
    citizens: Annotated[int, Query(ge=10, le=50_000)] = 1_000,
) -> CapacityProjection:
    return CapacityProjection(
        citizen_count=citizens,
        estimated_memory_mb=max(64, round(citizens * 0.018)),
        estimated_tick_ms=max(10, round(citizens * 0.045)),
        recommended_tier="local"
        if citizens <= 1_000
        else "worker"
        if citizens <= 10_000
        else "dedicated",
    )


@router.get("/worlds/{world_id}/map", response_model=WorldMapResponse)
async def world_map(world_id: UUID, user: CurrentUser, session: SessionDep) -> WorldMapResponse:
    await _owned_world(world_id, user.id, session)
    regions = (
        await session.scalars(
            select(Region).where(Region.world_id == world_id).order_by(Region.name)
        )
    ).all()
    cities = (
        await session.scalars(select(City).where(City.world_id == world_id).order_by(City.name))
    ).all()
    population_rows = (
        await session.execute(
            select(Citizen.city_id, func.count(Citizen.id))
            .where(Citizen.world_id == world_id)
            .group_by(Citizen.city_id)
        )
    ).all()
    business_rows = (
        await session.execute(
            select(
                Business.city_id,
                func.count(Business.id),
                func.coalesce(func.sum(Business.cash_minor), 0),
            )
            .where(Business.world_id == world_id, Business.is_active.is_(True))
            .group_by(Business.city_id)
        )
    ).all()
    population: dict[UUID, int] = {row[0]: row[1] for row in population_rows}
    business: dict[UUID, tuple[int, int]] = {row[0]: (row[1], row[2]) for row in business_rows}
    incidents = (
        await session.scalars(
            select(SimulationEvent)
            .where(
                SimulationEvent.world_id == world_id,
                SimulationEvent.category.in_(("environment", "disease", "disaster")),
            )
            .order_by(SimulationEvent.sequence.desc())
            .limit(50)
        )
    ).all()
    activity = (
        await session.scalars(
            select(SimulationEvent)
            .where(
                SimulationEvent.world_id == world_id,
                SimulationEvent.category.in_(("migration", "economy", "government")),
            )
            .order_by(SimulationEvent.sequence.desc())
            .limit(100)
        )
    ).all()
    landmark_businesses = (
        await session.scalars(
            select(Business).where(
                Business.world_id == world_id,
                Business.industry.in_(("healthcare", "hospital", "education", "school")),
            )
        )
    ).all()
    civic_buildings = (
        await session.scalars(
            select(Government).where(
                Government.world_id == world_id, Government.city_id.is_not(None)
            )
        )
    ).all()
    latest = (
        await session.scalar(
            select(func.max(SimulationEvent.sequence)).where(SimulationEvent.world_id == world_id)
        )
        or 0
    )
    return WorldMapResponse(
        regions=[
            RegionMapItem(id=item.id, name=item.name, terrain=item.terrain, area_km2=item.area_km2)
            for item in regions
        ],
        cities=[
            CityMapPoint(
                id=item.id,
                region_id=item.region_id,
                name=item.name,
                latitude=float(item.latitude),
                longitude=float(item.longitude),
                population=population.get(item.id, 0),
                businesses=business.get(item.id, (0, 0))[0],
                economic_activity_minor=business.get(item.id, (0, 0))[1],
            )
            for item in cities
        ],
        incident_events=[
            {
                "id": str(item.id),
                "city_id": str(item.city_id) if item.city_id else None,
                "type": item.event_type,
                "severity": item.severity,
                "date": item.simulation_date.isoformat(),
            }
            for item in incidents
        ],
        activity_events=[
            {
                "id": str(item.id),
                "city_id": str(item.city_id) if item.city_id else None,
                "category": item.category,
                "type": item.event_type,
                "date": item.simulation_date.isoformat(),
            }
            for item in activity
        ],
        landmarks=[
            *[
                MapLandmark(
                    id=item.id,
                    city_id=item.city_id,
                    kind=("hospital" if item.industry in {"healthcare", "hospital"} else "school"),
                    name=item.name,
                )
                for item in landmark_businesses
            ],
            *[
                MapLandmark(id=item.id, city_id=item.city_id, kind="government", name=item.name)
                for item in civic_buildings
            ],
        ],
        generated_at_sequence=latest,
    )


@router.get("/worlds/{world_id}/analytics", response_model=AnalyticsResponse)
async def analytics(
    world_id: UUID,
    user: CurrentUser,
    session: SessionDep,
    metric: Annotated[list[str] | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=2_000)] = 500,
) -> AnalyticsResponse:
    await _owned_world(world_id, user.id, session)
    statement = select(WorldMetric).where(
        WorldMetric.world_id == world_id, WorldMetric.scope == "world"
    )
    if metric:
        statement = statement.where(WorldMetric.name.in_(metric))
    rows = (
        await session.scalars(statement.order_by(WorldMetric.simulation_date.desc()).limit(limit))
    ).all()
    grouped: dict[tuple[str, str], list[MetricPoint]] = {}
    for row in reversed(rows):
        grouped.setdefault((row.name, row.unit), []).append(
            MetricPoint(simulation_date=row.simulation_date, value=float(row.value))
        )
    categories = Counter(
        (
            await session.scalars(
                select(SimulationEvent.category).where(SimulationEvent.world_id == world_id)
            )
        ).all()
    )
    citizens = (await session.scalars(select(Citizen).where(Citizen.world_id == world_id))).all()
    buckets = Counter(
        "under_10k"
        if item.wealth_minor < 10_000
        else "10k_100k"
        if item.wealth_minor < 100_000
        else "100k_plus"
        for item in citizens
    )
    city_rows = (
        await session.execute(
            select(City.name, func.count(Citizen.id))
            .outerjoin(Citizen, Citizen.city_id == City.id)
            .where(City.world_id == world_id)
            .group_by(City.id, City.name)
        )
    ).all()
    return AnalyticsResponse(
        series=[
            MetricSeries(name=name, unit=unit, points=points)
            for (name, unit), points in sorted(grouped.items())
        ],
        event_categories=dict(categories),
        wealth_buckets=dict(buckets),
        city_population={row[0]: row[1] for row in city_rows},
    )


@router.post("/worlds/{world_id}/compare", response_model=CompareResponse)
async def compare(
    world_id: UUID, payload: CompareRequest, user: CurrentUser, session: SessionDep
) -> CompareResponse:
    await _owned_world(world_id, user.id, session)
    if payload.left_date == payload.right_date:
        raise ApiError(
            422, "Invalid comparison", "Choose two different dates.", "identical_compare_dates"
        )
    rows = (
        await session.scalars(
            select(WorldMetric).where(
                WorldMetric.world_id == world_id,
                WorldMetric.scope == "world",
                WorldMetric.name.in_(payload.metrics),
                WorldMetric.simulation_date.in_((payload.left_date, payload.right_date)),
            )
        )
    ).all()
    values = {(row.name, row.simulation_date): float(row.value) for row in rows}
    changes: dict[str, dict[str, float | None]] = {}
    for name in payload.metrics:
        left, right = values.get((name, payload.left_date)), values.get((name, payload.right_date))
        percent = None
        if left is not None and left != 0 and right is not None:
            percent = (right - left) / left * 100
        changes[name] = {
            "left": left,
            "right": right,
            "absolute": right - left if left is not None and right is not None else None,
            "percent": percent,
        }
    return CompareResponse(
        left_date=payload.left_date, right_date=payload.right_date, changes=changes
    )


@router.get("/worlds/{world_id}/compare/entities", response_model=EntityCompareResponse)
async def compare_entities(
    world_id: UUID,
    user: CurrentUser,
    session: SessionDep,
    kind: Annotated[str, Query(pattern="^(city|citizen|policy|run)$")],
    left_id: UUID,
    right_id: UUID,
) -> EntityCompareResponse:
    await _owned_world(world_id, user.id, session)
    if left_id == right_id:
        raise ApiError(
            422, "Invalid comparison", "Choose two different records.", "identical_compare_entities"
        )

    async def record(entity_id: UUID) -> dict[str, Any] | None:
        if kind == "city":
            city = await session.scalar(
                select(City).where(City.id == entity_id, City.world_id == world_id)
            )
            if city is None:
                return None
            population = (
                await session.scalar(
                    select(func.count()).select_from(Citizen).where(Citizen.city_id == entity_id)
                )
                or 0
            )
            businesses = (
                await session.scalar(
                    select(func.count())
                    .select_from(Business)
                    .where(Business.city_id == entity_id, Business.is_active.is_(True))
                )
                or 0
            )
            wealth = (
                await session.scalar(
                    select(func.coalesce(func.sum(Citizen.wealth_minor), 0)).where(
                        Citizen.city_id == entity_id
                    )
                )
                or 0
            )
            return {
                "id": str(city.id),
                "name": city.name,
                "population": population,
                "active_businesses": businesses,
                "citizen_wealth_minor": wealth,
            }
        if kind == "citizen":
            citizen = await session.scalar(
                select(Citizen).where(Citizen.id == entity_id, Citizen.world_id == world_id)
            )
            if citizen is None:
                return None
            return {
                "id": str(citizen.id),
                "name": citizen.full_name,
                "health": citizen.health,
                "happiness": citizen.happiness,
                "income_minor": citizen.income_minor,
                "wealth_minor": citizen.wealth_minor,
                "reputation": citizen.reputation,
            }
        if kind == "policy":
            law = await session.scalar(
                select(Law).where(Law.id == entity_id, Law.world_id == world_id)
            )
            if law is None:
                return None
            event_count = (
                await session.scalar(
                    select(func.count())
                    .select_from(SimulationEvent)
                    .where(
                        SimulationEvent.world_id == world_id,
                        SimulationEvent.payload["law_id"].as_string() == str(entity_id),
                    )
                )
                or 0
            )
            return {
                "id": str(law.id),
                "code": law.code,
                "title": law.title,
                "status": law.status,
                "enacted_on": law.enacted_on.isoformat() if law.enacted_on else None,
                "related_events": event_count,
            }
        snapshot = await session.scalar(
            select(SimulationSnapshot).where(
                SimulationSnapshot.id == entity_id, SimulationSnapshot.world_id == world_id
            )
        )
        if snapshot is None:
            return None
        return {
            "id": str(snapshot.id),
            "simulation_date": snapshot.simulation_date.isoformat(),
            "event_sequence": snapshot.event_sequence,
            "engine_version": snapshot.engine_version,
            "checksum": snapshot.checksum,
        }

    left = await record(left_id)
    right = await record(right_id)
    if left is None or right is None:
        raise ApiError(
            404,
            "Not found",
            "One or both comparison records do not exist.",
            "compare_entity_not_found",
        )
    return EntityCompareResponse(kind=kind, left=left, right=right)


@router.get("/worlds/{world_id}/export")
async def export_world(
    world_id: UUID,
    user: CurrentUser,
    session: SessionDep,
    format: Annotated[str, Query(pattern="^(json|csv|summary)$")] = "json",
) -> Response:
    world = await _owned_world(world_id, user.id, session)
    events = (
        await session.scalars(
            select(SimulationEvent)
            .where(SimulationEvent.world_id == world_id)
            .order_by(SimulationEvent.sequence)
        )
    ).all()
    if format == "csv":
        stream = io.StringIO()
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(("sequence", "date", "category", "event_type", "severity", "importance"))
        writer.writerows(
            (
                item.sequence,
                item.simulation_date,
                item.category,
                item.event_type,
                item.severity,
                item.importance,
            )
            for item in events
        )
        return PlainTextResponse(
            stream.getvalue(),
            media_type="text/csv",
            headers={
                "Content-Disposition": f'attachment; filename="genesis-{world_id}-events.csv"'
            },
        )
    settings = await session.scalar(select(WorldSettings).where(WorldSettings.world_id == world_id))
    payload: dict[str, Any] = {
        "schema_version": 1,
        "world": {
            "id": str(world.id),
            "name": world.name,
            "scenario": settings.scenario if settings else "unknown",
        },
        "event_count": len(events),
    }
    if format == "json":
        payload["events"] = [
            {
                "sequence": item.sequence,
                "simulation_date": item.simulation_date.isoformat(),
                "category": item.category,
                "event_type": item.event_type,
                "severity": item.severity,
                "importance": item.importance,
                "payload": item.payload,
            }
            for item in events
        ]
        return Response(
            json.dumps(payload, separators=(",", ":")),
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="genesis-{world_id}.json"'},
        )
    summary = (
        "GENESIS simulation summary\n"
        f"World: {world.name}\n"
        f"Scenario: {payload['world']['scenario']}\n"
        f"Committed events: {len(events)}\n"
    )
    return PlainTextResponse(
        summary,
        headers={"Content-Disposition": f'attachment; filename="genesis-{world_id}-summary.txt"'},
    )


@router.get("/admin/overview", response_model=AdminOverview)
async def admin_overview(request: Request, user: CurrentUser, session: SessionDep) -> AdminOverview:
    settings = request.app.state.settings
    if settings.is_production:
        raise ApiError(404, "Not found", "The endpoint does not exist.", "not_found")
    owned = (
        await session.scalar(
            select(func.count()).select_from(World).where(World.owner_id == user.id)
        )
        or 0
    )
    active = (
        await session.scalar(
            select(func.count())
            .select_from(WorldSettings)
            .join(World)
            .where(World.owner_id == user.id, WorldSettings.is_paused.is_(False))
        )
        or 0
    )
    pending = (
        await session.scalar(
            select(func.count())
            .select_from(SimulationCommand)
            .join(World)
            .where(World.owner_id == user.id, SimulationCommand.processed_at.is_(None))
        )
        or 0
    )
    outbox = (
        await session.scalar(
            select(func.count())
            .select_from(SimulationOutbox)
            .join(World)
            .where(World.owner_id == user.id, SimulationOutbox.published_at.is_(None))
        )
        or 0
    )
    ai_calls = (
        await session.scalar(
            select(func.count()).select_from(AIUsage).join(World).where(World.owner_id == user.id)
        )
        or 0
    )
    return AdminOverview(
        environment=settings.environment,
        owned_worlds=owned,
        active_simulations=active,
        pending_commands=pending,
        pending_outbox_events=outbox,
        connected_streams=request.app.state.stream_hub.connection_count,
        ai_calls=ai_calls,
    )

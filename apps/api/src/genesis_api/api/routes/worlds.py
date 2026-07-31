from uuid import UUID

from fastapi import APIRouter, status
from sqlalchemy import Select, select
from sqlalchemy.orm import selectinload

from genesis_api.api.dependencies import CsrfProtected, CurrentUser, SessionDep
from genesis_api.api.errors import ApiError
from genesis_api.api.schemas.worlds import (
    WorldCreateRequest,
    WorldListResponse,
    WorldResponse,
)
from genesis_api.db.models import World, WorldSettings
from genesis_api.services.world_initializer import WorldInitializer

router = APIRouter(prefix="/worlds", tags=["worlds"])


def _owned_world_query(world_id: UUID, owner_id: UUID) -> Select[tuple[World]]:
    return (
        select(World)
        .options(selectinload(World.settings))
        .where(World.id == world_id, World.owner_id == owner_id)
    )


@router.post("", response_model=WorldResponse, status_code=status.HTTP_201_CREATED)
async def create_world(
    payload: WorldCreateRequest,
    user: CurrentUser,
    session: SessionDep,
    _csrf: CsrfProtected,
) -> WorldResponse:
    world = World(owner_id=user.id, name=" ".join(payload.name.split()))
    world.settings = WorldSettings(
        seed=payload.seed,
        tick_rate=payload.tick_rate,
        initial_population=payload.initial_population,
        city_count=payload.city_count,
        scenario=payload.scenario,
        scenario_config=payload.model_dump(
            exclude={"name", "seed", "tick_rate", "initial_population", "city_count", "scenario"}
        ),
    )
    session.add(world)
    await session.flush()
    await WorldInitializer().initialize(session, world.id)
    await session.commit()
    created = await session.scalar(_owned_world_query(world.id, user.id))
    if created is None:
        raise RuntimeError("Created world could not be reloaded")
    return WorldResponse.model_validate(created)


@router.get("", response_model=WorldListResponse)
async def list_worlds(user: CurrentUser, session: SessionDep) -> WorldListResponse:
    worlds = (
        await session.scalars(
            select(World)
            .options(selectinload(World.settings))
            .where(World.owner_id == user.id)
            .order_by(World.created_at.desc())
        )
    ).all()
    return WorldListResponse(items=[WorldResponse.model_validate(world) for world in worlds])


@router.get("/{world_id}", response_model=WorldResponse)
async def get_world(
    world_id: UUID,
    user: CurrentUser,
    session: SessionDep,
) -> WorldResponse:
    world = await session.scalar(_owned_world_query(world_id, user.id))
    if world is None:
        raise ApiError(404, "Not found", "The world does not exist.", "world_not_found")
    return WorldResponse.model_validate(world)


@router.delete("/{world_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_world(
    world_id: UUID,
    user: CurrentUser,
    session: SessionDep,
    _csrf: CsrfProtected,
) -> None:
    world = await session.scalar(_owned_world_query(world_id, user.id))
    if world is None:
        raise ApiError(404, "Not found", "The world does not exist.", "world_not_found")
    await session.delete(world)
    await session.commit()

from collections.abc import Sequence
from typing import Protocol
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from genesis_api.db.models import Citizen, City, Household, Occupation, Region, World


class CivilizationRepository(Protocol):
    async def get_world(self, world_id: UUID) -> World | None: ...

    async def get_region(self, region_id: UUID) -> Region | None: ...

    async def get_city(self, city_id: UUID) -> City | None: ...

    async def get_household(self, household_id: UUID) -> Household | None: ...

    async def get_occupation(self, occupation_id: UUID) -> Occupation | None: ...

    async def add_region(self, region: Region) -> Region: ...

    async def add_city(self, city: City) -> City: ...

    async def add_citizen(self, citizen: Citizen) -> Citizen: ...

    async def list_citizens(
        self, world_id: UUID, *, offset: int, limit: int
    ) -> Sequence[Citizen]: ...


class SqlAlchemyCivilizationRepository:
    """SQLAlchemy implementation; transaction ownership stays with the service caller."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_world(self, world_id: UUID) -> World | None:
        return await self._session.get(World, world_id)

    async def get_region(self, region_id: UUID) -> Region | None:
        return await self._session.get(Region, region_id)

    async def get_city(self, city_id: UUID) -> City | None:
        return await self._session.get(City, city_id)

    async def get_household(self, household_id: UUID) -> Household | None:
        return await self._session.get(Household, household_id)

    async def get_occupation(self, occupation_id: UUID) -> Occupation | None:
        return await self._session.get(Occupation, occupation_id)

    async def add_region(self, region: Region) -> Region:
        self._session.add(region)
        await self._session.flush()
        return region

    async def add_city(self, city: City) -> City:
        self._session.add(city)
        await self._session.flush()
        return city

    async def add_citizen(self, citizen: Citizen) -> Citizen:
        self._session.add(citizen)
        await self._session.flush()
        return citizen

    async def list_citizens(
        self, world_id: UUID, *, offset: int = 0, limit: int = 100
    ) -> Sequence[Citizen]:
        query = (
            select(Citizen)
            .where(Citizen.world_id == world_id)
            .order_by(Citizen.id)
            .offset(offset)
            .limit(limit)
        )
        return (await self._session.scalars(query)).all()

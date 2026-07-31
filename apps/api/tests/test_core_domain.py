from collections.abc import AsyncIterator
from datetime import date

import pytest
from sqlalchemy.exc import IntegrityError

from genesis_api.db.base import Base
from genesis_api.db.manager import DatabaseManager
from genesis_api.db.models import Citizen, SimulationEvent
from genesis_api.domain.types import EmploymentStatus
from genesis_api.domain.validation import DomainValidationError
from genesis_api.repositories.domain import SqlAlchemyCivilizationRepository
from genesis_api.services.civilization import (
    BeliefInput,
    CivilizationService,
    CreateCitizenCommand,
    GoalInput,
    SkillInput,
)
from tests.factories import (
    city_factory,
    household_factory,
    occupation_factory,
    region_factory,
    user_factory,
    world_factory,
)


@pytest.fixture
async def domain_database() -> AsyncIterator[DatabaseManager]:
    manager = DatabaseManager("sqlite+aiosqlite:///:memory:")
    await manager.create_schema(Base)
    try:
        yield manager
    finally:
        await manager.close()


async def test_service_creates_normalized_citizen_aggregate(
    domain_database: DatabaseManager,
) -> None:
    async for session in domain_database.session():
        owner = user_factory()
        world = world_factory(owner=owner)
        session.add(world)
        await session.flush()
        region = region_factory(world=world)
        session.add(region)
        await session.flush()
        city = city_factory(world=world, region=region)
        session.add(city)
        await session.flush()
        household = household_factory(world=world, city=city)
        occupation = occupation_factory(world=world)
        session.add_all((household, occupation))
        await session.commit()

        service = CivilizationService(SqlAlchemyCivilizationRepository(session))
        citizen = await service.create_citizen(
            CreateCitizenCommand(
                world_id=world.id,
                city_id=city.id,
                household_id=household.id,
                occupation_id=occupation.id,
                given_name="  Mira ",
                family_name="  Arden  ",
                birth_date=date(2175, 6, 10),
                dna_seed=9081,
                employment_status=EmploymentStatus.EMPLOYED,
                health=91,
                happiness=74,
                skills=(SkillInput("Engineering", 82),),
                beliefs=(BeliefInput("Civic duty", "Mutual aid", 77),),
                goals=(GoalInput("Improve the water network", 85),),
            )
        )
        await session.commit()

        assert citizen.full_name == "Mira Arden"
        assert citizen.age_on(date(2200, 1, 1)) == 24
        assert citizen.skills[0].name == "Engineering"
        assert citizen.beliefs[0].conviction == 77
        assert citizen.goals[0].priority == 85
        assert len(await SqlAlchemyCivilizationRepository(session).list_citizens(world.id)) == 1


async def test_service_rejects_invalid_domain_state(
    domain_database: DatabaseManager,
) -> None:
    async for session in domain_database.session():
        owner = user_factory(email="validation@example.com")
        world = world_factory(owner=owner)
        session.add(world)
        await session.flush()
        region = region_factory(world=world)
        session.add(region)
        await session.flush()
        city = city_factory(world=world, region=region)
        session.add(city)
        await session.commit()
        service = CivilizationService(SqlAlchemyCivilizationRepository(session))

        with pytest.raises(DomainValidationError, match="occupation"):
            await service.create_citizen(
                CreateCitizenCommand(
                    world_id=world.id,
                    city_id=city.id,
                    given_name="Nia",
                    family_name="Vale",
                    birth_date=date(2170, 1, 1),
                    dna_seed=1,
                    employment_status=EmploymentStatus.EMPLOYED,
                )
            )

        with pytest.raises(DomainValidationError, match="birth_date"):
            await service.create_citizen(
                CreateCitizenCommand(
                    world_id=world.id,
                    city_id=city.id,
                    given_name="Future",
                    family_name="Citizen",
                    birth_date=date(2201, 1, 1),
                    dna_seed=2,
                )
            )


async def test_database_enforces_scores_and_event_ordering(
    domain_database: DatabaseManager,
) -> None:
    async for session in domain_database.session():
        owner = user_factory(email="constraints@example.com")
        world = world_factory(owner=owner)
        session.add(world)
        await session.flush()
        region = region_factory(world=world)
        session.add(region)
        await session.flush()
        city = city_factory(world=world, region=region)
        session.add(city)
        await session.flush()
        session.add(
            Citizen(
                world_id=world.id,
                city_id=city.id,
                given_name="Invalid",
                family_name="Health",
                birth_date=date(2180, 1, 1),
                dna_seed=9,
                health=101,
            )
        )
        with pytest.raises(IntegrityError):
            await session.commit()
        await session.rollback()

        first = SimulationEvent(
            world_id=world.id,
            sequence=1,
            simulation_date=date(2200, 1, 1),
            category="world",
            event_type="world.created",
        )
        duplicate = SimulationEvent(
            world_id=world.id,
            sequence=1,
            simulation_date=date(2200, 1, 1),
            category="world",
            event_type="world.duplicate",
        )
        session.add_all((first, duplicate))
        with pytest.raises(IntegrityError):
            await session.commit()

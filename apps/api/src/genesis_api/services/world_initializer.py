from datetime import date
from decimal import Decimal
from math import ceil
from typing import Any, cast
from uuid import NAMESPACE_URL, UUID, uuid5

from genesis_simulation.engine import SimulationEngine
from genesis_simulation.model import CitizenState, WorldState
from genesis_simulation.randomness import DeterministicRandom, state_to_json
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from genesis_api.db.models import (
    Business,
    Citizen,
    CitizenBelief,
    CitizenGoal,
    CitizenSkill,
    City,
    Government,
    Household,
    Law,
    Occupation,
    Region,
    SimulationSnapshot,
    World,
    WorldMetric,
)
from genesis_api.repositories.history import CommittedEvent, EventRepository

GIVEN_NAMES = (
    "Amina",
    "Arden",
    "Bao",
    "Cleo",
    "Dara",
    "Elias",
    "Farah",
    "Hugo",
    "Imani",
    "Jun",
    "Kaia",
    "Leon",
    "Mara",
    "Niko",
    "Orla",
    "Priya",
    "Quinn",
    "Ravi",
    "Sana",
    "Tariq",
    "Uma",
    "Vera",
    "Wren",
    "Yara",
)
FAMILY_NAMES = (
    "Aster",
    "Bennett",
    "Chen",
    "Das",
    "Elian",
    "Farouk",
    "Garcia",
    "Hale",
    "Ito",
    "Javed",
    "Khan",
    "Lowe",
    "Mensah",
    "Novak",
    "Okafor",
    "Park",
    "Reyes",
    "Singh",
    "Tan",
    "Usman",
    "Vale",
    "Wang",
    "Young",
    "Zaman",
)
CITY_NAMES = (
    "Solace",
    "Aurora",
    "Meridian",
    "Lumen",
    "Haven",
    "Verdant",
    "Concord",
    "Axiom",
    "Cinder",
    "Tidelock",
    "Northstar",
    "Emberfall",
)
OCCUPATIONS = (
    ("General Worker", "services", 10_000),
    ("Engineer", "infrastructure", 16_000),
    ("Educator", "education", 13_000),
    ("Clinician", "healthcare", 15_000),
    ("Grower", "agriculture", 11_000),
)


def stable_id(world_id: UUID, kind: str, index: int) -> UUID:
    return uuid5(NAMESPACE_URL, f"genesis:{world_id}:{kind}:{index}")


class WorldInitializer:
    """Creates a complete deterministic civilization from saved world settings."""

    async def initialize(self, session: AsyncSession, world_id: UUID) -> bool:
        world = await session.scalar(select(World).where(World.id == world_id).with_for_update())
        if world is None or world.settings is None:
            raise ValueError("world settings are missing")
        existing = await session.scalar(
            select(func.count()).select_from(City).where(City.world_id == world_id)
        )
        if existing:
            return False

        settings = world.settings
        settings.start_date = date(2200, 1, 1)
        settings.simulation_date = settings.start_date
        random = DeterministicRandom(seed=settings.seed)

        region_count = max(1, ceil(settings.city_count / 4))
        regions = [
            Region(
                id=stable_id(world_id, "region", index),
                world_id=world_id,
                name=f"Region {index + 1:02d}",
                terrain=("temperate", "coastal", "highland", "arid")[index % 4],
                area_km2=8_000 + random.randint(0, 12_000),
            )
            for index in range(region_count)
        ]
        session.add_all(regions)
        await session.flush()

        cities = [
            City(
                id=stable_id(world_id, "city", index),
                world_id=world_id,
                region_id=regions[index % region_count].id,
                name=(CITY_NAMES[index] if index < len(CITY_NAMES) else f"City {index + 1:02d}"),
                founded_year=2180 + random.randint(0, 19),
                latitude=Decimal(random.randint(-6500, 6500)) / 100,
                longitude=Decimal(random.randint(-16000, 16000)) / 100,
            )
            for index in range(settings.city_count)
        ]
        session.add_all(cities)
        occupations = [
            Occupation(
                id=stable_id(world_id, "occupation", index),
                world_id=world_id,
                name=name,
                sector=sector,
                minimum_education="secondary" if index else "none",
                base_salary_minor=salary,
            )
            for index, (name, sector, salary) in enumerate(OCCUPATIONS)
        ]
        session.add_all(occupations)
        await session.flush()

        household_count = ceil(settings.initial_population / 4)
        households = [
            Household(
                id=stable_id(world_id, "household", index),
                world_id=world_id,
                city_id=cities[index % len(cities)].id,
                name=f"Household {index + 1:05d}",
                wealth_minor=20_000 + random.randint(0, 180_000),
            )
            for index in range(household_count)
        ]
        session.add_all(households)
        await session.flush()

        citizens: list[Citizen] = []
        for index in range(settings.initial_population):
            household = households[index // 4]
            age = random.randint(1, 88)
            lifecycle = "child" if age < 18 else "adult" if age < 65 else "elder"
            employed = lifecycle == "adult" and random.random() < 0.72
            occupation = occupations[random.choice_index(len(occupations))] if employed else None
            citizen = Citizen(
                id=stable_id(world_id, "citizen", index),
                world_id=world_id,
                city_id=household.city_id,
                household_id=household.id,
                occupation_id=occupation.id if occupation else None,
                given_name=GIVEN_NAMES[random.choice_index(len(GIVEN_NAMES))],
                family_name=FAMILY_NAMES[random.choice_index(len(FAMILY_NAMES))],
                birth_date=date(2200 - age, 1 + random.randint(0, 11), 1 + random.randint(0, 27)),
                biological_sex=("female", "male", "intersex")[random.randint(0, 2)],
                lifecycle_status=lifecycle,
                education_level=(
                    "primary"
                    if age < 14
                    else "secondary"
                    if age < 22
                    else ("vocational", "tertiary", "secondary")[random.randint(0, 2)]
                ),
                employment_status=(
                    "employed"
                    if employed
                    else "retired"
                    if lifecycle == "elder"
                    else "not_in_workforce"
                    if lifecycle == "child"
                    else "unemployed"
                ),
                income_minor=occupation.base_salary_minor if occupation else 0,
                wealth_minor=5_000 + random.randint(0, 250_000),
                health=55 + random.randint(0, 45),
                happiness=35 + random.randint(0, 55),
                reputation=random.randint(-15, 40),
                openness=random.randint(20, 90),
                conscientiousness=random.randint(20, 90),
                extraversion=random.randint(20, 90),
                agreeableness=random.randint(20, 90),
                neuroticism=random.randint(10, 80),
                dna_seed=random.randint(0, 2_147_483_647),
            )
            citizen.skills = [CitizenSkill(name="adaptability", proficiency=random.randint(20, 90))]
            citizen.beliefs = [
                CitizenBelief(
                    topic="civic_trust",
                    position=("supportive", "neutral", "skeptical")[random.randint(0, 2)],
                    conviction=random.randint(20, 90),
                )
            ]
            citizen.goals = [
                CitizenGoal(
                    title=("Complete education" if lifecycle == "child" else "Improve wellbeing"),
                    priority=random.randint(35, 85),
                )
            ]
            citizens.append(citizen)
        session.add_all(citizens)
        await session.flush()

        industries = ("agriculture", "manufacturing", "services", "healthcare", "education")
        businesses: list[Business] = []
        for city_index, city in enumerate(cities):
            for business_index, industry in enumerate(industries):
                businesses.append(
                    Business(
                        id=stable_id(world_id, f"business-{city_index}", business_index),
                        world_id=world_id,
                        city_id=city.id,
                        owner_citizen_id=citizens[
                            (city_index * 7 + business_index) % len(citizens)
                        ].id,
                        name=f"{city.name} {industry.title()} Cooperative",
                        industry=industry,
                        cash_minor=250_000 + random.randint(0, 1_000_000),
                        founded_on=settings.start_date,
                    )
                )
        session.add_all(businesses)

        government = Government(
            id=stable_id(world_id, "government", 0),
            world_id=world_id,
            name=f"{world.name} Assembly",
            scope="world",
            government_type="democracy",
            leader_citizen_id=citizens[0].id,
            treasury_minor=1_000_000,
            term_started_on=settings.start_date,
            term_ends_on=date(2204, 1, 1),
        )
        government.laws = [
            Law(
                id=stable_id(world_id, "law", 0),
                world_id=world_id,
                code="FOUNDATION-001",
                title="Civic Foundation Act",
                text="Establishes the initial democratic institutions of the world.",
                status="active",
                enacted_on=settings.start_date,
            )
        ]
        session.add(government)

        initial_state = WorldState(
            world_id=str(world_id),
            seed=settings.seed,
            simulation_date=settings.start_date,
            citizens={
                str(item.id): CitizenState(
                    id=str(item.id),
                    birth_date=item.birth_date,
                    lifecycle_status=item.lifecycle_status,
                    health=item.health,
                    happiness=item.happiness,
                    employment_status=item.employment_status,
                    occupation=(
                        next(
                            (
                                occupation.name
                                for occupation in occupations
                                if occupation.id == item.occupation_id
                            ),
                            None,
                        )
                    ),
                    income_minor=item.income_minor,
                    wealth_minor=item.wealth_minor,
                    relationship_strength=50,
                )
                for item in citizens
            },
            paused=True,
            treasury_minor=government.treasury_minor,
        )
        engine = SimulationEngine(initial_state)
        settings.rng_state = cast(list[Any], state_to_json(engine.state.rng_state))
        settings.simulation_tick = 0
        settings.event_sequence = 0
        snapshot = engine.snapshot()
        session.add(
            SimulationSnapshot(
                world_id=world_id,
                event_sequence=0,
                simulation_date=settings.start_date,
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
        averages = {
            "population": settings.initial_population,
            "employed_population": sum(item.employment_status == "employed" for item in citizens),
            "social_cohesion": 50,
            "environmental_quality": 70,
            "gdp_minor": sum(item.income_minor for item in citizens),
            "government_approval": 50,
            "crime_rate": 0,
            "environmental_risk": 30,
        }
        for name, value in averages.items():
            session.add(
                WorldMetric(
                    world_id=world_id,
                    simulation_date=settings.start_date,
                    name=name,
                    scope="world",
                    entity_id=world_id,
                    value=Decimal(value),
                    unit=(
                        "citizens"
                        if "population" in name
                        else "minor_units"
                        if name == "gdp_minor"
                        else "score"
                    ),
                )
            )
        await EventRepository(session).append(
            world_id,
            (
                CommittedEvent(
                    simulation_date=settings.start_date,
                    category="history",
                    event_type="world.civilization_initialized",
                    payload={
                        "population": settings.initial_population,
                        "cities": settings.city_count,
                        "scenario": settings.scenario,
                    },
                    engine_version="1.0.0",
                    severity="notice",
                    importance=100,
                ),
            ),
        )
        settings.event_sequence = 1
        return True

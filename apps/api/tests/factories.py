from datetime import date
from uuid import uuid4

from genesis_api.db.models import (
    City,
    Household,
    Occupation,
    Region,
    User,
    World,
    WorldSettings,
)


def user_factory(*, email: str = "founder@example.com") -> User:
    return User(
        email=email,
        display_name="Domain Founder",
        password_hash="not-used-by-domain-tests",
    )


def world_factory(*, owner: User, name: str = "Aurora", seed: int = 42) -> World:
    world = World(owner=owner, name=name)
    world.settings = WorldSettings(
        seed=seed,
        tick_rate=1,
        start_date=date(2200, 1, 1),
        simulation_date=date(2200, 1, 1),
    )
    return world


def region_factory(*, world: World, name: str = "North Reach") -> Region:
    return Region(world_id=world.id, name=name, terrain="temperate", area_km2=12_000)


def city_factory(*, world: World, region: Region, name: str = "Solace") -> City:
    return City(
        world_id=world.id,
        region_id=region.id,
        name=name,
        founded_year=2190,
    )


def household_factory(*, world: World, city: City, name: str = "Arden") -> Household:
    return Household(
        world_id=world.id,
        city_id=city.id,
        name=name,
        wealth_minor=25_000,
    )


def occupation_factory(*, world: World, name: str = "Engineer") -> Occupation:
    return Occupation(
        id=uuid4(),
        world_id=world.id,
        name=name,
        sector="infrastructure",
        base_salary_minor=8_000,
    )

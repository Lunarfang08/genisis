from dataclasses import dataclass
from datetime import date
from uuid import UUID

from genesis_api.db.models import Citizen, CitizenBelief, CitizenGoal, CitizenSkill, City, Region
from genesis_api.domain.types import (
    BiologicalSex,
    EducationLevel,
    EmploymentStatus,
    LifecycleStatus,
)
from genesis_api.domain.validation import (
    DomainValidationError,
    normalized_name,
    validate_birth_date,
    validate_score,
)
from genesis_api.repositories.domain import CivilizationRepository


@dataclass(frozen=True, slots=True)
class SkillInput:
    name: str
    proficiency: int


@dataclass(frozen=True, slots=True)
class BeliefInput:
    topic: str
    position: str
    conviction: int


@dataclass(frozen=True, slots=True)
class GoalInput:
    title: str
    priority: int = 50


@dataclass(frozen=True, slots=True)
class CreateCitizenCommand:
    world_id: UUID
    city_id: UUID
    given_name: str
    family_name: str
    birth_date: date
    dna_seed: int
    household_id: UUID | None = None
    occupation_id: UUID | None = None
    biological_sex: BiologicalSex = BiologicalSex.UNSPECIFIED
    lifecycle_status: LifecycleStatus = LifecycleStatus.ADULT
    education_level: EducationLevel = EducationLevel.NONE
    employment_status: EmploymentStatus = EmploymentStatus.NOT_IN_WORKFORCE
    health: int = 100
    happiness: int = 50
    reputation: int = 0
    skills: tuple[SkillInput, ...] = ()
    beliefs: tuple[BeliefInput, ...] = ()
    goals: tuple[GoalInput, ...] = ()


class CivilizationService:
    """Validates cross-entity invariants before state reaches the database."""

    def __init__(self, repository: CivilizationRepository) -> None:
        self._repository = repository

    async def create_region(
        self, world_id: UUID, *, name: str, terrain: str, area_km2: int
    ) -> Region:
        if await self._repository.get_world(world_id) is None:
            raise DomainValidationError("world does not exist")
        if area_km2 <= 0:
            raise DomainValidationError("area_km2 must be positive")
        region = Region(
            world_id=world_id,
            name=normalized_name(name),
            terrain=normalized_name(terrain, field="terrain", maximum=40).lower(),
            area_km2=area_km2,
        )
        return await self._repository.add_region(region)

    async def create_city(
        self, world_id: UUID, region_id: UUID, *, name: str, founded_year: int = 0
    ) -> City:
        region = await self._repository.get_region(region_id)
        if region is None or region.world_id != world_id:
            raise DomainValidationError("region does not belong to world")
        if founded_year < 0:
            raise DomainValidationError("founded_year cannot be negative")
        city = City(
            world_id=world_id,
            region_id=region_id,
            name=normalized_name(name),
            founded_year=founded_year,
        )
        return await self._repository.add_city(city)

    async def create_citizen(self, command: CreateCitizenCommand) -> Citizen:
        world = await self._repository.get_world(command.world_id)
        if world is None or world.settings is None:
            raise DomainValidationError("world does not exist or has no settings")
        city = await self._repository.get_city(command.city_id)
        if city is None or city.world_id != command.world_id:
            raise DomainValidationError("city does not belong to world")

        if command.household_id is not None:
            household = await self._repository.get_household(command.household_id)
            if (
                household is None
                or household.world_id != command.world_id
                or household.city_id != command.city_id
            ):
                raise DomainValidationError("household does not belong to citizen's city")

        if command.occupation_id is not None:
            occupation = await self._repository.get_occupation(command.occupation_id)
            if occupation is None or occupation.world_id != command.world_id:
                raise DomainValidationError("occupation does not belong to world")

        if (
            command.employment_status in {EmploymentStatus.EMPLOYED, EmploymentStatus.SELF_EMPLOYED}
            and command.occupation_id is None
        ):
            raise DomainValidationError("working citizens require an occupation")

        validate_birth_date(command.birth_date, world.settings.simulation_date)
        health = validate_score(command.health, field="health")
        happiness = validate_score(command.happiness, field="happiness")
        reputation = validate_score(
            command.reputation, field="reputation", minimum=-100, maximum=100
        )

        skill_names = [
            normalized_name(item.name, field="skill", maximum=80) for item in command.skills
        ]
        if len(set(name.casefold() for name in skill_names)) != len(skill_names):
            raise DomainValidationError("skill names must be unique per citizen")
        belief_topics = [
            normalized_name(item.topic, field="belief topic", maximum=80)
            for item in command.beliefs
        ]
        if len(set(topic.casefold() for topic in belief_topics)) != len(belief_topics):
            raise DomainValidationError("belief topics must be unique per citizen")

        citizen = Citizen(
            world_id=command.world_id,
            city_id=command.city_id,
            household_id=command.household_id,
            occupation_id=command.occupation_id,
            given_name=normalized_name(command.given_name, field="given_name", maximum=80),
            family_name=normalized_name(command.family_name, field="family_name", maximum=80),
            birth_date=command.birth_date,
            dna_seed=command.dna_seed,
            biological_sex=command.biological_sex.value,
            lifecycle_status=command.lifecycle_status.value,
            education_level=command.education_level.value,
            employment_status=command.employment_status.value,
            health=health,
            happiness=happiness,
            reputation=reputation,
        )
        citizen.skills = [
            CitizenSkill(
                name=name,
                proficiency=validate_score(item.proficiency, field=f"{name} proficiency"),
            )
            for name, item in zip(skill_names, command.skills, strict=True)
        ]
        citizen.beliefs = [
            CitizenBelief(
                topic=topic,
                position=normalized_name(item.position, field="belief position"),
                conviction=validate_score(item.conviction, field=f"{topic} conviction"),
            )
            for topic, item in zip(belief_topics, command.beliefs, strict=True)
        ]
        citizen.goals = [
            CitizenGoal(
                title=normalized_name(item.title, field="goal", maximum=160),
                priority=validate_score(item.priority, field="goal priority"),
            )
            for item in command.goals
        ]
        return await self._repository.add_citizen(citizen)

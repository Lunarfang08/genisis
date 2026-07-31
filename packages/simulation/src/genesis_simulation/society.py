from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum

from genesis_simulation.randomness import DeterministicRandom


class RelationshipType(StrEnum):
    PARENT = "parent"
    CHILD = "child"
    SIBLING = "sibling"
    PARTNER = "partner"
    SPOUSE = "spouse"
    FRIEND = "friend"
    RIVAL = "rival"
    COLLEAGUE = "colleague"
    EMPLOYER = "employer"
    EMPLOYEE = "employee"
    POLITICAL_ALLY = "political_ally"
    POLITICAL_OPPONENT = "political_opponent"


@dataclass(slots=True)
class LifeProfile:
    citizen_id: str
    birth_date: date
    household_id: str | None = None
    education_progress: int = 0
    skill: int = 0
    health: int = 100
    happiness: int = 50
    status: str = "child"
    employment_status: str = "not_in_workforce"
    dependents: int = 0
    wealth_minor: int = 0

    def age_on(self, on_date: date) -> int:
        years = on_date.year - self.birth_date.year
        return years - ((on_date.month, on_date.day) < (self.birth_date.month, self.birth_date.day))


@dataclass(frozen=True, slots=True)
class LifecycleConfig:
    adulthood_age: int = 18
    retirement_age: int = 65
    daily_education_gain: int = 1
    base_illness_per_10k: int = 2
    elder_illness_per_10k: int = 20
    mortality_health_threshold: int = 5


def advance_lifecycle(
    profile: LifeProfile,
    on_date: date,
    random: DeterministicRandom,
    config: LifecycleConfig | None = None,
) -> tuple[str, ...]:
    """Apply one deterministic lifecycle day and return canonical event names."""

    config = config or LifecycleConfig()
    if profile.status == "deceased":
        return ()
    events: list[str] = []
    age = profile.age_on(on_date)
    if age < config.adulthood_age:
        profile.status = "child"
        old_progress = profile.education_progress
        profile.education_progress = min(
            100, profile.education_progress + config.daily_education_gain
        )
        if profile.education_progress != old_progress:
            profile.skill = min(100, profile.skill + (profile.education_progress // 25))
    elif age < config.retirement_age:
        if profile.status != "adult":
            events.append("CitizenReachedAdulthood")
        profile.status = "adult"
        if profile.employment_status == "not_in_workforce":
            profile.employment_status = "unemployed"
    else:
        if profile.status != "elder":
            events.append("CitizenRetired")
        profile.status = "elder"
        profile.employment_status = "retired"

    illness_chance = (
        config.elder_illness_per_10k if profile.status == "elder" else config.base_illness_per_10k
    )
    if random.randint(1, 10_000) <= illness_chance:
        profile.health = max(0, profile.health - random.randint(5, 20))
        events.append("CitizenBecameIll")
    if profile.health <= config.mortality_health_threshold:
        profile.status = "deceased"
        profile.employment_status = "not_in_workforce"
        events.append("CitizenDied")
    return tuple(events)


@dataclass(slots=True)
class Relationship:
    source_id: str
    target_id: str
    type: RelationshipType
    started_on: date
    strength: int = 50
    trust: int = 50
    familiarity: int = 1
    conflict: int = 0
    last_interaction: date | None = None
    active: bool = True

    def __post_init__(self) -> None:
        if self.source_id == self.target_id:
            raise ValueError("self relationships are not allowed")
        for name in ("strength", "trust", "familiarity", "conflict"):
            if not 0 <= getattr(self, name) <= 100:
                raise ValueError(f"{name} must be between 0 and 100")


_RECIPROCAL = {
    RelationshipType.PARENT: RelationshipType.CHILD,
    RelationshipType.CHILD: RelationshipType.PARENT,
    RelationshipType.EMPLOYER: RelationshipType.EMPLOYEE,
    RelationshipType.EMPLOYEE: RelationshipType.EMPLOYER,
}


@dataclass(slots=True)
class RelationshipGraph:
    _edges: dict[tuple[str, str, RelationshipType], Relationship] = field(default_factory=dict)

    def connect(self, relationship: Relationship) -> tuple[Relationship, Relationship]:
        key = (relationship.source_id, relationship.target_id, relationship.type)
        if key in self._edges:
            raise ValueError("relationship already exists")
        reciprocal_type = _RECIPROCAL.get(relationship.type, relationship.type)
        reciprocal = Relationship(
            source_id=relationship.target_id,
            target_id=relationship.source_id,
            type=reciprocal_type,
            started_on=relationship.started_on,
            strength=relationship.strength,
            trust=relationship.trust,
            familiarity=relationship.familiarity,
            conflict=relationship.conflict,
            last_interaction=relationship.last_interaction,
        )
        self._edges[key] = relationship
        self._edges[(reciprocal.source_id, reciprocal.target_id, reciprocal.type)] = reciprocal
        return relationship, reciprocal

    def connections(self, citizen_id: str) -> tuple[Relationship, ...]:
        return tuple(
            edge
            for key, edge in sorted(
                self._edges.items(), key=lambda item: (item[0][1], item[0][2].value)
            )
            if key[0] == citizen_id and edge.active
        )

    def decay(self, days: int) -> None:
        if days < 0:
            raise ValueError("days cannot be negative")
        loss = days // 30
        for edge in self._edges.values():
            if edge.type not in {
                RelationshipType.PARENT,
                RelationshipType.CHILD,
                RelationshipType.SIBLING,
                RelationshipType.SPOUSE,
            }:
                edge.familiarity = max(0, edge.familiarity - loss)
                edge.strength = max(0, edge.strength - loss)

    def family_tree(self, citizen_id: str, max_depth: int = 4) -> dict[str, tuple[str, ...]]:
        if not 1 <= max_depth <= 10:
            raise ValueError("max_depth must be between 1 and 10")
        result: dict[str, tuple[str, ...]] = {}
        frontier = [citizen_id]
        visited = {citizen_id}
        for _ in range(max_depth):
            next_frontier: list[str] = []
            for current in sorted(frontier):
                family = tuple(
                    edge.target_id
                    for edge in self.connections(current)
                    if edge.type
                    in {
                        RelationshipType.PARENT,
                        RelationshipType.CHILD,
                        RelationshipType.SIBLING,
                        RelationshipType.SPOUSE,
                    }
                )
                result[current] = family
                for relative in family:
                    if relative not in visited:
                        visited.add(relative)
                        next_frontier.append(relative)
            frontier = next_frontier
            if not frontier:
                break
        return result

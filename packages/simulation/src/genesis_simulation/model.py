from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum
from typing import cast

from genesis_simulation.randomness import RandomStateValue, state_from_json, state_to_json

type JsonScalar = str | int | float | bool | None
type JsonValue = JsonScalar | list[JsonValue] | dict[str, JsonValue]


class CommandType(StrEnum):
    TICK = "tick"
    PAUSE = "pause"
    RESUME = "resume"
    STEP = "step"
    SET_SPEED = "set_speed"
    RESET = "reset"


@dataclass(frozen=True, slots=True)
class EngineCommand:
    type: CommandType
    value: int | None = None

    @classmethod
    def tick(cls) -> "EngineCommand":
        return cls(CommandType.TICK)

    @classmethod
    def pause(cls) -> "EngineCommand":
        return cls(CommandType.PAUSE)

    @classmethod
    def resume(cls) -> "EngineCommand":
        return cls(CommandType.RESUME)

    @classmethod
    def step(cls) -> "EngineCommand":
        return cls(CommandType.STEP)

    @classmethod
    def set_speed(cls, speed: int) -> "EngineCommand":
        return cls(CommandType.SET_SPEED, speed)

    @classmethod
    def reset(cls) -> "EngineCommand":
        return cls(CommandType.RESET)


@dataclass(frozen=True, slots=True)
class EngineConfig:
    engine_version: str = "1.0.0"
    days_per_tick: int = 1
    citizen_batch_size: int = 500
    snapshot_interval: int = 30
    minimum_speed: int = 1
    maximum_speed: int = 60

    def __post_init__(self) -> None:
        if self.days_per_tick <= 0:
            raise ValueError("days_per_tick must be positive")
        if self.citizen_batch_size <= 0:
            raise ValueError("citizen_batch_size must be positive")
        if self.snapshot_interval < 0:
            raise ValueError("snapshot_interval cannot be negative")
        if self.minimum_speed <= 0 or self.maximum_speed < self.minimum_speed:
            raise ValueError("invalid speed range")


@dataclass(slots=True)
class CitizenState:
    id: str
    birth_date: date
    lifecycle_status: str = "adult"
    health: int = 100
    happiness: int = 50
    employment_status: str = "unemployed"
    occupation: str | None = None
    income_minor: int = 0
    wealth_minor: int = 0
    relationship_strength: int = 50

    def to_dict(self) -> dict[str, JsonValue]:
        return {
            "id": self.id,
            "birth_date": self.birth_date.isoformat(),
            "lifecycle_status": self.lifecycle_status,
            "health": self.health,
            "happiness": self.happiness,
            "employment_status": self.employment_status,
            "occupation": self.occupation,
            "income_minor": self.income_minor,
            "wealth_minor": self.wealth_minor,
            "relationship_strength": self.relationship_strength,
        }

    @classmethod
    def from_dict(cls, value: dict[str, JsonValue]) -> "CitizenState":
        return cls(
            id=cast(str, value["id"]),
            birth_date=date.fromisoformat(cast(str, value["birth_date"])),
            lifecycle_status=cast(str, value["lifecycle_status"]),
            health=cast(int, value["health"]),
            happiness=cast(int, value["happiness"]),
            employment_status=cast(str, value["employment_status"]),
            occupation=cast(str | None, value["occupation"]),
            income_minor=cast(int, value["income_minor"]),
            wealth_minor=cast(int, value["wealth_minor"]),
            relationship_strength=cast(int, value["relationship_strength"]),
        )


@dataclass(slots=True)
class WorldState:
    world_id: str
    seed: int
    simulation_date: date
    citizens: dict[str, CitizenState] = field(default_factory=dict)
    tick: int = 0
    event_sequence: int = 0
    paused: bool = False
    speed: int = 1
    treasury_minor: int = 0
    social_cohesion: int = 50
    environmental_quality: int = 70
    rng_state: RandomStateValue | None = None

    def to_dict(self) -> dict[str, JsonValue]:
        rng_json = state_to_json(self.rng_state) if self.rng_state is not None else None
        return {
            "world_id": self.world_id,
            "seed": self.seed,
            "simulation_date": self.simulation_date.isoformat(),
            "citizens": {
                citizen_id: self.citizens[citizen_id].to_dict()
                for citizen_id in sorted(self.citizens)
            },
            "tick": self.tick,
            "event_sequence": self.event_sequence,
            "paused": self.paused,
            "speed": self.speed,
            "treasury_minor": self.treasury_minor,
            "social_cohesion": self.social_cohesion,
            "environmental_quality": self.environmental_quality,
            "rng_state": cast(JsonValue, rng_json),
        }

    @classmethod
    def from_dict(cls, value: dict[str, JsonValue]) -> "WorldState":
        citizen_values = cast(dict[str, JsonValue], value["citizens"])
        rng_json = cast(int | None | list[object], value["rng_state"])
        return cls(
            world_id=cast(str, value["world_id"]),
            seed=cast(int, value["seed"]),
            simulation_date=date.fromisoformat(cast(str, value["simulation_date"])),
            citizens={
                citizen_id: CitizenState.from_dict(cast(dict[str, JsonValue], citizen))
                for citizen_id, citizen in citizen_values.items()
            },
            tick=cast(int, value["tick"]),
            event_sequence=cast(int, value["event_sequence"]),
            paused=cast(bool, value["paused"]),
            speed=cast(int, value["speed"]),
            treasury_minor=cast(int, value["treasury_minor"]),
            social_cohesion=cast(int, value["social_cohesion"]),
            environmental_quality=cast(int, value["environmental_quality"]),
            rng_state=state_from_json(rng_json) if rng_json is not None else None,
        )


@dataclass(frozen=True, slots=True)
class StateChange:
    scope: str
    entity_id: str | None
    field: str
    value: JsonScalar


@dataclass(frozen=True, slots=True)
class EventDraft:
    category: str
    event_type: str
    payload: dict[str, JsonValue]
    actor_id: str | None = None
    target_id: str | None = None
    importance: int = 0
    severity: str = "info"


@dataclass(frozen=True, slots=True)
class DomainEvent:
    id: str
    world_id: str
    sequence: int
    tick: int
    simulation_date: date
    category: str
    event_type: str
    payload: dict[str, JsonValue]
    engine_version: str
    schema_version: int = 1
    actor_id: str | None = None
    target_id: str | None = None
    importance: int = 0
    severity: str = "info"


@dataclass(frozen=True, slots=True)
class MetricPoint:
    name: str
    value: int | float
    unit: str
    scope: str = "world"
    entity_id: str | None = None


@dataclass(frozen=True, slots=True)
class SystemResult:
    changes: tuple[StateChange, ...] = ()
    events: tuple[EventDraft, ...] = ()
    metrics: tuple[MetricPoint, ...] = ()


@dataclass(frozen=True, slots=True)
class SimulationSnapshot:
    world_id: str
    tick: int
    event_sequence: int
    engine_version: str
    rng_algorithm: str
    rng_version: int
    system_manifest: tuple[str, ...]
    state: dict[str, JsonValue]
    checksum: str


@dataclass(frozen=True, slots=True)
class EngineResult:
    command: EngineCommand
    state: WorldState
    events: tuple[DomainEvent, ...] = ()
    metrics: tuple[MetricPoint, ...] = ()
    snapshot: SimulationSnapshot | None = None
    advanced: bool = False

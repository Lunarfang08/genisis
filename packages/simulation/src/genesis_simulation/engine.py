from copy import deepcopy
from uuid import NAMESPACE_URL, uuid5

from genesis_simulation.clock import advance_clock
from genesis_simulation.errors import InvalidCommandError, InvariantViolation
from genesis_simulation.model import (
    CommandType,
    DomainEvent,
    EngineCommand,
    EngineConfig,
    EngineResult,
    EventDraft,
    MetricPoint,
    SimulationSnapshot,
    StateChange,
    WorldState,
)
from genesis_simulation.randomness import DeterministicRandom
from genesis_simulation.snapshots import create_snapshot, restore_snapshot
from genesis_simulation.systems import default_systems
from genesis_simulation.systems.base import SimulationContext, SimulationSystem

_WORLD_CHANGE_FIELDS = {
    "treasury_minor",
    "social_cohesion",
    "environmental_quality",
}
_CITIZEN_CHANGE_FIELDS = {
    "lifecycle_status",
    "health",
    "happiness",
    "employment_status",
    "occupation",
    "income_minor",
    "wealth_minor",
    "relationship_strength",
}


class SimulationEngine:
    """A deterministic command processor bound to one world run."""

    def __init__(
        self,
        initial_state: WorldState,
        *,
        config: EngineConfig | None = None,
        systems: tuple[SimulationSystem, ...] | None = None,
    ) -> None:
        self.config = config or EngineConfig()
        configured_systems = systems or default_systems()
        self._systems = tuple(sorted(configured_systems, key=lambda system: system.order))
        self._validate_system_registry()

        loaded = deepcopy(initial_state)
        if loaded.rng_state is None:
            loaded.rng_state = DeterministicRandom(seed=loaded.seed).get_state()
        self._validate_state(loaded)
        self._initial_state = deepcopy(loaded)
        self._state = loaded
        self._commands: list[EngineCommand] = []
        self._events: list[DomainEvent] = []

    @property
    def state(self) -> WorldState:
        return deepcopy(self._state)

    @property
    def commands(self) -> tuple[EngineCommand, ...]:
        return tuple(self._commands)

    @property
    def events(self) -> tuple[DomainEvent, ...]:
        return tuple(self._events)

    @property
    def system_manifest(self) -> tuple[str, ...]:
        return tuple(f"{system.order}:{system.name}@{system.version}" for system in self._systems)

    def apply(self, command: EngineCommand) -> EngineResult:
        if command.type is CommandType.TICK:
            result = self._advance(command, ignore_pause=False)
        elif command.type is CommandType.STEP:
            result = self._advance(command, ignore_pause=True)
        elif command.type is CommandType.PAUSE:
            self._state.paused = True
            result = self._result(command)
        elif command.type is CommandType.RESUME:
            self._state.paused = False
            result = self._result(command)
        elif command.type is CommandType.SET_SPEED:
            result = self._set_speed(command)
        elif command.type is CommandType.RESET:
            self._state = deepcopy(self._initial_state)
            self._events.clear()
            result = self._result(command)
        else:
            raise InvalidCommandError(f"unsupported command: {command.type}")
        self._commands.append(command)
        return result

    def run_ticks(self, count: int) -> tuple[EngineResult, ...]:
        if count < 0:
            raise InvalidCommandError("tick count cannot be negative")
        return tuple(self.apply(EngineCommand.tick()) for _ in range(count))

    def snapshot(self) -> SimulationSnapshot:
        return create_snapshot(
            self._state,
            engine_version=self.config.engine_version,
            system_manifest=self.system_manifest,
        )

    def restore(self, snapshot: SimulationSnapshot) -> None:
        restored = restore_snapshot(
            snapshot,
            expected_engine_version=self.config.engine_version,
            expected_system_manifest=self.system_manifest,
        )
        self._validate_state(restored)
        if restored.world_id != self._initial_state.world_id:
            raise InvariantViolation("snapshot belongs to a different world")
        self._state = restored
        self._events.clear()

    @classmethod
    def replay(
        cls,
        initial_state: WorldState,
        commands: tuple[EngineCommand, ...],
        *,
        config: EngineConfig | None = None,
        systems: tuple[SimulationSystem, ...] | None = None,
    ) -> "SimulationEngine":
        engine = cls(initial_state, config=config, systems=systems)
        for command in commands:
            engine.apply(command)
        return engine

    def _advance(self, command: EngineCommand, *, ignore_pause: bool) -> EngineResult:
        if self._state.paused and not ignore_pause:
            return self._result(command)
        if self._state.rng_state is None:
            raise InvariantViolation("world RNG state is missing")

        working = deepcopy(self._state)
        random = DeterministicRandom(state=working.rng_state)
        clock = advance_clock(working.simulation_date, self.config.days_per_tick)
        working.simulation_date = clock.current_date
        working.tick += 1
        context = SimulationContext(
            tick=working.tick,
            clock=clock,
            random=random,
            citizen_batch_size=self.config.citizen_batch_size,
        )

        drafts = [
            EventDraft(
                category="clock",
                event_type="simulation.day_advanced",
                payload={"days": clock.days, "date": clock.current_date.isoformat()},
            )
        ]
        if clock.month_changed:
            drafts.append(
                EventDraft(
                    category="clock",
                    event_type="simulation.month_changed",
                    payload={
                        "year": clock.current_date.year,
                        "month": clock.current_date.month,
                    },
                    importance=5,
                )
            )
        if clock.year_changed:
            drafts.append(
                EventDraft(
                    category="clock",
                    event_type="simulation.year_changed",
                    payload={"year": clock.current_date.year},
                    importance=10,
                )
            )

        metrics: list[MetricPoint] = []
        for system in self._systems:
            system_result = system.process(context, working)
            self._apply_changes(working, system_result.changes)
            drafts.extend(system_result.events)
            metrics.extend(system_result.metrics)

        working.rng_state = random.get_state()
        self._validate_state(working)
        events = self._materialize_events(working, drafts)
        self._state = working
        self._events.extend(events)
        snapshot = (
            self.snapshot()
            if self.config.snapshot_interval and working.tick % self.config.snapshot_interval == 0
            else None
        )
        return self._result(
            command,
            events=events,
            metrics=tuple(metrics),
            snapshot=snapshot,
            advanced=True,
        )

    def _set_speed(self, command: EngineCommand) -> EngineResult:
        speed = command.value
        if speed is None or not self.config.minimum_speed <= speed <= self.config.maximum_speed:
            raise InvalidCommandError(
                f"speed must be between {self.config.minimum_speed} and {self.config.maximum_speed}"
            )
        self._state.speed = speed
        return self._result(command)

    def _apply_changes(self, state: WorldState, changes: tuple[StateChange, ...]) -> None:
        for change in changes:
            if change.scope == "world":
                if change.entity_id is not None or change.field not in _WORLD_CHANGE_FIELDS:
                    raise InvariantViolation(f"invalid world change: {change}")
                setattr(state, change.field, change.value)
                continue
            if change.scope != "citizen" or change.entity_id is None:
                raise InvariantViolation(f"invalid state change scope: {change}")
            if change.field not in _CITIZEN_CHANGE_FIELDS:
                raise InvariantViolation(f"invalid citizen change: {change}")
            citizen = state.citizens.get(change.entity_id)
            if citizen is None:
                raise InvariantViolation(f"unknown citizen: {change.entity_id}")
            setattr(citizen, change.field, change.value)

    def _materialize_events(
        self, state: WorldState, drafts: list[EventDraft]
    ) -> tuple[DomainEvent, ...]:
        events: list[DomainEvent] = []
        for draft in drafts:
            state.event_sequence += 1
            sequence = state.event_sequence
            event_id = str(
                uuid5(
                    NAMESPACE_URL,
                    f"genesis:{state.world_id}:{sequence}:{state.tick}:{draft.event_type}",
                )
            )
            events.append(
                DomainEvent(
                    id=event_id,
                    world_id=state.world_id,
                    sequence=sequence,
                    tick=state.tick,
                    simulation_date=state.simulation_date,
                    category=draft.category,
                    event_type=draft.event_type,
                    payload=draft.payload,
                    engine_version=self.config.engine_version,
                    actor_id=draft.actor_id,
                    target_id=draft.target_id,
                    importance=draft.importance,
                    severity=draft.severity,
                )
            )
        return tuple(events)

    def _result(
        self,
        command: EngineCommand,
        *,
        events: tuple[DomainEvent, ...] = (),
        metrics: tuple[MetricPoint, ...] = (),
        snapshot: SimulationSnapshot | None = None,
        advanced: bool = False,
    ) -> EngineResult:
        return EngineResult(
            command=command,
            state=deepcopy(self._state),
            events=events,
            metrics=metrics,
            snapshot=snapshot,
            advanced=advanced,
        )

    def _validate_system_registry(self) -> None:
        names = [system.name for system in self._systems]
        orders = [system.order for system in self._systems]
        if len(names) != len(set(names)):
            raise ValueError("system names must be unique")
        if len(orders) != len(set(orders)):
            raise ValueError("system order values must be unique")

    def _validate_state(self, state: WorldState) -> None:
        if not state.world_id:
            raise InvariantViolation("world_id must not be blank")
        if state.tick < 0 or state.event_sequence < 0:
            raise InvariantViolation("tick and event sequence cannot be negative")
        if not self.config.minimum_speed <= state.speed <= self.config.maximum_speed:
            raise InvariantViolation("world speed is outside the configured range")
        if not 0 <= state.social_cohesion <= 100:
            raise InvariantViolation("social cohesion must be between 0 and 100")
        if not 0 <= state.environmental_quality <= 100:
            raise InvariantViolation("environmental quality must be between 0 and 100")
        for citizen_id, citizen in state.citizens.items():
            if citizen_id != citizen.id:
                raise InvariantViolation("citizen map key must match citizen ID")
            if citizen.birth_date > state.simulation_date:
                raise InvariantViolation("citizen birth date cannot be in the future")
            for name, value in (
                ("health", citizen.health),
                ("happiness", citizen.happiness),
                ("relationship_strength", citizen.relationship_strength),
            ):
                if not 0 <= value <= 100:
                    raise InvariantViolation(f"citizen {name} must be between 0 and 100")
            if citizen.income_minor < 0:
                raise InvariantViolation("citizen income cannot be negative")

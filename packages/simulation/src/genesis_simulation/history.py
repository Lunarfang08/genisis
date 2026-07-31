from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from datetime import date

from genesis_simulation.errors import InvariantViolation
from genesis_simulation.model import DomainEvent, SimulationSnapshot, WorldState
from genesis_simulation.snapshots import restore_snapshot


@dataclass(frozen=True, slots=True)
class TimelineFilter:
    citizen_id: str | None = None
    city_id: str | None = None
    category: str | None = None
    date_from: date | None = None
    date_to: date | None = None
    minimum_importance: int = 0
    after_sequence: int = 0
    limit: int = 100

    def __post_init__(self) -> None:
        if not 0 <= self.minimum_importance <= 100:
            raise ValueError("minimum_importance must be between 0 and 100")
        if self.after_sequence < 0:
            raise ValueError("after_sequence cannot be negative")
        if not 1 <= self.limit <= 500:
            raise ValueError("limit must be between 1 and 500")
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValueError("date_from cannot be after date_to")


EventSubscriber = Callable[[tuple[DomainEvent, ...]], None]


@dataclass(slots=True)
class EventHistory:
    """Append-only, world-scoped event history with resumable subscriptions."""

    world_id: str
    _events: list[DomainEvent] = field(default_factory=list)
    _snapshots: list[SimulationSnapshot] = field(default_factory=list)
    _subscribers: dict[str, EventSubscriber] = field(default_factory=dict)

    @property
    def latest_sequence(self) -> int:
        return self._events[-1].sequence if self._events else 0

    def append(self, events: Iterable[DomainEvent]) -> tuple[DomainEvent, ...]:
        batch = tuple(events)
        expected = self.latest_sequence + 1
        seen_ids = {event.id for event in self._events}
        for event in batch:
            if event.world_id != self.world_id:
                raise InvariantViolation("event belongs to a different world")
            if event.id in seen_ids:
                raise InvariantViolation("event IDs are immutable and unique")
            if event.sequence != expected:
                raise InvariantViolation(f"event sequence must be contiguous; expected {expected}")
            expected += 1
            seen_ids.add(event.id)
        if not batch:
            return ()
        self._events.extend(batch)
        for subscriber_id in sorted(self._subscribers):
            self._subscribers[subscriber_id](batch)
        return batch

    def add_snapshot(self, snapshot: SimulationSnapshot) -> None:
        if snapshot.world_id != self.world_id:
            raise InvariantViolation("snapshot belongs to a different world")
        if snapshot.event_sequence > self.latest_sequence:
            raise InvariantViolation("snapshot cannot be ahead of event history")
        if any(item.event_sequence == snapshot.event_sequence for item in self._snapshots):
            raise InvariantViolation("snapshot sequence already exists")
        self._snapshots.append(snapshot)
        self._snapshots.sort(key=lambda item: item.event_sequence)

    def snapshots(self) -> tuple[SimulationSnapshot, ...]:
        return tuple(reversed(self._snapshots))

    def nearest_snapshot(self, sequence: int | None = None) -> SimulationSnapshot | None:
        ceiling = self.latest_sequence if sequence is None else sequence
        compatible = [
            snapshot for snapshot in self._snapshots if snapshot.event_sequence <= ceiling
        ]
        return compatible[-1] if compatible else None

    def query(self, filters: TimelineFilter | None = None) -> tuple[DomainEvent, ...]:
        query = filters or TimelineFilter()
        matches: list[DomainEvent] = []
        for event in self._events:
            payload_city = event.payload.get("city_id")
            if event.sequence <= query.after_sequence:
                continue
            if query.citizen_id not in (None, event.actor_id, event.target_id):
                continue
            if query.city_id is not None and payload_city != query.city_id:
                continue
            if query.category is not None and event.category != query.category:
                continue
            if query.date_from is not None and event.simulation_date < query.date_from:
                continue
            if query.date_to is not None and event.simulation_date > query.date_to:
                continue
            if event.importance < query.minimum_importance:
                continue
            matches.append(event)
            if len(matches) == query.limit:
                break
        return tuple(matches)

    def subscribe(
        self, subscriber_id: str, callback: EventSubscriber, *, after_sequence: int = 0
    ) -> tuple[DomainEvent, ...]:
        if not subscriber_id:
            raise ValueError("subscriber_id must not be blank")
        self._subscribers[subscriber_id] = callback
        return self.query(TimelineFilter(after_sequence=after_sequence, limit=500))

    def unsubscribe(self, subscriber_id: str) -> None:
        self._subscribers.pop(subscriber_id, None)

    def restore(
        self,
        *,
        engine_version: str,
        system_manifest: tuple[str, ...],
        sequence: int | None = None,
    ) -> tuple[WorldState, tuple[DomainEvent, ...]]:
        snapshot = self.nearest_snapshot(sequence)
        if snapshot is None:
            raise InvariantViolation("no compatible snapshot is available")
        state = restore_snapshot(
            snapshot,
            expected_engine_version=engine_version,
            expected_system_manifest=system_manifest,
        )
        ceiling = self.latest_sequence if sequence is None else sequence
        tail = tuple(
            event for event in self._events if snapshot.event_sequence < event.sequence <= ceiling
        )
        return state, tail

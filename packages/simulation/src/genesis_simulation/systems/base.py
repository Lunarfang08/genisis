from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from typing import Protocol

from genesis_simulation.clock import ClockAdvance
from genesis_simulation.model import CitizenState, SystemResult, WorldState
from genesis_simulation.randomness import DeterministicRandom


@dataclass(frozen=True, slots=True)
class SimulationContext:
    tick: int
    clock: ClockAdvance
    random: DeterministicRandom
    citizen_batch_size: int

    def citizen_batches(self, state: WorldState) -> Iterator[Sequence[CitizenState]]:
        ordered = [state.citizens[citizen_id] for citizen_id in sorted(state.citizens)]
        for offset in range(0, len(ordered), self.citizen_batch_size):
            yield ordered[offset : offset + self.citizen_batch_size]


class SimulationSystem(Protocol):
    @property
    def name(self) -> str: ...

    @property
    def version(self) -> str: ...

    @property
    def order(self) -> int: ...

    def process(self, context: SimulationContext, state: WorldState) -> SystemResult: ...

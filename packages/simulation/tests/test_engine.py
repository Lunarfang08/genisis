from copy import deepcopy
from dataclasses import replace
from datetime import date

import pytest

from genesis_simulation.engine import SimulationEngine
from genesis_simulation.errors import (
    InvalidCommandError,
    InvariantViolation,
    SnapshotIntegrityError,
)
from genesis_simulation.model import EngineCommand, EngineConfig
from tests.factories import CITIZEN_A, CITIZEN_B, world_state_factory


def test_same_seed_and_commands_are_byte_for_byte_deterministic() -> None:
    config = EngineConfig(snapshot_interval=2, citizen_batch_size=1)
    first = SimulationEngine(world_state_factory(), config=config)
    second = SimulationEngine(
        world_state_factory(reverse_citizens=True),
        config=config,
    )

    first_results = first.run_ticks(5)
    second_results = second.run_ticks(5)

    assert first.state.to_dict() == second.state.to_dict()
    assert first.events == second.events
    assert [result.metrics for result in first_results] == [
        result.metrics for result in second_results
    ]
    assert first_results[1].snapshot == second_results[1].snapshot


def test_different_seeds_diverge() -> None:
    first = SimulationEngine(world_state_factory(seed=1))
    second = SimulationEngine(world_state_factory(seed=2))

    first.run_ticks(3)
    second.run_ticks(3)

    assert first.state.to_dict() != second.state.to_dict()


def test_pause_step_speed_resume_and_reset_controls() -> None:
    engine = SimulationEngine(world_state_factory())
    initial = engine.state.to_dict()

    engine.apply(EngineCommand.pause())
    paused_tick = engine.apply(EngineCommand.tick())
    assert paused_tick.advanced is False
    assert paused_tick.state.tick == 0

    stepped = engine.apply(EngineCommand.step())
    assert stepped.advanced is True
    assert stepped.state.tick == 1
    assert stepped.state.paused is True

    engine.apply(EngineCommand.set_speed(12))
    assert engine.state.speed == 12
    engine.apply(EngineCommand.resume())
    assert engine.apply(EngineCommand.tick()).state.tick == 2

    reset = engine.apply(EngineCommand.reset())
    assert reset.state.to_dict() == initial
    assert engine.events == ()

    with pytest.raises(InvalidCommandError, match="speed"):
        engine.apply(EngineCommand.set_speed(0))


def test_systems_update_state_in_stable_order() -> None:
    engine = SimulationEngine(world_state_factory())
    result = engine.apply(EngineCommand.tick())
    citizen = result.state.citizens[CITIZEN_A]

    assert result.state.simulation_date == date(2200, 12, 31)
    assert citizen.income_minor == 100
    assert citizen.wealth_minor == 1_090
    assert result.state.treasury_minor == 10
    assert [metric.name for metric in result.metrics] == [
        "population",
        "employed_population",
        "social_cohesion",
        "gross_income",
        "tax_revenue",
        "environmental_quality",
    ]
    assert engine.system_manifest == (
        "100:lifecycle@1",
        "200:employment@1",
        "300:relationships@1",
        "400:economy@1",
        "500:government@1",
        "600:environment@1",
    )


def test_year_progression_drives_lifecycle_events() -> None:
    engine = SimulationEngine(world_state_factory())

    engine.run_ticks(2)

    assert engine.state.simulation_date == date(2201, 1, 1)
    assert engine.state.citizens[CITIZEN_B].lifecycle_status == "adult"
    second_tick_types = [event.event_type for event in engine.events if event.tick == 2]
    assert "simulation.month_changed" in second_tick_types
    assert "simulation.year_changed" in second_tick_types
    assert "citizen.lifecycle_changed" in second_tick_types


def test_snapshot_restore_continues_the_same_run() -> None:
    config = EngineConfig(snapshot_interval=2)
    uninterrupted = SimulationEngine(world_state_factory(), config=config)
    results = uninterrupted.run_ticks(2)
    snapshot = results[-1].snapshot
    assert snapshot is not None

    resumed = SimulationEngine(world_state_factory(), config=config)
    resumed.restore(snapshot)
    uninterrupted.apply(EngineCommand.tick())
    resumed.apply(EngineCommand.tick())

    assert resumed.state.to_dict() == uninterrupted.state.to_dict()
    assert resumed.events == uninterrupted.events[-len(resumed.events) :]


def test_snapshot_rejects_tampering() -> None:
    engine = SimulationEngine(world_state_factory())
    snapshot = engine.snapshot()
    damaged_state = deepcopy(snapshot.state)
    damaged_state["tick"] = 99
    damaged = replace(snapshot, state=damaged_state)

    with pytest.raises(SnapshotIntegrityError, match="checksum"):
        engine.restore(damaged)


def test_replay_reexecutes_recorded_commands() -> None:
    original = SimulationEngine(world_state_factory())
    commands = (
        EngineCommand.tick(),
        EngineCommand.pause(),
        EngineCommand.tick(),
        EngineCommand.step(),
        EngineCommand.set_speed(4),
        EngineCommand.resume(),
        EngineCommand.tick(),
    )
    for command in commands:
        original.apply(command)

    replayed = SimulationEngine.replay(world_state_factory(), commands)

    assert replayed.state.to_dict() == original.state.to_dict()
    assert replayed.events == original.events
    assert replayed.commands == original.commands


def test_invalid_initial_state_is_rejected() -> None:
    state = world_state_factory()
    state.citizens[CITIZEN_A].birth_date = date(2300, 1, 1)

    with pytest.raises(InvariantViolation, match="birth date"):
        SimulationEngine(state)

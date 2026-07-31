import asyncio
from datetime import date

import pytest

from genesis_simulation.ai import (
    AIService,
    GenerationRequest,
    MockProvider,
    major_event_eligible,
)
from genesis_simulation.economy import (
    BusinessAccount,
    EconomicCitizen,
    EconomyConfig,
    simulate_economy,
)
from genesis_simulation.engine import SimulationEngine
from genesis_simulation.environment import (
    DisasterType,
    EnvironmentConfig,
    EnvironmentState,
    simulate_environment,
)
from genesis_simulation.errors import InvariantViolation
from genesis_simulation.government import Candidate, Party, PublicPolicy, Voter, run_election
from genesis_simulation.history import EventHistory, TimelineFilter
from genesis_simulation.memory import CitizenMind, Goal, Memory, MemoryType
from genesis_simulation.model import EngineConfig, JsonValue
from genesis_simulation.randomness import DeterministicRandom
from genesis_simulation.realtime import StreamBroker
from genesis_simulation.society import (
    LifeProfile,
    Relationship,
    RelationshipGraph,
    RelationshipType,
    advance_lifecycle,
)
from tests.factories import CITIZEN_A, CITIZEN_B, WORLD_ID, world_state_factory


def test_milestone_5_history_orders_filters_subscribes_and_restores() -> None:
    engine = SimulationEngine(world_state_factory(), config=EngineConfig(snapshot_interval=2))
    history = EventHistory(WORLD_ID)
    delivered: list[int] = []
    history.subscribe("dashboard", lambda batch: delivered.extend(item.sequence for item in batch))

    first, second = engine.run_ticks(2)
    history.append(first.events)
    history.append(second.events)
    assert second.snapshot is not None
    history.add_snapshot(second.snapshot)

    assert delivered == list(range(1, history.latest_sequence + 1))
    clock = history.query(TimelineFilter(category="clock", limit=50))
    assert clock and all(item.category == "clock" for item in clock)
    important = history.query(TimelineFilter(minimum_importance=10, limit=50))
    assert all(item.importance >= 10 for item in important)
    restored, tail = history.restore(
        engine_version=engine.config.engine_version,
        system_manifest=engine.system_manifest,
    )
    assert restored.to_dict() == engine.state.to_dict()
    assert tail == ()

    with pytest.raises(InvariantViolation, match="unique"):
        history.append((first.events[0],))


def test_milestone_6_lifecycle_is_configurable_and_deterministic() -> None:
    first = LifeProfile("citizen", date(2000, 1, 1), health=100)
    second = LifeProfile("citizen", date(2000, 1, 1), health=100)
    events_a = advance_lifecycle(first, date(2018, 1, 1), DeterministicRandom(seed=7))
    events_b = advance_lifecycle(second, date(2018, 1, 1), DeterministicRandom(seed=7))
    assert first == second
    assert events_a == events_b
    assert first.status == "adult"
    assert first.employment_status == "unemployed"


def test_milestone_7_relationships_are_reciprocal_and_traversable() -> None:
    graph = RelationshipGraph()
    graph.connect(
        Relationship(
            CITIZEN_A,
            CITIZEN_B,
            RelationshipType.PARENT,
            date(2200, 1, 1),
            strength=90,
        )
    )
    assert graph.connections(CITIZEN_A)[0].type is RelationshipType.PARENT
    assert graph.connections(CITIZEN_B)[0].type is RelationshipType.CHILD
    assert graph.family_tree(CITIZEN_A)[CITIZEN_A] == (CITIZEN_B,)


def test_milestone_8_economy_balances_income_tax_consumption_and_businesses() -> None:
    citizens = [
        EconomicCitizen("a", "h", True, 10_000, 1_000),
        EconomicCitizen("b", "h", False, 0, 500),
    ]
    businesses = [BusinessAccount("shop", "retail", 1_000, 1, 100, 10, 2_000)]
    metrics = simulate_economy(
        citizens, businesses, EconomyConfig(tax_percent=10, inflation_basis_points=100)
    )
    assert metrics.household_income_minor == 10_000
    assert metrics.tax_revenue_minor == 1_000
    assert metrics.gdp_minor == 16_000
    assert metrics.employed == 1 and metrics.unemployed == 1
    assert citizens[0].wealth_minor == 4_000
    assert businesses[0].cash_minor == 5_000


def test_milestone_9_elections_and_policy_are_deterministic() -> None:
    parties = (Party("center", "Civic", 50), Party("green", "Green", 25))
    candidates = (
        Candidate("alice", "center", 80, 70),
        Candidate("bob", "green", 70, 60),
    )
    voters = (
        Voter("v1", 48, 1_000, True, 60, 70, 60),
        Voter("v2", 20, 800, False, 80, 50, 40),
    )
    result = run_election(date(2200, 1, 1), parties, candidates, voters)
    assert result.turnout == 2
    assert sum(result.votes.values()) == 2
    policy = PublicPolicy("EDU", 12, 25, 3)
    treasury, happiness = policy.enact(10_000)
    assert (treasury, happiness, policy.active) == (7_500, 3, True)


def test_milestone_10_environment_uses_seeded_disasters() -> None:
    state_a = EnvironmentState()
    state_b = EnvironmentState()
    config = EnvironmentConfig(disaster_frequency_per_10k=10_000, disease_frequency_per_10k=10_000)
    first = simulate_environment(date(2200, 7, 1), state_a, DeterministicRandom(seed=4), config)
    second = simulate_environment(date(2200, 7, 1), state_b, DeterministicRandom(seed=4), config)
    assert first == second
    assert state_a == state_b
    assert DisasterType.DISEASE in first.disasters
    assert first.government_cost_minor > 0


def test_milestones_11_and_12_ai_is_optional_validated_cached_and_budgeted() -> None:
    provider = MockProvider({"history": {"title": "A vote", "text": "A new term began."}})
    service = AIService({"mock": provider}, primary="mock", enabled=True, daily_call_budget=1)
    request = GenerationRequest("history", "Summarize a committed election.", {})

    def validate(value: dict[str, JsonValue]) -> bool:
        return isinstance(value.get("text"), str)

    result = service.generate(
        simulation_day="2200-01-01",
        cache_key="event:1",
        request=request,
        validator=validate,
    )
    cached = service.generate(
        simulation_day="2200-01-01",
        cache_key="event:1",
        request=request,
        validator=validate,
    )
    assert result.content["title"] == "A vote"
    assert cached.cached is True
    assert provider.calls == 1
    assert major_event_eligible(90, "government")
    assert not major_event_eligible(20, "government")
    with pytest.raises(RuntimeError, match="budget"):
        service.generate(
            simulation_day="2200-01-01",
            cache_key="event:2",
            request=request,
            validator=validate,
        )


def test_milestone_13_major_memories_influence_decisions_and_goals() -> None:
    mind = CitizenMind(short_term_limit=2)
    mind.remember(
        Memory(
            "m1",
            MemoryType.TRAUMATIC,
            date(2200, 1, 1),
            95,
            -90,
            related_citizens=("rival",),
        )
    )
    mind.remember(Memory("m2", MemoryType.PERSONAL, date(2200, 1, 2), 10, 10))
    mind.decay(10_000)
    assert mind.decision_bias("rival") < -50
    assert [item.memory_id for item in mind.memories] == ["m1"]
    failed = Goal("g1", "Old goal", 90)
    failed.fail()
    mind.goals.append(failed)
    mind.replace_failed_goal(Goal("g2", "Recover", 80))
    assert [goal.status for goal in mind.goals] == ["replaced", "active"]


def test_milestone_14_broker_channels_heartbeats_and_backpressure() -> None:
    async def scenario() -> None:
        broker = StreamBroker(queue_size=1)
        queue = broker.connect("client", frozenset({"events"}))
        broker.publish("metrics", {"gdp": 1})
        assert queue.empty()
        expected = broker.publish("events", {"type": "ElectionCompleted"})
        assert await queue.get() == expected
        broker.publish("events", {"type": "one"})
        broker.publish("events", {"type": "two"})
        assert "client" not in broker._clients

    asyncio.run(scenario())

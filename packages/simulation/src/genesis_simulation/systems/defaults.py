from dataclasses import dataclass
from datetime import date

from genesis_simulation.model import (
    EventDraft,
    MetricPoint,
    StateChange,
    SystemResult,
    WorldState,
)
from genesis_simulation.systems.base import SimulationContext, SimulationSystem


def _age_on(birth_date: date, on_date: date) -> int:
    years = on_date.year - birth_date.year
    if (on_date.month, on_date.day) < (birth_date.month, birth_date.day):
        years -= 1
    return years


@dataclass(frozen=True, slots=True)
class LifecycleSystem:
    name: str = "lifecycle"
    version: str = "1"
    order: int = 100

    def process(self, context: SimulationContext, state: WorldState) -> SystemResult:
        changes: list[StateChange] = []
        events: list[EventDraft] = []
        living = 0
        for batch in context.citizen_batches(state):
            for citizen in batch:
                if citizen.lifecycle_status == "deceased":
                    continue
                living += 1
                age = _age_on(citizen.birth_date, context.clock.current_date)
                lifecycle = "child" if age < 18 else "adult" if age < 65 else "elder"
                if lifecycle != citizen.lifecycle_status:
                    changes.append(
                        StateChange("citizen", citizen.id, "lifecycle_status", lifecycle)
                    )
                    events.append(
                        EventDraft(
                            category="lifecycle",
                            event_type="citizen.lifecycle_changed",
                            actor_id=citizen.id,
                            payload={"lifecycle_status": lifecycle, "age": age},
                            importance=20,
                        )
                    )
                health = max(0, min(100, citizen.health + context.random.randint(-1, 1)))
                if health != citizen.health:
                    changes.append(StateChange("citizen", citizen.id, "health", health))
        return SystemResult(
            changes=tuple(changes),
            events=tuple(events),
            metrics=(MetricPoint("population", living, "citizens"),),
        )


@dataclass(frozen=True, slots=True)
class EmploymentSystem:
    name: str = "employment"
    version: str = "1"
    order: int = 200

    def process(self, context: SimulationContext, state: WorldState) -> SystemResult:
        changes: list[StateChange] = []
        events: list[EventDraft] = []
        employed = 0
        for batch in context.citizen_batches(state):
            for citizen in batch:
                if citizen.employment_status == "employed":
                    employed += 1
                    continue
                if (
                    citizen.lifecycle_status == "adult"
                    and citizen.employment_status == "unemployed"
                    and context.random.random() < 0.05
                ):
                    employed += 1
                    changes.extend(
                        (
                            StateChange("citizen", citizen.id, "employment_status", "employed"),
                            StateChange("citizen", citizen.id, "occupation", "general_worker"),
                        )
                    )
                    events.append(
                        EventDraft(
                            category="employment",
                            event_type="citizen.employed",
                            actor_id=citizen.id,
                            payload={"occupation": "general_worker"},
                            importance=15,
                        )
                    )
        return SystemResult(
            changes=tuple(changes),
            events=tuple(events),
            metrics=(MetricPoint("employed_population", employed, "citizens"),),
        )


@dataclass(frozen=True, slots=True)
class RelationshipSystem:
    name: str = "relationships"
    version: str = "1"
    order: int = 300

    def process(self, context: SimulationContext, state: WorldState) -> SystemResult:
        changes: list[StateChange] = []
        strengths: list[int] = []
        for batch in context.citizen_batches(state):
            for citizen in batch:
                strength = max(
                    0,
                    min(100, citizen.relationship_strength + context.random.randint(-1, 1)),
                )
                strengths.append(strength)
                if strength != citizen.relationship_strength:
                    changes.append(
                        StateChange("citizen", citizen.id, "relationship_strength", strength)
                    )
        cohesion = round(sum(strengths) / len(strengths)) if strengths else 50
        changes.append(StateChange("world", None, "social_cohesion", cohesion))
        return SystemResult(
            changes=tuple(changes),
            metrics=(MetricPoint("social_cohesion", cohesion, "score"),),
        )


@dataclass(frozen=True, slots=True)
class EconomySystem:
    name: str = "economy"
    version: str = "1"
    order: int = 400
    daily_income_minor: int = 100

    def process(self, context: SimulationContext, state: WorldState) -> SystemResult:
        changes: list[StateChange] = []
        gross_income = 0
        for batch in context.citizen_batches(state):
            for citizen in batch:
                income = (
                    self.daily_income_minor * context.clock.days
                    if citizen.employment_status == "employed"
                    else 0
                )
                gross_income += income
                changes.extend(
                    (
                        StateChange("citizen", citizen.id, "income_minor", income),
                        StateChange(
                            "citizen",
                            citizen.id,
                            "wealth_minor",
                            citizen.wealth_minor + income,
                        ),
                    )
                )
        return SystemResult(
            changes=tuple(changes),
            metrics=(MetricPoint("gross_income", gross_income, "minor_units"),),
        )


@dataclass(frozen=True, slots=True)
class GovernmentSystem:
    name: str = "government"
    version: str = "1"
    order: int = 500
    tax_percent: int = 10

    def process(self, context: SimulationContext, state: WorldState) -> SystemResult:
        changes: list[StateChange] = []
        tax_total = 0
        for batch in context.citizen_batches(state):
            for citizen in batch:
                tax = citizen.income_minor * self.tax_percent // 100
                if tax:
                    tax_total += tax
                    changes.append(
                        StateChange(
                            "citizen",
                            citizen.id,
                            "wealth_minor",
                            citizen.wealth_minor - tax,
                        )
                    )
        treasury = state.treasury_minor + tax_total
        changes.append(StateChange("world", None, "treasury_minor", treasury))
        events = (
            EventDraft(
                category="government",
                event_type="government.taxes_collected",
                payload={"amount_minor": tax_total},
                importance=10,
            ),
        )
        return SystemResult(
            changes=tuple(changes),
            events=events,
            metrics=(MetricPoint("tax_revenue", tax_total, "minor_units"),),
        )


@dataclass(frozen=True, slots=True)
class EnvironmentSystem:
    name: str = "environment"
    version: str = "1"
    order: int = 600

    def process(self, context: SimulationContext, state: WorldState) -> SystemResult:
        quality = max(
            0,
            min(100, state.environmental_quality + context.random.randint(-1, 1)),
        )
        return SystemResult(
            changes=(StateChange("world", None, "environmental_quality", quality),),
            metrics=(MetricPoint("environmental_quality", quality, "score"),),
        )


def default_systems() -> tuple[SimulationSystem, ...]:
    return (
        LifecycleSystem(),
        EmploymentSystem(),
        RelationshipSystem(),
        EconomySystem(),
        GovernmentSystem(),
        EnvironmentSystem(),
    )

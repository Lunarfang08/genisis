from datetime import date, datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class EventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    sequence: int
    simulation_date: date
    category: str
    event_type: str
    schema_version: int
    engine_version: str
    actor_citizen_id: UUID | None
    target_citizen_id: UUID | None
    city_id: UUID | None
    causation_id: UUID | None
    correlation_id: UUID
    severity: str
    importance: int
    payload: dict[str, Any]


class EventListResponse(BaseModel):
    items: list[EventResponse]
    next_sequence: int | None


class SnapshotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    event_sequence: int
    simulation_date: date
    schema_version: int
    engine_version: str
    checksum: str
    created_at: datetime


class ReplayStatusResponse(BaseModel):
    world_id: UUID
    latest_event_sequence: int
    latest_snapshot_sequence: int | None
    replay_event_count: int
    compatible: bool


class RelationshipResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    target_citizen_id: UUID
    relationship_type: str
    strength: int
    trust: int
    familiarity: int
    conflict: int
    started_on: date
    last_interaction_on: date | None
    is_active: bool


class MemoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    memory_type: str
    importance: int
    emotional_score: int
    recall_score: int
    occurred_on: date
    related_event_id: UUID | None
    related_citizen_ids: list[str]
    is_consolidated: bool


class CitizenProfileResponse(BaseModel):
    id: UUID
    full_name: str
    age: int
    lifecycle_status: str
    education_level: str
    employment_status: str
    household_id: UUID | None
    employer_business_id: UUID | None
    income_minor: int
    wealth_minor: int
    health: int
    happiness: int
    reputation: int
    personality: dict[str, int]
    skills: dict[str, int]
    beliefs: dict[str, dict[str, str | int]]
    goals: list[dict[str, str | int | None]]
    memories: list[MemoryResponse]
    major_events: list[EventResponse]


class WorldDashboardResponse(BaseModel):
    population: int
    employed: int
    unemployed: int
    average_income_minor: int
    total_wealth_minor: int
    average_health: float
    average_happiness: float
    active_businesses: int
    treasury_minor: int
    latest_metrics: dict[str, float]


class GovernmentResponse(BaseModel):
    id: UUID
    name: str
    government_type: str
    leader_citizen_id: UUID | None
    treasury_minor: int
    term_started_on: date | None
    term_ends_on: date | None
    laws: list[dict[str, str | date | None]]


class AIActivityResponse(BaseModel):
    calls: int
    cache_hits: int
    failures: int
    input_tokens: int
    output_tokens: int
    estimated_cost_micros: int
    providers: dict[str, int]


class ControlRequest(BaseModel):
    command: Literal[
        "start",
        "pause",
        "resume",
        "step",
        "set_speed",
        "jump_to_date",
        "reset",
        "replay",
    ]
    speed: int | None = Field(default=None, ge=1, le=60)
    target_date: date | None = None
    snapshot_id: UUID | None = None

    @model_validator(mode="after")
    def validate_command_payload(self) -> "ControlRequest":
        if self.command == "set_speed" and self.speed is None:
            raise ValueError("speed is required for set_speed")
        if self.command == "jump_to_date" and self.target_date is None:
            raise ValueError("target_date is required for jump_to_date")
        if self.command == "replay" and self.snapshot_id is None:
            raise ValueError("snapshot_id is required for replay")
        return self


class ControlResponse(BaseModel):
    id: UUID
    sequence: int
    command: str
    accepted: bool
    is_paused: bool
    speed: int
    correlation_id: UUID

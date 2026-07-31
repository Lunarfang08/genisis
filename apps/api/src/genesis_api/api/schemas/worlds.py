from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

ScenarioKey = Literal[
    "balanced",
    "economic_crisis",
    "rapid_growth",
    "resource_scarcity",
    "political_instability",
    "disaster_prone",
    "high_technology",
]


class WorldCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    seed: int = Field(ge=0, le=2_147_483_647)
    tick_rate: int = Field(default=1, ge=1, le=60)
    initial_population: int = Field(default=1_000, ge=10, le=50_000)
    city_count: int = Field(default=3, ge=1, le=50)
    government_type: Literal["democracy"] = "democracy"
    economic_difficulty: int = Field(default=50, ge=0, le=100)
    resource_abundance: int = Field(default=50, ge=0, le=100)
    disaster_frequency: int = Field(default=20, ge=0, le=100)
    disease_frequency: int = Field(default=20, ge=0, le=100)
    technology_level: int = Field(default=30, ge=0, le=100)
    ai_enabled: bool = False
    ai_provider: Literal["mock", "groq", "ollama"] = "mock"
    social_volatility: int = Field(default=30, ge=0, le=100)
    scenario: ScenarioKey = "balanced"

    @model_validator(mode="after")
    def validate_capacity(self) -> "WorldCreateRequest":
        if self.initial_population < self.city_count * 10:
            raise ValueError("initial_population must allow at least 10 citizens per city")
        if not self.ai_enabled and self.ai_provider != "mock":
            raise ValueError("cloud or local AI providers require ai_enabled")
        return self


class WorldSettingsResponse(BaseModel):
    seed: int
    tick_rate: int
    initial_population: int
    city_count: int
    scenario: str
    scenario_config: dict[str, str | int | bool]
    start_date: date
    simulation_date: date
    is_paused: bool
    simulation_tick: int
    event_sequence: int

    model_config = {"from_attributes": True}


class WorldResponse(BaseModel):
    id: UUID
    name: str
    created_at: datetime
    updated_at: datetime
    settings: WorldSettingsResponse

    model_config = {"from_attributes": True}


class WorldListResponse(BaseModel):
    items: list[WorldResponse]

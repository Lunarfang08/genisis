from datetime import date
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ScenarioTemplate(BaseModel):
    key: str
    name: str
    description: str
    settings: dict[str, int]


class CapacityProjection(BaseModel):
    citizen_count: int
    estimated_memory_mb: int
    estimated_tick_ms: int
    recommended_tier: str


class CityMapPoint(BaseModel):
    id: UUID
    region_id: UUID
    name: str
    latitude: float
    longitude: float
    population: int
    businesses: int
    economic_activity_minor: int


class MapLandmark(BaseModel):
    id: UUID
    city_id: UUID | None
    kind: str
    name: str


class RegionMapItem(BaseModel):
    id: UUID
    name: str
    terrain: str
    area_km2: int


class WorldMapResponse(BaseModel):
    regions: list[RegionMapItem]
    cities: list[CityMapPoint]
    incident_events: list[dict[str, Any]]
    activity_events: list[dict[str, Any]]
    landmarks: list[MapLandmark]
    generated_at_sequence: int


class MetricPoint(BaseModel):
    simulation_date: date
    value: float


class MetricSeries(BaseModel):
    name: str
    unit: str
    points: list[MetricPoint]


class AnalyticsResponse(BaseModel):
    series: list[MetricSeries]
    event_categories: dict[str, int]
    wealth_buckets: dict[str, int]
    city_population: dict[str, int]


class CompareRequest(BaseModel):
    left_date: date
    right_date: date
    metrics: list[str] = Field(min_length=1, max_length=12)


class CompareResponse(BaseModel):
    left_date: date
    right_date: date
    changes: dict[str, dict[str, float | None]]


class EntityCompareResponse(BaseModel):
    kind: str
    left: dict[str, Any]
    right: dict[str, Any]


class AdminOverview(BaseModel):
    environment: str
    owned_worlds: int
    active_simulations: int
    pending_commands: int
    pending_outbox_events: int
    connected_streams: int
    ai_calls: int

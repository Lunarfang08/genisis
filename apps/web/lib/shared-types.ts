export type ServiceStatus = "ok" | "degraded";

export interface DependencyStatus {
  status: ServiceStatus;
  latencyMs: number;
  detail?: string;
}

export interface ReadinessResponse {
  status: ServiceStatus;
  service: "genesis-api";
  version: string;
  dependencies: {
    database: DependencyStatus;
    redis: DependencyStatus;
  };
}

export interface User {
  id: string;
  email: string;
  display_name: string;
  created_at: string;
}

export interface WorldSettings {
  seed: number;
  tick_rate: number;
  initial_population: number;
  city_count: number;
  scenario: string;
  scenario_config: Record<string, string | number | boolean>;
  start_date: string;
  simulation_date: string;
  is_paused: boolean;
  simulation_tick: number;
  event_sequence: number;
}

export interface World {
  id: string;
  name: string;
  created_at: string;
  updated_at: string;
  settings: WorldSettings;
}

export interface TimelineEvent {
  id: string;
  sequence: number;
  simulation_date: string;
  category: string;
  event_type: string;
  severity: string;
  importance: number;
  actor_citizen_id: string | null;
  target_citizen_id: string | null;
  payload: Record<string, unknown>;
}

export interface TimelineResponse {
  items: TimelineEvent[];
  next_sequence: number | null;
}

export interface WorldDashboard {
  population: number;
  employed: number;
  unemployed: number;
  average_income_minor: number;
  total_wealth_minor: number;
  average_health: number;
  average_happiness: number;
  active_businesses: number;
  treasury_minor: number;
  latest_metrics: Record<string, number>;
}

export interface ReplayStatus {
  world_id: string;
  latest_event_sequence: number;
  latest_snapshot_sequence: number | null;
  replay_event_count: number;
  compatible: boolean;
}

export interface AIActivity {
  calls: number;
  cache_hits: number;
  failures: number;
  input_tokens: number;
  output_tokens: number;
  estimated_cost_micros: number;
  providers: Record<string, number>;
}

export interface ControlResponse {
  id: string;
  sequence: number;
  command: string;
  accepted: boolean;
  is_paused: boolean;
  speed: number;
  correlation_id: string;
}

export interface CityMapPoint {
  id: string;
  region_id: string;
  name: string;
  latitude: number;
  longitude: number;
  population: number;
  businesses: number;
  economic_activity_minor: number;
}

export interface WorldMap {
  regions: Array<{
    id: string;
    name: string;
    terrain: string;
    area_km2: number;
  }>;
  cities: CityMapPoint[];
  incident_events: Array<{
    id: string;
    city_id: string | null;
    type: string;
    severity: string;
    date: string;
  }>;
  activity_events: Array<{
    id: string;
    city_id: string | null;
    category: string;
    type: string;
    date: string;
  }>;
  landmarks: Array<{
    id: string;
    city_id: string | null;
    kind: string;
    name: string;
  }>;
  generated_at_sequence: number;
}

export interface Analytics {
  series: Array<{
    name: string;
    unit: string;
    points: Array<{ simulation_date: string; value: number }>;
  }>;
  event_categories: Record<string, number>;
  wealth_buckets: Record<string, number>;
  city_population: Record<string, number>;
}

export interface ScenarioTemplate {
  key: string;
  name: string;
  description: string;
  settings: Record<string, number>;
}

export interface CapacityProjection {
  citizen_count: number;
  estimated_memory_mb: number;
  estimated_tick_ms: number;
  recommended_tier: string;
}

export interface Relationship {
  target_citizen_id: string;
  relationship_type: string;
  strength: number;
  trust: number;
  familiarity: number;
  conflict: number;
  started_on: string;
  last_interaction_on: string | null;
  is_active: boolean;
}

export interface CitizenMemory {
  id: string;
  memory_type: string;
  importance: number;
  emotional_score: number;
  recall_score: number;
  occurred_on: string;
  related_event_id: string | null;
  related_citizen_ids: string[];
  is_consolidated: boolean;
}

export interface CitizenProfile {
  id: string;
  full_name: string;
  age: number;
  lifecycle_status: string;
  education_level: string;
  employment_status: string;
  household_id: string | null;
  employer_business_id: string | null;
  income_minor: number;
  wealth_minor: number;
  health: number;
  happiness: number;
  reputation: number;
  personality: Record<string, number>;
  skills: Record<string, number>;
  beliefs: Record<string, { position: string; conviction: number }>;
  goals: Array<{
    title: string;
    status: string;
    priority: number;
    target_date: string | null;
  }>;
  memories: CitizenMemory[];
  major_events: TimelineEvent[];
}

export interface ProblemDetail {
  title: string;
  status: number;
  detail: string;
  code: string;
}

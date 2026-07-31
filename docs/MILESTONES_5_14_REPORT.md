# GENESIS Milestones 5-14 Report

Status: Complete as one explicitly authorized batch  
Next: Milestone 15 - Premium World Dashboard

## Delivered scope

| Milestone | Delivered |
|---:|---|
| 5 | Append-only per-world history, contiguous ordering, resumable subscriptions, snapshot catalog/restoration, filtered timeline/citizen history/important-event/replay APIs, and a transactional outbox schema. |
| 6 | Configurable deterministic education, adulthood, work eligibility, retirement, illness, mortality, household/dependent state, citizen detail API, and citizen profile UI. |
| 7 | Typed reciprocal relationships, decay, family traversal, social-network persistence/API, and a citizen social graph. PostgreSQL remains authoritative. |
| 8 | Integer-only income, tax, consumption, savings, demand, pricing, business profit/bankruptcy, employment, inflation, and GDP formulas plus world economy metrics/UI. |
| 9 | Deterministic multi-factor democratic voting, terms/policy records, public-budget effects, government/law API, and government UI. No provider output affects elections. |
| 10 | Seeded seasons, weather, resources, food, pollution, disease, fire/flood/drought risk, cross-system impacts, health/environment metrics, timeline, and fictional risk-map UI. |
| 11 | Provider protocol, factory-ready provider map, deterministic mock, timeout/retry integration boundary, validation, usage/cost model, cache, fallback, circuit breaker, and disabled-by-default operation. |
| 12 | Major-event eligibility, structured requests, validation, cache/budget enforcement, deterministic fallback boundary, and AI activity analytics. |
| 13 | Bounded short-term memory, consolidation, decay, recall, decision bias, goal progress/failure/replacement, persistence, API, and profile UI. |
| 14 | Authenticated SSE, Last-Event-ID backlog, channels, heartbeats, bounded queues, slow-client cleanup, compact updates, and CSRF-protected persisted controls for run/pause/resume/step/speed/jump/reset/replay. |

## Architecture decisions

- Deterministic mechanics remain in the separately installable simulation
  package. FastAPI coordinates authorization, persistence, queries, commands,
  and delivery.
- PostgreSQL is the authoritative event, relationship, memory, command, and
  usage store. Redis remains optional fan-out infrastructure; loss of Redis
  cannot lose history.
- SSE is used for server-to-browser updates. Commands remain authenticated HTTP
  requests.
- Money and election formulas use integers. AI annotations are never mechanics
  inputs.
- Relationship traversal stays in PostgreSQL/in-process deterministic graph
  logic; Neo4j and vector retrieval remain postponed.

## Database changes

Migration `20260731_0003_simulation_platform.py` adds:

- `world_settings.is_paused`
- `citizen_relationships`
- `citizen_memories`
- `simulation_outbox`
- `simulation_commands`
- `ai_usage`

The existing simulation event, snapshot, metric, citizen, household, business,
government, and law tables remain authoritative.

## Environment variables

No provider secret is required. The application operates with AI disabled.
Existing `GENESIS_DATABASE_URL`, `GENESIS_REDIS_URL`, authentication, and web
API URL settings are unchanged. Provider secrets should only be added when a
concrete adapter is enabled in a later deployment configuration.

## Important formulas

- Citizen savings = salary - integer tax - integer consumption.
- Period tax = employed income x tax percent / 100.
- Consumption = employed income x consumption percent / 100.
- Business profit = allocated demand revenue - operating cost.
- GDP approximation = household earned income + business demand revenue.
- Price adjustment = unit price x inflation basis points / 10,000.
- Voting score combines ideology fit, employment confidence, approval,
  education/wellbeing, candidate competence/reputation, social influence, and
  recent-event sentiment with stable citizen-ID tie-breaking.

## Verification

- Simulation: Ruff format/lint, strict MyPy, and 20 tests pass.
- API: Ruff format/lint, strict MyPy, and 14 tests pass.
- Web: Prettier, ESLint, TypeScript, production build, and 2 rendered HTML tests
  pass.
- Tests cover event ordering/restoration, lifecycle determinism, reciprocal
  graphs, accounting, elections/policy, seeded disasters, AI caching/budgets,
  memory-influenced decisions, SSE backpressure, API ownership, CSRF, command
  validation, and command ordering.

## Known limitations

- Cloud/provider adapters are represented by the provider-neutral contract and
  deterministic mock; no external AI call is enabled.
- The command queue is the durable control boundary. A continuously running
  background command consumer is intentionally deferred to Milestone 19, so
  deployments must run the engine worker to turn accepted commands into ticks.
- Multi-instance SSE fan-out can use the outbox plus Redis later; the current
  in-process hub provides bounded single-instance delivery and durable backlog
  recovery from PostgreSQL.
- The risk map is fictional and does not claim real-world predictive accuracy.
- Advanced charts, broad navigation, compare mode, and visual polish continue
  in Milestones 15-17.

## Commands

Use `make check` for the full repository quality sequence. Apply the database
migration with `uv run alembic upgrade head` from `apps/api`.

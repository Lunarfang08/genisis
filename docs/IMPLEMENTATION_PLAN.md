# GENESIS Implementation Plan

Status: Milestone 25 complete - release candidate 1.0.0-rc.1  
Primary source: `GENESIS_Artificial_Civilization_Simulator_Architecture.md`  
Implementation sequence: `GENESIS Codex Implementation Prompts.pdf`

## 1. Product boundary

GENESIS is a deterministic, event-driven civilization simulator with an
optional AI narrative layer. The simulation owns facts and outcomes. AI may
later explain or dramatize important outcomes, but it must never be required
for core world progression.

The first useful release is a single-developer, local-first application:

- One web application and one API service.
- PostgreSQL as the authoritative data store.
- Redis for coordination, caching, and ephemeral state only when a concrete
  use case is implemented.
- A deterministic Python simulation engine that can run without a network.
- Server-Sent Events (SSE) for the initial live dashboard.
- AI disabled by default and absent from the MVP critical path.

## 2. Delivery tiers

### MVP requirements

- Local development with Docker Compose and documented non-container commands.
- Authentication and user-owned worlds.
- Normalized core domain models and database migrations.
- Seeded, deterministic simulation ticks with pause, resume, step, reset,
  snapshots, events, and replay.
- Functional citizen lifecycle, relationships, economy, democratic government,
  and environment systems.
- World dashboard, citizen profiles, timeline, controls, and 2D visualization.
- Tests for determinism, authorization, event ordering, replay, and critical
  formulas.
- Demo mode that does not require paid services or an AI key.

### Portfolio-polish requirements

- Premium responsive UI, motion, accessibility, guided demo, historical
  comparisons, exports, architecture pages, and transparent AI activity.
- Profiling and verified scale targets.
- Operational dashboards, security hardening, deployment examples, screenshots,
  and a demo video script.
- Optional Groq or local Ollama narratives for a small number of major events.

### Stretch goals

- Neo4j projection for graph-heavy analytics.
- Vector retrieval for narrative context.
- 3D world views.
- Multiple nations, diplomacy, conflict, newspapers, technology progression,
  modding, multiplayer worlds, voice, and media generation.

## 3. Recommended monorepo

```text
genesis/
|-- apps/
|   |-- api/
|   |   |-- alembic/
|   |   |-- src/genesis_api/
|   |   |   |-- api/
|   |   |   |-- core/
|   |   |   |-- db/
|   |   |   |-- models/
|   |   |   |-- repositories/
|   |   |   |-- schemas/
|   |   |   `-- services/
|   |   `-- tests/
|   `-- web/
|       |-- app/
|       |-- components/
|       |-- features/
|       |-- lib/
|       |-- stores/
|       `-- tests/
|-- packages/
|   |-- simulation/
|   |   |-- src/genesis_simulation/
|   |   `-- tests/
|   `-- shared-types/
|-- infrastructure/
|   |-- docker/
|   `-- scripts/
|-- docs/
|-- .env.example
|-- docker-compose.yml
|-- Makefile
`-- README.md
```

The simulation is a Python package, not an API subfolder. This keeps domain
logic independent from FastAPI and makes deterministic unit tests fast.
`shared-types` holds generated or hand-maintained API contracts only; it must
not become a second domain model.

## 4. Frontend architecture

- Next.js App Router, React, and strict TypeScript.
- Server components for initial page composition; client components only for
  interactive dashboards, controls, charts, and streaming.
- Feature folders (`worlds`, `citizens`, `timeline`, `economy`, `government`)
  containing UI, queries, and feature-specific types.
- TanStack Query for server state and cache invalidation.
- Zustand for transient interface state such as selected date, filters, and
  simulation controls. Authoritative world state stays on the server.
- A typed `fetch` client generated from or checked against the OpenAPI schema.
- Tailwind CSS with design tokens; Framer Motion used selectively.
- React Flow for relationship/family graphs. Start world visualization with
  Canvas or PixiJS; add Three.js only after profiling shows a useful 3D case.
- Accessible dark-first interface with keyboard controls, reduced-motion
  support, loading, empty, offline, and error states.

## 5. Backend architecture

FastAPI uses a layered modular monolith:

```text
HTTP/SSE -> API schemas -> application services -> repositories
                                      |
                                      v
                             simulation package
                                      |
                                      v
                         PostgreSQL + event outbox
```

- Pydantic validates boundaries and settings.
- SQLAlchemy 2.x owns persistence; Alembic owns schema changes.
- Repositories isolate queries. Services enforce authorization and coordinate
  transactions.
- Domain logic remains in the simulation package rather than routes or ORM
  models.
- RFC 9457-style problem responses provide consistent API errors.
- Structured JSON logging includes request, user, world, correlation, and
  causation identifiers while excluding tokens and private payloads.
- Background workers are postponed until measured tick duration or concurrent
  worlds justify them. The initial worker can be a separate process using the
  same Python packages.

## 6. Simulation engine

The engine processes a world in an explicit, stable order:

1. Load a versioned snapshot and pending user commands.
2. Construct the seeded pseudo-random generator from stored engine state.
3. Advance the simulation clock.
4. Execute registered systems in a versioned order.
5. Collect proposed state changes and domain events.
6. Validate invariants.
7. Persist state, immutable events, RNG state, and an outbox atomically.
8. Optionally create a snapshot.
9. Publish committed changes to live subscribers.

Each system implements a small interface such as:

```text
process(context, state) -> SystemResult(changes, events, metrics)
```

Rules:

- Never use wall-clock time, global randomness, unordered database iteration,
  or provider output in deterministic mechanics.
- Persist the seed, RNG algorithm/version, system order, engine version, input
  commands, and relevant configuration.
- Sort batches by stable identifiers before processing.
- Use decimal or integer minor units for money.
- Version formulas and event payload schemas.
- AI-generated text is an annotation of a committed event, never an input to
  the deterministic state transition unless explicitly converted into a
  validated user command.

## 7. Event-driven architecture

PostgreSQL is both the transactional store and the initial durable event store.
Events are append-only and contain:

- Event ID, world ID, simulation timestamp, sequence number, category, and type.
- Schema and engine versions.
- Actor/target references.
- Causation and correlation IDs.
- Importance and severity.
- Validated JSON payload and creation timestamp.

A transactional outbox prevents state/event broadcasts from being lost between
the database commit and Redis publication. Consumers must be idempotent. Event
ordering is guaranteed per world by a monotonically increasing sequence, not by
wall-clock timestamps.

Snapshots are versioned checkpoints. Replay loads the nearest compatible
snapshot, validates its checksum, then applies ordered events or re-executes
recorded commands depending on the test being performed.

## 8. Data responsibilities

### PostgreSQL

Authoritative users, worlds, settings, citizens, households, cities,
businesses, governments, relationships, metrics, commands, events, snapshots,
refresh-token metadata, and audit records. It also enforces constraints,
transactions, ownership, and per-world ordering.

### Redis

Ephemeral rate-limit counters, short-lived query caches, simulation leases,
presence, SSE fan-out, and job coordination. Redis loss must not lose world
history. Redis is included in the development environment but only adopted
feature-by-feature.

### Neo4j

Postponed. PostgreSQL adjacency tables and recursive queries are sufficient for
the first relationship and family-tree implementation. If profiling later
proves a need, Neo4j becomes a rebuildable read projection; PostgreSQL remains
authoritative.

### Vector memory

Postponed and optional. Deterministic indexed memory retrieval is enough for
mechanics. A vector store may later retrieve bounded context for narratives,
but no simulation outcome may depend on it.

## 9. AI provider abstraction

Milestone 11 introduces a provider-neutral interface for structured generation,
health, and usage reporting. Initial providers are mock, Groq, and Ollama;
OpenAI and Anthropic remain optional adapters.

The layer includes validated structured output, timeouts, bounded retries with
jitter, rate-limit handling, a circuit breaker, cache keys based on normalized
inputs, usage/cost records, a daily world budget, and deterministic fallbacks.
Provider secrets are read only from the runtime environment. AI is off by
default and all AI paths must have tests using the mock provider.

## 10. Real-time strategy

Use SSE first because the dominant traffic is authenticated server-to-browser
updates. Commands continue over normal HTTP, which simplifies authorization,
retries, observability, and proxies.

- Authenticate when opening a world stream.
- Send event IDs so clients can resume with `Last-Event-ID`.
- Use heartbeats, bounded per-client queues, event batching, and channel
  subscriptions.
- Send compact deltas and invalidation hints, never the full world per tick.
- Redis pub/sub supports multi-instance fan-out later; PostgreSQL/outbox remains
  the durable source.

WebSockets should be reconsidered only if bidirectional low-latency interaction
becomes a measured requirement.

## 11. Local development

Milestone 1 will provide one root command that starts:

- Next.js web development server.
- FastAPI development server.
- PostgreSQL with a persistent local volume.
- Redis with a health check.

The repository will include `.env.example`, Docker health checks, migration
commands, seed/demo commands, and separate commands for format, lint, typecheck,
test, and production builds. Ollama and all cloud AI providers are optional.

## 12. Testing strategy

- Simulation: pure unit, invariant/property, determinism, replay, snapshot
  compatibility, and formula tests.
- Backend: service, repository, migration, authentication/authorization, API,
  outbox, SSE, and failure-path tests.
- Frontend: component, hook, query/store, accessibility, and API-contract tests.
- End to end: registration, world creation, simulation control, timeline, and
  demo-mode flows.
- Performance: fixed datasets of 1k, 10k, and eventually 50k citizens with
  hardware and configuration recorded.
- CI: formatting, linting, Python and TypeScript type checks, tests, migration
  verification, production builds, and dependency/security scans.

Tests use isolated databases and deterministic factories. Flaky timing-based
assertions and live AI calls are prohibited in CI.

## 13. Deployment strategy

Start with Docker Compose on one development machine. A cost-conscious hosted
shape is:

- Next.js on Vercel or a container host.
- API and simulation worker on a small container host.
- Managed PostgreSQL.
- Optional managed Redis, or no Redis for a single-process demo.
- Groq only when explicitly enabled; Ollama for local demonstrations.

Containers will be multi-stage, non-root, health-checked, and pinned. Migrations
run as a release task, not independently in every replica. Scale the API and
workers separately only after simulation leases and idempotency are proven.

## 14. Security

- Argon2id password hashing, short-lived access tokens, rotating refresh tokens,
  and revocation metadata.
- Prefer secure, HTTP-only, same-site cookies for the browser; require CSRF
  protection on state-changing cookie-authenticated requests.
- World-scoped authorization in services and repositories to prevent IDOR.
- Strict CORS allowlists, trusted-host checks, security headers, request-size
  limits, rate limiting, and safe problem responses.
- Parameterized queries, validated identifiers, output encoding, and no
  untrusted HTML.
- Redact credentials, cookies, prompts containing private data, and AI outputs
  from logs.
- Validate AI output as untrusted input and restrict provider egress.
- Least-privilege database roles, non-root containers, locked dependencies,
  scanning, backups, and restore drills.

## 15. Performance

- Process citizens in deterministic batches with bulk reads/writes.
- Store metrics as time-series aggregates rather than recalculating dashboards.
- Index by `world_id` plus common time, sequence, and status filters.
- Paginate timelines and virtualize large frontend lists.
- Snapshot at configurable intervals based on replay cost.
- Measure tick duration, query count, memory, event volume, stream queue depth,
  and render time before introducing workers, Neo4j, or vector search.
- Make no population-scale claim without a repeatable benchmark.

## 16. Assumptions and unresolved product decisions

- Initial release supports one civilization per world and one active simulation
  writer per world.
- Initial government implementation is democratic; other types remain modeled
  settings until their mechanics exist.
- “Rewind” creates a branch or read-only historical view; it does not mutate the
  append-only history in place.
- Crime, war, religion, mental health, and disease require explicit domain rules
  and careful fictional framing in their respective milestones.
- Deployment vendors are examples, not requirements.
- Exact UI visual language, initial population cap, snapshot interval, and
  simulation calendar are decided with measured prototypes in later milestones.

## 17. Definition of done for every implementation milestone

- The milestone scope is implemented without silently starting the next one.
- Formatting, linting, type checks, tests, and relevant builds pass.
- Migrations, environment variables, assumptions, limitations, and commands are
  documented.
- The application remains runnable using documented steps.
- No secret, fake production data, or unverified capability claim is committed.

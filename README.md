# GENESIS

GENESIS is an AI-enhanced artificial civilization simulator. Its core is a
deterministic, seeded, replayable engine where citizens, households,
businesses, governments, and environments evolve through explicit rules and
immutable events. AI is optional and narrates selected committed events without
controlling world mechanics.

## Current status

Milestone 25 - Final Audit and Release Candidate: **complete**

The repository now contains:

- A premium responsive Next.js observation deck.
- A FastAPI gateway with validated settings and structured request logging.
- PostgreSQL and Redis connection lifecycle management.
- Separate liveness and dependency-aware readiness endpoints.
- Docker Compose services and container health checks.
- Root commands, pinned dependencies, automated tests, and CI quality gates.
- Shared TypeScript API contracts.
- Argon2id authentication with rotating refresh sessions and CSRF protection.
- Protected frontend/API routes and owner-scoped world authorization.
- User, World, WorldSettings, and refresh-session database migrations.
- Private world creation, listing, opening, and deletion.
- Normalized regions, cities, households, occupations, citizens, businesses,
  governments, laws, simulation events, snapshots, and world metrics.
- Citizen skills, beliefs, goals, personality, wellbeing, employment, and
  integer-minor-unit financial state.
- Domain repositories, service validation, database constraints, indexes, and
  deterministic test-data factories.
- A separately testable, seeded pure-Python simulation package.
- Deterministic clock and tick processing with stable versioned system order.
- Functional lifecycle, employment, relationship, economy, government, and
  environment system foundations.
- Pause, resume, single-step, speed, reset, checksummed snapshots, and command
  replay.
- Append-only event history, subscriptions, snapshots, filtered timelines, and
  snapshot-plus-event replay.
- Deterministic lifecycle, education, retirement, illness, relationship,
  economy, democratic election, policy, environment, disease, and disaster
  rules.
- PostgreSQL relationship, memory, outbox, command, and AI usage records.
- Citizen profiles, social graphs, world analytics, government/environment
  readouts, AI activity, and major-event timelines.
- Optional provider-neutral AI with structured validation, caching, budgets,
  fallback, circuit breaking, and deterministic mock tests.
- Authenticated resumable SSE with channels, heartbeats, bounded queues, and
  changed-data-only messages.
- Premium live vital signs, historical charts, a selectable 2D city map,
  compare analytics, and JSON/CSV/summary exports backed by real data.
- A validated seven-template creation wizard with capacity projections, plus a
  separately scalable command/outbox worker with single-world Redis leases.
- Security hardening, aggregate operational diagnostics, production Compose,
  a no-login deterministic demo, and complete release documentation.

## Start locally

Prerequisites:

- Docker Desktop with Docker Compose.
- Ports `3000` and `8000` available.

Create an environment file:

```bash
cp .env.example .env
```

Start the complete local stack with one command:

```bash
docker compose up --build
```

Open:

- Web application: <http://localhost:3000>
- API documentation: <http://localhost:8000/docs>
- API liveness: <http://localhost:8000/api/v1/health/live>
- API readiness: <http://localhost:8000/api/v1/health/ready>

Stop the stack with `docker compose down`.

### Use the app

1. Open <http://localhost:3000/register> and create a local account.
2. Create a world from the workspace. GENESIS immediately seeds its cities,
   citizens, households, jobs, businesses, government, history, and metrics.
3. Open the world and press **Run**. The worker advances the civilization and
   the observatory refreshes automatically. Use **Pause**, **Step**, **Reset**,
   and **Speed** to control it.
4. Explore the map, population, economy, citizen profiles, timeline, analytics,
   environment, government, and exports from the world screen.

No LLM key is required for the simulation. To enable optional Groq-written
historical notes, set these values in the untracked `.env`, restart the stack,
and select Groq when creating a world:

```dotenv
GENESIS_AI_ENABLED=true
GENESIS_AI_PROVIDER=groq
GENESIS_AI_MODEL=llama-3.3-70b-versatile
GENESIS_GROQ_API_KEY=replace-with-a-new-key
```

The deterministic mechanics continue working if Groq is unavailable; only the
prose annotation falls back.

## Host development

Node.js 22 and [uv](https://docs.astral.sh/uv/) are required.
PostgreSQL and Redis must be available at the URLs configured in `.env`.

```bash
npm install
cd apps/api && uv sync
uv run alembic upgrade head
```

Run the frontend and backend in separate terminals:

```bash
npm run dev:web
```

```bash
cd apps/api
uv run uvicorn genesis_api.main:app --reload
```

Run `uv run genesis-worker` from `apps/api` in a third terminal for background
command consumption and outbox publication.

Use `localhost` for both applications. Browser session cookies will not cross
between `localhost` and `127.0.0.1`.

## Quality commands

```bash
npm run format:check --workspace @genesis/web
npm run lint:web
npm run typecheck:web
npm run test:web

cd apps/api
uv run ruff format --check .
uv run ruff check .
uv run mypy src tests
uv run pytest

cd ../../packages/simulation
uv sync
uv run ruff format --check .
uv run ruff check .
uv run mypy src tests
uv run pytest
```

On systems with `make`, `make check` runs the complete quality sequence.

## Repository map

```text
apps/
  api/                  FastAPI application
  web/                  Next.js observation deck
packages/
  simulation/           Deterministic pure-Python simulation engine
  shared-types/         Network boundary contracts
infrastructure/
  docker/               Container definitions
  scripts/              Local orchestration helpers
docs/                   Architecture and milestone records
```

## Configuration

Runtime configuration uses environment variables prefixed with `GENESIS_`.
Browser-visible variables use `NEXT_PUBLIC_`. Copy `.env.example` and keep the
real `.env` untracked.

AI credentials are optional. AI is disabled by default, the deterministic mock
requires no key, and provider output cannot alter mechanics. Groq uses its
OpenAI-compatible chat-completions endpoint. Never commit keys.

## Architecture documents

- [Implementation plan](docs/IMPLEMENTATION_PLAN.md)
- [Architecture decisions](docs/ARCHITECTURE_DECISIONS.md)
- [Milestones and dependency graph](docs/MILESTONES.md)
- [Risk register](docs/RISKS.md)
- [Authentication design](docs/AUTHENTICATION.md)
- [Core domain model](docs/DOMAIN_MODEL.md)
- [Simulation engine](docs/SIMULATION_ENGINE.md)
- [Milestone 1 report](docs/MILESTONE_1_REPORT.md)
- [Milestone 2 report](docs/MILESTONE_2_REPORT.md)
- [Milestone 3 report](docs/MILESTONE_3_REPORT.md)
- [Milestone 4 report](docs/MILESTONE_4_REPORT.md)
- [Milestones 5-14 report](docs/MILESTONES_5_14_REPORT.md)
- [Milestones 15-25 report](docs/MILESTONES_15_25_REPORT.md)
- [API guide](docs/API_GUIDE.md)
- [Deployment guide](docs/DEPLOYMENT.md)
- [Security guide](docs/SECURITY.md)
- [Release checklist](docs/RELEASE_CHECKLIST.md)
- [Performance benchmark](docs/PERFORMANCE_BENCHMARK.md)
- [Known limitations](docs/KNOWN_LIMITATIONS.md)

## Release status

Release candidate `1.0.0-rc.1` implements milestones 1-25. Optional milestones
26-29 remain outside the release critical path.

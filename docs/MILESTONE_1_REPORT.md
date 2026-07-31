# Milestone 1 Completion Report

Completed: 2026-07-27

## What was implemented

- npm workspace monorepo with `apps/web`, `apps/api`, and
  `packages/shared-types`.
- Responsive GENESIS observation deck with accessible focus states,
  reduced-motion handling, empty/error-aware content, and no fabricated world
  metrics.
- Typed frontend readiness client with a bounded request timeout.
- FastAPI application factory surface with Pydantic environment settings,
  structured JSON logging, request IDs, strict CORS origins, and graceful
  resource cleanup.
- SQLAlchemy asynchronous PostgreSQL manager and asynchronous Redis manager.
- Liveness and dependency-aware readiness endpoints.
- Docker Compose stack for web, API, PostgreSQL, and Redis with health checks
  and persistent database/cache volumes.
- Pinned Python lockfile, npm lockfile, frontend rendered-output tests, backend
  API tests, and GitHub Actions quality gates.
- A project-specific social preview image and runtime-derived Open Graph URLs.

## Architecture decisions applied

- Modular monolith rather than distributed services.
- PostgreSQL is authoritative; Redis remains ephemeral.
- API liveness does not depend on external services. Readiness reports
  PostgreSQL and Redis state and returns HTTP 503 when either is unavailable.
- The frontend shows explicit empty states until real domain data exists.
- AI is neither configured nor invoked.
- Docker Compose is the single-command local workflow.

## Files created or changed

- Root: `.env.example`, `.gitignore`, `package.json`, `package-lock.json`,
  `Makefile`, `docker-compose.yml`, `README.md`.
- API: `apps/api/pyproject.toml`, `apps/api/uv.lock`, application package,
  health routes, resource managers, and tests.
- Web: Next.js application shell, API client, styles, metadata, social image,
  rendered HTML tests, and quality configuration.
- Infrastructure: API/web Dockerfiles, readiness helper, and CI workflow.
- Documentation: milestone status and this report.

## Database changes

No application tables or migrations were created. PostgreSQL is provisioned and
health-checked only. Domain schema work begins in Milestone 2.

## Environment variables

See `.env.example`:

- `GENESIS_ENVIRONMENT`
- `GENESIS_LOG_LEVEL`
- `GENESIS_API_HOST`
- `GENESIS_API_PORT`
- `GENESIS_API_PREFIX`
- `GENESIS_CORS_ORIGINS`
- `GENESIS_DATABASE_URL`
- `GENESIS_REDIS_URL`
- `GENESIS_HEALTH_TIMEOUT_SECONDS`
- `NEXT_PUBLIC_API_URL`
- `GENESIS_INTERNAL_API_URL`

No AI key is used.

## Commands to run

Complete stack:

```bash
docker compose up --build
```

Frontend:

```bash
npm run dev:web
```

Backend:

```bash
cd apps/api
uv sync
uv run uvicorn genesis_api.main:app --reload
```

Quality commands are documented in the root README and Makefile.

## Test results

- Backend formatting: passed.
- Backend Ruff linting: passed.
- Backend strict mypy: passed.
- Backend Pytest: 3 passed.
- Frontend Prettier check: passed.
- Frontend ESLint: passed.
- Frontend strict TypeScript: passed.
- Frontend rendered-output tests: passed.
- Frontend production build: passed.

Docker Compose execution was not exercised on the implementation workstation
because Docker is not installed there. The Compose file is still syntax-checked
where tooling permits and exercised by its documented health contracts.

## Known limitations

- The world creation buttons and future module navigation are deliberately
  disabled until their milestones.
- Readiness is degraded without running PostgreSQL and Redis.
- No database migrations, authentication, simulation, live events, or AI
  providers exist yet.
- Local infrastructure requires Docker Desktop or independently running
  PostgreSQL and Redis.

## Recommended next milestone

Milestone 2: secure authentication and user-owned world workspaces.

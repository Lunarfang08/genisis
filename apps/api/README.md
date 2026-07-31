# GENESIS API

FastAPI gateway and worker runtime for secure private worlds, simulation
history/control/streaming, analytics/maps/exports, optional AI activity,
operational diagnostics, and background command/outbox handling.

World creation immediately persists a deterministic starting civilization. The
worker consumes controls, hydrates the engine from the database, advances active
worlds, persists citizens/metrics/events/snapshots, and optionally annotates
major committed events with Groq. AI is never part of the mechanics.

## Local commands

```bash
uv sync
uv run alembic upgrade head
uv run uvicorn genesis_api.main:app --reload
uv run genesis-worker
uv run ruff format --check .
uv run ruff check .
uv run mypy src tests
uv run pytest
```

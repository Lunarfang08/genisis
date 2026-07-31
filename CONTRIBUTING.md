# Contributing

Use Node 22.13+, Python 3.13, uv 0.11.32, PostgreSQL 17, and Redis 8. Create focused changes, preserve determinism, add negative authorization/failure tests, and never commit secrets or generated private data.

Run `make format`, then `make check`. Schema changes require an Alembic revision and `uv run alembic heads` from `apps/api`. Simulation rules must avoid wall-clock time, global randomness, unordered iteration, network calls, and AI output. Document user-visible changes in `CHANGELOG.md`.

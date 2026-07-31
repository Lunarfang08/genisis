# Milestone 3 Completion Report

Completed: 2026-07-31

## Implemented

- SQLAlchemy models and Alembic migration for Region, City, Citizen, Household,
  Occupation, Business, Government, Law, SimulationEvent,
  SimulationSnapshot, and WorldMetric.
- Normalized citizen skills, beliefs, and goals.
- Citizen identity, birth-derived age, biological and lifecycle state,
  education, employment, income, wealth, health, happiness, reputation, and
  OCEAN personality traits.
- Expanded world settings for simulation date and currency metadata.
- UUID keys, timestamps, deletion policies, uniqueness rules, checks, and
  world-scoped indexes.
- Typed application enums backed by portable constrained strings.
- Repository protocol and SQLAlchemy implementation.
- Civilization service with name, score, temporal, employment, and cross-scope
  validation.
- Deterministic factories for users, worlds, regions, cities, households, and
  occupations.

## Validation

- Backend tests: 11 passed, including domain aggregate creation, invalid-state
  rejection, database score constraints, and per-world event ordering.
- Ruff format and lint: passed.
- Strict mypy for source and tests: passed.
- Alembic PostgreSQL SQL generation through revision `20260731_0002`: passed.
- Frontend Prettier, ESLint, strict TypeScript, production build, and rendered
  HTML tests: passed.
- Existing authentication, authorization, health, and readiness tests remain
  green.

## Design decisions

- Age is derived from birth date to avoid inconsistent duplicated state.
- Skills, beliefs, and goals are normalized child tables.
- Money is stored as integer minor units.
- Event payloads, snapshot state, RNG state, and metric labels are the only new
  JSON boundaries.
- Database-native enum types are avoided to keep status evolution and
  migrations controlled.
- Cross-world and cross-city reference invariants are enforced by services in
  addition to ordinary foreign keys.

## Boundaries

No simulation ticks, lifecycle mechanics, relationship edges, economy rules,
government behavior, live event publication, replay, AI calls, or new domain
UI/API workflows were added. Neo4j remains deferred.

## Next milestone

Milestone 4: deterministic, seeded, replayable simulation engine.

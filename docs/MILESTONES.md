# GENESIS Milestones

## Status legend

- Complete: scope implemented and reviewed.
- Next: approved next unit, not started.
- Planned: dependent work, not started.
- Optional: stretch work, not part of the release critical path.

## Progress

| ID | Milestone | Status | Depends on |
|---:|---|---|---|
| 0 | Architecture review and implementation plan | Complete | - |
| 1 | Monorepo and development environment | Complete | 0 |
| 2 | Authentication and user workspace | Complete | 1 |
| 3 | Core domain models and schema | Complete | 2 |
| 4 | Deterministic simulation engine | Complete | 3 |
| 5 | Events, history, snapshots, and replay | Complete | 4 |
| 6 | Citizen lifecycle and households | Complete | 5 |
| 7 | Relationships and social dynamics | Complete | 6 |
| 8 | Economy and businesses | Complete | 6, 7 |
| 9 | Government, elections, laws, and policy | Complete | 8 |
| 10 | Environment, disease, and disasters | Complete | 6, 8 |
| 11 | AI provider abstraction | Complete | 1, 5 |
| 12 | AI decisions and narratives | Complete | 9, 10, 11 |
| 13 | Memory and goals | Complete | 6, 7 |
| 14 | Real-time streaming and controls | Complete | 5 |
| 15 | Premium world dashboard | Complete | 8, 9, 10, 14 |
| 16 | Interactive city/world visualization | Complete | 3, 14 |
| 17 | Analytics, compare mode, explorer | Complete | 5, 8, 9, 10 |
| 18 | World creation wizard and scenarios | Complete | 3, 4 |
| 19 | Performance and background processing | Complete | 14-18 |
| 20 | Security hardening | Complete | 2, 11, 14 |
| 21 | Automated testing and quality gates | Complete | Continuous; audit after 20 |
| 22 | Observability and administration | Complete | 14, 19 |
| 23 | Dockerization and deployment | Complete | 19-22 |
| 24 | Portfolio polish and demo | Complete | 15-18, 23 |
| 25 | Final audit and release candidate | Complete | 24 |
| 26 | Newspaper and archive | Optional | 5, 11, 12 |
| 27 | Technology progression | Optional | 8, 11 |
| 28 | Migration, diplomacy, and conflict | Optional | 8-10 |
| 29 | Modding and scenario SDK | Optional | Stable engine/events |

## Dependency graph

```text
0 -> 1 -> 2 -> 3 -> 4 -> 5 -> 6 -> 7 -> 8 -> 9
                         |         |         |
                         |         |         `------> 12
                         |         `---------------> 13
                         `-> 14 -> 15 -> 16 -> 17 -> 19
                                  ^       ^
3 -----------------------------> 18 -----|
6 ----------------> 10 ------------------|
1 + 5 ------------> 11 -> 12 ------------|
19 -> 20 -> 21 -> 22 -> 23 -> 24 -> 25
```

The numbered order remains the default delivery order, but the graph identifies
work that can later be scheduled independently. Milestones 5-14 and 15-25 were
authorized as batches and each has a combined implementation report.

## Scope corrections

The source architecture is ambitious enough to become several products. The
following constraints keep it deliverable:

- Milestone 1 includes PostgreSQL and Redis services, but Redis-backed product
  behavior is introduced only when needed.
- Neo4j, ChromaDB, Celery, Three.js, and multi-provider AI are postponed until
  measured requirements justify their operating cost.
- Relationship and family traversal use PostgreSQL first.
- A 2D world view precedes 3D.
- SSE precedes WebSockets.
- AI comes after deterministic history, despite an API key being available.
- Quality work is continuous; Milestones 20 and 21 are audits, not the first
  time security and tests are addressed.

## Milestone 1 acceptance preview

Milestone 1 may start only on explicit approval. It will be complete when:

- The documented monorepo exists with pinned toolchains.
- Web, API, PostgreSQL, and Redis start using one root command.
- API and dependency health endpoints distinguish liveness and readiness.
- Logging, settings, CORS, connection lifecycle, and graceful shutdown exist.
- The frontend has a polished responsive shell and typed API health client.
- Docker health checks and basic CI are configured.
- Format, lint, typecheck, tests, and production builds pass.
- No civilization mechanics, authentication, or AI integration are smuggled
  into the milestone.

## Milestone 2 acceptance record

- Registration, login, logout, current-user, and refresh endpoints exist.
- Argon2id password hashing and rotating refresh-token families are implemented.
- Browser credentials use HTTP-only same-site cookies with CSRF protection.
- User, World, and WorldSettings are introduced through an Alembic migration.
- Users can create, list, open, and delete only their own worlds.
- Protected frontend and backend routes reject unauthenticated access.
- Authentication throttling uses Redis fixed windows and fails open only when
  Redis is unavailable; readiness still reports that degradation.
- Authentication, refresh rotation, CSRF, validation, CRUD, and negative
  ownership tests pass.
- Social login, payments, and civilization mechanics remain out of scope.

## Milestone 3 acceptance record

- Normalized models exist for regions, cities, citizens, households,
  occupations, businesses, governments, laws, events, snapshots, and metrics.
- Citizen identity, biological and lifecycle state, education, employment,
  money, wellbeing, personality, skills, beliefs, and goals are represented.
- UUID keys, timestamps, foreign keys, uniqueness rules, checks, and
  world-scoped query indexes are defined in SQLAlchemy and Alembic.
- Money uses integer minor units; versioned event and snapshot documents use
  JSON only at intentional schema boundaries.
- Database enum churn is avoided through typed application enums backed by
  constrained strings.
- Repository and service abstractions enforce cross-world and cross-city
  invariants before persistence.
- Deterministic test factories and domain, constraint, and ordering tests pass.
- Neo4j, simulation processing, event publication, and API/UI domain workflows
  remain out of scope.

## Milestone 4 acceptance record

- A separately installable pure-Python simulation package exists with no API,
  database, network, frontend, or AI dependency.
- Seeded MT19937 state is private to each engine run, versioned, serializable,
  and restored from snapshots.
- The clock advances deterministically across days, months, years, and leap
  days.
- Commands implement tick, pause, resume, single-step, speed selection, and
  reset-from-seed behavior.
- Lifecycle, employment, relationship, economy, government, and environment
  systems implement one stable, versioned system protocol and order.
- Citizen processing is UUID-sorted and batched independently of insertion
  order.
- State changes, metrics, and in-memory events are deterministic; event IDs and
  per-world sequence numbers do not depend on wall-clock time.
- Snapshots carry state, RNG state, engine/system compatibility metadata, and a
  canonical SHA-256 checksum.
- Re-executing the same recorded commands from the same initial state produces
  identical state, events, metrics, and snapshots.
- Durable history, event subscriptions, timeline queries, outbox publication,
  and database-backed replay remain Milestone 5 work.

# GENESIS Architecture Decisions

This file records accepted initial decisions. Decisions may be superseded only
with a dated entry explaining the migration and compatibility impact.

## ADR-001: Modular monolith first

- Status: Accepted
- Decision: Use one Next.js application, one FastAPI application, and one
  separately testable Python simulation package in a monorepo.
- Why: The domain boundaries are still evolving, and a single developer gains
  little from distributed service operations.
- Consequence: Modules require clear interfaces and ownership, but deployment
  stays simple. Services may be extracted only after measured scaling or
  ownership pressure.

## ADR-002: PostgreSQL is authoritative

- Status: Accepted
- Decision: Store transactional state, relationships, immutable events,
  snapshots, and metrics in PostgreSQL.
- Why: Transactions must atomically couple state changes and history. PostgreSQL
  supports the initial relational and graph-like workloads.
- Consequence: Neo4j and vector databases cannot be required for correctness.

## ADR-003: Redis is ephemeral

- Status: Accepted
- Decision: Use Redis only for caches, leases, rate limits, fan-out, and job
  coordination.
- Why: World history must survive Redis loss.
- Consequence: Every Redis-derived value is reconstructable or disposable.

## ADR-004: Deterministic mechanics are isolated from AI

- Status: Accepted
- Decision: Simulation outcomes use versioned rules, stored configuration, and
  seeded randomness. AI may add validated narrative annotations later.
- Why: Replay, testing, cost control, offline use, and trust all require
  reproducible mechanics.
- Consequence: Provider output cannot directly mutate world state.

## ADR-005: Python owns simulation logic

- Status: Accepted
- Decision: Implement the engine as a pure Python package consumed by FastAPI
  and future workers.
- Why: It provides mature numerical/testing tools and avoids coupling mechanics
  to HTTP or React.
- Consequence: Browser previews call the API rather than running a second
  TypeScript implementation.

## ADR-006: Append-only events plus snapshots

- Status: Accepted
- Decision: Assign a strictly increasing per-world event sequence and persist
  immutable, versioned events with periodic snapshots.
- Why: Timeline, audit, replay, and historical comparisons are core features.
- Consequence: Corrections use compensating events or migrations; history is not
  silently edited.

## ADR-007: Transactional outbox

- Status: Accepted
- Decision: Persist live-notification records in the same transaction as state
  and events, then publish asynchronously.
- Why: Direct publication after a commit can lose messages during crashes.
- Consequence: Consumers are idempotent and the outbox requires retention and
  monitoring.

## ADR-008: SSE before WebSockets

- Status: Accepted
- Decision: Stream committed changes with SSE; send commands over HTTP.
- Why: Initial traffic is primarily server-to-client and SSE provides simpler
  reconnect and proxy behavior.
- Consequence: Reassess WebSockets only for proven bidirectional latency needs.

## ADR-009: PostgreSQL relationships before Neo4j

- Status: Accepted
- Decision: Model typed relationship edges in PostgreSQL through the initial
  social-dynamics milestone.
- Why: One source of truth and fewer services keep the MVP achievable.
- Consequence: A future Neo4j instance, if justified by profiling, is a
  rebuildable read projection.

## ADR-010: No vector store in the MVP

- Status: Accepted
- Decision: Use typed memories, importance, decay, and deterministic queries.
- Why: Mechanics do not need semantic embeddings.
- Consequence: Vector retrieval is optional context selection for later AI
  narratives only.

## ADR-011: Cookie-based browser sessions

- Status: Accepted in Milestone 2
- Decision: Prefer secure HTTP-only cookies containing short-lived access
  credentials and rotating refresh credentials; protect state changes from
  CSRF.
- Why: Browser JavaScript should not hold long-lived bearer tokens.
- Consequence: Cross-origin deployment, cookie scope, refresh rotation, and CSRF
  behavior require integration coverage.
- Validation: Milestone 2 tests cover cookie sessions, CSRF failure, refresh
  rotation, logout, and protected routes.

## ADR-012: Money uses integer minor units

- Status: Accepted
- Decision: Store currency values as integers in a world-defined minor unit and
  use explicit rounding rules for formulas.
- Why: Binary floating point would undermine economic invariants and replay.
- Consequence: APIs provide formatted display values separately.

## ADR-013: One writer per world

- Status: Accepted
- Decision: Guard each running world with a lease so only one engine process
  advances it at a time.
- Why: Concurrent ticks would break sequence ordering and determinism.
- Consequence: Lease expiry, fencing tokens, and recovery are required before
  multiple workers are enabled.

## ADR-014: Rewind creates a branch

- Status: Proposed for Milestone 5 validation
- Decision: Historical inspection is read-only. Continuing from the past creates
  a new world branch with lineage metadata.
- Why: Mutating history conflicts with immutable events and reproducible replay.
- Consequence: The UI must distinguish viewing, replaying, and branching.

## ADR-015: Contracts at boundaries

- Status: Accepted
- Decision: Pydantic/OpenAPI define network contracts; TypeScript clients are
  generated or contract-tested from the schema.
- Why: Duplicated handwritten types drift.
- Consequence: The shared-types package contains boundary contracts, not Python
  domain internals.

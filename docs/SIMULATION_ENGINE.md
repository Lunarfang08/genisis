# GENESIS Deterministic Simulation Engine

Status: Accepted in Milestone 4

## Boundary

`packages/simulation` is a pure-Python package. It imports no FastAPI,
SQLAlchemy, Redis, frontend, network, or AI code. A world run is driven only by
its initial state, engine configuration, registered system versions, and
ordered commands.

Milestone 4 keeps events and snapshots in memory. Milestone 5 will add durable
event persistence, subscriptions, timeline queries, outbox delivery, and
database-backed replay.

## Tick pipeline

Each advancing tick performs this exact sequence:

1. Deep-copy the current world state.
2. Reconstruct the private PRNG from persisted RNG state.
3. Advance the calendar by the configured number of days.
4. Execute systems in unique numeric order.
5. Process citizens in stable ID order and fixed-size batches.
6. Apply typed state changes after each system.
7. Validate world and citizen invariants.
8. Persist the new PRNG state in the in-memory world state.
9. Assign deterministic UUIDv5 event IDs and increasing world sequences.
10. Create a checksummed snapshot when the interval is reached.

No mechanics use wall-clock time, global module randomness, collection insertion
order, network output, or AI output.

## Default system manifest

| Order | System | Initial functional behavior |
|---:|---|---|
| 100 | Lifecycle | Age-derived lifecycle transitions and bounded health drift |
| 200 | Employment | Seeded employment entry for eligible unemployed adults |
| 300 | Relationships | Bounded relationship drift and social-cohesion aggregate |
| 400 | Economy | Daily employed income and wealth updates in minor units |
| 500 | Government | Integer tax calculation and treasury updates |
| 600 | Environment | Bounded environmental-quality drift |

System names, versions, and order form the snapshot compatibility manifest.
Duplicate names or order values are rejected.

## Commands and controls

- `tick` advances only when the world is running.
- `pause` prevents ordinary ticks from consuming RNG or changing state.
- `step` advances exactly once while preserving pause state.
- `resume` permits ordinary ticks again.
- `set_speed` stores validated scheduler speed; speed does not change formulas
  or the number of simulated days per tick.
- `reset` restores the initialized seeded state and clears generated events.

All accepted commands are recorded. Control commands use the same deterministic
command path as advancing ticks.

## Randomness contract

The initial implementation uses Python's local MT19937 generator through a
restricted wrapper:

- Algorithm identifier: `python-mt19937`
- State format version: `1`
- Seed initialization version: Python `random.seed(..., version=2)`

The full RNG state is stored in world state and snapshots. Systems receive only
the run-scoped wrapper from `SimulationContext`. Changing algorithm, call order,
system order, or formulas requires an engine/system version change.

## Events and snapshots

Events include world ID, event sequence, tick, simulation date, category, type,
payload, engine/schema versions, references, severity, and importance.
UUIDv5 IDs derive from stable event facts.

Snapshots contain:

- Serialized world and citizen state
- Serialized RNG state
- Tick and event sequence
- Engine version
- RNG algorithm and version
- Ordered system manifest
- Canonical SHA-256 checksum

Restore rejects altered checksums and incompatible engine, RNG, or system
manifests.

## Replay contract

Milestone 4 replay re-executes the recorded command stream from the same initial
state. Tests prove identical:

- Serialized final state and RNG state
- Event IDs, ordering, and payloads
- System metrics
- Scheduled snapshots

Snapshot continuation also produces the same next state as an uninterrupted
run. Applying stored events to rebuild state is deliberately deferred to
Milestone 5.

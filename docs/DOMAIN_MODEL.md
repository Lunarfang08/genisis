# GENESIS Core Domain Model

Status: Accepted in Milestone 3

## Boundary

PostgreSQL is the authoritative store. The schema represents durable
civilization facts but does not implement simulation rules. All mutable records
are world-scoped, and application services validate that referenced records
belong to the same world before persistence.

## Entity map

| Entity | Purpose | Important boundaries |
|---|---|---|
| World / WorldSettings | Ownership and deterministic configuration | Seed, simulation date, tick rate, currency |
| Region / City | Geographic hierarchy | Names unique within their parent |
| Household | Residence and shared wealth | Belongs to one city and world |
| Occupation | World-specific work definition | Salary stored in minor units |
| Citizen | Individual durable state | Birth date is authoritative for age |
| CitizenSkill | Repeatable learned capability | Unique name per citizen, score 0-100 |
| CitizenBelief | Repeatable position and conviction | Unique topic per citizen |
| CitizenGoal | Current and historical goals | Status and priority are constrained |
| Business | City-based economic organization | Optional citizen owner |
| Government / Law | World, region, or city authority and policy | Scope target is constrained |
| SimulationEvent | Immutable ordered history envelope | Unique increasing sequence per world |
| SimulationSnapshot | Versioned replay checkpoint | Unique event sequence per world |
| WorldMetric | Time-series aggregate | Unique scope/entity/name/date point |

## Citizen representation

- Identity uses UUID, given name, family name, birth date, and DNA seed.
- Age is calculated from `birth_date` and the requested simulation date; it is
  not duplicated as mutable state.
- Biological sex and lifecycle status use application enums persisted as
  constrained strings.
- Personality uses the five 0-100 OCEAN trait columns.
- Education and employment have constrained statuses and optional world-scoped
  occupation and employer references.
- Income and wealth are integer minor units. Negative wealth is permitted so
  later debt mechanics do not require a schema change; income is non-negative.
- Health and happiness are 0-100; reputation is -100 to 100.
- Skills, beliefs, and goals are normalized child records rather than opaque
  JSON arrays.

## Intentional JSON boundaries

JSON is limited to data whose schema is explicitly versioned or naturally
open-ended:

- Simulation event payloads
- Snapshot world state and RNG state
- Metric labels

Event and snapshot rows carry schema and engine versions. Later milestones will
add serializers, checksum verification, append-only enforcement, outbox
publication, and replay behavior without changing this foundation.

## Integrity strategy

- UUID primary keys and explicit foreign-key deletion policies.
- Unique constraints for parent-scoped names and per-world event ordering.
- Check constraints for scores, statuses, lifecycle/death consistency,
  government scope targets, and law repeal state.
- Composite indexes for world/date, world/category, citizen employment,
  geographic traversal, and active goals.
- Repository protocols isolate persistence.
- Services validate same-world, same-city, required-employment, and temporal
  invariants.

Cross-table world consistency cannot always be expressed portably without
duplicating composite keys. It is therefore checked in services and will also
be exercised by simulation and authorization tests.

## Deferred work

Milestone 3 does not add simulation ticks, event publication, replay,
relationship edges, economy formulas, lifecycle rules, domain CRUD endpoints,
or dashboard screens. Neo4j remains deferred; PostgreSQL stays authoritative.

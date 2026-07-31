# GENESIS Risk Register

Ratings are current planning estimates. Owners are roles until a project team is
defined.

| ID | Risk | Likelihood | Impact | Mitigation / trigger | Owner |
|---|---|---|---|---|---|
| R-01 | Scope overwhelms a single developer | High | High | Enforce milestone stops, MVP tiers, and one polished vertical slice at a time | Product/Tech lead |
| R-02 | Determinism breaks through time, randomness, query order, or floats | High | Critical | Inject clock/RNG, stable sorting, integer money, engine/formula versions, golden replay tests | Simulation |
| R-03 | Event and relational state diverge | Medium | Critical | One transaction, outbox, invariants, checksums, replay verification | Backend |
| R-04 | Schema/event evolution makes old worlds unreadable | Medium | High | Version payloads/snapshots, compatibility tests, explicit migrations | Backend |
| R-05 | Tick processing does not scale | High | High | Batch access, profiling from 1k upward, stored aggregates, honest caps | Simulation |
| R-06 | Too many infrastructure services reduce reliability | High | High | Modular monolith; postpone Neo4j, vector DB, and task queues | Architecture |
| R-07 | AI cost, latency, or outage harms core use | Medium | Medium | AI off by default, daily budgets, cache, circuit breaker, deterministic fallback | AI |
| R-08 | AI invents facts or injects unsafe content | Medium | High | Ground prompts in committed events, schema validation, output treatment as untrusted, transparency UI | AI/Security |
| R-09 | Exposed provider credentials are abused | High | High | Never commit keys, rotate disclosed keys, environment-only loading, redact logs, budgets and provider limits | Security |
| R-10 | Cross-world authorization permits IDOR | Medium | Critical | Service/repository ownership filters, negative authorization tests, opaque UUIDs are not treated as authorization | Backend/Security |
| R-11 | Refresh-token or cookie design enables theft/CSRF | Medium | High | HTTP-only secure cookies, rotation/reuse detection, CSRF tokens, strict origins | Security |
| R-12 | Live streams exhaust memory or send stale state | Medium | High | Bounded queues, deltas, batching, resume IDs, backpressure metrics | Backend |
| R-13 | Multiple workers advance one world | Medium | Critical | Per-world leases with fencing tokens; one writer until tested | Simulation |
| R-14 | Rewind semantics destroy append-only history | Medium | High | Read-only replay; branch when continuing from the past | Product/Backend |
| R-15 | PostgreSQL graph traversal becomes slow | Medium | Medium | Index edges, cap interactive depth, profile; add Neo4j read projection only at threshold | Data |
| R-16 | Synthetic social/health/political systems imply real-world validity | Medium | High | Clearly label fictional mechanics, document formulas/biases, avoid predictive claims | Product |
| R-17 | Dashboard looks polished but uses fake data | Medium | High | Empty/skeleton states; every released chart backed by API data | Frontend |
| R-18 | Docker-only setup slows contribution | Medium | Medium | Document container and host workflows; pin versions and add health diagnostics | DevEx |
| R-19 | Hosted free tiers sleep, throttle, or lose performance | High | Medium | Honest deployment guide, demo mode, local fallback, no uptime claims | DevOps |
| R-20 | Dependency or container vulnerabilities ship | Medium | High | Lockfiles, automated scanning, non-root images, patch cadence | Security |
| R-21 | Generated volume makes backups/restores impractical | Medium | High | Retention, snapshot policy, compressed exports, restore drills | Data/DevOps |
| R-22 | Sensitive data appears in structured logs or AI prompts | Medium | High | Field allowlists, redaction tests, minimal prompt context, restricted admin views | Security |
| R-23 | Frontend graph/map becomes unusable for large worlds | High | Medium | Aggregation, level of detail, clustering, virtualization, render budgets | Frontend |
| R-24 | A milestone passes tests but clean-clone setup fails | Medium | High | CI starts from clean checkout, applies migrations, and runs smoke tests | DevEx |

## Immediate actions

1. Rotate the API credential shared outside a secret manager before using Groq.
2. In Milestone 1, commit only `.env.example`; ignore real environment files.
3. Establish deterministic coding rules before any simulation implementation.
4. Keep Neo4j, vector storage, background queues, and 3D rendering out of the
   MVP until a documented performance or product trigger is reached.
5. Treat initial population and tick-rate limits as benchmark results, not
   marketing targets.

## Contradictions and missing requirements

- The architecture proposes both WebSockets and SSE without choosing one. This
  plan selects SSE first.
- The folder structure separates `simulation`, `ai`, and `engines` at the root,
  while the implementation prompt recommends `packages`. This plan places the
  engine in `packages/simulation` and keeps provider adapters in the API until
  independent deployment is justified.
- “Rewind” conflicts with immutable history unless branching semantics are
  defined. Branching is the proposed resolution.
- Redis is required in Milestone 1 even though no product requirement needs it
  yet. It will be available but not made authoritative.
- The source does not define calendar rules, numeric precision, RNG algorithm,
  event schema compatibility, failure recovery, or one-writer concurrency.
  These become explicit engine decisions before Milestone 4.
- User deletion versus immutable historical events needs a retention and
  anonymization policy before production.
- World collaboration, data residency, backup objectives, supported browsers,
  and accessibility conformance level are unspecified.
- Other government types are listed in the architecture, but only democracy has
  milestone mechanics. They remain stretch implementations.


# Milestones 15-25 implementation report

Status: Complete - release candidate `1.0.0-rc.1`  
Date: 2026-07-31

## Acceptance record

- **15:** Real responsive vital signs, historical series, simulation controls,
  durable feed, AI disclosure/activity, keyboard focus, and honest states.
- **16:** Aggregated region/city API and a zoomable, selectable, layer-filtered
  2D city network with tooltips and drill-down context.
- **17:** Bounded metric/event/wealth/city analytics; date, city, citizen,
  policy, and snapshot/run comparison; timeline filters; and exports.
- **18:** All required scenario fields and seven templates, validation, optional
  AI/provider selection, and pre-creation capacity estimates.
- **19:** Indexed/bounded reads, Redis-leased command/outbox worker, and
  repeatable 1k/10k/50k time/memory benchmarks. No million-citizen claim.
- **20:** Production setting validation, trusted hosts, request limits, security
  headers, existing CSRF/rate limits/owner scopes, audits, and security guide.
- **21:** Release API/security tests and CI gates for format, lint, strict types,
  tests, builds, migration heads, dependencies, Compose, and container scanning.
- **22:** Structured request/worker logs, health/AI/stream counts, and an
  aggregate development admin endpoint disabled in production.
- **23:** Non-root pinned images, local/production Compose, one-shot migrations,
  worker, health checks, volumes, HTTPS proxy, and deployment guidance.
- **24:** Premium landing page, deterministic no-login demo, architecture,
  technology, performance, AI transparency, recruiter summary, and video script.
- **25:** Updated setup/API/deployment/security/contribution/changelog/release/
  limitations/roadmap/checklist documentation and an explicit final audit.

## Honest limitations

The worker hydrates, advances, and atomically persists deterministic worlds
under a single-writer lease. City detail currently reuses world context. Rich
citizen/policy/run comparison and production telemetry backends remain future
work and are not represented as completed capabilities.

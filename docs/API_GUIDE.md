# API guide

The OpenAPI document is available at `/openapi.json`; interactive docs are enabled outside production. Browser authentication uses same-site cookies through `/api/genesis/*`. State-changing requests require the readable `genesis_csrf` cookie value in `X-CSRF-Token`.

Core resources:

- `/api/v1/auth/*` registration, login, refresh, logout, and current user.
- `/api/v1/worlds` private world registry and validated scenario creation.
- `/api/v1/world-scenarios` and `/capacity-projection` creation support.
- `/api/v1/worlds/{id}/dashboard`, `/map`, `/analytics`, `/compare`, `/timeline`, and `/export` read surfaces.
- `/api/v1/worlds/{id}/controls` ordered commands; `/stream` resumable SSE with bounded channels and `Last-Event-ID`.
- `/api/v1/admin/overview` aggregate development/demo diagnostics, disabled in production.

Errors use `application/problem+json` with stable `code`, `status`, `title`, and safe `detail` fields. Timeline queries are cursor-like through `after_sequence`; list limits are bounded.

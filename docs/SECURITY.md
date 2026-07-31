# Security

## Supported release

Security fixes target the current release candidate on `main`. Report vulnerabilities privately to the repository owner; do not include credentials or user data in an issue.

## Controls

- Argon2id passwords, short access tokens, rotating refresh-token families, HTTP-only cookies, and double-submit CSRF protection.
- Owner-scoped service queries protect every private world surface from IDOR. SQLAlchemy parameterizes queries and Pydantic validates identifiers and payloads.
- Exact CORS/trusted-host allowlists, secure production cookies, a 1 MiB default body limit, authentication throttling, safe problem responses, and CSP/frame/content/referrer/permissions headers.
- Provider secrets are environment-only. AI output is untrusted, schema-validated annotation; provider URLs are configured by operators rather than supplied by users, limiting SSRF and prompt-injection impact.
- Structured logs exclude cookies, authorization headers, request bodies, prompts, and private records. Administration returns aggregate operational counts only and is disabled in production.
- Containers run as non-root. CI runs static analysis, dependency audits, migration-head checks, tests, builds, Compose validation, and high/critical filesystem scanning.

## Operator checklist

Use a unique 32+ character authentication secret, HTTPS, `GENESIS_COOKIE_SECURE=true`, least-privilege database credentials, exact hosts/origins, protected backups, and pinned image/dependency updates. Never expose PostgreSQL or Redis publicly. Terminate TLS at the supplied reverse proxy or a managed edge. Test backup restoration before release.

## Residual risks

The project does not accept file uploads. The development admin endpoint must not be treated as a production monitoring system. Redis rate limiting fails open during Redis loss so availability does not lock users out; an edge limiter should be used for public deployments. See [Known limitations](KNOWN_LIMITATIONS.md).

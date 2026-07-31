# Authentication and Authorization

GENESIS uses application-owned email/password authentication. Social login and
payments are intentionally excluded.

## Browser session design

- Passwords are hashed with Argon2id and never logged or returned.
- A signed access credential expires after 15 minutes by default.
- A cryptographically random refresh credential expires after 30 days by
  default. Only its SHA-256 digest is stored.
- Access and refresh credentials are stored in HTTP-only, SameSite=Lax cookies.
- State-changing authenticated requests require a matching CSRF cookie and
  `X-CSRF-Token` header.
- Refresh credentials rotate on use. Reuse of a revoked credential revokes its
  entire token family.
- Logout revokes the current refresh session and clears all session cookies.

Production must provide a unique `GENESIS_AUTH_SECRET_KEY` of at least 32
characters and set `GENESIS_COOKIE_SECURE=true` behind HTTPS.

## Authorization

World queries always include both the world ID and authenticated owner ID. A
world belonging to another user returns the same 404 response as a nonexistent
world, preventing identifier-based data disclosure.

## Rate limiting

Registration and login use a Redis fixed-window limit keyed by action and client
IP. The default is 10 attempts per minute. If Redis is unavailable, the limiter
fails open so authentication remains usable during local development, while the
readiness endpoint continues to report Redis as degraded. Production monitoring
should alert on that degraded state.

## Local cookies

Browser authentication goes through the frontend's same-origin `/api/genesis`
proxy. The proxy forwards requests to the configured internal API and returns
session cookies on the frontend host. This prevents `localhost` and
`127.0.0.1` host mismatches from silently discarding an otherwise valid login.

For a standard PostgreSQL 16 installation on Windows, initialize the local
development role and database with:

```powershell
.\infrastructure\scripts\setup-local-postgres.ps1
```

The helper prompts for the PostgreSQL administrator password and does not store
or print it.

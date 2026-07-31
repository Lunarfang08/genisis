# Deployment guide

## Production Compose example

1. Copy `.env.example` to a private environment file and set `POSTGRES_PASSWORD`, `GENESIS_AUTH_SECRET_KEY`, and `GENESIS_HOST`.
2. Place TLS `fullchain.pem` and `privkey.pem` in `certificates/`, readable only by the operator.
3. Run `docker compose -f docker-compose.production.yml config --quiet`.
4. Run `docker compose -f docker-compose.production.yml up --build -d`.
5. Confirm `/api/v1/health/ready`, then create and restore a test backup.

The one-shot `migrate` service applies Alembic before API/worker startup. Containers are non-root, health-checked, restartable, and use persistent PostgreSQL/Redis volumes. Nginx terminates HTTPS, caps request bodies, rate limits API traffic, preserves request IDs, and disables SSE buffering.

## Cost-conscious hosted shape

Deploy `apps/web` to Vercel or the web image to a small container host. Run API and worker as separate processes against managed PostgreSQL; Redis is recommended for multiple instances and worker leases. Free tiers may sleep, cap connections, or discard data and are demonstration-only. Groq is opt-in. Ollama is suitable for local demonstrations but usually exceeds free-host memory.

## Backup and rollback

Take a PostgreSQL logical backup before migration. Deploy migrations once, then API, worker, and web. Roll application images back first; only run Alembic downgrade after verifying the migration is reversible and backing up again. Redis can be rebuilt from authoritative PostgreSQL history.

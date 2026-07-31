FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:${PATH}"

RUN groupadd --system genesis \
    && useradd --system --gid genesis --create-home genesis

WORKDIR /workspace/apps/api

COPY --from=ghcr.io/astral-sh/uv:0.11.32 /uv /uvx /bin/
COPY apps/api/pyproject.toml apps/api/uv.lock ./
COPY packages/simulation /workspace/packages/simulation
RUN uv sync --frozen --no-dev

COPY apps/api/src ./src
COPY apps/api/alembic.ini ./
COPY apps/api/migrations ./migrations

USER genesis
EXPOSE 8000

CMD ["uvicorn", "genesis_api.main:app", "--host", "0.0.0.0", "--port", "8000"]

.PHONY: dev down logs format lint typecheck test build check api-dev web-dev

dev:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs --follow

api-dev:
	cd apps/api && uv run uvicorn genesis_api.main:app --reload

migrate:
	cd apps/api && uv run alembic upgrade head

web-dev:
	npm run dev:web

format:
	cd apps/api && uv run ruff format .
	cd apps/api && uv run ruff check --fix .
	cd packages/simulation && uv run ruff format .
	cd packages/simulation && uv run ruff check --fix .
	npm run format:web

lint:
	cd apps/api && uv run ruff format --check .
	cd apps/api && uv run ruff check .
	cd packages/simulation && uv run ruff format --check .
	cd packages/simulation && uv run ruff check .
	npm run lint:web

typecheck:
	cd apps/api && uv run mypy src tests
	cd packages/simulation && uv run mypy src tests
	npm run typecheck:web

test:
	cd apps/api && uv run pytest
	cd packages/simulation && uv run pytest
	npm run test:web

build:
	npm run build:web

check: lint typecheck test build

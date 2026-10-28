.PHONY: dev test lint format check seed ingest run

dev:
	docker compose up -d

stop:
	docker compose down

test:
	uv run pytest --cov=src/atendente --cov-report=term-missing

lint:
	uv run ruff check .
	uv run mypy --strict src
	uv run lint-imports

format:
	uv run ruff format .
	uv run ruff check --fix .

check: lint test

seed:
	uv run python -m atendente.infra.db.seed

run:
	uv run uvicorn atendente.api.main:app --reload --port 8000

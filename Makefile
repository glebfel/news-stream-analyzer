.PHONY: install lint format test up down logs migrate seed pre-commit clean

install:
	uv sync --all-packages
	uv run pre-commit install

lint:
	uv run ruff check .
	uv run mypy .

format:
	uv run ruff format .
	uv run ruff check --fix .

pre-commit:
	uv run pre-commit run --all-files

test:
	uv run pytest

up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f --tail=200

migrate:
	OPENSEARCH_URL=http://localhost:9200 NEO4J_URL=bolt://localhost:7687 \
		uv run python scripts/migrate.py

seed:
	REDIS_URL=redis://localhost:6379/0 \
		uv run python scripts/seed_mock.py --count 200

clean:
	docker compose down -v
	rm -rf .pytest_cache .mypy_cache .ruff_cache

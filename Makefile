.PHONY: install lint format test up down logs migrate seed pre-commit clean \
        eval-ner eval-sentiment eval-throughput eval-latency eval-all

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

eval-ner:
	uv run python scripts/eval_ner.py

eval-sentiment:
	uv run python scripts/eval_sentiment.py --builtin

eval-throughput:
	REDIS_URL=redis://localhost:6379/0 \
	OPENSEARCH_URL=http://localhost:9200 \
	NEO4J_URL=bolt://localhost:7687 \
		uv run python scripts/eval_throughput.py --count 500

eval-latency:
	uv run python scripts/eval_latency.py --n 200 --base-url http://localhost:8000

eval-all: eval-ner eval-sentiment eval-throughput eval-latency

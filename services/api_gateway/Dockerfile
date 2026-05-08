FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock* ./
COPY libs/ ./libs/
COPY services/api_gateway/ ./services/api_gateway/

RUN uv sync --package api-gateway --frozen 2>/dev/null || uv sync --package api-gateway

# Bundle migrations so the same image can run schema bootstrap
COPY scripts/migrate.py ./scripts/migrate.py
COPY infra/migrations ./infra/migrations

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "api_gateway.app:app", "--host", "0.0.0.0", "--port", "8000"]

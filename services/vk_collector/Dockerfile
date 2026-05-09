FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock* ./
COPY libs/ ./libs/
COPY services/vk_collector/ ./services/vk_collector/

RUN uv sync --package vk-collector --frozen 2>/dev/null || uv sync --package vk-collector

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

CMD ["python", "-m", "vk_collector.main"]

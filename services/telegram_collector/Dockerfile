FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock* ./
COPY libs/ ./libs/
COPY services/telegram_collector/ ./services/telegram_collector/

RUN uv sync --package telegram-collector --frozen 2>/dev/null || uv sync --package telegram-collector

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

CMD ["python", "-m", "telegram_collector"]

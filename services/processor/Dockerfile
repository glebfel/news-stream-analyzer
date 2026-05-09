FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock* ./
COPY libs/ ./libs/
COPY services/processor/ ./services/processor/

RUN uv sync --package processor --frozen 2>/dev/null || uv sync --package processor

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

CMD ["python", "-m", "processor.main"]

FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock* ./
COPY libs/ ./libs/
COPY services/graph_builder/ ./services/graph_builder/

RUN uv sync --package graph-builder --frozen 2>/dev/null || uv sync --package graph-builder

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

CMD ["python", "-m", "graph_builder"]

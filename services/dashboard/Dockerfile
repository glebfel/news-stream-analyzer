FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock* ./
COPY libs/ ./libs/
COPY services/dashboard/ ./services/dashboard/

RUN uv sync --package dashboard --frozen 2>/dev/null || uv sync --package dashboard

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

CMD ["streamlit", "run", "services/dashboard/src/dashboard/app.py", "--server.port=8501", "--server.address=0.0.0.0"]

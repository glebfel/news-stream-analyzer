FROM python:3.11-slim

ARG NLP_EXTRAS=""

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock* ./
COPY libs/ ./libs/
COPY services/nlp_worker/ ./services/nlp_worker/

RUN if [ -n "$NLP_EXTRAS" ]; then \
        uv sync --package nlp-worker --extra $NLP_EXTRAS; \
    else \
        uv sync --package nlp-worker; \
    fi

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV TRANSFORMERS_CACHE=/app/models/cache
ENV HF_HOME=/app/models/cache

CMD ["python", "-m", "nlp_worker"]

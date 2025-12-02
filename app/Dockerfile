FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS runtime

ENV UV_LINK_MODE=copy

WORKDIR /app

COPY pyproject.toml ./
COPY uv.lock ./
RUN uv venv .venv
RUN . .venv/bin/activate && uv sync --active --frozen

COPY ./ ./

ENV PYTHONPATH=/app

CMD ["uv" "run" "python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--reload"]

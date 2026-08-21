FROM python:3.12-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:0.8.13 /uv /uvx /bin/
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY app ./app
RUN uv sync --frozen --no-dev

FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PATH="/app/.venv/bin:$PATH"
WORKDIR /app
RUN groupadd --system --gid 1001 portfolio && useradd --system --uid 1001 --gid portfolio portfolio
COPY --from=builder --chown=portfolio:portfolio /app/.venv ./.venv
COPY --chown=portfolio:portfolio app ./app
COPY --chown=portfolio:portfolio alembic.ini ./
COPY --chown=portfolio:portfolio alembic ./alembic
USER portfolio
EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --log-level ${LOG_LEVEL:-info}"]

# syntax=docker/dockerfile:1
FROM python:3.13-slim

# uv pinned by version tag and digest
COPY --from=ghcr.io/astral-sh/uv:0.11.7@sha256:240fb85ab0f263ef12f492d8476aa3a2e4e1e333f7d67fbdd923d00a506a516a /uv /usr/local/bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

# ffmpeg: voice uploads are sniffed, measured and transcoded before STT (Plan 7).
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --system --create-home --uid 10001 app
WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY alembic.ini ./
COPY alembic ./alembic
COPY app ./app
COPY scripts ./scripts
# Server-side strings (spoken fallback answers): packages/i18n/messages, passed as the named
# build context `i18n` (docker build --build-context i18n=packages/i18n/messages apps/api).
COPY --from=i18n *.json ./i18n/
ENV I18N_MESSAGES_DIR=/app/i18n
# Files stay root-owned and read-only for the app user (no runtime writes to /app).
RUN uv sync --frozen --no-dev

USER app
ENV PORT=8080
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s \
    CMD python -c "import os,urllib.request as u; u.urlopen(f'http://127.0.0.1:{os.environ.get(\"PORT\",\"8080\")}/v1/health', timeout=2)" || exit 1

CMD ["sh", "-c", "exec uvicorn app.main:create_app --factory --host 0.0.0.0 --port ${PORT:-8080}"]

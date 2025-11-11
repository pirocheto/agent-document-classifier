FROM python:3.13-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1

# Change the working directory to the `app` directory
WORKDIR /app

# Install dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project


FROM python:3.13-slim

# Copy the environment, but not the source code
COPY --from=builder --chown=app:app /app/.venv /app/.venv

# Copy the project into the intermediate image
ADD ./app /app

ENV PATH="/app/.venv/bin:$PATH"

ENV OTEL_SERVICE_NAME=agent-classification-fastapi
ENV OTEL_TRACES_EXPORTER=console
ENV OTEL_METRICS_EXPORTER=console
ENV TRACELOOP_TRACE_CONTENT=false

CMD ["opentelemetry-instrument", "fastapi", "run", "/app/api/app.py"]
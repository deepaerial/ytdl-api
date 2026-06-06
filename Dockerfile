FROM python:3.11-slim as base

EXPOSE 80

ENV PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100

COPY --from=ghcr.io/astral-sh/uv:0.8.0-debian-slim /usr/local/bin/uv /usr/local/bin/uvx /usr/local/bin/

RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/* && \
    addgroup --system --gid 1001 app && \
    adduser --system --uid 1001 --ingroup app --home /app --shell /bin/sh --disabled-password app && \
    mkdir -p /app/media && \
    chown app:app /app/media

FROM base as project-base
WORKDIR /app
# Copy project files
COPY pyproject.toml uv.lock /app/
# Project initialization: installing project's Python dependencies
RUN uv sync --frozen --no-dev --no-install-project
COPY ./ytdl_api /app/ytdl_api
# Opening port
########### Dev ###############
FROM project-base as dev
COPY --from=project-base /app/.venv /app/.venv
# Installing dev dependencies
RUN uv sync --frozen
# Running uvicorn server
CMD ["uv", "run", "uvicorn", "ytdl_api.asgi:app", "--host", "0.0.0.0", "--port", "80", "--log-level", "debug", "--reload"]

############ Test ###################
FROM dev as test
WORKDIR /app/
COPY --from=project-base /app/.venv /app/.venv
COPY ./tests /app/tests
RUN uv sync --frozen
USER app
ENTRYPOINT ["uv", "run", "pytest"]
############ Prod ###################
FROM project-base as prod
RUN uv sync --frozen --no-dev
USER app
CMD ["uv", "run", "uvicorn", "ytdl_api.asgi:app", "--host", "0.0.0.0", "--port", "80", "--log-level", "info"]
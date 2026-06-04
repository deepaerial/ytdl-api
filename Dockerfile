FROM python:3.11-slim as base

EXPOSE 80

ENV PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VERSION=2.4.1

RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/* && \
    pip install --upgrade pip && \
    pip install --no-cache-dir "poetry==$POETRY_VERSION" && \
    poetry config virtualenvs.in-project true && \
    addgroup --system --gid 1001 app && \
    adduser --system --uid 1001 --ingroup app --home /app --shell /bin/sh --disabled-password app && \
    mkdir -p /app/media && \
    chown app:app /app/media

FROM base as project-base
WORKDIR /app
# Copy project files
COPY pyproject.toml poetry.lock /app/
# Project initialization: installing project's Python dependencies
RUN poetry install --no-root --without dev
COPY ./ytdl_api /app/ytdl_api
# Opening port
########### Dev ###############
FROM project-base as dev
COPY --from=project-base /app/.venv /app/.venv
# Installing dev dependencies
RUN poetry install
# Running uvicorn server
CMD ["poetry", "run", "uvicorn", "ytdl_api.asgi:app", "--host", "0.0.0.0", "--port", "80", "--log-level", "debug", "--reload"]

############ Test ###################
FROM dev as test
WORKDIR /app/
COPY --from=project-base /app/.venv /app/.venv
COPY ./tests /app/tests
RUN poetry install
USER app
ENTRYPOINT [ "poetry", "run", "pytest"]
############ Prod ###################
FROM project-base as prod
RUN poetry install --without dev
USER app
CMD ["poetry", "run", "uvicorn", "ytdl_api.asgi:app", "--host", "0.0.0.0", "--port", "80", "--log-level", "info"]
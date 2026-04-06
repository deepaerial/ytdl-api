# AGENT.md

## Project Overview

REST-based API for downloading video or extracting audio from YouTube videos.

## Dependency Management

All dependency management is done via [Poetry](https://python-poetry.org/). Use `poetry add` to add dependencies and `poetry lock --no-update` to update the lock file.

## Commands

| Command | Description |
|---------|-------------|
| `./scripts/run_devserver.sh` | Run development server on http://127.0.0.1:8080 |

For testing and linting, use the available skills:
- **project-testing**: Run tests with optional coverage
- **linting**: Run ruff linter with auto-fix

## Key Files

| Path | Description |
|------|-------------|
| `ytdl_api/asgi.py` | Application entry point |
| `ytdl_api/config.py` | Settings and configuration |
| `ytdl_api/endpoints.py` | API endpoint handlers |
| `ytdl_api/downloaders.py` | Video/audio download logic |
| `ytdl_api/schemas/` | Pydantic request/response models |

## Testing Notes

- Requires `.env.test` file in project root (can be empty)
- Tests use in-memory database (no external DB required)
- Run `poetry install` before running tests for the first time

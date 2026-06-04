---
name: version-bump
description: Handles Python release workflow using Poetry - bumps version and updates CHANGELOG.md
---

# Version Bump Skill

Bump version using `poetry version` and add entries to CHANGELOG.md.

## Workflow

### Step 1: Version Bump

Ask the user for bump type (major, minor, or patch), then run:

```bash
poetry version {bump_type}
```

Update `pyproject.toml` version field based on the output.

### Step 2: Changelog Update

Read current `CHANGELOG.md` and ask the user for:
- Change type: Added / Changed / Fixed / Removed / Deprecated
- Change description (can add multiple)

Parse existing version format: `[X.Y.Z] - YYYY-MM-DD`

Prepend new entry at the top (below header) in this format:

```markdown
## [X.Y.Z] - YYYY-MM-DD
### {Type}
- {Description}
```

Example:

```markdown## [1.11.1] - 2026-06-04
### Changed
- Docker containerization: switched to python:3.11-slim base (~50% size reduction),
  added non-root `app` user, added healthcheck endpoint and HTTP health probes.
- Upgraded Poetry from 1.7.1 to 2.4.1 and updated build-system config for Poetry 2.x compatibility.
- Expanded .dockerignore to reduce build context.
### Added
- `GET /api/health` endpoint for container orchestration liveness probes.
- Healthcheck configuration in compose.yaml and fly.toml.
### Removed
- Deta support
```

Write changes directly to CHANGELOG.md without preview.

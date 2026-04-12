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

Write changes directly to CHANGELOG.md without preview.

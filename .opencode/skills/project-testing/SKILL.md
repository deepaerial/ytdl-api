---
name: project-testing
description: Run project tests using pytest with optional coverage reporting
---

# Project Testing Skill

Run tests with optional coverage generation.

## Workflow

### Step 1: Options

Ask the user:
- "Do you want to include coverage report?" (Yes/No)

### Step 2: Run Tests

If coverage requested:
```bash
poetry run pytest . --cov=ytdl_api --cov-report=term-missing
```

If no coverage:
```bash
poetry run pytest .
```

Always run in the repository root directory.

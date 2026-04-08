---
name: run-tests-with-uv-pytest
description: Runs unit and integration tests using uv + pytest after changes. Use when implementations are complete, before committing/PRs, or when the user asks to run tests with uv/pytest.
---

# Run unit + integration tests with `uv` + `pytest`

## When to use

Use this workflow whenever new changes/implementations are done, and before considering work complete.

## Standard commands (uv-managed)

- Prefer running tests via `uv`:
  - `uv run pytest`

## Ensuring unit + integration coverage (markers-first)

1. If the project defines pytest markers for unit/integration, run both explicitly:
   - `uv run pytest -m unit`
   - `uv run pytest -m integration`
2. If markers are not configured or those commands select nothing / error, fall back to running the full suite:
   - `uv run pytest`

## Workflow

1. Run unit tests (marker) if available.
2. Run integration tests (marker) if available.
3. If failures occur, fix the underlying issue and re-run the relevant command(s) until passing.


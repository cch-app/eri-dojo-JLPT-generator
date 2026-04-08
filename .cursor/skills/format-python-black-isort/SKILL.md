---
name: format-python-black-isort
description: Formats Python code with isort and Black for consistency. Use after implementing changes, before committing, or when the user asks to format/standardize the codebase with black/isort.
---

# Format Python with isort + Black

## When to use

Use this workflow whenever new changes/implementations are done, or when asked to format the project.

## Standard commands (uv-managed)

- Prefer running formatters via `uv`:
  - `uv run isort <paths>`
  - `uv run black <paths>`

## Path selection

- If `src/` and/or `tests/` exist, format only those directories.
- Otherwise, format the whole repo (`.`).

## Workflow

1. Choose paths:
   - Default: `src tests` (only include the ones that exist)
   - Fallback: `.`
2. Run isort first, then Black:
   - `uv run isort <paths>`
   - `uv run black <paths>`
3. If formatting changes files, re-run until stable (no additional diffs).

## Notes

- Do not assume formatter flags; rely on repo configuration (typically `pyproject.toml`) when present.
- If formatter configuration is missing and formatting is requested, add config only when asked (otherwise just run the tools).


---
name: verify-containerization-docker-compose
description: Validates the project remains containerizable by running docker compose build and bringing services up after changes. Use when implementations are complete, when Docker/Compose files change, or when deployment/containerization is a concern.
---

# Verify containerization with `docker compose`

## When to use

Use this workflow whenever new changes/implementations are done (especially changes that touch runtime behavior, dependencies, environment variables, or deployment concerns).

## Compose file selection

- Use the default Compose file resolution (e.g. `compose.yaml`, `compose.yml`, `docker-compose.yaml`, `docker-compose.yml`) unless the repo specifies otherwise.

## Required workflow (definition of success: build + up)

1. Build images:
   - `docker compose build`
2. Start services:
   - `docker compose up -d`
3. Verify the stack didn’t immediately fail:
   - `docker compose ps`
   - `docker compose logs --no-color --tail=200`

## If there are failures

- Identify the failing service(s) from `ps`/`logs`, fix the underlying issue, then rerun the workflow.
- Common fixes include missing env vars, wrong ports, missing build context/files, or runtime-only dependencies.

## Cleanup (optional)

- If the workflow was run for validation only, shut down afterward:
  - `docker compose down`


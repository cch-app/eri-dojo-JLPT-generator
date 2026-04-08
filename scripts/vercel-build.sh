#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${API_URL:-}" ]]; then
  echo "ERROR: API_URL is required for Reflex static export on Vercel." >&2
  echo "Set it in your Vercel Project Settings → Environment Variables." >&2
  exit 1
fi

if command -v uv >/dev/null 2>&1; then
  echo "Using existing uv."
else
  echo "Installing uv (build-time only)."
  python -m pip install --upgrade pip >/dev/null
  python -m pip install --upgrade uv >/dev/null
fi

echo "Syncing Python dependencies (locked)."
uv sync --no-dev --frozen

echo "Exporting Reflex frontend (API_URL=${API_URL})."
uv run reflex export --frontend-only --no-zip

if [[ ! -d ".web/build/client" ]]; then
  echo "ERROR: Expected output directory '.web/build/client' was not created." >&2
  exit 1
fi

echo "OK: Static site ready at .web/build/client"

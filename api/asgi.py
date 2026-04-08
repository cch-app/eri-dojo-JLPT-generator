from __future__ import annotations

"""
Vercel Python runtime entrypoint.

Vercel detects Python projects (pyproject/requirements) and requires an ASGI/WSGI
callable named `app` in a known entrypoint path. Reflex keeps its API server as
an internal Starlette app on `rx.App._api`.
"""

from JLPT_generator.JLPT_generator import app as reflex_app

# Starlette is an ASGI callable.
app = reflex_app._api  # noqa: SLF001


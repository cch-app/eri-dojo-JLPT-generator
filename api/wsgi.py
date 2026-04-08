from __future__ import annotations

"""
Vercel Python runtime entrypoint (WSGI).

Expose a module-level `app` callable for the deployment platform.
"""

from JLPT_generator.webapp.app import create_app

app = create_app()


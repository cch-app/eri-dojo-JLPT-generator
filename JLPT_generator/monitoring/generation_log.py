from __future__ import annotations

import logging
from typing import Any

generation_logger = logging.getLogger("jlpt.generation")


def log_generation(event: str, **fields: Any) -> None:
    """Lightweight structured-ish logs for question generation observability."""
    if fields:
        generation_logger.info("event=%s %s", event, fields)
    else:
        generation_logger.info("event=%s", event)

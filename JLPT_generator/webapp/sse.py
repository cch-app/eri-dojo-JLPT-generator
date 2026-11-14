from __future__ import annotations

import json
from collections.abc import Iterator
from typing import Any

from flask import Response, stream_with_context


def sse_event(obj: dict[str, Any]) -> str:
    return f"data: {json.dumps(obj, ensure_ascii=False)}\n\n"


def sse_response(events: Iterator[dict[str, Any]]) -> Response:
    """Stream JSON events as ``text/event-stream`` without proxy buffering."""

    def gen() -> Iterator[str]:
        for event in events:
            yield sse_event(event)

    return Response(
        stream_with_context(gen()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )

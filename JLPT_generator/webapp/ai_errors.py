"""Turn AI provider failures into messages a learner can act on.

Known failures (no credits, bad key, ...) get a translated explanation and the
raw vendor text is only logged; unknown failures keep the vendor detail so
nothing is hidden while debugging.
"""

from __future__ import annotations

from typing import Any

from JLPT_generator.adapters.ai import AiFailure, AiProviderError
from JLPT_generator.i18n import translate
from JLPT_generator.monitoring.generation_log import log_generation


def ai_error_event(
    ui_locale: str,
    *,
    kind: AiFailure,
    retryable: bool,
    detail: str,
    fallback_key: str,
    request_id: str | None = None,
) -> dict[str, Any]:
    log_generation(
        "ai_provider_failed",
        request_id=request_id or "-",
        kind=kind.value,
        detail=detail,
    )
    if kind == AiFailure.unknown:
        message = translate(ui_locale, fallback_key, detail=detail)
    else:
        message = translate(ui_locale, f"err_ai_{kind.value}")
    return {
        "type": "error",
        "message": message,
        "code": kind.value,
        "retryable": retryable,
    }


def ai_error_event_from(
    ui_locale: str,
    error: Exception,
    *,
    fallback_key: str,
    request_id: str | None = None,
) -> dict[str, Any]:
    if isinstance(error, AiProviderError):
        kind, retryable = error.kind, error.retryable
    else:
        kind, retryable = AiFailure.unknown, True
    return ai_error_event(
        ui_locale,
        kind=kind,
        retryable=retryable,
        detail=str(error),
        fallback_key=fallback_key,
        request_id=request_id,
    )

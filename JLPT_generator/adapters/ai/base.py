from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol


class AiFailure(StrEnum):
    """Why the AI provider refused a request, independent of the vendor."""

    quota = "quota"  # out of credits / plan limit (e.g. HTTP 402)
    auth = "auth"  # missing, invalid or unauthorized API key (401/403)
    rate_limited = "rate_limited"  # too many requests (429)
    model_missing = "model_missing"  # configured model does not exist (404)
    unavailable = "unavailable"  # cannot connect, timeout or 5xx
    config = "config"  # the app itself is misconfigured (env vars)
    unknown = "unknown"


# Failures that can succeed on a later attempt without anyone changing anything.
_RETRYABLE = frozenset(
    {AiFailure.rate_limited, AiFailure.unavailable, AiFailure.unknown}
)


class AiProviderError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        kind: AiFailure = AiFailure.unknown,
        status_code: int | None = None,
    ) -> None:
        super().__init__(message)
        self.kind = kind
        self.status_code = status_code

    @property
    def retryable(self) -> bool:
        return self.kind in _RETRYABLE


@dataclass(frozen=True)
class AiText:
    text: str


class AiProvider(Protocol):
    def generate_question_json(self, *, prompt: str) -> dict: ...

    def analyze_session_text(self, *, prompt: str) -> AiText: ...

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class AiProviderError(RuntimeError):
    pass


@dataclass(frozen=True)
class AiText:
    text: str


class AiProvider(Protocol):
    def generate_question_json(self, *, prompt: str) -> dict: ...

    def analyze_session_text(self, *, prompt: str) -> AiText: ...

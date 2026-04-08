from __future__ import annotations

from typing import Any

from JLPT_generator.adapters.ai.base import AiProviderError
from JLPT_generator.adapters.ai.ollama import _parse_json_strict
from JLPT_generator.domain import Question


def parse_questions_batch_json(
    *, text: str, expected_count: int
) -> list[dict[str, Any]]:
    """
    Parse strict JSON object {"questions": [...]} and validate each item as Question.
    Returns list of JSON-serializable dicts for Reflex state.
    """
    raw = _parse_json_strict(text)
    items = raw.get("questions")
    if not isinstance(items, list):
        raise AiProviderError("Expected top-level JSON key 'questions' to be an array.")
    if len(items) != expected_count:
        raise AiProviderError(
            f"Expected exactly {expected_count} questions, got {len(items)}."
        )
    out: list[dict[str, Any]] = []
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            raise AiProviderError(f"questions[{i}] must be a JSON object.")
        q = Question.model_validate(item)
        out.append(q.model_dump(mode="json"))
    return out

"""Signed-token payloads exchanged with the dojo front end.

Two kinds of payload travel through ``TokenCodec``:

* a *launch* payload, which authorizes one question-generation stream, and
* an *analysis* payload, which carries a finished run (questions + attempts)
  to the AI feedback stream and the PDF download.

Everything here is pure (no Flask) so it can be unit tested in isolation.
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from JLPT_generator.domain import (
    Attempt,
    JLPTLevel,
    Question,
    QuestionSection,
    SessionRun,
)
from JLPT_generator.i18n import SUPPORTED_LOCALES
from JLPT_generator.use_cases.generate_question import _question_from_payload
from JLPT_generator.webapp.token_codec import TokenDecodeError

MAX_NUM_QUESTIONS = 10

READING_CATEGORIES = (
    "grammar",
    "vocabulary",
    "reading_comprehension",
)

LISTENING_CATEGORIES = (
    "task_based",
    "point_comprehension",
    "listening_comprehension",
)

_LAUNCH_KEYS = ("ui_locale", "section", "level", "category", "num_questions")


class PayloadError(ValueError):
    """Raised when a client request cannot be turned into a valid payload."""


def normalize_ui_locale(raw: str | None) -> str:
    ui_locale = (raw or "en").strip()
    return ui_locale if ui_locale in SUPPORTED_LOCALES else "en"


def categories_for_section(section: QuestionSection) -> tuple[str, ...]:
    if section == QuestionSection.listening:
        return LISTENING_CATEGORIES
    return READING_CATEGORIES


def _parse_section(raw: Any) -> QuestionSection:
    try:
        return QuestionSection(str(raw or QuestionSection.reading.value).strip())
    except ValueError as e:
        raise PayloadError(f"Unknown section: {raw!r}") from e


def _parse_level(raw: Any) -> JLPTLevel:
    try:
        return JLPTLevel(str(raw or "").strip().upper())
    except ValueError as e:
        raise PayloadError(f"Unknown level: {raw!r}") from e


def _parse_count(raw: Any) -> int:
    try:
        count = int(raw)
    except (TypeError, ValueError) as e:
        raise PayloadError("num_questions must be an integer.") from e
    return max(1, min(MAX_NUM_QUESTIONS, count))


def build_launch_payload(data: Mapping[str, Any]) -> dict[str, Any]:
    section = _parse_section(data.get("section"))
    level = _parse_level(data.get("level"))
    category = str(data.get("category") or "").strip()
    if category not in categories_for_section(section):
        raise PayloadError(f"Unknown category for {section.value}: {category!r}")
    return {
        "v": 1,
        "kind": "launch",
        "ui_locale": normalize_ui_locale(data.get("ui_locale")),
        "section": section.value,
        "level": level.value,
        "category": category,
        "num_questions": _parse_count(data.get("num_questions", 5)),
    }


def decode_launch_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    if payload.get("kind") != "launch":
        raise TokenDecodeError("Invalid launch token.")
    for key in _LAUNCH_KEYS:
        if key not in payload:
            raise TokenDecodeError("Launch token is incomplete.")
    return dict(payload)


def normalize_streamed_question(
    raw: Mapping[str, Any], *, launch: Mapping[str, Any]
) -> dict[str, Any]:
    """Validate a parsed question against the launch it was generated for."""
    question = _question_from_payload(
        dict(raw),
        fallback_section=QuestionSection(str(launch["section"])),
        fallback_level=JLPTLevel(str(launch["level"])),
        category=str(launch["category"]),
    )
    return question.model_dump(mode="json")


def _attempts_for(
    questions: Sequence[Question], answers: Sequence[Any]
) -> list[dict[str, Any]]:
    if len(answers) != len(questions):
        raise PayloadError("answers must have one entry per question.")
    attempts: list[dict[str, Any]] = []
    for question, answer in zip(questions, answers):
        selected = None if answer is None else int(answer)
        attempt = Attempt(
            question_id=question.id,
            selected_index=selected,
            is_correct=selected == question.answer_index,
        )
        attempts.append(attempt.model_dump(mode="json"))
    return attempts


def build_analysis_payload(data: Mapping[str, Any]) -> dict[str, Any]:
    """Turn a finished run posted by the client into an analysis payload.

    Correctness is recomputed here from ``answer_index`` rather than trusted
    from the client.
    """
    raw_questions = data.get("questions")
    if not isinstance(raw_questions, list) or not raw_questions:
        raise PayloadError("questions must be a non-empty list.")
    if len(raw_questions) > MAX_NUM_QUESTIONS:
        raise PayloadError(f"At most {MAX_NUM_QUESTIONS} questions per session.")
    raw_answers = data.get("answers")
    if not isinstance(raw_answers, list):
        raise PayloadError("answers must be a list.")

    section = _parse_section(data.get("section"))
    level = _parse_level(data.get("level"))
    questions = [Question.model_validate(q) for q in raw_questions]
    categories = sorted({q.category for q in questions})
    return {
        "v": 1,
        "kind": "analysis",
        "ui_locale": normalize_ui_locale(data.get("ui_locale")),
        "section": section.value,
        "level": level.value,
        "category": ",".join(categories),
        "num_questions": len(questions),
        "questions": [q.model_dump(mode="json") for q in questions],
        "attempts": _attempts_for(questions, raw_answers),
        "final_analysis": "",
    }


def session_run_from_payload(payload: Mapping[str, Any]) -> SessionRun:
    return SessionRun(
        section=QuestionSection(str(payload.get("section") or "")),
        level=JLPTLevel(str(payload.get("level") or "")),
        category=str(payload.get("category") or ""),
        num_questions=int(payload.get("num_questions") or 5),
        questions=[Question.model_validate(q) for q in payload.get("questions") or []],
        attempts=[
            Attempt.model_validate(a)
            for a in payload.get("attempts") or []
            if isinstance(a, dict) and a.get("question_id")
        ],
    )


def score_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    attempts = payload.get("attempts") or []
    if not isinstance(attempts, list):
        attempts = []
    total = len(attempts)
    correct = sum(1 for a in attempts if isinstance(a, dict) and a.get("is_correct"))
    return {
        "total_answered": total,
        "correct": correct,
        "accuracy": (correct / total) if total else 0.0,
    }

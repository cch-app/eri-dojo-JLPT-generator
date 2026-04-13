import json

import pytest

from JLPT_generator.domain import JLPTLevel, QuestionSection
from JLPT_generator.parsers.markers import QUESTION_END, QUESTION_START
from JLPT_generator.use_cases.stream_questions_generation import (
    iter_question_stream_events,
)


def _block(prompt: str, answer_index: int = 0) -> str:
    obj = {
        "section": "reading",
        "level": "N5",
        "category": "grammar",
        "prompt": prompt,
        "choices": ["い", "ろ", "は", "に"],
        "answer_index": answer_index,
        "explanation": "e",
        "metadata": {},
    }
    return f"{QUESTION_START}{json.dumps(obj, ensure_ascii=False)}{QUESTION_END}"


class _FakeProvider:
    def __init__(self, stream_body: str, topoff: str = "") -> None:
        self._stream_body = stream_body
        self._topoff = topoff

    def stream_text(self, *, prompt: str):
        # One char at a time to exercise incremental parsing
        for ch in self._stream_body:
            yield ch

    def complete_text(self, *, prompt: str) -> str:
        return self._topoff


@pytest.mark.unit
def test_iter_question_stream_emits_questions_and_done():
    body = _block("a", 0) + _block("b", 1)
    prov = _FakeProvider(body)
    events = list(
        iter_question_stream_events(
            provider=prov,
            section=QuestionSection.reading,
            level=JLPTLevel.n5,
            category="grammar",
            num_questions=2,
            explanation_locale="English",
            request_id="t1",
        )
    )
    types = [e.get("type") for e in events]
    assert types.count("question") == 2
    assert events[-1]["type"] == "done"
    assert events[-1]["received"] == 2
    assert events[-1]["partial"] is False


@pytest.mark.unit
def test_iter_question_stream_topoff_when_short():
    body = _block("only", 0)
    topoff = _block("second", 1)
    prov = _FakeProvider(body, topoff=topoff)
    events = list(
        iter_question_stream_events(
            provider=prov,
            section=QuestionSection.reading,
            level=JLPTLevel.n5,
            category="grammar",
            num_questions=2,
            explanation_locale="English",
            request_id="t2",
        )
    )
    assert sum(1 for e in events if e.get("type") == "question") == 2
    assert events[-1]["received"] == 2

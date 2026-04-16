import json

import pytest

from JLPT_generator.domain import JLPTLevel, QuestionSection
from JLPT_generator.parsers.markers import QUESTION_END, QUESTION_START
from JLPT_generator.use_cases.reading_question_generation import iter_reading_questions


class _FakeProvider:
    def __init__(self, topoff: str = "") -> None:
        self._topoff = topoff

    def complete_text(self, *, prompt: str) -> str:
        _ = prompt
        return self._topoff


def _block(prompt: str) -> str:
    obj = {
        "section": "reading",
        "level": "N5",
        "category": "grammar",
        "prompt": prompt,
        "choices": ["a", "b", "c", "d"],
        "answer_index": 0,
        "explanation": "e",
        "metadata": {},
    }
    return f"{QUESTION_START}{json.dumps(obj)}{QUESTION_END}"


@pytest.mark.unit
def test_iter_reading_questions_uses_topoff():
    provider = _FakeProvider(topoff=_block("q2"))
    questions, parser = iter_reading_questions(
        provider=provider,
        stream_text=iter(_block("q1")),
        section=QuestionSection.reading,
        level=JLPTLevel.n5,
        category="grammar",
        num_questions=2,
        explanation_locale="English",
    )
    assert len(questions) == 2
    assert parser.malformed_blocks == 0

import json

import pytest

from JLPT_generator.domain import JLPTLevel, QuestionSection
from JLPT_generator.parsers.delimited_questions import DelimitedQuestionStreamParser
from JLPT_generator.parsers.markers import QUESTION_END, QUESTION_START


def _q_json(prompt: str, answer_index: int = 0) -> str:
    obj = {
        "section": "reading",
        "level": "N5",
        "category": "grammar",
        "prompt": prompt,
        "choices": ["い", "ろ", "は", "に"],
        "answer_index": answer_index,
        "explanation": "Because grammar.",
        "metadata": {},
    }
    return json.dumps(obj, ensure_ascii=False)


@pytest.mark.unit
def test_parser_extracts_single_question_across_chunks():
    inner = _q_json(" stem 一 ")
    block = f"{QUESTION_START}{inner}{QUESTION_END}"
    p = DelimitedQuestionStreamParser(
        section=QuestionSection.reading,
        level=JLPTLevel.n5,
        category="grammar",
    )
    mid = len(block) // 2
    assert p.feed(block[:mid]) == []
    out = p.feed(block[mid:])
    assert len(out) == 1
    assert out[0]["prompt"] == " stem 一 "


@pytest.mark.unit
def test_parser_skips_malformed_then_recoveres():
    inner_ok = _q_json("ok")
    bad_inner = "not-json"
    blob = f"{QUESTION_START}{bad_inner}{QUESTION_END}{QUESTION_START}{inner_ok}{QUESTION_END}"
    p = DelimitedQuestionStreamParser(
        section=QuestionSection.reading,
        level=JLPTLevel.n5,
        category="grammar",
    )
    out = p.feed(blob)
    assert len(out) == 1
    assert p.malformed_blocks >= 1


@pytest.mark.unit
def test_parser_skips_duplicate_prompts():
    inner = _q_json("same")
    blob = f"{QUESTION_START}{inner}{QUESTION_END}{QUESTION_START}{inner}{QUESTION_END}"
    p = DelimitedQuestionStreamParser(
        section=QuestionSection.reading,
        level=JLPTLevel.n5,
        category="grammar",
    )
    out = p.feed(blob)
    assert len(out) == 1
    assert p.duplicate_skipped == 1

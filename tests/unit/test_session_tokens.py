import pytest

from JLPT_generator.webapp.session_tokens import (
    MAX_NUM_QUESTIONS,
    PayloadError,
    build_analysis_payload,
    build_launch_payload,
    decode_launch_payload,
    normalize_streamed_question,
    score_summary,
    session_run_from_payload,
)
from JLPT_generator.webapp.token_codec import TokenDecodeError


def _question(answer_index: int = 0, category: str = "grammar") -> dict:
    return {
        "section": "reading",
        "level": "N5",
        "category": category,
        "prompt": "p",
        "choices": ["a", "b", "c", "d"],
        "answer_index": answer_index,
        "explanation": "e",
    }


@pytest.mark.unit
def test_launch_payload_normalizes_and_clamps():
    p = build_launch_payload(
        {
            "level": "n4",
            "section": "reading",
            "category": "vocabulary",
            "num_questions": 99,
            "ui_locale": "fr",
        }
    )
    assert p["kind"] == "launch"
    assert p["level"] == "N4"
    assert p["num_questions"] == MAX_NUM_QUESTIONS
    assert p["ui_locale"] == "en"
    assert decode_launch_payload(p) == p


@pytest.mark.unit
@pytest.mark.parametrize(
    "data",
    [
        {"level": "N9", "section": "reading", "category": "grammar"},
        {"level": "N5", "section": "reading", "category": "task_based"},
        {"level": "N5", "section": "writing", "category": "grammar"},
        {
            "level": "N5",
            "section": "reading",
            "category": "grammar",
            "num_questions": "x",
        },
    ],
)
def test_launch_payload_rejects_bad_input(data):
    with pytest.raises(PayloadError):
        build_launch_payload(data)


@pytest.mark.unit
def test_decode_launch_rejects_other_kinds():
    with pytest.raises(TokenDecodeError):
        decode_launch_payload({"kind": "analysis"})


@pytest.mark.unit
def test_streamed_question_gets_launch_defaults_and_id():
    launch = {"section": "reading", "level": "N3", "category": "grammar"}
    q = normalize_streamed_question(
        {"prompt": "p", "choices": ["a", "b"], "answer_index": 1, "explanation": "e"},
        launch=launch,
    )
    assert q["level"] == "N3"
    assert q["category"] == "grammar"
    assert q["id"]


@pytest.mark.unit
def test_analysis_payload_recomputes_correctness():
    qs = [_question(0, "vocabulary"), _question(2, "grammar"), _question(1, "grammar")]
    p = build_analysis_payload(
        {"level": "N5", "section": "reading", "questions": qs, "answers": [0, 1, None]}
    )
    assert [a["is_correct"] for a in p["attempts"]] == [True, False, False]
    assert p["category"] == "grammar,vocabulary"
    assert score_summary(p) == {"total_answered": 3, "correct": 1, "accuracy": 1 / 3}
    run = session_run_from_payload(p)
    assert len(run.questions) == 3 and len(run.attempts) == 3


@pytest.mark.unit
def test_analysis_payload_requires_one_answer_per_question():
    with pytest.raises(PayloadError):
        build_analysis_payload(
            {
                "level": "N5",
                "section": "reading",
                "questions": [_question()],
                "answers": [],
            }
        )

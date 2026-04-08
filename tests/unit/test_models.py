import pytest

from JLPT_generator.domain import JLPTLevel, Question, QuestionSection


@pytest.mark.unit
def test_question_correct_label():
    q = Question(
        section=QuestionSection.reading,
        level=JLPTLevel.n5,
        category="grammar",
        prompt="テスト",
        choices=["a", "b", "c", "d"],
        answer_index=2,
        explanation="because",
    )
    assert q.correct_label() == "C"

import pytest

from JLPT_generator.domain import JLPTLevel, QuestionSection, SessionRun
from JLPT_generator.use_cases.prompts import (
    final_analysis_prompt,
    question_generation_prompt,
)


@pytest.mark.unit
def test_question_generation_prompt_contains_schema():
    p = question_generation_prompt(
        section=QuestionSection.reading, level=JLPTLevel.n3, category="grammar"
    )
    assert "Return ONLY valid JSON" in p
    assert '"choices"' in p
    assert "answer_index" in p


@pytest.mark.unit
def test_final_analysis_prompt_contains_session_payload():
    s = SessionRun(
        section=QuestionSection.reading,
        level=JLPTLevel.n2,
        category="reading_comprehension",
        num_questions=3,
    )
    p = final_analysis_prompt(session=s, output_language_name="English")
    assert "User session data" in p
    assert '"level"' in p
    assert "Markdown" in p
    assert "English" in p

import pytest

from JLPT_generator.adapters.ai.base import AiProviderError
from JLPT_generator.domain import JLPTLevel, QuestionSection
from JLPT_generator.use_cases.batch_questions import parse_questions_batch_json


@pytest.mark.unit
def test_parse_questions_batch_json_success():
    text = """
    {"questions": [
        {"section": "reading", "level": "N5", "category": "grammar",
         "prompt": "p", "choices": ["a","b","c","d"], "answer_index": 0,
         "explanation": "e", "metadata": {}},
        {"section": "reading", "level": "N5", "category": "grammar",
         "prompt": "p2", "choices": ["a","b","c","d"], "answer_index": 1,
         "explanation": "e2", "metadata": {}}
    ]}
    """
    out = parse_questions_batch_json(text=text, expected_count=2)
    assert len(out) == 2
    assert out[0]["answer_index"] == 0
    assert out[1]["answer_index"] == 1


@pytest.mark.unit
def test_parse_questions_batch_json_wrong_count():
    text = '{"questions": [{"section":"reading","level":"N5","category":"g","prompt":"p","choices":["a","b","c","d"],"answer_index":0,"explanation":"e","metadata":{}}]}'
    with pytest.raises(AiProviderError, match="exactly 2"):
        parse_questions_batch_json(text=text, expected_count=2)

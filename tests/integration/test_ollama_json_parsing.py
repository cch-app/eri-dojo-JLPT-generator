import pytest

from JLPT_generator.adapters.ai.ollama import _parse_json_strict


@pytest.mark.integration
def test_parse_json_strict_strips_code_fence():
    obj = _parse_json_strict(
        '```json\n{"prompt": "x", "choices": ["a","b","c","d"], "answer_index": 0, "explanation": "e"}\n```'
    )
    assert obj["answer_index"] == 0

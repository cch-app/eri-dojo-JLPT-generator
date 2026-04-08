import pytest

from JLPT_generator.adapters.ai.ollama_sdk_provider import OllamaSdkProvider


@pytest.mark.unit
def test_parse_question_json_from_stream_buffers_and_parses():
    provider = OllamaSdkProvider.__new__(OllamaSdkProvider)  # type: ignore[misc]
    obj = provider.parse_question_json_from_stream(
        deltas=[
            "{",
            '"prompt":"x",',
            '"choices":["a","b","c","d"],',
            '"answer_index":2,',
            '"explanation":"e"',
            "}",
        ]
    )
    assert obj["answer_index"] == 2

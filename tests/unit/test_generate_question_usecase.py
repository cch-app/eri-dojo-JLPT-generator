import pytest

from JLPT_generator.adapters.ai import AiProviderError
from JLPT_generator.domain import JLPTLevel, QuestionSection
from JLPT_generator.use_cases.generate_question import GenerateQuestionUseCase


class FakeProvider:
    def __init__(self, payloads):
        self._payloads = list(payloads)

    def generate_question_json(self, *, prompt: str) -> dict:
        if not self._payloads:
            raise AiProviderError("no more payloads")
        v = self._payloads.pop(0)
        if isinstance(v, Exception):
            raise v
        return v

    def analyze_session_text(self, *, prompt: str):
        raise NotImplementedError


@pytest.mark.unit
def test_generate_question_success():
    provider = FakeProvider(
        [
            {
                "section": "reading",
                "level": "N5",
                "category": "grammar",
                "prompt": "（ ）に入るものはどれですか。",
                "choices": ["a", "b", "c", "d"],
                "answer_index": 0,
                "explanation": "explain",
                "metadata": {},
            }
        ]
    )
    q = GenerateQuestionUseCase(provider=provider).run(
        section=QuestionSection.reading, level=JLPTLevel.n5, category="grammar"
    )
    assert q.answer_index == 0


@pytest.mark.unit
def test_generate_question_repair_retry():
    provider = FakeProvider(
        [
            AiProviderError("bad json"),
            {
                "section": "reading",
                "level": "N5",
                "category": "grammar",
                "prompt": "Q",
                "choices": ["a", "b", "c", "d"],
                "answer_index": 1,
                "explanation": "ok",
                "metadata": {},
            },
        ]
    )
    q = GenerateQuestionUseCase(provider=provider).run(
        section=QuestionSection.reading, level=JLPTLevel.n5, category="grammar"
    )
    assert q.answer_index == 1

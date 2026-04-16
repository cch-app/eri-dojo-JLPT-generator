import json

import pytest

from JLPT_generator.domain import JLPTLevel, QuestionSection
from JLPT_generator.parsers.markers import QUESTION_END, QUESTION_START
from JLPT_generator.use_cases.listening_question_generation import (
    attach_listening_audio,
    resolve_listening_playback_transcript,
    iter_listening_questions,
    resolve_listening_transcript,
    validate_listening_question,
)


class _FakeProvider:
    def complete_text(self, *, prompt: str) -> str:
        _ = prompt
        return ""

    def generate_listening_audio_base64(self, *, transcript: str) -> tuple[str, str]:
        _ = transcript
        return "QUJD", "audio/wav"


def _block(prompt: str) -> str:
    obj = {
        "section": "listening",
        "level": "N5",
        "category": "task_based",
        "prompt": prompt,
        "choices": ["a", "b", "c", "d"],
        "answer_index": 0,
        "explanation": "e",
        "metadata": {},
    }
    return f"{QUESTION_START}{json.dumps(obj)}{QUESTION_END}"


@pytest.mark.unit
def test_iter_listening_questions_attaches_audio():
    provider = _FakeProvider()
    questions, _ = iter_listening_questions(
        provider=provider,
        stream_text=iter(_block("男：すみません、駅はどこですか。\n問題：男の人は何を聞いていますか。")),
        section=QuestionSection.listening,
        level=JLPTLevel.n5,
        category="task_based",
        num_questions=1,
        explanation_locale="English",
    )
    metadata = questions[0]["metadata"]
    assert metadata["listening_story_audio_base64"] == "QUJD"
    assert metadata["listening_question_audio_base64"] == "QUJD"
    assert "listening_transcript_spoken" in metadata
    assert "男：" not in metadata["listening_transcript_spoken"]


@pytest.mark.unit
def test_attach_listening_audio_falls_back_to_tts_on_audio_error():
    class _BadAudioProvider(_FakeProvider):
        def generate_listening_audio_base64(
            self, *, transcript: str
        ) -> tuple[str, str]:
            _ = transcript
            raise RuntimeError("invalid audio payload")

    out = attach_listening_audio(
        provider=_BadAudioProvider(),
        question={
            "prompt": "こんにちは",
            "metadata": {},
        },
    )
    metadata = out["metadata"]
    assert metadata["listening_story_audio_fallback_tts"] is True
    assert metadata["listening_question_audio_fallback_tts"] is True
    assert metadata["listening_story_audio_base64"] == ""
    assert metadata["listening_question_audio_base64"] == ""
    assert "invalid audio payload" in metadata["listening_story_audio_error"]


@pytest.mark.unit
def test_resolve_listening_transcript_prefers_explicit_transcript():
    question = {
        "prompt": "story only",
        "metadata": {
            "listening_transcript": "story and question",
            "question_transcript": "question only",
        },
    }
    assert resolve_listening_transcript(question) == "story and question"


@pytest.mark.unit
def test_resolve_listening_transcript_combines_story_and_question():
    question = {
        "prompt": "fallback prompt",
        "metadata": {
            "story_transcript": "Aさんは駅にいます。",
            "question_transcript": "Aさんはこのあと何をしますか。",
        },
    }
    assert resolve_listening_transcript(question) == (
        "Aさんは駅にいます。\nAさんはこのあと何をしますか。"
    )


@pytest.mark.unit
def test_resolve_listening_playback_transcript_prefers_question_line():
    question = {
        "prompt": "物語です。",
        "metadata": {
            "listening_transcript": "物語です。質問です。",
            "question_transcript": "質問です。",
        },
    }
    assert resolve_listening_playback_transcript(question) == "質問です。"


@pytest.mark.unit
def test_attach_listening_audio_sets_playback_transcript():
    out = attach_listening_audio(
        provider=_FakeProvider(),
        question={
            "prompt": "物語です。",
            "metadata": {"question_transcript": "質問です。"},
        },
    )
    metadata = out["metadata"]
    assert metadata["listening_playback_transcript"] == "質問です。"


@pytest.mark.unit
def test_attach_listening_audio_generates_story_and_question_tracks():
    out = attach_listening_audio(
        provider=_FakeProvider(),
        question={
            "prompt": "物語です。",
            "metadata": {
                "story_transcript": "物語です。",
                "question_transcript": "質問です。",
            },
        },
    )
    metadata = out["metadata"]
    assert metadata["listening_story_transcript"] == "物語です。\n質問です。"
    assert metadata["listening_question_transcript"] == "質問です。"
    assert metadata["listening_story_audio_base64"] == "QUJD"
    assert metadata["listening_question_audio_base64"] == "QUJD"


@pytest.mark.unit
def test_validate_listening_question_rejects_blank_fill():
    ok, reason = validate_listening_question(
        {
            "prompt": "この料理は味が濃すぎて、ちょっと______です。\n問題：男の人は何が言いたいですか。",
            "metadata": {},
        }
    )
    assert ok is False
    assert "blank" in reason


@pytest.mark.unit
def test_validate_listening_question_requires_context_and_question():
    ok, _reason = validate_listening_question(
        {
            "prompt": "今日お店休みですので、明日営業します",
            "metadata": {},
        }
    )
    assert ok is False


@pytest.mark.unit
def test_attach_listening_audio_derives_story_and_question_from_prompt():
    out = attach_listening_audio(
        provider=_FakeProvider(),
        question={
            "prompt": "女：じゃあ、バスで行きましょう。\n問題：二人はこの後どうしますか。",
            "metadata": {},
        },
    )
    metadata = out["metadata"]
    assert metadata["story_transcript"] == "女：じゃあ、バスで行きましょう。"
    assert metadata["question_transcript"].startswith("問題")
    assert metadata["listening_transcript_spoken"] == "じゃあ、バスで行きましょう。\n問題。二人はこの後どうしますか"

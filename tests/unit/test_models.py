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


@pytest.mark.unit
def test_listening_question_section_and_metadata():
    q = Question(
        section=QuestionSection.listening,
        level=JLPTLevel.n4,
        category="task_based",
        prompt="駅までどう行きますか。",
        choices=["左に曲がる", "右に曲がる", "まっすぐ行く", "バスに乗る"],
        answer_index=2,
        explanation="The speaker says to go straight.",
        metadata={
            "listening_transcript": "駅までどう行きますか。",
            "listening_audio_base64": "QUJD",
            "listening_audio_mime_type": "audio/wav",
        },
    )
    assert q.section == QuestionSection.listening

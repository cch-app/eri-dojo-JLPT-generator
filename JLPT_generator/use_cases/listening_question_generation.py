from __future__ import annotations

from collections.abc import Iterator
import re
from typing import Any, Protocol

from JLPT_generator.domain import JLPTLevel, QuestionSection
from JLPT_generator.parsers.delimited_questions import DelimitedQuestionStreamParser
from JLPT_generator.use_cases.reading_question_generation import (
    SupportsReadingGeneration,
    build_reading_stream_prompt,
    iter_reading_questions,
)

_BLANK_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"_{2,}"),  # ______
    re.compile(r"＿{2,}"),  # full-width underscore
    re.compile(r"（\s*）"),  # （ ）
    re.compile(r"\(\s*\)"),  # ( )
    re.compile(r"【\s*】"),  # 【 】
)

_SPEAKER_LINE_RE = re.compile(r"^\s*(?P<label>[^\s：:]{1,8})\s*[：:]\s*(?P<body>.*)\s*$")


class SupportsListeningGeneration(SupportsReadingGeneration, Protocol):
    def generate_listening_audio_base64(
        self, *, transcript: str
    ) -> tuple[str, str]: ...


def _strip_speaker_labels(transcript: str) -> str:
    """
    Prepare a transcript for "fallback TTS" playback (e.g., browser speechSynthesis).
    Speaker labels like '男：'/'女：' are removed so they are not spoken aloud.
    """
    lines = [ln.strip() for ln in str(transcript or "").splitlines() if ln.strip()]
    if not lines:
        return str(transcript or "").strip()
    out: list[str] = []
    for ln in lines:
        m = _SPEAKER_LINE_RE.match(ln)
        if not m:
            out.append(ln)
            continue
        label = (m.group("label") or "").strip()
        body = (m.group("body") or "").strip()
        if label in {"問題", "質問"}:
            out.append(f"{label}。{body}".strip("。"))
        else:
            out.append(body)
    return "\n".join([x for x in out if x]).strip()


def _split_story_and_question_from_prompt(prompt: str) -> tuple[str, str]:
    """
    Best-effort split of a spoken prompt into (story, question).
    We keep this heuristic simple because the LLM is instructed to emit
    the question line explicitly as '問題：' or '質問：'.
    """
    lines = [ln.strip() for ln in (prompt or "").splitlines() if ln.strip()]
    if not lines:
        return "", ""

    # Find the last explicit question line.
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].startswith(("問題", "質問")):
            story = "\n".join(lines[:i]).strip()
            question = lines[i].strip()
            return story, question

    # Fallback: treat final line as question if it looks like a question.
    last = lines[-1]
    looks_like_question = (
        "？" in last
        or last.endswith(("か", "か。", "か？", "かね", "かね。", "でしょうか", "でしょうか。"))
        or last.startswith(("ど", "なに", "何", "いつ", "どこ", "だれ", "誰", "どう"))
    )
    if len(lines) >= 2 and looks_like_question:
        return "\n".join(lines[:-1]).strip(), last.strip()
    return "", ""


def validate_listening_question(question: dict[str, Any]) -> tuple[bool, str]:
    prompt = str(question.get("prompt") or "").strip()
    if not prompt:
        return False, "missing prompt"

    for pat in _BLANK_PATTERNS:
        if pat.search(prompt):
            return False, "blank-fill pattern detected"

    metadata = question.get("metadata")
    story = ""
    qline = ""
    if isinstance(metadata, dict):
        story = str(metadata.get("story_transcript") or metadata.get("listening_story_transcript") or "").strip()
        qline = str(
            metadata.get("question_transcript")
            or metadata.get("listening_question_transcript")
            or metadata.get("question_prompt")
            or ""
        ).strip()

    if not story or not qline:
        story2, qline2 = _split_story_and_question_from_prompt(prompt)
        story = story or story2
        qline = qline or qline2

    if not story:
        return False, "missing context/story"
    if not qline:
        return False, "missing explicit question prompt"

    # Require an explicit "question-ness" in the question line.
    if not (
        qline.startswith(("問題", "質問"))
        or "？" in qline
        or qline.endswith(("か", "か。", "か？", "でしょうか", "でしょうか。"))
    ):
        return False, "question line does not look like a question"

    return True, ""


def build_listening_stream_prompt(
    *,
    section: QuestionSection,
    level: JLPTLevel,
    category: str,
    num_questions: int,
    explanation_locale: str,
) -> str:
    return build_reading_stream_prompt(
        section=section,
        level=level,
        category=category,
        num_questions=num_questions,
        explanation_locale=explanation_locale,
    )


def iter_listening_questions(
    *,
    provider: SupportsListeningGeneration,
    stream_text: Iterator[str],
    section: QuestionSection,
    level: JLPTLevel,
    category: str,
    num_questions: int,
    explanation_locale: str,
) -> tuple[list[dict[str, Any]], DelimitedQuestionStreamParser]:
    questions, parser = iter_reading_questions(
        provider=provider,
        stream_text=stream_text,
        section=section,
        level=level,
        category=category,
        num_questions=num_questions,
        explanation_locale=explanation_locale,
    )
    with_audio: list[dict[str, Any]] = []
    for q in questions:
        ok, _reason = validate_listening_question(q)
        if not ok:
            continue
        with_audio.append(attach_listening_audio(provider=provider, question=q))
    return with_audio, parser


def attach_listening_audio(
    *, provider: SupportsListeningGeneration, question: dict[str, Any]
) -> dict[str, Any]:
    out = dict(question)
    metadata = out.get("metadata")
    if not isinstance(metadata, dict):
        metadata = {}

    # If the model did not provide separate story/question fields, derive them from prompt.
    if not str(metadata.get("story_transcript") or "").strip() or not str(
        metadata.get("question_transcript") or ""
    ).strip():
        story, qline = _split_story_and_question_from_prompt(
            str(out.get("prompt") or "").strip()
        )
        if story and not str(metadata.get("story_transcript") or "").strip():
            metadata["story_transcript"] = story
        if qline and not str(metadata.get("question_transcript") or "").strip():
            metadata["question_transcript"] = qline

    story_transcript = resolve_listening_transcript(out)
    question_transcript = resolve_listening_playback_transcript(out)

    def _attach_audio_track(*, key_prefix: str, transcript: str) -> None:
        if not transcript:
            metadata[f"{key_prefix}_audio_base64"] = ""
            metadata[f"{key_prefix}_audio_mime_type"] = "audio/wav"
            metadata[f"{key_prefix}_audio_fallback_tts"] = False
            metadata[f"{key_prefix}_audio_error"] = ""
            return
        try:
            audio_base64, audio_mime_type = provider.generate_listening_audio_base64(
                transcript=transcript
            )
            metadata[f"{key_prefix}_audio_base64"] = audio_base64
            metadata[f"{key_prefix}_audio_mime_type"] = audio_mime_type
            metadata[f"{key_prefix}_audio_fallback_tts"] = False
            metadata[f"{key_prefix}_audio_error"] = ""
        except Exception as e:  # noqa: BLE001
            metadata[f"{key_prefix}_audio_base64"] = ""
            metadata[f"{key_prefix}_audio_mime_type"] = "audio/wav"
            metadata[f"{key_prefix}_audio_fallback_tts"] = True
            metadata[f"{key_prefix}_audio_error"] = str(e)

    metadata.setdefault("listening_transcript", story_transcript)
    metadata["listening_story_transcript"] = story_transcript
    metadata["listening_playback_transcript"] = question_transcript
    metadata["listening_question_transcript"] = question_transcript
    metadata["listening_story_transcript_spoken"] = _strip_speaker_labels(story_transcript)
    metadata["listening_question_transcript_spoken"] = _strip_speaker_labels(question_transcript)
    metadata["listening_transcript_spoken"] = _strip_speaker_labels(story_transcript)

    _attach_audio_track(key_prefix="listening_story", transcript=story_transcript)
    _attach_audio_track(
        key_prefix="listening_question", transcript=question_transcript
    )

    # Backward compatibility for already-wired template fields.
    metadata["listening_audio_base64"] = metadata.get("listening_story_audio_base64", "")
    metadata["listening_audio_mime_type"] = metadata.get(
        "listening_story_audio_mime_type", "audio/wav"
    )
    metadata["listening_audio_fallback_tts"] = bool(
        metadata.get("listening_story_audio_fallback_tts", False)
    )
    metadata["listening_audio_error"] = str(
        metadata.get("listening_story_audio_error") or ""
    )
    out["metadata"] = metadata
    return out


def resolve_listening_transcript(question: dict[str, Any]) -> str:
    prompt = str(question.get("prompt") or "").strip()
    metadata = question.get("metadata")
    if not isinstance(metadata, dict):
        return prompt

    explicit = str(metadata.get("listening_transcript") or "").strip()
    story = str(
        metadata.get("listening_story_transcript")
        or metadata.get("story_transcript")
        or ""
    ).strip()
    qline = str(
        metadata.get("listening_question_transcript")
        or metadata.get("question_transcript")
        or metadata.get("question_prompt")
        or ""
    ).strip()

    if explicit:
        return explicit
    if story and qline:
        return f"{story}\n{qline}"
    if qline:
        return qline
    if story:
        return story
    return prompt


def resolve_listening_playback_transcript(question: dict[str, Any]) -> str:
    prompt = str(question.get("prompt") or "").strip()
    metadata = question.get("metadata")
    if not isinstance(metadata, dict):
        return prompt

    # Playback should prioritize the actual question utterance when provided.
    qline = str(
        metadata.get("listening_question_transcript")
        or metadata.get("question_transcript")
        or metadata.get("question_prompt")
        or ""
    ).strip()
    if qline:
        return qline

    explicit_playback = str(metadata.get("listening_playback_transcript") or "").strip()
    if explicit_playback:
        return explicit_playback

    explicit = str(metadata.get("listening_transcript") or "").strip()
    if explicit:
        return explicit

    return prompt

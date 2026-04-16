import pytest

from JLPT_generator.adapters.ai.base import AiProviderError
from JLPT_generator.adapters.ai.ollama_sdk_provider import (
    OllamaSdkConfig,
    OllamaSdkProvider,
)

def _wav_payload_base64(*, duration_ms: int = 30) -> str:
    import base64
    import io
    import wave

    framerate = 8000
    nchannels = 1
    sampwidth = 2  # 16-bit
    nframes = int(framerate * (duration_ms / 1000.0))
    pcm = b"\x00\x00" * nframes

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(nchannels)
        wf.setsampwidth(sampwidth)
        wf.setframerate(framerate)
        wf.writeframes(pcm)
    return base64.b64encode(buf.getvalue()).decode("ascii")


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


@pytest.mark.unit
def test_generate_listening_audio_base64_rejects_non_audio_payload():
    provider = OllamaSdkProvider(OllamaSdkConfig(host="http://x", model="m", api_key=None, listening_audio_model=None))
    provider._generate_audio_text = lambda **_: "QUJD"  # type: ignore[method-assign]

    with pytest.raises(AiProviderError, match="valid playable audio bytes"):
        provider.generate_listening_audio_base64(transcript="こんにちは")


@pytest.mark.unit
def test_generate_listening_audio_base64_accepts_wav_payload():
    provider = OllamaSdkProvider(OllamaSdkConfig(host="http://x", model="m", api_key=None, listening_audio_model=None))
    # Plausible WAV header bytes (44-byte minimum).
    wav_b64 = _wav_payload_base64()
    provider._generate_audio_text = lambda **_: wav_b64  # type: ignore[method-assign]

    payload, mime = provider.generate_listening_audio_base64(transcript="こんにちは")
    assert payload == wav_b64
    assert mime == "audio/wav"


@pytest.mark.unit
def test_generate_listening_audio_base64_uses_data_uri_mime():
    provider = OllamaSdkProvider(
        OllamaSdkConfig(
            host="http://x", model="m", api_key=None, listening_audio_model=None
        )
    )
    provider._generate_audio_text = (  # type: ignore[method-assign]
        lambda **_: "data:audio/mpeg;base64,SUQzAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=="
    )

    payload, mime = provider.generate_listening_audio_base64(transcript="こんにちは")
    assert payload == "SUQzAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=="
    assert mime == "audio/mpeg"


@pytest.mark.unit
def test_generate_listening_audio_base64_strips_speaker_labels_for_single_pass():
    provider = OllamaSdkProvider(
        OllamaSdkConfig(
            host="http://x", model="m", api_key=None, listening_audio_model=None
        )
    )
    seen_prompts: list[str] = []
    wav_b64 = _wav_payload_base64()

    def _fake_generate_audio_text(**kwargs: str) -> str:
        seen_prompts.append(str(kwargs.get("prompt") or ""))
        return wav_b64

    provider._generate_audio_text = _fake_generate_audio_text  # type: ignore[method-assign]

    provider.generate_listening_audio_base64(
        transcript="男：明日の会議、何時からですか？\n問題：会議は何時からですか？"
    )
    assert seen_prompts
    sent = seen_prompts[0].split("Transcript:\n", 1)[-1]
    # Transcript must NOT include labels.
    assert "男：" not in sent
    # But must keep the spoken content.
    assert "明日の会議、何時からですか？" in sent


@pytest.mark.unit
def test_generate_listening_audio_base64_multi_speaker_uses_multiple_calls_and_voice_hints():
    provider = OllamaSdkProvider(
        OllamaSdkConfig(
            host="http://x", model="m", api_key=None, listening_audio_model=None
        )
    )
    seen_prompts: list[str] = []
    wav_b64 = _wav_payload_base64()

    def _fake_generate_audio_text(**kwargs: str) -> str:
        seen_prompts.append(str(kwargs.get("prompt") or ""))
        return wav_b64

    provider._generate_audio_text = _fake_generate_audio_text  # type: ignore[method-assign]

    payload, mime = provider.generate_listening_audio_base64(
        transcript=(
            "男：明日の会議、何時からですか？\n"
            "女：10時からですよ。\n"
            "問題：会議は何時からですか？"
        )
    )
    assert mime == "audio/wav"
    # Should be multiple calls (at least the two dialogue turns + question line).
    assert len(seen_prompts) >= 2
    # Transcripts should not include speaker labels.
    sent_transcripts = [p.split("Transcript:\n", 1)[-1] for p in seen_prompts]
    assert all(("男：" not in t and "女：" not in t) for t in sent_transcripts)
    # Voice hints should vary across speakers.
    assert any("Adult male voice" in p for p in seen_prompts)
    assert any("Adult female voice" in p for p in seen_prompts)
    # Returned payload should still be decodable base64.
    import base64

    out = base64.b64decode(payload, validate=True)
    assert out.startswith(b"RIFF")


@pytest.mark.unit
def test_generate_listening_audio_base64_multi_speaker_forces_wav_even_if_configured_mp3():
    provider = OllamaSdkProvider(
        OllamaSdkConfig(
            host="http://x",
            model="m",
            api_key=None,
            listening_audio_model=None,
            listening_audio_mime_type="audio/mpeg",
        )
    )
    wav_b64 = _wav_payload_base64()
    provider._generate_audio_text = lambda **_: wav_b64  # type: ignore[method-assign]

    payload, mime = provider.generate_listening_audio_base64(
        transcript=(
            "男：明日の会議は何時ですか？\n"
            "女：10時です。\n"
            "問題：会議は何時からですか？"
        )
    )
    assert mime == "audio/wav"
    assert payload

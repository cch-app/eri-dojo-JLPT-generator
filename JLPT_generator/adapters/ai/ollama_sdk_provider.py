from __future__ import annotations

import base64
import binascii
import os
import re
import io
import wave
from dataclasses import dataclass
from typing import Iterable, Iterator, Mapping, Optional
from urllib.parse import urlparse

from ollama import Client

from .base import AiProviderError
from .ollama import _parse_json_strict


@dataclass(frozen=True)
class OllamaSdkConfig:
    host: str
    model: str
    api_key: Optional[str]
    listening_audio_model: Optional[str]
    listening_audio_mime_type: str = "audio/wav"
    timeout_s: float = 300.0


def _hostname(host: str) -> str:
    try:
        netloc = (urlparse(host).netloc or host).strip().lower()
        return netloc.split(":")[0]
    except Exception:  # noqa: BLE001
        return host.lower().split("/")[0].split(":")[0]


def _requires_api_key_for_host(host: str) -> bool:
    hn = _hostname(host)
    return hn == "ollama.com" or hn.endswith(".ollama.com")


class OllamaSdkProvider:
    """
    Ollama via the official `ollama` Python client (local daemon or Ollama Cloud).

    See https://docs.ollama.com/cloud#python
    """

    def __init__(self, config: OllamaSdkConfig) -> None:
        self._config = config
        headers: Optional[Mapping[str, str]] = None
        if config.api_key:
            headers = {"Authorization": f"Bearer {config.api_key}"}
        self._client = Client(
            host=config.host,
            headers=headers,
            timeout=config.timeout_s,
        )

    @staticmethod
    def from_env() -> OllamaSdkProvider:
        model = os.getenv("OLLAMA_MODEL", "").strip()
        host = os.getenv("OLLAMA_HOST", "http://localhost:11434").strip()
        api_key = os.getenv("OLLAMA_API_KEY", "").strip() or None
        listening_audio_model = (
            os.getenv("OLLAMA_LISTENING_AUDIO_MODEL", "").strip() or None
        )
        listening_audio_mime_type = (
            os.getenv("OLLAMA_LISTENING_AUDIO_MIME_TYPE", "audio/wav").strip()
            or "audio/wav"
        )

        if not model:
            raise AiProviderError("Missing OLLAMA_MODEL.")
        if _requires_api_key_for_host(host) and not api_key:
            raise AiProviderError(
                "OLLAMA_API_KEY is required when OLLAMA_HOST points to Ollama Cloud "
                "(e.g. https://ollama.com). Create a key at https://ollama.com/settings/keys"
            )

        return OllamaSdkProvider(
            OllamaSdkConfig(
                host=host,
                model=model,
                api_key=api_key,
                listening_audio_model=listening_audio_model,
                listening_audio_mime_type=listening_audio_mime_type,
            )
        )

    def _messages(self, prompt: str) -> list[dict[str, str]]:
        return [
            {"role": "system", "content": "You are a careful assistant."},
            {"role": "user", "content": prompt},
        ]

    def stream_text(self, *, prompt: str) -> Iterator[str]:
        try:
            stream = self._client.chat(
                model=self._config.model,
                messages=self._messages(prompt),
                stream=True,
            )
        except Exception as e:  # noqa: BLE001
            raise AiProviderError(f"Ollama request failed: {e}") from e

        for part in stream:
            chunk = _message_content_delta(part)
            if chunk:
                yield chunk

    def complete_text(self, *, prompt: str) -> str:
        try:
            resp = self._client.chat(
                model=self._config.model,
                messages=self._messages(prompt),
                stream=False,
            )
        except Exception as e:  # noqa: BLE001
            raise AiProviderError(f"Ollama request failed: {e}") from e
        return _full_message_content(resp).strip()

    def parse_question_json_from_stream(self, *, deltas: Iterable[str]) -> dict:
        text = "".join(deltas).strip()
        return _parse_json_strict(text)

    def generate_listening_audio_base64(self, *, transcript: str) -> tuple[str, str]:
        model = self._config.listening_audio_model or self._config.model
        configured_mime_type = self._config.listening_audio_mime_type
        turns = _parse_dialogue_turns(transcript)
        is_multi_speaker = len({t.speaker_key for t in turns if t.speaker_key}) >= 2

        # Multi-speaker: generate each turn separately with voice guidance, then stitch.
        #
        # We stitch WAV reliably. If the configured output mime type is not WAV, we still
        # force WAV for multi-speaker dialogue to preserve distinct voices and natural turn-taking.
        # (Re-encoding stitched audio to mp3/ogg is out of scope and would add dependencies.)
        desired_mime_for_multi = "audio/wav"
        if is_multi_speaker:
            audio_chunks: list[bytes] = []
            for t in turns:
                if not t.spoken_text:
                    continue
                voice_hint = _voice_hint_for_speaker(t.speaker_key or "")
                prompt = _listening_audio_prompt(
                    spoken_text=t.spoken_text,
                    voice_hint=voice_hint,
                )
                payload, chunk_mime = self._generate_audio_base64_with_fallback(
                    model=model, prompt=prompt, desired_mime=desired_mime_for_multi
                )
                chunk_bytes = _decode_audio_base64_or_raise(payload)
                if not _looks_like_audio_payload(chunk_bytes, mime_type=chunk_mime):
                    raise AiProviderError(
                        "Ollama audio payload is not valid playable audio bytes."
                    )
                audio_chunks.append(chunk_bytes)
                # Add a short pause between turns for natural dialogue.
                audio_chunks.append(_wav_silence_like(chunk_bytes, duration_ms=250))

            stitched = _wav_concat(audio_chunks)
            stitched_b64 = base64.b64encode(stitched).decode("ascii")
            return stitched_b64, "audio/wav"

        # Single speaker (or non-wav): strip labels and synthesize in one go.
        cleaned = _strip_speaker_labels(transcript)
        prompt = _listening_audio_prompt(spoken_text=cleaned, voice_hint=None)
        payload, out_mime = self._generate_audio_base64_with_fallback(
            model=model, prompt=prompt, desired_mime=configured_mime_type
        )
        audio_bytes = _decode_audio_base64_or_raise(payload)
        if not _looks_like_audio_payload(audio_bytes, mime_type=out_mime):
            raise AiProviderError("Ollama audio payload is not valid playable audio bytes.")
        return payload, out_mime

    def _generate_audio_base64_with_fallback(
        self, *, model: str, prompt: str, desired_mime: str
    ) -> tuple[str, str]:
        tried_fallback = False
        raw_text = ""
        chosen_model = model
        while True:
            try:
                raw_text = self._generate_audio_text(model=chosen_model, prompt=prompt)
                break
            except AiProviderError as e:
                can_fallback = (
                    bool(self._config.listening_audio_model)
                    and chosen_model != self._config.model
                    and not tried_fallback
                    and "not found" in str(e).lower()
                )
                if not can_fallback:
                    raise
                chosen_model = self._config.model
                tried_fallback = True

        raw_text = raw_text.strip()
        if not raw_text:
            raise AiProviderError("Ollama audio generation returned empty payload.")

        sanitized = re.sub(r"\s+", "", raw_text)
        mime_type = desired_mime
        if sanitized.startswith("data:"):
            parsed = _parse_data_url_audio_payload(sanitized)
            if parsed is not None:
                mime_type, sanitized = parsed
        if not sanitized:
            raise AiProviderError("Ollama audio payload was empty after sanitization.")
        return sanitized, mime_type

    def _generate_audio_text(self, *, model: str, prompt: str) -> str:
        try:
            resp = self._client.generate(
                model=model,
                prompt=prompt,
                stream=False,
            )
        except Exception as e:  # noqa: BLE001
            raise AiProviderError(f"Ollama audio generation failed: {e}") from e
        return _extract_generate_response_text(resp)


def _message_content_delta(part: object) -> str:
    msg = getattr(part, "message", None)
    if msg is not None:
        c = getattr(msg, "content", None)
        if c:
            return str(c)
    if isinstance(part, dict):
        m = part.get("message")
        if isinstance(m, dict):
            c = m.get("content")
            if c:
                return str(c)
    return ""


def _full_message_content(resp: object) -> str:
    msg = getattr(resp, "message", None)
    if msg is not None:
        c = getattr(msg, "content", None)
        if c is not None:
            return str(c)
    if isinstance(resp, dict):
        m = resp.get("message")
        if isinstance(m, dict):
            return str(m.get("content") or "")
    return ""


def _extract_generate_response_text(resp: object) -> str:
    if isinstance(resp, dict):
        return str(resp.get("response") or "")
    c = getattr(resp, "response", None)
    if c is not None:
        return str(c)
    return ""


def _decode_audio_base64_or_raise(payload: str) -> bytes:
    try:
        return base64.b64decode(payload, validate=True)
    except (binascii.Error, ValueError) as e:
        raise AiProviderError("Ollama audio payload is not valid base64.") from e


def _parse_data_url_audio_payload(value: str) -> tuple[str, str] | None:
    if not value.startswith("data:"):
        return None
    parts = value.split(",", 1)
    if len(parts) != 2:
        return None
    header, payload = parts
    if ";base64" not in header:
        return None
    mime = header[5:].split(";", 1)[0].strip().lower() or "audio/wav"
    return mime, payload


def _looks_like_audio_payload(audio_bytes: bytes, *, mime_type: str) -> bool:
    if len(audio_bytes) < 32:
        return False
    mime = mime_type.lower().strip()
    if mime == "audio/wav" or mime == "audio/x-wav":
        # WAV needs enough bytes for a plausible header + minimal data.
        return (
            len(audio_bytes) >= 44
            and audio_bytes.startswith(b"RIFF")
            and audio_bytes[8:12] == b"WAVE"
        )
    if mime == "audio/mpeg" or mime == "audio/mp3":
        if audio_bytes.startswith(b"ID3"):
            return True
        return len(audio_bytes) > 1 and audio_bytes[0] == 0xFF and (
            audio_bytes[1] & 0xE0
        ) == 0xE0
    if mime == "audio/ogg":
        return audio_bytes.startswith(b"OggS")
    if mime == "audio/webm":
        return audio_bytes.startswith(b"\x1A\x45\xDF\xA3")
    if mime == "audio/mp4" or mime == "audio/aac":
        return len(audio_bytes) > 12 and audio_bytes[4:8] == b"ftyp"
    # Unknown audio mime types: keep validation permissive once base64 is valid.
    return True


_SPEAKER_LINE_RE = re.compile(
    r"^\s*(?P<label>[^\s：:]{1,8})\s*[：:]\s*(?P<body>.*)\s*$"
)


@dataclass(frozen=True)
class _DialogueTurn:
    speaker_key: str | None
    spoken_text: str


def _parse_dialogue_turns(transcript: str) -> list[_DialogueTurn]:
    lines = [ln.strip() for ln in str(transcript or "").splitlines() if ln.strip()]
    if not lines:
        return []

    turns: list[_DialogueTurn] = []
    for ln in lines:
        m = _SPEAKER_LINE_RE.match(ln)
        if m:
            label = (m.group("label") or "").strip()
            body = (m.group("body") or "").strip()
            # Treat question prompt markers as narration, not a "speaker".
            if label in {"問題", "質問"}:
                spoken = f"{label}。{body}".strip("。")
                turns.append(_DialogueTurn(speaker_key=None, spoken_text=spoken))
            else:
                turns.append(_DialogueTurn(speaker_key=label or None, spoken_text=body))
        else:
            turns.append(_DialogueTurn(speaker_key=None, spoken_text=ln))
    return turns


def _strip_speaker_labels(transcript: str) -> str:
    turns = _parse_dialogue_turns(transcript)
    if not turns:
        return str(transcript or "").strip()
    out_lines: list[str] = []
    for t in turns:
        if t.spoken_text:
            out_lines.append(t.spoken_text)
    return "\n".join(out_lines).strip()


def _voice_hint_for_speaker(speaker_key: str) -> str | None:
    key = (speaker_key or "").strip()
    if not key:
        return None
    # Common JLPT labels
    if "男" in key or "男性" in key:
        return "Adult male voice. Natural Japanese conversation."
    if "女" in key or "女性" in key:
        return "Adult female voice. Natural Japanese conversation."
    # Alphabetic labels: provide concrete, alternating hints for consistency.
    match key.upper():
        case "A" | "C":
            return "Adult male voice. Natural Japanese conversation."
        case "B" | "D":
            return "Adult female voice. Natural Japanese conversation."
        case _:
            pass
    # Fallback for other labels (母/父/店員/客 etc.)
    if "店員" in key:
        return "Polite shop staff voice (丁寧)."
    if "客" in key:
        return "Customer voice (natural, casual)."
    if "先生" in key:
        return "Teacher voice (clear, calm)."
    if "学生" in key:
        return "Student voice (natural, casual)."
    return "A distinct conversational voice (different from other speakers)."


def _listening_audio_prompt(*, spoken_text: str, voice_hint: str | None) -> str:
    hint = f"Voice: {voice_hint}\n" if voice_hint else ""
    return (
        "Convert the Japanese transcript below into natural JLPT-style listening audio.\n"
        + hint
        + "Important:\n"
        "- Do NOT read speaker labels aloud (e.g., no '男：', '女：', 'A:', 'B:').\n"
        "- Speak naturally, like real conversation.\n"
        "Return ONLY the final audio encoded as base64 bytes. "
        "Do not add markdown, labels, or extra text.\n\n"
        f"Transcript:\n{spoken_text}"
    )


def _wav_concat(chunks: list[bytes]) -> bytes:
    wav_chunks = [c for c in chunks if c]
    if not wav_chunks:
        raise AiProviderError("No audio chunks to stitch.")

    params: wave._wave_params | None = None  # type: ignore[attr-defined]
    fmt_sig: tuple[int, int, int, str, str] | None = None
    frames: list[bytes] = []
    for b in wav_chunks:
        with wave.open(io.BytesIO(b), "rb") as wf:
            if params is None:
                params = wf.getparams()
                fmt_sig = (
                    wf.getnchannels(),
                    wf.getsampwidth(),
                    wf.getframerate(),
                    wf.getcomptype(),
                    wf.getcompname(),
                )
            else:
                cur_sig = (
                    wf.getnchannels(),
                    wf.getsampwidth(),
                    wf.getframerate(),
                    wf.getcomptype(),
                    wf.getcompname(),
                )
                if fmt_sig is not None and cur_sig != fmt_sig:
                    raise AiProviderError("Incompatible WAV chunks (format mismatch).")
            frames.append(wf.readframes(wf.getnframes()))

    if params is None:
        raise AiProviderError("No valid WAV chunks to stitch.")

    out = io.BytesIO()
    with wave.open(out, "wb") as wout:
        wout.setparams(params)
        for fr in frames:
            if fr:
                wout.writeframes(fr)
    return out.getvalue()


def _wav_silence_like(example_wav: bytes, *, duration_ms: int) -> bytes:
    if duration_ms <= 0:
        return b""
    try:
        with wave.open(io.BytesIO(example_wav), "rb") as wf:
            nchannels = wf.getnchannels()
            sampwidth = wf.getsampwidth()
            framerate = wf.getframerate()
            comptype = wf.getcomptype()
            compname = wf.getcompname()
    except wave.Error:
        # If a provider returns malformed WAV bytes, avoid crashing the whole request.
        # We'll just omit the pause.
        return b""

    nframes = int(framerate * (duration_ms / 1000.0))
    frame_bytes = b"\x00" * (nframes * nchannels * sampwidth)
    out = io.BytesIO()
    with wave.open(out, "wb") as wout:
        wout.setnchannels(nchannels)
        wout.setsampwidth(sampwidth)
        wout.setframerate(framerate)
        wout.setcomptype(comptype, compname)
        wout.writeframes(frame_bytes)
    return out.getvalue()

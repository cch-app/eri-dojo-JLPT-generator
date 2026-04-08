from __future__ import annotations

import os
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

        if not model:
            raise AiProviderError("Missing OLLAMA_MODEL.")
        if _requires_api_key_for_host(host) and not api_key:
            raise AiProviderError(
                "OLLAMA_API_KEY is required when OLLAMA_HOST points to Ollama Cloud "
                "(e.g. https://ollama.com). Create a key at https://ollama.com/settings/keys"
            )

        return OllamaSdkProvider(
            OllamaSdkConfig(host=host, model=model, api_key=api_key)
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

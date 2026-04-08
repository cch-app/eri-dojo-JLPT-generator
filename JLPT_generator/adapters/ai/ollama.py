from __future__ import annotations

import json
from dataclasses import dataclass

import httpx

from .base import AiProviderError, AiText


@dataclass(frozen=True)
class OllamaConfig:
    base_url: str
    model: str
    timeout_s: float = 60.0


class OllamaProvider:
    """
    Minimal Ollama-compatible provider.

    Uses the chat endpoint and expects JSON-only responses for question generation.
    """

    def __init__(self, config: OllamaConfig):
        self._config = config

    def generate_question_json(self, *, prompt: str) -> dict:
        text = self._chat(prompt=prompt)
        return _parse_json_strict(text)

    def analyze_session_text(self, *, prompt: str) -> AiText:
        text = self._chat(prompt=prompt)
        return AiText(text=text.strip())

    def _chat(self, *, prompt: str) -> str:
        url = f"{self._config.base_url.rstrip('/')}/api/chat"
        payload = {
            "model": self._config.model,
            "stream": False,
            "messages": [
                {"role": "system", "content": "You are a careful assistant."},
                {"role": "user", "content": prompt},
            ],
        }
        try:
            with httpx.Client(timeout=self._config.timeout_s) as client:
                resp = client.post(url, json=payload)
                resp.raise_for_status()
        except Exception as e:  # noqa: BLE001
            raise AiProviderError(f"Ollama request failed: {e}") from e

        try:
            data = resp.json()
            # Ollama returns: {"message":{"role":"assistant","content":"..."}, ...}
            return (data.get("message") or {}).get("content") or ""
        except Exception as e:  # noqa: BLE001
            raise AiProviderError(f"Invalid Ollama response JSON: {e}") from e


def _parse_json_strict(text: str) -> dict:
    """
    Best-effort strict JSON parsing.

    Many models wrap JSON in code fences; strip common wrappers but do not attempt
    to 'fix' arbitrary invalid JSON.
    """
    raw = text.strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        # If it started with ```json, remove leading 'json'
        raw = raw.lstrip().removeprefix("json").lstrip()
    raw = raw.strip()
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError as e:
        raise AiProviderError(
            "Model did not return valid JSON. " f"First 200 chars: {text[:200]!r}"
        ) from e
    if not isinstance(obj, dict):
        raise AiProviderError("Expected a JSON object at top-level.")
    return obj

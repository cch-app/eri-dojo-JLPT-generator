"""An exhausted Ollama Cloud account (HTTP 402) must fail fast and explain itself."""

import json

import httpx
import pytest
from ollama import ResponseError

from JLPT_generator.adapters.ai import AiFailure, AiProviderError
from JLPT_generator.adapters.ai.ollama_sdk_provider import (
    OllamaSdkConfig,
    OllamaSdkProvider,
)
from JLPT_generator.domain import JLPTLevel, QuestionSection
from JLPT_generator.use_cases.stream_questions_generation import (
    iter_question_stream_events,
)
from JLPT_generator.webapp import routes
from JLPT_generator.webapp.app import create_app

QUOTA_BODY = json.dumps(
    {"error": "Add usage credits or subscribe: https://ollama.com/plans (ref: x)"}
)


class _LazyFailingClient:
    """Mimics the ollama SDK: a streaming chat only raises once iterated."""

    def __init__(self, exc: Exception) -> None:
        self.exc = exc
        self.calls = 0

    def chat(self, *, stream: bool, **_):
        self.calls += 1
        if not stream:
            raise self.exc

        def gen():
            raise self.exc
            yield  # pragma: no cover

        return gen()


def _provider(exc: Exception) -> tuple[OllamaSdkProvider, _LazyFailingClient]:
    p = OllamaSdkProvider(
        OllamaSdkConfig(
            host="http://x", model="m", api_key=None, listening_audio_model=None
        )
    )
    client = _LazyFailingClient(exc)
    p._client = client  # type: ignore[assignment]
    return p, client


@pytest.mark.unit
@pytest.mark.parametrize(
    ("exc", "kind", "retryable"),
    [
        (ResponseError(QUOTA_BODY, 402), AiFailure.quota, False),
        (ResponseError("unauthorized", 401), AiFailure.auth, False),
        (ResponseError("model 'm' not found", 404), AiFailure.model_missing, False),
        (ResponseError("slow down", 429), AiFailure.rate_limited, True),
        (ResponseError("boom", 503), AiFailure.unavailable, True),
        (ConnectionError("refused"), AiFailure.unavailable, True),
        (httpx.ReadTimeout("timeout"), AiFailure.unavailable, True),
    ],
)
def test_stream_errors_raised_lazily_are_classified(exc, kind, retryable):
    provider, _ = _provider(exc)
    with pytest.raises(AiProviderError) as info:
        list(provider.stream_text(prompt="p"))
    assert info.value.kind == kind
    assert info.value.retryable is retryable


@pytest.mark.unit
def test_quota_error_is_not_retried_or_topped_off():
    provider, client = _provider(ResponseError(QUOTA_BODY, 402))
    events = list(
        iter_question_stream_events(
            provider=provider,
            section=QuestionSection.reading,
            level=JLPTLevel.n5,
            category="grammar",
            num_questions=3,
            explanation_locale="English",
        )
    )
    error = events[-1]
    assert error["type"] == "error"
    assert error["code"] == "quota"
    assert error["retryable"] is False
    assert client.calls == 1  # no retry, no top-off request


@pytest.mark.unit
def test_route_sends_translated_message_without_vendor_text(monkeypatch):
    provider, _ = _provider(ResponseError(QUOTA_BODY, 402))
    monkeypatch.setattr(routes, "_provider", lambda: provider)
    client = create_app().test_client()
    token = client.post(
        "/api/launch",
        json={
            "level": "N5",
            "section": "reading",
            "category": "grammar",
            "ui_locale": "zh_TW",
        },
    ).get_json()["token"]

    text = client.get("/stream/questions", query_string={"token": token}).get_data(
        as_text=True
    )
    events = [json.loads(c[len("data: ") :]) for c in text.split("\n\n") if c.strip()]
    error = [e for e in events if e["type"] == "error"][0]
    assert error["code"] == "quota" and error["retryable"] is False
    assert "額度" in error["message"]
    assert "ollama.com/plans" not in error["message"]


@pytest.mark.unit
def test_unknown_errors_keep_vendor_detail(monkeypatch):
    provider, _ = _provider(ValueError("weird parse failure"))
    monkeypatch.setattr(routes, "_provider", lambda: provider)
    client = create_app().test_client()
    token = client.post(
        "/api/launch", json={"level": "N5", "section": "reading", "category": "grammar"}
    ).get_json()["token"]
    text = client.get("/stream/questions", query_string={"token": token}).get_data(
        as_text=True
    )
    assert "weird parse failure" in text

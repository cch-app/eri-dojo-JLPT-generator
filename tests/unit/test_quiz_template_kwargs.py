"""Tests for quiz template context (e.g. Finish vs Next while streaming)."""

from __future__ import annotations

import pytest

from JLPT_generator.webapp.routes import _quiz_template_kwargs


def _q(i: int) -> dict:
    return {
        "id": str(i),
        "prompt": f"Q{i}",
        "choices": ["a", "b", "c", "d"],
        "answer_index": 0,
    }


def test_streaming_not_last_when_buffer_smaller_than_requested() -> None:
    """On last buffered question but more requested: show Next, not Finish."""
    n_buf = 3
    payload = {
        "ui_locale": "en",
        "section": "reading",
        "level": "n5",
        "category": "grammar",
        "current_index": n_buf - 1,
        "revealed": False,
        "selected_index": None,
        "stream_complete": False,
        "stream_total_requested": 10,
        "questions": [_q(i) for i in range(n_buf)],
    }
    kw = _quiz_template_kwargs(payload, token="t", error=None)
    assert kw["is_last"] is False


def test_streaming_finish_only_when_all_requested_arrived() -> None:
    total = 5
    payload = {
        "ui_locale": "en",
        "section": "reading",
        "level": "n5",
        "category": "grammar",
        "current_index": total - 1,
        "revealed": False,
        "selected_index": None,
        "stream_complete": False,
        "stream_total_requested": total,
        "questions": [_q(i) for i in range(total)],
    }
    kw = _quiz_template_kwargs(payload, token="t", error=None)
    assert kw["is_last"] is True


def test_stream_complete_partial_still_finish_on_last_buffered() -> None:
    """Stream ended early: Finish on last question we have."""
    payload = {
        "ui_locale": "en",
        "section": "reading",
        "level": "n5",
        "category": "grammar",
        "current_index": 7,
        "revealed": False,
        "selected_index": None,
        "stream_complete": True,
        "stream_total_requested": 10,
        "questions": [_q(i) for i in range(8)],
    }
    kw = _quiz_template_kwargs(payload, token="t", error=None)
    assert kw["is_last"] is True


def test_non_stream_uses_buffer_length() -> None:
    n = 4
    payload = {
        "ui_locale": "en",
        "section": "reading",
        "level": "n5",
        "category": "grammar",
        "current_index": n - 1,
        "revealed": False,
        "selected_index": None,
        "questions": [_q(i) for i in range(n)],
    }
    kw = _quiz_template_kwargs(payload, token="t", error=None)
    assert kw["is_last"] is True


@pytest.mark.parametrize("revealed", [True, False])
def test_stream_waiting_more_never_shows_finish(revealed: bool) -> None:
    """When waiting for more questions after reveal, secondary nav is not Finish."""
    payload = {
        "ui_locale": "en",
        "section": "reading",
        "level": "n5",
        "category": "grammar",
        "current_index": 2,
        "revealed": revealed,
        "selected_index": None,
        "stream_complete": False,
        "stream_total_requested": 10,
        "questions": [_q(i) for i in range(3)],
    }
    kw = _quiz_template_kwargs(payload, token="t", error=None)
    if revealed:
        assert kw["stream_waiting_more"] is True
        assert kw["is_last"] is False
    else:
        assert kw["stream_waiting_more"] is False
        assert kw["is_last"] is False

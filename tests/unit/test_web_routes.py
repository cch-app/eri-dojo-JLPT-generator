import json

import pytest

from JLPT_generator.parsers.markers import QUESTION_END, QUESTION_START
from JLPT_generator.webapp import routes
from JLPT_generator.webapp.app import create_app


class _FakeProvider:
    def __init__(self, body: str) -> None:
        self._body = body

    def stream_text(self, *, prompt: str):
        yield self._body

    def complete_text(self, *, prompt: str) -> str:
        return ""


def _block(prompt: str) -> str:
    obj = {
        "prompt": prompt,
        "choices": ["い", "ろ", "は", "に"],
        "answer_index": 2,
        "explanation": "e",
    }
    return f"{QUESTION_START}\n{json.dumps(obj, ensure_ascii=False)}\n{QUESTION_END}\n"


def _events(resp) -> list[dict]:
    text = resp.get_data(as_text=True)
    return [json.loads(c[len("data: ") :]) for c in text.split("\n\n") if c.strip()]


@pytest.fixture
def client():
    return create_app().test_client()


@pytest.mark.unit
def test_dojo_page_injects_config(client):
    resp = client.get("/", headers={"Accept-Language": "zh-TW"})
    html = resp.get_data(as_text=True)
    assert resp.status_code == 200
    assert 'lang="zh-Hant"' in html
    assert '"launch": "/api/launch"' in html or '"launch":"/api/launch"' in html
    assert "js/dojo/main.js" in html


@pytest.mark.unit
def test_launch_then_stream_yields_normalized_questions(client, monkeypatch):
    monkeypatch.setattr(
        routes, "_provider", lambda: _FakeProvider(_block("a") + _block("b"))
    )
    launch = client.post(
        "/api/launch",
        json={
            "level": "N5",
            "section": "reading",
            "category": "grammar",
            "num_questions": 2,
        },
    ).get_json()
    assert launch["ok"]

    events = _events(
        client.get("/stream/questions", query_string={"token": launch["token"]})
    )
    questions = [e for e in events if e["type"] == "question"]
    assert [q["index"] for q in questions] == [0, 1]
    assert all(
        q["question"]["level"] == "N5" and q["question"]["id"] for q in questions
    )


@pytest.mark.unit
def test_launch_rejects_unknown_category(client):
    resp = client.post(
        "/api/launch", json={"level": "N5", "section": "reading", "category": "nope"}
    )
    assert resp.status_code == 400
    assert resp.get_json()["ok"] is False


@pytest.mark.unit
def test_session_token_feeds_analysis_stream(client, monkeypatch):
    monkeypatch.setattr(routes, "_provider", lambda: _FakeProvider("## Good work"))
    question = {
        "section": "reading",
        "level": "N5",
        "category": "grammar",
        "prompt": "p",
        "choices": ["a", "b"],
        "answer_index": 0,
        "explanation": "e",
    }
    session = client.post(
        "/api/session",
        json={
            "level": "N5",
            "section": "reading",
            "questions": [question],
            "answers": [0],
        },
    ).get_json()
    assert session["ok"]

    events = _events(
        client.get("/stream/analysis", query_string={"token": session["token"]})
    )
    done = [e for e in events if e["type"] == "done"]
    assert done and "Good work" in done[0]["analysis_html"]


@pytest.mark.unit
def test_pdf_without_feedback_is_rejected(client):
    assert (
        client.post("/download/feedback.pdf", data={"token": "bogus"}).status_code
        == 400
    )

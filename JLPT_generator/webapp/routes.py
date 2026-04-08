from __future__ import annotations

import datetime
import json
import os
from typing import Any, Optional

from flask import (
    Blueprint,
    Response,
    current_app,
    make_response,
    render_template,
    request,
    stream_with_context,
)

from JLPT_generator.adapters.ai import AiProviderError
from JLPT_generator.adapters.ai.ollama_sdk_provider import OllamaSdkProvider
from JLPT_generator.adapters.pdf import build_feedback_pdf_bytes
from JLPT_generator.domain import Attempt, JLPTLevel, Question, QuestionSection, SessionRun
from JLPT_generator.i18n import (
    SUPPORTED_LOCALES,
    explanation_locale_name,
    final_analysis_language_name,
    label_for_category,
    label_for_section,
    locale_label_for_code,
    translate,
)
from JLPT_generator.use_cases.batch_questions import parse_questions_batch_json
from JLPT_generator.use_cases.prompts import (
    final_analysis_prompt,
    questions_batch_generation_prompt,
    questions_batch_repair_prompt,
)
from JLPT_generator.webapp.markdown import markdown_to_safe_html
from JLPT_generator.webapp.token_codec import TokenCodec, TokenDecodeError

bp = Blueprint("web", __name__)

MAX_NUM_QUESTIONS = 20

READING_CATEGORIES = [
    "grammar",
    "vocabulary",
    "reading_comprehension",
]

LISTENING_CATEGORIES = [
    "task_based",
    "point_comprehension",
    "listening_comprehension",
]


def _provider() -> OllamaSdkProvider:
    return OllamaSdkProvider.from_env()


def _codec() -> TokenCodec:
    secret = os.getenv("SECRET_KEY", "").strip() or current_app.secret_key or ""
    return TokenCodec.from_secret(secret_key=str(secret))


def _safe_int(value: str, *, default: int, min_v: int, max_v: int) -> int:
    try:
        v = int(value)
    except ValueError:
        return default
    return max(min_v, min(max_v, v))


def _load_payload_from_form() -> dict[str, Any]:
    token = (request.form.get("token") or "").strip()
    if not token:
        raise TokenDecodeError("Missing session token.")
    return _codec().decode(token)


def _render_error(ui_locale: str, message_key: str, *, detail: str = "") -> str:
    return translate(ui_locale, message_key, detail=detail) if detail else translate(ui_locale, message_key)


@bp.get("/")
def setup_page() -> str:
    ui_locale = (request.args.get("ui_locale") or "en").strip()
    if ui_locale not in SUPPORTED_LOCALES:
        ui_locale = "en"
    return render_template(
        "setup.html",
        supported_locales=SUPPORTED_LOCALES,
        reading_categories=READING_CATEGORIES,
        listening_categories=LISTENING_CATEGORIES,
        levels=[lvl.value for lvl in JLPTLevel],
        sections=[sec.value for sec in QuestionSection],
        t=translate,
        ui_locale=ui_locale,
        locale_label_for_code=locale_label_for_code,
        label_for_section=label_for_section,
        label_for_category=label_for_category,
    )


@bp.post("/start")
def start() -> str:
    ui_locale = (request.form.get("ui_locale") or "en").strip()
    if ui_locale not in SUPPORTED_LOCALES:
        ui_locale = "en"

    section = (request.form.get("section") or QuestionSection.reading.value).strip()
    level = (request.form.get("level") or JLPTLevel.n5.value).strip()
    category = (request.form.get("category") or READING_CATEGORIES[0]).strip()
    num_questions = _safe_int(
        request.form.get("num_questions") or "10",
        default=10,
        min_v=1,
        max_v=MAX_NUM_QUESTIONS,
    )

    expl_name = explanation_locale_name(ui_locale)
    try:
        provider = _provider()
        prompt = questions_batch_generation_prompt(
            section=QuestionSection(section),
            level=JLPTLevel(level),
            category=category,
            num_questions=num_questions,
            explanation_locale=expl_name,
        )
        raw = provider.complete_text(prompt=prompt)
        parsed = parse_questions_batch_json(text=raw, expected_count=num_questions)
    except Exception as e:  # noqa: BLE001
        try:
            provider = _provider()
            repair = questions_batch_repair_prompt(
                bad_output=str(e),
                expected_count=num_questions,
                section=QuestionSection(section),
                level=JLPTLevel(level),
                category=category,
                explanation_locale=expl_name,
            )
            raw2 = provider.complete_text(prompt=repair)
            parsed = parse_questions_batch_json(text=raw2, expected_count=num_questions)
        except Exception as e2:  # noqa: BLE001
            return render_template(
                "setup.html",
                supported_locales=SUPPORTED_LOCALES,
                reading_categories=READING_CATEGORIES,
                listening_categories=LISTENING_CATEGORIES,
                levels=[lvl.value for lvl in JLPTLevel],
                sections=[sec.value for sec in QuestionSection],
                t=translate,
                ui_locale=ui_locale,
                locale_label_for_code=locale_label_for_code,
                label_for_section=label_for_section,
                label_for_category=label_for_category,
                error=_render_error(ui_locale, "err_generate", detail=str(e2)),
                form={
                    "ui_locale": ui_locale,
                    "section": section,
                    "level": level,
                    "category": category,
                    "num_questions": num_questions,
                },
            )

    payload: dict[str, Any] = {
        "v": 1,
        "ui_locale": ui_locale,
        "section": section,
        "level": level,
        "category": category,
        "num_questions": num_questions,
        "questions": parsed,
        "attempts": [],
        "current_index": 0,
        "revealed": False,
        "selected_index": None,
        "final_analysis": "",
    }
    token = _codec().encode(payload)
    return _render_test(payload, token=token, error=None)


def _current_question(payload: dict[str, Any]) -> dict[str, Any]:
    idx = int(payload.get("current_index") or 0)
    questions = payload.get("questions") or []
    if not isinstance(questions, list) or not (0 <= idx < len(questions)):
        raise TokenDecodeError("Session token contains no current question.")
    q = questions[idx]
    if not isinstance(q, dict):
        raise TokenDecodeError("Invalid question payload.")
    return q


def _render_test(payload: dict[str, Any], *, token: str, error: Optional[str]) -> str:
    ui_locale = str(payload.get("ui_locale") or "en")
    q = _current_question(payload)
    idx = int(payload.get("current_index") or 0)
    num = int(payload.get("num_questions") or 0)
    revealed = bool(payload.get("revealed"))
    selected_index = payload.get("selected_index")
    try:
        selected_int = int(selected_index) if selected_index is not None else None
    except ValueError:
        selected_int = None
    answer_index = int(q.get("answer_index") or 0)

    return render_template(
        "test.html",
        t=translate,
        token=token,
        ui_locale=ui_locale,
        section=str(payload.get("section") or ""),
        section_label=label_for_section(ui_locale, str(payload.get("section") or "")),
        level=str(payload.get("level") or ""),
        category=str(payload.get("category") or ""),
        category_label=label_for_category(ui_locale, str(payload.get("category") or "")),
        idx=idx,
        num_questions=num,
        question=q,
        revealed=revealed,
        selected_index=selected_int,
        is_correct=(selected_int == answer_index) if (revealed and selected_int is not None) else None,
        correct_label=["A", "B", "C", "D"][answer_index],
        error=error,
        is_last=(idx >= num - 1) if num else False,
    )

@bp.post("/answer")
def submit_answer() -> str:
    payload = _load_payload_from_form()
    ui_locale = str(payload.get("ui_locale") or "en")
    q = _current_question(payload)
    qid = str(q.get("id") or "")

    selected_raw = (request.form.get("selected_index") or "").strip()
    try:
        selected_int = int(selected_raw)
    except ValueError:
        token = _codec().encode(payload)
        return _render_test(
            payload, token=token, error=_render_error(ui_locale, "err_select_first")
        )

    payload["selected_index"] = selected_int
    answer_index = int(q.get("answer_index") or 0)
    payload_attempts = payload.get("attempts")
    if not isinstance(payload_attempts, list):
        payload_attempts = []
        payload["attempts"] = payload_attempts
    payload_attempts.append(
        {
            "question_id": qid,
            "selected_index": selected_int,
            "is_correct": selected_int == answer_index,
        }
    )
    payload["revealed"] = True

    token = _codec().encode(payload)
    return _render_test(payload, token=token, error=None)


@bp.post("/next")
def next_question() -> str:
    payload = _load_payload_from_form()
    ui_locale = str(payload.get("ui_locale") or "en")

    if not payload.get("revealed"):
        token = _codec().encode(payload)
        return _render_test(payload, token=token, error=_render_error(ui_locale, "err_check_first"))

    idx = int(payload.get("current_index") or 0)
    num = int(payload.get("num_questions") or 0)
    if num and idx >= num - 1:
        return finish()

    payload["current_index"] = idx + 1
    payload["revealed"] = False
    payload["selected_index"] = None

    token = _codec().encode(payload)
    return _render_test(payload, token=token, error=None)


@bp.post("/finish")
def finish() -> str:
    payload = _load_payload_from_form()
    ui_locale = str(payload.get("ui_locale") or "en")

    token = _codec().encode(payload)
    return render_template(
        "results.html",
        t=translate,
        token=token,
        ui_locale=ui_locale,
        error=None,
        summary=_score_summary(payload),
        analysis_raw="",
        analysis_html="",
        stream_enabled=True,
    )


@bp.get("/stream/analysis")
def stream_analysis() -> Response:
    token = (request.args.get("token") or "").strip()
    if not token:
        return Response("Missing token.", status=400)

    # Capture app-bound dependencies up front so the streaming generator
    # does not touch `current_app` outside an application context.
    codec = _codec()

    try:
        payload = codec.decode(token)
    except TokenDecodeError as e:
        return Response(str(e), status=400)

    ui_locale = str(payload.get("ui_locale") or "en")

    def gen():
        def send(obj: dict[str, Any]) -> str:
            return f"data: {json.dumps(obj, ensure_ascii=False)}\n\n"

        # Let the client show skeleton immediately.
        yield send({"type": "status", "status": "started"})

        try:
            session = SessionRun(
                section=QuestionSection(str(payload.get("section") or "")),
                level=JLPTLevel(str(payload.get("level") or "")),
                category=str(payload.get("category") or ""),
                num_questions=int(payload.get("num_questions") or 10),
                questions=[
                    Question.model_validate(q) for q in (payload.get("questions") or [])
                ],
                attempts=[
                    Attempt.model_validate(a)
                    for a in (payload.get("attempts") or [])
                    if isinstance(a, dict) and a.get("question_id")
                ],
            )
            provider = _provider()
            lang = final_analysis_language_name(ui_locale)
            prompt = final_analysis_prompt(session=session, output_language_name=lang)

            chunks: list[str] = []
            for i, delta in enumerate(provider.stream_text(prompt=prompt)):
                chunks.append(delta)
                # Stream heartbeats to prove streaming is active.
                if i % 16 == 0:
                    yield send({"type": "status", "status": "streaming"})

            analysis = "".join(chunks).strip()
            payload["final_analysis"] = analysis
            new_token = codec.encode(payload)
            yield send(
                {
                    "type": "done",
                    "token": new_token,
                    "analysis_html": markdown_to_safe_html(analysis),
                }
            )
        except Exception as e:  # noqa: BLE001
            yield send(
                {
                    "type": "error",
                    "message": _render_error(ui_locale, "err_analyze", detail=str(e)),
                }
            )

    return Response(
        stream_with_context(gen()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


def _score_summary(payload: dict[str, Any]) -> dict[str, Any]:
    attempts = payload.get("attempts") or []
    if not isinstance(attempts, list):
        attempts = []
    total = len(attempts)
    correct = sum(1 for a in attempts if isinstance(a, dict) and a.get("is_correct"))
    return {
        "total_answered": total,
        "correct": correct,
        "accuracy": (correct / total) if total else 0.0,
    }


@bp.post("/download/feedback.pdf")
def download_feedback_pdf() -> Response:
    payload = _load_payload_from_form()
    ui_locale = str(payload.get("ui_locale") or "en")
    analysis = str(payload.get("final_analysis") or "").strip()
    if not analysis:
        token = _codec().encode(payload)
        return make_response(
            render_template(
                "results.html",
                t=translate,
                token=token,
                ui_locale=ui_locale,
                error=_render_error(ui_locale, "err_no_feedback_pdf"),
                summary=_score_summary(payload),
                analysis_raw="",
                analysis_html="",
            ),
            400,
        )

    summary = _score_summary(payload)
    title = translate(ui_locale, "feedback")
    subtitle = f"{summary['correct']}/{summary['total_answered']}"
    generated_on = translate(
        ui_locale,
        "pdf_generated",
        date=datetime.date.today().isoformat(),
    )
    data = build_feedback_pdf_bytes(
        title=title,
        markdown_body=analysis,
        subtitle_line=subtitle,
        generated_on=generated_on,
    )
    fn = f"jlpt-feedback-{datetime.date.today().isoformat()}.pdf"

    resp = make_response(data)
    resp.headers["Content-Type"] = "application/pdf"
    resp.headers["Content-Disposition"] = f'attachment; filename="{fn}"'
    return resp


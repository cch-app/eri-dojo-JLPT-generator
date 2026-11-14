from __future__ import annotations

import datetime
import os
import uuid
from collections.abc import Iterator
from typing import Any

from flask import (
    Blueprint,
    Response,
    current_app,
    jsonify,
    make_response,
    render_template,
    request,
    url_for,
)
from pydantic import ValidationError

from JLPT_generator.adapters.ai import AiFailure, AiProviderError
from JLPT_generator.adapters.ai.ollama_sdk_provider import OllamaSdkProvider
from JLPT_generator.adapters.pdf import build_feedback_pdf_bytes
from JLPT_generator.domain import JLPTLevel, QuestionSection
from JLPT_generator.i18n import (
    explanation_locale_name,
    final_analysis_language_name,
    map_browser_language,
    translate,
)
from JLPT_generator.monitoring.generation_log import log_generation
from JLPT_generator.use_cases.prompts import final_analysis_prompt
from JLPT_generator.use_cases.stream_questions_generation import (
    iter_question_stream_events,
)
from JLPT_generator.webapp.ai_errors import ai_error_event, ai_error_event_from
from JLPT_generator.webapp.markdown import markdown_to_safe_html
from JLPT_generator.webapp.session_tokens import (
    MAX_NUM_QUESTIONS,
    PayloadError,
    build_analysis_payload,
    build_launch_payload,
    decode_launch_payload,
    normalize_streamed_question,
    normalize_ui_locale,
    score_summary,
    session_run_from_payload,
)
from JLPT_generator.webapp.sse import sse_response
from JLPT_generator.webapp.token_codec import TokenCodec, TokenDecodeError

bp = Blueprint("web", __name__)

UI_LOCALE_COOKIE = "ui_locale"


def _provider() -> OllamaSdkProvider:
    return OllamaSdkProvider.from_env()


def _codec() -> TokenCodec:
    secret = os.getenv("SECRET_KEY", "").strip() or current_app.secret_key or ""
    return TokenCodec.from_secret(secret_key=str(secret))


def _resolve_ui_locale() -> str:
    raw = request.args.get(UI_LOCALE_COOKIE) or request.cookies.get(UI_LOCALE_COOKIE)
    if raw:
        return normalize_ui_locale(raw)
    best = request.accept_languages.best or ""
    return map_browser_language(best)


def _render_error(ui_locale: str, message_key: str, *, detail: str = "") -> str:
    return (
        translate(ui_locale, message_key, detail=detail)
        if detail
        else translate(ui_locale, message_key)
    )


def _json_error(message: str, status: int = 400) -> tuple[Response, int]:
    return jsonify({"ok": False, "error": message}), status


@bp.get("/")
def dojo_page() -> Response:
    ui_locale = _resolve_ui_locale()
    config = {
        "uiLocale": ui_locale,
        "maxQuestions": MAX_NUM_QUESTIONS,
        "endpoints": {
            "launch": url_for("web.api_launch"),
            "questions": url_for("web.stream_questions"),
            "session": url_for("web.api_session"),
            "analysis": url_for("web.stream_analysis"),
            "feedbackPdf": url_for("web.download_feedback_pdf"),
        },
    }
    return make_response(
        render_template("dojo.html", ui_locale=ui_locale, dojo_config=config)
    )


@bp.post("/api/launch")
def api_launch() -> Any:
    """Mint a signed launch token for one question-generation stream."""
    try:
        payload = build_launch_payload(request.get_json(silent=True) or {})
    except PayloadError as e:
        return _json_error(str(e))
    return jsonify({"ok": True, "token": _codec().encode(payload)})


@bp.post("/api/session")
def api_session() -> Any:
    """Sign a finished run so it can be analyzed and exported as PDF."""
    try:
        payload = build_analysis_payload(request.get_json(silent=True) or {})
    except (PayloadError, ValidationError, TypeError, ValueError) as e:
        return _json_error(str(e))
    return jsonify({"ok": True, "token": _codec().encode(payload)})


@bp.get("/stream/questions")
def stream_questions() -> Response:
    token = (request.args.get("token") or "").strip()
    if not token:
        return Response("Missing token.", status=400)

    try:
        launch = decode_launch_payload(_codec().decode(token))
    except TokenDecodeError as e:
        return Response(str(e), status=400)

    ui_locale = str(launch.get("ui_locale") or "en")
    num_questions = int(launch.get("num_questions") or 5)
    request_id = str(uuid.uuid4())
    log_generation(
        "http_request_received",
        request_id=request_id,
        path="stream_questions",
        num_questions=num_questions,
    )

    def events() -> Iterator[dict[str, Any]]:
        try:
            provider = _provider()
        except AiProviderError as e:
            yield ai_error_event_from(
                ui_locale, e, fallback_key="err_generate", request_id=request_id
            )
            return
        index = 0
        try:
            for event in iter_question_stream_events(
                provider=provider,
                section=QuestionSection(str(launch["section"])),
                level=JLPTLevel(str(launch["level"])),
                category=str(launch["category"]),
                num_questions=num_questions,
                explanation_locale=explanation_locale_name(ui_locale),
                request_id=request_id,
            ):
                if event.get("type") == "error":
                    yield ai_error_event(
                        ui_locale,
                        kind=AiFailure(event.get("code") or AiFailure.unknown),
                        retryable=bool(event.get("retryable", True)),
                        detail=str(event.get("message") or ""),
                        fallback_key="err_generate",
                        request_id=request_id,
                    )
                    continue
                if event.get("type") != "question":
                    yield event
                    continue
                try:
                    question = normalize_streamed_question(
                        event.get("question") or {}, launch=launch
                    )
                except (ValidationError, KeyError, TypeError) as e:
                    log_generation(
                        "stream_question_rejected", request_id=request_id, detail=str(e)
                    )
                    continue
                yield {"type": "question", "index": index, "question": question}
                index += 1
        except GeneratorExit:
            log_generation("sse_disconnected", request_id=request_id)
            raise

    return sse_response(events())


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

    def events() -> Iterator[dict[str, Any]]:
        # Let the client show skeleton immediately.
        yield {"type": "status", "status": "started"}

        try:
            session = session_run_from_payload(payload)
            provider = _provider()
            lang = final_analysis_language_name(ui_locale)
            prompt = final_analysis_prompt(session=session, output_language_name=lang)

            chunks: list[str] = []
            for i, delta in enumerate(provider.stream_text(prompt=prompt)):
                chunks.append(delta)
                # Stream heartbeats to prove streaming is active.
                if i % 16 == 0:
                    yield {"type": "status", "status": "streaming"}

            analysis = "".join(chunks).strip()
            payload["final_analysis"] = analysis
            yield {
                "type": "done",
                "token": codec.encode(payload),
                "analysis_html": markdown_to_safe_html(analysis),
            }
        except Exception as e:  # noqa: BLE001
            yield ai_error_event_from(ui_locale, e, fallback_key="err_analyze")

    return sse_response(events())


@bp.post("/download/feedback.pdf")
def download_feedback_pdf() -> Response:
    token = (request.form.get("token") or "").strip()
    try:
        payload = _codec().decode(token)
    except TokenDecodeError as e:
        return Response(str(e), status=400)

    ui_locale = str(payload.get("ui_locale") or "en")
    analysis = str(payload.get("final_analysis") or "").strip()
    if not analysis:
        return Response(_render_error(ui_locale, "err_no_feedback_pdf"), status=400)

    summary = score_summary(payload)
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

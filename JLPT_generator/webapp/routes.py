from __future__ import annotations

import datetime
import json
import os
import uuid
from typing import Any, Optional

from flask import (
    Blueprint,
    Response,
    current_app,
    jsonify,
    make_response,
    render_template,
    request,
    stream_with_context,
    url_for,
)
from pydantic import ValidationError

from JLPT_generator.adapters.ai import AiProviderError
from JLPT_generator.adapters.ai.ollama_sdk_provider import OllamaSdkProvider
from JLPT_generator.adapters.pdf import build_feedback_pdf_bytes
from JLPT_generator.domain import (
    Attempt,
    JLPTLevel,
    Question,
    QuestionSection,
    SessionRun,
)
from JLPT_generator.i18n import (
    SUPPORTED_LOCALES,
    explanation_locale_name,
    final_analysis_language_name,
    label_for_category,
    label_for_section,
    locale_label_for_code,
    map_browser_language,
    translate,
)
from JLPT_generator.monitoring.generation_log import log_generation
from JLPT_generator.use_cases.generate_question import _question_from_payload
from JLPT_generator.use_cases.listening_question_generation import (
    resolve_listening_playback_transcript,
    resolve_listening_transcript,
)
from JLPT_generator.use_cases.prompts import final_analysis_prompt
from JLPT_generator.use_cases.stream_questions_generation import (
    iter_question_stream_events,
)
from JLPT_generator.webapp.markdown import markdown_to_safe_html
from JLPT_generator.webapp.token_codec import TokenCodec, TokenDecodeError

bp = Blueprint("web", __name__)

MAX_NUM_QUESTIONS = 10
UI_LOCALE_COOKIE = "ui_locale"

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


def _quiz_stream_request() -> bool:
    return request.headers.get("X-Quiz-Stream", "").strip() == "1"


def _load_payload_and_raw_token() -> tuple[dict[str, Any], str]:
    if request.is_json and _quiz_stream_request():
        data = request.get_json(silent=True) or {}
        token = (data.get("token") or "").strip()
        if not token:
            raise TokenDecodeError("Missing session token.")
        return _codec().decode(token), token
    token = (request.form.get("token") or "").strip()
    if not token:
        raise TokenDecodeError("Missing session token.")
    return _codec().decode(token), token


def _load_payload_from_form() -> dict[str, Any]:
    payload, _ = _load_payload_and_raw_token()
    return payload


def _sync_num_questions(payload: dict[str, Any]) -> None:
    qs = payload.get("questions")
    if isinstance(qs, list):
        payload["num_questions"] = len(qs)


def _new_stream_session_payload(
    launch: dict[str, Any], questions: list[dict[str, Any]]
) -> dict[str, Any]:
    return {
        "v": 1,
        "ui_locale": str(launch["ui_locale"]),
        "section": str(launch["section"]),
        "level": str(launch["level"]),
        "category": str(launch["category"]),
        "questions": questions,
        "attempts": [],
        "current_index": 0,
        "revealed": False,
        "selected_index": None,
        "final_analysis": "",
        "stream_complete": False,
        "stream_total_requested": int(launch["num_questions"]),
        "num_questions": len(questions),
    }


def _validate_stream_question_dict(
    raw: dict[str, Any],
    *,
    section: QuestionSection,
    level: JLPTLevel,
    category: str,
) -> dict[str, Any]:
    q = _question_from_payload(
        raw,
        fallback_section=section,
        fallback_level=level,
        category=category,
    )
    return q.model_dump(mode="json")


def _quiz_template_kwargs(
    payload: dict[str, Any], *, token: str, error: Optional[str]
) -> dict[str, Any]:
    ui_locale = str(payload.get("ui_locale") or "en")
    q = _current_question(payload)
    idx = int(payload.get("current_index") or 0)
    questions = payload.get("questions")

    if not isinstance(questions, list):
        questions = []
    num = len(questions)
    revealed = bool(payload.get("revealed"))
    selected_index = payload.get("selected_index")

    try:
        selected_int = int(selected_index) if selected_index is not None else None
    except ValueError:
        selected_int = None

    answer_index = int(q.get("answer_index") or 0)
    is_listening = str(payload.get("section") or "") == QuestionSection.listening.value
    qmeta = q.get("metadata")
    if not isinstance(qmeta, dict):
        qmeta = {}
    listening_story_audio_base64 = (
        str(
            qmeta.get("listening_story_audio_base64")
            or qmeta.get("listening_audio_base64")
            or ""
        ).strip()
        if is_listening
        else ""
    )
    listening_story_audio_mime = (
        str(
            qmeta.get("listening_story_audio_mime_type")
            or qmeta.get("listening_audio_mime_type")
            or "audio/wav"
        ).strip()
        if is_listening
        else "audio/wav"
    )
    listening_question_audio_base64 = (
        str(qmeta.get("listening_question_audio_base64") or "").strip()
        if is_listening
        else ""
    )
    listening_question_audio_mime = (
        str(qmeta.get("listening_question_audio_mime_type") or "audio/wav").strip()
        if is_listening
        else "audio/wav"
    )
    listening_transcript = resolve_listening_transcript(q) if is_listening else ""
    listening_playback_transcript = (
        resolve_listening_playback_transcript(q) if is_listening else ""
    )
    listening_transcript_spoken = (
        str(qmeta.get("listening_transcript_spoken") or "").strip()
        if is_listening
        else ""
    ) or listening_transcript
    listening_story_audio_src = (
        f"data:{listening_story_audio_mime};base64,{listening_story_audio_base64}"
        if listening_story_audio_base64
        else ""
    )
    listening_question_audio_src = (
        f"data:{listening_question_audio_mime};base64,{listening_question_audio_base64}"
        if listening_question_audio_base64
        else ""
    )
    listening_story_audio_fallback_tts = bool(
        qmeta.get("listening_story_audio_fallback_tts")
        if is_listening
        else False
    )
    listening_question_audio_fallback_tts = bool(
        qmeta.get("listening_question_audio_fallback_tts")
        if is_listening
        else False
    )
    stream_complete = bool(payload.get("stream_complete", True))
    stream_waiting_more = (
        revealed and num > 0 and idx >= num - 1 and not stream_complete
    )
    stream_total_raw = payload.get("stream_total_requested")
    stream_total: Optional[int] = None

    if stream_total_raw is not None:
        try:
            stream_total = int(stream_total_raw)
        except (TypeError, ValueError):
            stream_total = None
    if not num:
        is_last = False
    elif stream_total is None or stream_total <= 0:
        is_last = idx >= num - 1
    elif stream_complete:
        is_last = idx >= num - 1
    else:
        # Still streaming: only the configured last index may show Finish.
        is_last = num >= stream_total and idx >= stream_total - 1

    kwargs: dict[str, Any] = {
        "t": translate,
        "token": token,
        "ui_locale": ui_locale,
        "url_for_locale": _url_for_locale(ui_locale),
        "section": str(payload.get("section") or ""),
        "section_label": label_for_section(
            ui_locale, str(payload.get("section") or "")
        ),
        "level": str(payload.get("level") or ""),
        "category": str(payload.get("category") or ""),
        "category_label": label_for_category(
            ui_locale, str(payload.get("category") or "")
        ),
        "idx": idx,
        "num_questions": num,
        "question": q,
        "revealed": revealed,
        "selected_index": selected_int,
        "is_correct": (
            (selected_int == answer_index)
            if (revealed and selected_int is not None)
            else None
        ),
        "correct_label": ["A", "B", "C", "D"][answer_index],
        "error": error,
        "is_last": is_last and not stream_waiting_more,
        "stream_waiting_more": stream_waiting_more,
        "is_listening": is_listening,
        "listening_story_audio_src": listening_story_audio_src,
        "listening_question_audio_src": listening_question_audio_src,
        "listening_transcript": listening_transcript,
        "listening_transcript_spoken": listening_transcript_spoken,
        "listening_playback_transcript": listening_playback_transcript,
        "listening_story_audio_fallback_tts": listening_story_audio_fallback_tts,
        "listening_question_audio_fallback_tts": listening_question_audio_fallback_tts,
    }
    if "stream_total_requested" in payload:
        kwargs["stream_total_requested"] = int(payload["stream_total_requested"])
    return kwargs


def _render_quiz_mount_html(
    payload: dict[str, Any], *, token: str, error: Optional[str]
) -> str:
    kwargs = _quiz_template_kwargs(payload, token=token, error=error)
    return render_template("_quiz_mount.html", **kwargs)


def _render_error(ui_locale: str, message_key: str, *, detail: str = "") -> str:
    return (
        translate(ui_locale, message_key, detail=detail)
        if detail
        else translate(ui_locale, message_key)
    )


def _url_for_locale(ui_locale: str):
    def _inner(endpoint: str, **values: Any) -> str:
        values.setdefault("ui_locale", ui_locale)
        return url_for(endpoint, **values)

    return _inner


def _normalize_ui_locale(raw: str | None) -> str:
    ui_locale = (raw or "en").strip()
    return ui_locale if ui_locale in SUPPORTED_LOCALES else "en"


def _resolve_ui_locale() -> str:
    return _normalize_ui_locale(
        request.args.get(UI_LOCALE_COOKIE)
        or request.form.get(UI_LOCALE_COOKIE)
        or request.cookies.get(UI_LOCALE_COOKIE)
    )


def _decode_launch_token(payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("kind") != "launch":
        raise TokenDecodeError("Invalid launch token.")
    for key in ("ui_locale", "section", "level", "category", "num_questions"):
        if key not in payload:
            raise TokenDecodeError("Launch token is incomplete.")
    return payload


@bp.get("/")
def setup_page() -> Response:
    ui_locale = _resolve_ui_locale()
    resp = make_response(
        render_template(
            "setup.html",
            supported_locales=SUPPORTED_LOCALES,
            reading_categories=READING_CATEGORIES,
            listening_categories=LISTENING_CATEGORIES,
            levels=[lvl.value for lvl in JLPTLevel],
            sections=[sec.value for sec in QuestionSection],
            t=translate,
            ui_locale=ui_locale,
            url_for_locale=_url_for_locale(ui_locale),
            locale_label_for_code=locale_label_for_code,
            label_for_section=label_for_section,
            label_for_category=label_for_category,
            form=None,
        )
    )
    resp.set_cookie(
        UI_LOCALE_COOKIE,
        ui_locale,
        max_age=60 * 60 * 24 * 30,
        samesite="Lax",
    )
    return resp


@bp.post("/start")
def start() -> Response:
    ui_locale = _resolve_ui_locale()

    section = (request.form.get("section") or QuestionSection.reading.value).strip()
    if section not in {s.value for s in QuestionSection}:
        section = QuestionSection.reading.value
    level = (request.form.get("level") or JLPTLevel.n5.value).strip()
    category_pool = (
        LISTENING_CATEGORIES
        if section == QuestionSection.listening.value
        else READING_CATEGORIES
    )
    category = (request.form.get("category") or category_pool[0]).strip()
    if category not in category_pool:
        category = category_pool[0]
    num_questions = _safe_int(
        request.form.get("num_questions") or "5",
        default=5,
        min_v=1,
        max_v=MAX_NUM_QUESTIONS,
    )

    launch_payload: dict[str, Any] = {
        "v": 1,
        "kind": "launch",
        "ui_locale": ui_locale,
        "section": section,
        "level": level,
        "category": category,
        "num_questions": num_questions,
    }
    launch_token = _codec().encode(launch_payload)
    resp = make_response(
        render_template(
            "quiz_stream.html",
            t=translate,
            ui_locale=ui_locale,
            url_for_locale=_url_for_locale(ui_locale),
            launch_token=launch_token,
            stream_questions_url=url_for("web.stream_questions"),
            quiz_stream_merge_url=url_for("web.quiz_stream_merge"),
            quiz_stream_finalize_url=url_for("web.quiz_stream_finalize"),
            form={
                "ui_locale": ui_locale,
                "section": section,
                "level": level,
                "category": category,
                "num_questions": num_questions,
            },
        )
    )
    resp.set_cookie(
        UI_LOCALE_COOKIE,
        ui_locale,
        max_age=60 * 60 * 24 * 30,
        samesite="Lax",
    )
    return resp


@bp.post("/quiz/stream_merge")
def quiz_stream_merge() -> Any:
    data = request.get_json(silent=True) or {}
    codec = _codec()
    try:
        if data.get("launch_token"):
            launch = _decode_launch_token(codec.decode(str(data["launch_token"])))
            idx = int(data.get("index", -1))
            if idx != 0:
                return jsonify({"ok": False, "error": "bad index"}), 400
            qraw = data.get("question")
            if not isinstance(qraw, dict):
                return jsonify({"ok": False, "error": "bad question"}), 400
            qdict = _validate_stream_question_dict(
                qraw,
                section=QuestionSection(str(launch["section"])),
                level=JLPTLevel(str(launch["level"])),
                category=str(launch["category"]),
            )
            payload = _new_stream_session_payload(launch, [qdict])
            token = codec.encode(payload)
        else:
            token_in = (data.get("token") or "").strip()
            if not token_in:
                return jsonify({"ok": False, "error": "missing token"}), 400
            payload = codec.decode(token_in)
            if payload.get("kind") == "launch":
                return jsonify({"ok": False, "error": "bad token"}), 400
            idx = int(data.get("index", -1))
            qraw = data.get("question")
            if not isinstance(qraw, dict):
                return jsonify({"ok": False, "error": "bad question"}), 400
            questions = payload.get("questions")
            if not isinstance(questions, list):
                questions = []
            if idx < len(questions):
                token = codec.encode(payload)
                return jsonify(
                    {
                        "ok": True,
                        "token": token,
                        "html": _render_quiz_mount_html(
                            payload, token=token, error=None
                        ),
                        "duplicate": True,
                    }
                )
            if idx != len(questions):
                return jsonify({"ok": False, "error": "index mismatch"}), 400
            qdict = _validate_stream_question_dict(
                qraw,
                section=QuestionSection(str(payload.get("section") or "")),
                level=JLPTLevel(str(payload.get("level") or "")),
                category=str(payload.get("category") or ""),
            )
            questions.append(qdict)
            payload["questions"] = questions
            _sync_num_questions(payload)
            ci = int(payload.get("current_index") or 0)
            if ci >= len(questions):
                payload["current_index"] = max(0, len(questions) - 1)
            token = codec.encode(payload)
    except (TokenDecodeError, ValueError, KeyError, ValidationError) as e:
        return jsonify({"ok": False, "error": str(e)}), 400

    return jsonify(
        {
            "ok": True,
            "token": token,
            "html": _render_quiz_mount_html(payload, token=token, error=None),
        }
    )


@bp.post("/quiz/stream_finalize")
def quiz_stream_finalize() -> Any:
    data = request.get_json(silent=True) or {}
    codec = _codec()
    token_in = (data.get("token") or "").strip()
    try:
        payload = codec.decode(token_in)
        if payload.get("kind") == "launch":
            return jsonify({"ok": False, "error": "bad token"}), 400
        payload["stream_complete"] = True
        _sync_num_questions(payload)
        token = codec.encode(payload)
    except TokenDecodeError as e:
        return jsonify({"ok": False, "error": str(e)}), 400

    return jsonify(
        {
            "ok": True,
            "token": token,
            "html": _render_quiz_mount_html(payload, token=token, error=None),
        }
    )


@bp.get("/stream/questions")
def stream_questions() -> Response:
    token = (request.args.get("token") or "").strip()
    if not token:
        return Response("Missing token.", status=400)

    codec = _codec()
    try:
        raw_launch = codec.decode(token)
        launch = _decode_launch_token(raw_launch)
    except TokenDecodeError as e:
        return Response(str(e), status=400)

    ui_locale = str(launch.get("ui_locale") or "en")
    section = str(launch.get("section") or "")
    level = str(launch.get("level") or "")
    category = str(launch.get("category") or "")
    num_questions = int(launch.get("num_questions") or 5)
    expl_name = explanation_locale_name(ui_locale)
    request_id = str(uuid.uuid4())
    log_generation(
        "http_request_received",
        request_id=request_id,
        path="stream_questions",
        num_questions=num_questions,
    )

    def gen():
        def send(obj: dict[str, Any]) -> str:
            return f"data: {json.dumps(obj, ensure_ascii=False)}\n\n"

        try:
            provider = _provider()
        except AiProviderError as e:
            yield send(
                {
                    "type": "error",
                    "message": _render_error(ui_locale, "err_generate", detail=str(e)),
                }
            )
            return
        try:
            for event in iter_question_stream_events(
                provider=provider,
                section=QuestionSection(section),
                level=JLPTLevel(level),
                category=category,
                num_questions=num_questions,
                explanation_locale=expl_name,
                request_id=request_id,
            ):
                yield send(event)
        except GeneratorExit:
            log_generation("sse_disconnected", request_id=request_id)
            raise

    return Response(
        stream_with_context(gen()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@bp.post("/enter")
def enter_session() -> str | Response:
    token = (request.form.get("token") or "").strip()
    if not token:
        return Response("Missing session token.", status=400)
    try:
        payload = _codec().decode(token)
    except TokenDecodeError as e:
        return Response(str(e), status=400)
    if payload.get("kind") == "launch":
        return Response("Session is not ready.", status=400)
    ui_locale = str(payload.get("ui_locale") or "en")
    questions = payload.get("questions") or []
    if not isinstance(questions, list) or not questions:
        resp = make_response(
            render_template(
                "setup.html",
                supported_locales=SUPPORTED_LOCALES,
                reading_categories=READING_CATEGORIES,
                listening_categories=LISTENING_CATEGORIES,
                levels=[lvl.value for lvl in JLPTLevel],
                sections=[sec.value for sec in QuestionSection],
                t=translate,
                ui_locale=ui_locale,
                url_for_locale=_url_for_locale(ui_locale),
                locale_label_for_code=locale_label_for_code,
                label_for_section=label_for_section,
                label_for_category=label_for_category,
                error=_render_error(
                    ui_locale, "err_generate", detail="No questions in session."
                ),
                form={
                    "ui_locale": ui_locale,
                    "section": str(payload.get("section") or ""),
                    "level": str(payload.get("level") or ""),
                    "category": str(payload.get("category") or ""),
                    "num_questions": int(payload.get("num_questions") or 5),
                },
            )
        )
        resp.set_cookie(
            UI_LOCALE_COOKIE,
            ui_locale,
            max_age=60 * 60 * 24 * 30,
            samesite="Lax",
        )
        return resp
    resp = make_response(_render_test(payload, token=token, error=None))
    resp.set_cookie(
        UI_LOCALE_COOKIE,
        ui_locale,
        max_age=60 * 60 * 24 * 30,
        samesite="Lax",
    )
    return resp


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
    _sync_num_questions(payload)
    kwargs = _quiz_template_kwargs(payload, token=token, error=error)
    return render_template("test.html", **kwargs)


@bp.post("/answer")
def submit_answer() -> Any:
    payload, _ = _load_payload_and_raw_token()
    _sync_num_questions(payload)
    ui_locale = str(payload.get("ui_locale") or "en")
    q = _current_question(payload)
    qid = str(q.get("id") or "")

    if request.is_json and _quiz_stream_request():
        data = request.get_json(silent=True) or {}
        raw_sel = data.get("selected_index")
        if raw_sel is None:
            selected_raw = ""
        else:
            selected_raw = str(raw_sel).strip()
    else:
        selected_raw = (request.form.get("selected_index") or "").strip()
    try:
        selected_int = int(selected_raw)
    except ValueError:
        token = _codec().encode(payload)
        err = _render_error(ui_locale, "err_select_first")
        if request.is_json and _quiz_stream_request():
            return jsonify(
                {
                    "ok": False,
                    "token": token,
                    "error": err,
                    "html": _render_quiz_mount_html(payload, token=token, error=err),
                }
            )
        return _render_test(payload, token=token, error=err)

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
    if request.is_json and _quiz_stream_request():
        return jsonify(
            {
                "ok": True,
                "token": token,
                "html": _render_quiz_mount_html(payload, token=token, error=None),
            }
        )
    return _render_test(payload, token=token, error=None)


@bp.post("/next")
def next_question() -> Any:
    payload, _ = _load_payload_and_raw_token()
    _sync_num_questions(payload)
    ui_locale = str(payload.get("ui_locale") or "en")

    if not payload.get("revealed"):
        token = _codec().encode(payload)
        err = _render_error(ui_locale, "err_check_first")
        if request.is_json and _quiz_stream_request():
            return jsonify(
                {
                    "ok": False,
                    "token": token,
                    "error": err,
                    "html": _render_quiz_mount_html(payload, token=token, error=err),
                }
            )
        return _render_test(payload, token=token, error=err)

    idx = int(payload.get("current_index") or 0)
    questions = payload.get("questions")
    if not isinstance(questions, list):
        questions = []
    num = len(questions)

    if num and idx >= num - 1:
        if not payload.get("stream_complete", True):
            token = _codec().encode(payload)
            err = _render_error(ui_locale, "err_wait_more_questions")
            if request.is_json and _quiz_stream_request():
                return jsonify(
                    {
                        "ok": False,
                        "token": token,
                        "error": err,
                        "html": _render_quiz_mount_html(
                            payload, token=token, error=err
                        ),
                    }
                )
            return _render_test(payload, token=token, error=err)
        if request.is_json and _quiz_stream_request():
            return jsonify(
                {
                    "action": "post_finish",
                    "token": _codec().encode(payload),
                    "finish_url": url_for("web.finish"),
                }
            )
        return finish()

    payload["current_index"] = idx + 1
    payload["revealed"] = False
    payload["selected_index"] = None

    token = _codec().encode(payload)
    if request.is_json and _quiz_stream_request():
        return jsonify(
            {
                "ok": True,
                "token": token,
                "html": _render_quiz_mount_html(payload, token=token, error=None),
            }
        )
    return _render_test(payload, token=token, error=None)


@bp.post("/finish")
def finish() -> str:
    payload = _load_payload_from_form()
    ui_locale = str(payload.get("ui_locale") or _resolve_ui_locale())

    token = _codec().encode(payload)
    resp = make_response(
        render_template(
            "results.html",
            t=translate,
            token=token,
            ui_locale=ui_locale,
            url_for_locale=_url_for_locale(ui_locale),
            error=None,
            summary=_score_summary(payload),
            analysis_raw="",
            analysis_html="",
            stream_enabled=True,
        )
    )
    resp.set_cookie(
        UI_LOCALE_COOKIE,
        ui_locale,
        max_age=60 * 60 * 24 * 30,
        samesite="Lax",
    )
    return resp


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
                num_questions=int(payload.get("num_questions") or 5),
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
                url_for_locale=_url_for_locale(ui_locale),
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

from __future__ import annotations

import os
import time
from collections.abc import Iterator
from typing import Protocol

from JLPT_generator.adapters.ai.base import AiProviderError
from JLPT_generator.domain import JLPTLevel, QuestionSection
from JLPT_generator.monitoring.generation_log import log_generation
from JLPT_generator.parsers.delimited_questions import DelimitedQuestionStreamParser
from JLPT_generator.use_cases.listening_question_generation import (
    SupportsListeningGeneration,
    attach_listening_audio,
    build_listening_stream_prompt,
    validate_listening_question,
)
from JLPT_generator.use_cases.reading_question_generation import (
    build_reading_stream_prompt,
)
from JLPT_generator.use_cases.prompts import questions_stream_topoff_prompt

class SupportsTextGeneration(Protocol):
    def stream_text(self, *, prompt: str) -> Iterator[str]: ...

    def complete_text(self, *, prompt: str) -> str: ...


def _max_stream_retries() -> int:
    raw = (os.getenv("OLLAMA_STREAM_MAX_RETRIES") or "1").strip()
    try:
        v = int(raw)
    except ValueError:
        return 1
    return max(0, min(5, v))


def _stream_with_retries(
    provider: SupportsTextGeneration, *, prompt: str
) -> Iterator[str]:
    attempts = _max_stream_retries() + 1
    last_err: Exception | None = None
    for attempt in range(attempts):
        try:
            yield from provider.stream_text(prompt=prompt)
            return
        except AiProviderError as e:
            last_err = e
            log_generation(
                "model_stream_error",
                attempt=attempt + 1,
                max_attempts=attempts,
                detail=str(e),
            )
            if attempt + 1 >= attempts:
                raise
            time.sleep(min(2.0, 0.4 * (2**attempt)))
    if last_err:
        raise last_err


def iter_question_stream_events(
    *,
    provider: SupportsTextGeneration,
    section: QuestionSection,
    level: JLPTLevel,
    category: str,
    num_questions: int,
    explanation_locale: str,
    request_id: str | None = None,
) -> Iterator[dict[str, Any]]:
    """
    Yields dicts suitable for JSON-SSE encoding (see web routes).

    Emits completed questions as they are parsed; supports partial success.
    """
    rid = request_id or "-"
    t0 = time.perf_counter()
    t_first: float | None = None
    log_generation(
        "generation_started",
        request_id=rid,
        section=section.value,
        level=level.value,
        category=category,
        num_questions=num_questions,
    )

    prompt = _build_stream_prompt(
        section=section,
        level=level,
        category=category,
        num_questions=num_questions,
        explanation_locale=explanation_locale,
    )
    parser = DelimitedQuestionStreamParser(
        section=section, level=level, category=category
    )
    questions: list[dict[str, Any]] = []
    stream_error: str | None = None

    yield {"type": "status", "status": "started", "requested": num_questions}

    chunk_index = 0
    try:
        for delta in _stream_with_retries(provider, prompt=prompt):
            chunk_index += 1
            if chunk_index % 24 == 0:
                yield {"type": "status", "status": "streaming"}
            for q in parser.feed(delta):
                if section == QuestionSection.listening:
                    ok, reason = validate_listening_question(q)
                    if not ok:
                        log_generation(
                            "listening_question_rejected",
                            request_id=rid,
                            detail=reason,
                            prompt_snippet=str(q.get("prompt") or "")[:240],
                        )
                        continue
                question = _prepare_question_for_section(
                    provider=provider, section=section, question=q
                )
                questions.append(question)
                if t_first is None:
                    t_first = time.perf_counter()
                    log_generation(
                        "first_question_ready",
                        request_id=rid,
                        ttfq_ms=round((t_first - t0) * 1000, 2),
                    )
                    yield {
                        "type": "question",
                        "index": len(questions) - 1,
                        "question": question,
                        "ttfq_ms": round((t_first - t0) * 1000, 2),
                    }
                else:
                    yield {
                        "type": "question",
                        "index": len(questions) - 1,
                        "question": question,
                    }
                if len(questions) >= num_questions:
                    break
            if len(questions) >= num_questions:
                break
    except GeneratorExit:
        log_generation(
            "generation_cancelled",
            request_id=rid,
            received=len(questions),
            duration_ms=round((time.perf_counter() - t0) * 1000, 2),
        )
        raise
    except Exception as e:  # noqa: BLE001
        stream_error = str(e)
        log_generation(
            "generation_stream_exception",
            request_id=rid,
            detail=stream_error,
            received=len(questions),
        )

    if len(questions) < num_questions:
        remaining = num_questions - len(questions)
        snippets = [str(q.get("prompt") or "") for q in questions]
        topoff = questions_stream_topoff_prompt(
            section=section,
            level=level,
            category=category,
            remaining=remaining,
            explanation_locale=explanation_locale,
            avoid_prompt_snippets=snippets,
        )
        try:
            text = provider.complete_text(prompt=topoff)
            for q in parser.feed(text):
                if section == QuestionSection.listening:
                    ok, reason = validate_listening_question(q)
                    if not ok:
                        log_generation(
                            "listening_question_rejected",
                            request_id=rid,
                            detail=reason,
                            prompt_snippet=str(q.get("prompt") or "")[:240],
                        )
                        continue
                question = _prepare_question_for_section(
                    provider=provider, section=section, question=q
                )
                questions.append(question)
                if t_first is None:
                    t_first = time.perf_counter()
                    log_generation(
                        "first_question_ready",
                        request_id=rid,
                        ttfq_ms=round((t_first - t0) * 1000, 2),
                    )
                    yield {
                        "type": "question",
                        "index": len(questions) - 1,
                        "question": question,
                        "ttfq_ms": round((t_first - t0) * 1000, 2),
                    }
                else:
                    yield {
                        "type": "question",
                        "index": len(questions) - 1,
                        "question": question,
                    }
                if len(questions) >= num_questions:
                    break
        except Exception as e:  # noqa: BLE001
            log_generation(
                "topoff_failed",
                request_id=rid,
                detail=str(e),
                had_partial=len(questions) > 0,
            )

    duration_ms = round((time.perf_counter() - t0) * 1000, 2)
    log_generation(
        "generation_finished",
        request_id=rid,
        requested=num_questions,
        received=len(questions),
        duration_ms=duration_ms,
        malformed_blocks=parser.malformed_blocks,
        duplicate_skipped=parser.duplicate_skipped,
    )

    if not questions:
        yield {
            "type": "error",
            "message": stream_error or "No questions were produced.",
            "partial_count": 0,
        }
        return

    done_event: dict[str, Any] = {
        "type": "done",
        "requested": num_questions,
        "received": len(questions),
        "partial": len(questions) < num_questions,
        "parser_malformed": parser.malformed_blocks,
        "parser_duplicates_skipped": parser.duplicate_skipped,
        "duration_ms": duration_ms,
    }
    if stream_error and len(questions) < num_questions:
        done_event["warning"] = stream_error
    yield done_event


def _build_stream_prompt(
    *,
    section: QuestionSection,
    level: JLPTLevel,
    category: str,
    num_questions: int,
    explanation_locale: str,
) -> str:
    match section:
        case QuestionSection.listening:
            return build_listening_stream_prompt(
                section=section,
                level=level,
                category=category,
                num_questions=num_questions,
                explanation_locale=explanation_locale,
            )
        case _:
            return build_reading_stream_prompt(
                section=section,
                level=level,
                category=category,
                num_questions=num_questions,
                explanation_locale=explanation_locale,
            )


def _prepare_question_for_section(
    *,
    provider: SupportsTextGeneration,
    section: QuestionSection,
    question: dict[str, Any],
) -> dict[str, Any]:
    match section:
        case QuestionSection.listening:
            if not hasattr(provider, "generate_listening_audio_base64"):
                raise AiProviderError(
                    "Listening section requires audio generation support."
                )
            return attach_listening_audio(
                provider=provider,  # type: ignore[arg-type]
                question=question,
            )
        case _:
            return question

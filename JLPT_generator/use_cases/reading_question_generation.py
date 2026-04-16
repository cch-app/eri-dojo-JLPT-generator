from __future__ import annotations

from collections.abc import Iterator
from typing import Any, Protocol

from JLPT_generator.domain import JLPTLevel, QuestionSection
from JLPT_generator.parsers.delimited_questions import DelimitedQuestionStreamParser
from JLPT_generator.use_cases.prompts import (
    questions_stream_delimited_prompt,
    questions_stream_topoff_prompt,
)


class SupportsReadingGeneration(Protocol):
    def stream_text(self, *, prompt: str) -> Iterator[str]: ...

    def complete_text(self, *, prompt: str) -> str: ...


def iter_reading_questions(
    *,
    provider: SupportsReadingGeneration,
    stream_text: Iterator[str],
    section: QuestionSection,
    level: JLPTLevel,
    category: str,
    num_questions: int,
    explanation_locale: str,
) -> tuple[list[dict[str, Any]], DelimitedQuestionStreamParser]:
    parser = DelimitedQuestionStreamParser(
        section=section,
        level=level,
        category=category,
    )
    questions: list[dict[str, Any]] = []
    for delta in stream_text:
        for q in parser.feed(delta):
            questions.append(q)
            if len(questions) >= num_questions:
                return questions, parser

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
        text = provider.complete_text(prompt=topoff)
        for q in parser.feed(text):
            questions.append(q)
            if len(questions) >= num_questions:
                break
    return questions, parser


def build_reading_stream_prompt(
    *,
    section: QuestionSection,
    level: JLPTLevel,
    category: str,
    num_questions: int,
    explanation_locale: str,
) -> str:
    return questions_stream_delimited_prompt(
        section=section,
        level=level,
        category=category,
        num_questions=num_questions,
        explanation_locale=explanation_locale,
    )

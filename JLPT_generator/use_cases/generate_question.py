from __future__ import annotations

from dataclasses import dataclass

from pydantic import ValidationError

from JLPT_generator.adapters.ai import AiProvider, AiProviderError
from JLPT_generator.domain import JLPTLevel, Question, QuestionSection
from JLPT_generator.use_cases.prompts import (
    question_generation_prompt,
    question_generation_repair_prompt,
)


@dataclass(frozen=True)
class GenerateQuestionUseCase:
    provider: AiProvider

    def run(
        self, *, section: QuestionSection, level: JLPTLevel, category: str
    ) -> Question:
        prompt = question_generation_prompt(
            section=section, level=level, category=category
        )
        try:
            payload = self.provider.generate_question_json(prompt=prompt)
            return _question_from_payload(
                payload,
                fallback_section=section,
                fallback_level=level,
                category=category,
            )
        except (AiProviderError, ValidationError, KeyError, TypeError) as e:
            # One repair attempt with stricter instruction.
            repair = question_generation_repair_prompt(bad_output=str(e))
            payload = self.provider.generate_question_json(prompt=repair)
            return _question_from_payload(
                payload,
                fallback_section=section,
                fallback_level=level,
                category=category,
            )


def _question_from_payload(
    payload: dict,
    *,
    fallback_section: QuestionSection,
    fallback_level: JLPTLevel,
    category: str,
) -> Question:
    normalized = dict(payload)
    normalized.setdefault("section", fallback_section.value)
    normalized.setdefault("level", fallback_level.value)
    normalized.setdefault("category", category)
    return Question.model_validate(normalized)

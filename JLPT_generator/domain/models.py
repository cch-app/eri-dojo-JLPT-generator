from __future__ import annotations

from enum import StrEnum
from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class QuestionSection(StrEnum):
    reading = "reading"
    listening = "listening"


class JLPTLevel(StrEnum):
    n1 = "N1"
    n2 = "N2"
    n3 = "N3"
    n4 = "N4"
    n5 = "N5"


ChoiceLabel = Literal["A", "B", "C", "D"]


class Question(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    section: QuestionSection
    level: JLPTLevel
    category: str

    prompt: str
    choices: list[str] = Field(min_length=2, max_length=4)
    answer_index: int = Field(ge=0, le=3)
    explanation: str

    metadata: dict[str, Any] = Field(default_factory=dict)

    def correct_label(self) -> ChoiceLabel:
        return ["A", "B", "C", "D"][self.answer_index]  # type: ignore[return-value]


class Attempt(BaseModel):
    question_id: UUID
    selected_index: int | None = Field(default=None, ge=0, le=3)
    is_correct: bool = False
    time_spent_ms: int | None = Field(default=None, ge=0)


class SessionRun(BaseModel):
    section: QuestionSection
    level: JLPTLevel
    category: str
    num_questions: int = Field(ge=1, le=20, default=10)

    questions: list[Question] = Field(default_factory=list)
    attempts: list[Attempt] = Field(default_factory=list)

    final_analysis: str | None = None

    def score_summary(self) -> dict[str, Any]:
        total = len(self.attempts)
        correct = sum(1 for a in self.attempts if a.is_correct)
        return {
            "total_answered": total,
            "correct": correct,
            "accuracy": (correct / total) if total else 0.0,
        }

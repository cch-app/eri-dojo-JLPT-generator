from __future__ import annotations

import json
from dataclasses import dataclass, field

from JLPT_generator.domain import JLPTLevel, QuestionSection
from JLPT_generator.parsers.markers import QUESTION_END, QUESTION_START
from JLPT_generator.use_cases.generate_question import _question_from_payload


def _normalize_prompt_key(prompt: str) -> str:
    return " ".join(prompt.split())


@dataclass
class DelimitedQuestionStreamParser:
    """
    Incrementally extracts JSON objects between QUESTION_START / QUESTION_END markers.
    Emits only Pydantic-validated questions; skips malformed blocks.
    """

    section: QuestionSection
    level: JLPTLevel
    category: str
    max_buffer_chars: int = 400_000
    _buffer: str = ""
    _seen_prompts: set[str] = field(default_factory=set)
    malformed_blocks: int = 0
    duplicate_skipped: int = 0

    def feed(self, chunk: str) -> list[dict]:
        if chunk:
            self._buffer += chunk
        if len(self._buffer) > self.max_buffer_chars:
            self._buffer = self._buffer[-self.max_buffer_chars :]
        out: list[dict] = []
        while True:
            start = self._buffer.find(QUESTION_START)
            if start == -1:
                break
            if start > 0:
                self._buffer = self._buffer[start:]
                start = 0
            end = self._buffer.find(QUESTION_END, start + len(QUESTION_START))
            if end == -1:
                break
            inner = self._buffer[start + len(QUESTION_START) : end].strip()
            self._buffer = self._buffer[end + len(QUESTION_END) :]
            raw_obj = self._try_parse_json_object(inner)
            if raw_obj is None:
                self.malformed_blocks += 1
                continue
            try:
                q = _question_from_payload(
                    raw_obj,
                    fallback_section=self.section,
                    fallback_level=self.level,
                    category=self.category,
                )
                qdict = q.model_dump(mode="json")
            except Exception:  # noqa: BLE001 — validation; count and continue
                self.malformed_blocks += 1
                continue
            key = _normalize_prompt_key(str(qdict.get("prompt") or ""))
            if not key:
                self.malformed_blocks += 1
                continue
            if key in self._seen_prompts:
                self.duplicate_skipped += 1
                continue
            self._seen_prompts.add(key)
            out.append(qdict)
        return out

    @staticmethod
    def _try_parse_json_object(inner: str) -> dict | None:
        raw = inner.strip()
        if raw.startswith("```"):
            raw = raw.strip("`")
            raw = raw.lstrip().removeprefix("json").lstrip()
        raw = raw.strip()
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError:
            return None
        if not isinstance(obj, dict):
            return None
        return obj

from __future__ import annotations

import re

_UUID_LINE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\s*$",
    re.IGNORECASE,
)


def preprocess_feedback_markdown(text: str) -> str:
    """Strip technical lines and normalize embedded rule separators."""
    lines_out: list[str] = []
    for line in text.replace("\r\n", "\n").split("\n"):
        stripped = line.strip()
        if re.search(r"(?i)question_id\s*[:=]", line):
            continue
        if _UUID_LINE.match(stripped):
            continue
        lines_out.append(line)
    joined = "\n".join(lines_out)
    joined = re.sub(r"\s+[-─]{3,}\s+", "\n\n", joined)
    return joined

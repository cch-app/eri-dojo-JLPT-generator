from __future__ import annotations

import json

from JLPT_generator.domain import JLPTLevel, QuestionSection, SessionRun
from JLPT_generator.parsers.markers import QUESTION_END, QUESTION_START

_EXPLANATION_RULES = (
    "For the 'explanation' field:\n"
    "- Write several sentences (not a single short line).\n"
    "- Explain clearly why the correct choice is right (grammar, vocabulary, or reading/listening logic).\n"
    "- Briefly explain why each incorrect option is wrong (one short phrase per distractor is enough).\n"
    "- You may mention a useful pattern or study tip.\n"
    "- Do NOT copy or closely paraphrase copyrighted JLPT or prep materials.\n"
)


def question_generation_prompt(
    *,
    section: QuestionSection,
    level: JLPTLevel,
    category: str,
    explanation_locale: str = "English",
) -> str:
    is_listening = section == QuestionSection.listening
    listening_schema_metadata: dict[str, object] = {
        "listening_transcript": "string (same as prompt; for rendering post-answer only)",
        "story_transcript": "string (context/story only; no explicit question)",
        "question_transcript": "string (the explicit question prompt only)",
        "tags": ["optional", "strings"],
        "difficulty": "optional",
    }
    schema = {
        "section": section.value,
        "level": level.value,
        "category": category,
        "prompt": (
            "string (the listening transcript in Japanese)"
            if is_listening
            else "string (the question stem, in Japanese)"
        ),
        "choices": ["string", "string", "string", "string"],
        "answer_index": 0,
        "explanation": "string (detailed; see rules below)",
        "metadata": (
            listening_schema_metadata
            if is_listening
            else {"tags": ["optional", "strings"], "difficulty": "optional"}
        ),
    }

    return (
        "You are generating ORIGINAL JLPT-style practice questions.\n"
        "Do NOT copy or closely paraphrase any real JLPT or copyrighted prep questions.\n"
        "First infer high-level patterns for the requested level/section/category, then create a new question.\n\n"
        f"Section: {section.value}\n"
        f"Level: {level.value}\n"
        f"Category: {category}\n\n"
        f"The question stem and all four choices must be in Japanese (authentic JLPT-style).\n"
        + (
            "For listening questions, 'prompt' must be the SPOKEN transcript in Japanese.\n"
            "Mandatory listening format:\n"
            "- Part 1 (Context/Story): a short natural situation, dialogue, or statement.\n"
            "- Part 2 (Question Prompt): an explicit question the learner must answer.\n"
            "  Prefer starting the question line with '問題：' (or '質問：').\n"
            "Hard rules for listening:\n"
            "- NO blanks/穴埋め (no '____', no '＿', no '（　）').\n"
            "- The audio must be answerable by listening alone (include context + the question).\n"
            "- Natural spoken Japanese only (avoid grammar worksheet tone).\n"
            "- Provide BOTH in metadata too: story_transcript (context only) and question_transcript (question only).\n"
            "- metadata.listening_transcript must match prompt.\n"
            "Do not include UI instructions like 'Read the transcript' or 'Choose A/B/C/D'.\n"
            if is_listening
            else ""
        )
        + f"The 'explanation' must be written entirely in {explanation_locale} "
        "(not Japanese), so the learner can understand in their UI language.\n\n"
        f"{_EXPLANATION_RULES}\n"
        "Return ONLY valid JSON (no markdown, no extra text). The JSON must match this shape:\n"
        f"{json.dumps(schema, ensure_ascii=False)}\n\n"
        "Rules:\n"
        "- choices must be 4 items.\n"
        "- answer_index must be 0..3.\n"
    )


def question_generation_repair_prompt(*, bad_output: str) -> str:
    return (
        "You previously returned invalid JSON.\n"
        "Return ONLY valid JSON. Do not include markdown code fences.\n"
        "Fix the output to be a single JSON object with keys:\n"
        "section, level, category, prompt, choices, answer_index, explanation, metadata.\n\n"
        "Invalid output:\n"
        f"{bad_output}\n"
    )


def _single_question_shape_example(
    *,
    section: QuestionSection,
    level: JLPTLevel,
    category: str,
    explanation_locale: str,
) -> dict:
    is_listening = section == QuestionSection.listening
    return {
        "section": section.value,
        "level": level.value,
        "category": category,
        "prompt": (
            "string (listening transcript in Japanese)"
            if is_listening
            else "string (stem in Japanese)"
        ),
        "choices": ["string", "string", "string", "string"],
        "answer_index": 0,
        "explanation": f"string (detailed explanation in {explanation_locale})",
        "metadata": (
            {
                "listening_transcript": "string (same as prompt)",
                "story_transcript": "string (context/story only; no explicit question)",
                "question_transcript": "string (explicit question prompt only)",
                "tags": ["optional"],
                "difficulty": "optional",
            }
            if is_listening
            else {"tags": ["optional"], "difficulty": "optional"}
        ),
    }


def questions_batch_generation_prompt(
    *,
    section: QuestionSection,
    level: JLPTLevel,
    category: str,
    num_questions: int,
    explanation_locale: str,
) -> str:
    one = _single_question_shape_example(
        section=section,
        level=level,
        category=category,
        explanation_locale=explanation_locale,
    )
    return (
        "You are generating ORIGINAL JLPT-style practice questions.\n"
        "Do NOT copy or closely paraphrase any real JLPT or copyrighted prep questions.\n"
        f"Create exactly {num_questions} distinct questions for the same session.\n"
        "Vary topics, grammar points, and vocabulary so questions are not repetitive.\n\n"
        f"Section: {section.value}\n"
        f"Level: {level.value}\n"
        f"Category: {category}\n\n"
        "Each item: question stem and all four choices must be in Japanese.\n"
        + (
            "For listening section, each 'prompt' is the SPOKEN transcript in Japanese; "
            "it will be rendered as audio.\n"
            "Mandatory listening format per prompt:\n"
            "- Part 1 (Context/Story): natural situation/dialogue.\n"
            "- Part 2 (Question Prompt): explicit question line, prefer '問題：...'.\n"
            "Hard rules: NO blanks/穴埋め ('____', '＿', '（　）'), and it must be answerable by audio alone.\n"
            "Also include in metadata: story_transcript + question_transcript, and listening_transcript == prompt.\n"
            if section == QuestionSection.listening
            else ""
        )
        + f"Each item's 'explanation' must be written entirely in {explanation_locale}.\n\n"
        f"{_EXPLANATION_RULES}\n"
        "Return ONLY valid JSON (no markdown, no extra text). Top-level object must have key "
        f"'questions' whose value is an array of exactly {num_questions} objects.\n"
        "Each object must match this shape (example shows one object; IDs may be omitted — "
        "they will be assigned if missing):\n"
        f"{json.dumps(one, ensure_ascii=False)}\n\n"
        "Rules per question:\n"
        "- choices: exactly 4 strings.\n"
        "- answer_index: integer 0..3.\n"
        "- section, level, category must match the session values above.\n"
    )


def questions_stream_delimited_prompt(
    *,
    section: QuestionSection,
    level: JLPTLevel,
    category: str,
    num_questions: int,
    explanation_locale: str,
) -> str:
    one = _single_question_shape_example(
        section=section,
        level=level,
        category=category,
        explanation_locale=explanation_locale,
    )
    inner_example = json.dumps(one, ensure_ascii=False)
    return (
        "You are generating ORIGINAL JLPT-style practice questions.\n"
        "Do NOT copy or closely paraphrase any real JLPT or copyrighted prep questions.\n"
        f"Output up to {num_questions} distinct questions for the same session.\n"
        "Vary topics, grammar points, and vocabulary so questions are not repetitive.\n\n"
        f"Section: {section.value}\n"
        f"Level: {level.value}\n"
        f"Category: {category}\n\n"
        "Each item: question stem and all four choices must be in Japanese.\n"
        + (
            "For listening section, each 'prompt' is the SPOKEN transcript in Japanese; "
            "it will be rendered as audio.\n"
            "Mandatory listening format per prompt:\n"
            "- Part 1 (Context/Story): natural situation/dialogue.\n"
            "- Part 2 (Question Prompt): explicit question line, prefer '問題：...'.\n"
            "Hard rules: NO blanks/穴埋め ('____', '＿', '（　）'), and it must be answerable by audio alone.\n"
            "Also include in metadata: story_transcript + question_transcript, and listening_transcript == prompt.\n"
            "Common JLPT-like patterns to emulate (original content only):\n"
            "- Speaker concern: 'どうしよう' → 問題：何を困っていますか。\n"
            "- Next action: 'じゃあ…' → 問題：二人はこの後どうしますか。\n"
            "- Reason: '～んです' → 問題：なぜ～ましたか。\n"
            "- Choice/decision: 'じゃあ、これにします' → 問題：何を選びましたか。\n"
            if section == QuestionSection.listening
            else ""
        )
        + f"Each item's 'explanation' must be written entirely in {explanation_locale}.\n\n"
        f"{_EXPLANATION_RULES}\n"
        "OUTPUT FORMAT (critical):\n"
        f"- Emit one question at a time using exactly these line-oriented markers:\n"
        f"  {QUESTION_START}\n"
        "  <single JSON object only, no markdown fences>\n"
        f"  {QUESTION_END}\n"
        "- Repeat for each question.\n"
        "- Do not wrap the JSON in ``` fences.\n"
        "- Do not output a top-level array or a 'questions' wrapper.\n"
        "- JSON objects must match this shape (example values are illustrative):\n"
        f"{inner_example}\n\n"
        "Rules per question:\n"
        "- choices: exactly 4 strings.\n"
        "- answer_index: integer 0..3.\n"
        "- section, level, category must match the session values above.\n"
        f"- Aim for {num_questions} questions; if you must stop early, still keep valid blocks.\n"
    )


def questions_stream_topoff_prompt(
    *,
    section: QuestionSection,
    level: JLPTLevel,
    category: str,
    remaining: int,
    explanation_locale: str,
    avoid_prompt_snippets: list[str],
) -> str:
    one = _single_question_shape_example(
        section=section,
        level=level,
        category=category,
        explanation_locale=explanation_locale,
    )
    inner_example = json.dumps(one, ensure_ascii=False)
    snippets = "\n".join(f"- {s[:200]}" for s in avoid_prompt_snippets[:12])
    base = (
        "You are generating additional ORIGINAL JLPT-style practice questions "
        f"to complete a session ({remaining} more needed).\n"
        "Do NOT copy or closely paraphrase any real JLPT or copyrighted prep questions.\n"
        "Do NOT repeat or lightly rephrase questions similar to these stems/snippets:\n"
        f"{snippets if snippets else '(none)'}\n\n"
        f"Section: {section.value}\n"
        f"Level: {level.value}\n"
        f"Category: {category}\n\n"
    )
    listening_rules = (
        "Listening-specific rules:\n"
        "- Each prompt must include BOTH context/story and an explicit question line.\n"
        "- Prefer formatting the question line as '問題：...'.\n"
        "- NO blanks/穴埋め ('____', '＿', '（　）').\n"
        "- Include metadata.story_transcript + metadata.question_transcript.\n"
        "- metadata.listening_transcript must match prompt.\n\n"
        if section == QuestionSection.listening
        else ""
    )
    return (
        base
        + listening_rules
        + f"Explanations must be entirely in {explanation_locale}.\n"
        + f"{_EXPLANATION_RULES}\n"
        + "OUTPUT FORMAT:\n"
        + f"Use {QUESTION_START} ... JSON object ... {QUESTION_END} for each question.\n"
        + f"Emit exactly {remaining} complete blocks if possible.\n"
        + f"JSON shape example:\n{inner_example}\n"
    )


def questions_batch_repair_prompt(
    *,
    bad_output: str,
    expected_count: int,
    section: QuestionSection,
    level: JLPTLevel,
    category: str,
    explanation_locale: str,
) -> str:
    one = _single_question_shape_example(
        section=section,
        level=level,
        category=category,
        explanation_locale=explanation_locale,
    )
    return (
        "You previously returned invalid JSON for a batch of questions.\n"
        "Return ONLY valid JSON. Do not include markdown code fences.\n"
        f"Top-level object must have key 'questions' with an array of exactly {expected_count} objects.\n"
        f"Each object must include: section, level, category, prompt, choices (4), answer_index, explanation, metadata.\n"
        f"Stems and choices in Japanese; explanations in {explanation_locale}.\n"
        f"section={section.value}, level={level.value}, category={category}.\n\n"
        "Shape reminder (one object):\n"
        f"{json.dumps(one, ensure_ascii=False)}\n\n"
        "Invalid output:\n"
        f"{bad_output}\n"
    )


def final_analysis_prompt(*, session: SessionRun, output_language_name: str) -> str:
    summary = session.score_summary()
    attempts = [
        {
            "question_id": str(a.question_id),
            "selected_index": a.selected_index,
            "is_correct": a.is_correct,
        }
        for a in session.attempts
    ]

    payload = {
        "section": session.section.value,
        "level": session.level.value,
        "category": session.category,
        "summary": summary,
        "attempts": attempts,
        "num_questions": session.num_questions,
    }

    return (
        "You are a Japanese language coach.\n"
        "Analyze the user's performance on JLPT-style practice questions and provide actionable feedback.\n"
        f"Write the ENTIRE response in {output_language_name} only (no other languages).\n"
        "Focus on strengths, weaknesses, and next study steps.\n"
        "Keep it structured and readable.\n"
        "Respond in Markdown only (no JSON): use ## headings, bullet lists, and **bold** for emphasis where helpful.\n"
        "Do not wrap the reply in a code fence.\n\n"
        "User session data:\n"
        f"{json.dumps(payload, ensure_ascii=False)}\n"
    )

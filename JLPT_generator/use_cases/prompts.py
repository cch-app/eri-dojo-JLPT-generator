from __future__ import annotations

import json

from JLPT_generator.domain import JLPTLevel, QuestionSection, SessionRun

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
    schema = {
        "section": section.value,
        "level": level.value,
        "category": category,
        "prompt": "string (the question stem, in Japanese)",
        "choices": ["string", "string", "string", "string"],
        "answer_index": 0,
        "explanation": "string (detailed; see rules below)",
        "metadata": {"tags": ["optional", "strings"], "difficulty": "optional"},
    }

    return (
        "You are generating ORIGINAL JLPT-style practice questions.\n"
        "Do NOT copy or closely paraphrase any real JLPT or copyrighted prep questions.\n"
        "First infer high-level patterns for the requested level/section/category, then create a new question.\n\n"
        f"Section: {section.value}\n"
        f"Level: {level.value}\n"
        f"Category: {category}\n\n"
        f"The question stem and all four choices must be in Japanese (authentic JLPT-style).\n"
        f"The 'explanation' must be written entirely in {explanation_locale} "
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
    return {
        "section": section.value,
        "level": level.value,
        "category": category,
        "prompt": "string (stem in Japanese)",
        "choices": ["string", "string", "string", "string"],
        "answer_index": 0,
        "explanation": f"string (detailed explanation in {explanation_locale})",
        "metadata": {"tags": ["optional"], "difficulty": "optional"},
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
        f"Each item's 'explanation' must be written entirely in {explanation_locale}.\n\n"
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

from __future__ import annotations

import datetime
from typing import Optional

import reflex as rx

from JLPT_generator.adapters.ai import OllamaSdkProvider
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
    category_option_labels,
    explanation_locale_name,
    final_analysis_language_name,
    label_for_category,
    label_for_section,
    language_option_labels,
    locale_label_for_code,
    map_browser_language,
    parse_category_label,
    parse_locale_label,
    parse_section_label,
    section_option_labels,
    translate,
)
from JLPT_generator.use_cases.batch_questions import parse_questions_batch_json
from JLPT_generator.use_cases.prompts import (
    final_analysis_prompt,
    questions_batch_generation_prompt,
    questions_batch_repair_prompt,
)


def _provider() -> OllamaSdkProvider:
    return OllamaSdkProvider.from_env()


MAX_NUM_QUESTIONS = 20

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

NUM_QUESTION_OPTIONS = [str(i) for i in range(1, MAX_NUM_QUESTIONS + 1)]

# --- Shared UI tokens (warm, bright, consistent radius / border / shadow / focus) ---
_RADIUS_CARD = "rounded-xl"
_RADIUS_FIELD = "rounded-xl"

_BORDER_WARM = "border-2 border-sky-200"
_BORDER_FIELD = "border-2 border-sky-300"

_SHADOW_CARD = "shadow-md shadow-sky-200/45"
_SHADOW_PRIMARY = "shadow-md shadow-sky-400/45"

_RING_FOCUS = (
    "focus-visible:ring-2 focus-visible:ring-sky-400 focus-visible:ring-offset-2"
)
_RING_FOCUS_WITHIN = (
    "focus-within:ring-2 focus-within:ring-sky-400 focus-within:ring-offset-0"
)

# Radix Select.Trigger: force white; list is portaled (trigger only under this root).
_SETUP_SELECT_CLASS = (
    f"w-full {_RADIUS_FIELD} {_BORDER_FIELD} bg-white text-slate-800 shadow-sm "
    "[&_button]:!bg-white [&_button]:!text-slate-800 "
    "[&_button]:hover:!bg-sky-50 [&_button]:active:!bg-sky-100 "
    "[&_button]:border-0 [&_button]:shadow-none "
    f"{_RING_FOCUS_WITHIN} focus-visible:outline-none"
)
_SETUP_SELECT_PROPS = {
    "variant": "classic",
    "color_scheme": "sky",
    "class_name": _SETUP_SELECT_CLASS,
}
_CARD_CLASS = (
    f"p-6 bg-white/90 {_BORDER_WARM} {_SHADOW_CARD} {_RADIUS_CARD}"
)
_SHELL_CLASS = (
    "mx-auto max-w-3xl px-4 py-10 min-h-screen flex flex-col "
    "bg-gradient-to-br from-sky-100/90 via-sky-50 to-white"
)
_BTN_PRIMARY = (
    "w-full bg-sky-600 hover:bg-sky-500 active:bg-sky-700 text-white font-semibold "
    f"border-0 {_SHADOW_PRIMARY} {_RING_FOCUS}"
)
_BTN_OUTLINE = (
    f"w-full {_BORDER_FIELD} text-slate-800 hover:bg-sky-50 hover:border-sky-500 "
    f"bg-white font-medium {_RING_FOCUS}"
)

_CHOICE_BTN_UNSELECTED = (
    f"w-full justify-start {_RADIUS_FIELD} {_BORDER_FIELD} bg-white "
    "text-left text-slate-800 hover:bg-sky-50 hover:border-sky-500"
)
_CHOICE_BTN_SELECTED = (
    f"w-full justify-start {_RADIUS_FIELD} border-2 border-sky-600 bg-sky-200 "
    f"text-left text-slate-800 font-semibold {_SHADOW_CARD}"
)

# Warm ink on light surfaces (no dark panel fills)
_TEXT_APP_TITLE = "text-2xl font-semibold text-sky-900 tracking-tight"
_TEXT_TAGLINE = "text-sm text-slate-600 leading-relaxed"
_TEXT_LABEL = "text-sm font-medium text-slate-700"
_TEXT_BODY_LG = "text-lg font-medium text-slate-800 leading-relaxed"
_TEXT_BODY = "text-sm text-slate-700 leading-relaxed"
_TEXT_STRONG = "text-sm font-semibold text-sky-900"
_TEXT_HEADING = "text-xl font-semibold text-sky-900"
_TEXT_MUTED = "text-sm text-slate-500"
_TEXT_ERROR = "text-sm font-medium text-rose-600"
_SKELETON_CLASS = (
    f"{_RADIUS_FIELD} bg-gradient-to-r from-sky-100 via-sky-50 to-sky-100 "
    "animate-pulse"
)

_MARKDOWN_PANEL_CLASS = (
    f"mt-2 min-h-[120px] w-full {_RADIUS_CARD} {_BORDER_FIELD} "
    "bg-gradient-to-b from-white via-sky-50/60 to-sky-50/30 "
    "p-4 text-sm leading-relaxed text-slate-800 "
    "[&_h1]:mb-2 [&_h1]:text-lg [&_h1]:font-semibold [&_h1]:text-sky-900 "
    "[&_h2]:mb-2 [&_h2]:mt-4 [&_h2]:text-base [&_h2]:font-semibold [&_h2]:text-sky-900 "
    "[&_li]:ml-4 [&_li]:list-disc [&_ul]:my-2 [&_ol]:my-2 "
    "[&_p]:my-2 [&_strong]:font-semibold [&_strong]:text-sky-900 "
    "[&_code]:rounded [&_code]:bg-sky-100 [&_code]:px-1 [&_code]:py-0.5 "
    "[&_code]:text-slate-700"
)


class AppState(rx.State):
    ui_locale: str = "en"
    locale_user_locked: bool = False

    section: str = QuestionSection.reading.value
    level: str = JLPTLevel.n5.value
    category: str = READING_CATEGORIES[0]
    num_questions: int = 10

    run_questions: list[dict] = []
    run_attempts: list[dict] = []
    final_analysis: str = ""
    analysis_stream: str = ""
    analyzing_session: bool = False

    current_index: int = 0
    current_question_id: str = ""
    current_prompt: str = ""
    current_choices: list[str] = []
    current_answer_index: int = 0
    current_explanation: str = ""

    selected_index: Optional[int] = None
    revealed: bool = False
    loading: bool = False
    error: Optional[str] = None

    @rx.var(cache=True)
    def selected_value(self) -> str:
        return "" if self.selected_index is None else str(self.selected_index)

    @rx.var(cache=True)
    def progress_text(self) -> str:
        return f"{self.current_index + 1}/{self.num_questions}"

    @rx.var(cache=True)
    def score_text(self) -> str:
        total = len(self.run_attempts)
        correct = sum(1 for a in self.run_attempts if a.get("is_correct"))
        return f"{correct}/{total}"

    @rx.var(cache=True)
    def has_question(self) -> bool:
        return 0 <= self.current_index < len(self.run_questions) and bool(
            self.current_question_id
        )

    @rx.var(cache=True)
    def is_last_question(self) -> bool:
        return self.current_index >= self.num_questions - 1

    @rx.var(cache=True)
    def correct_label(self) -> str:
        return ["A", "B", "C", "D"][self.current_answer_index]

    @rx.var(cache=True)
    def categories(self) -> list[str]:
        # return (
        #     READING_CATEGORIES
        #     if self.section == QuestionSection.reading.value
        #     else LISTENING_CATEGORIES
        # )
        # Listening is temporarily disabled (no audio playback yet).
        return READING_CATEGORIES

    @rx.var(cache=True)
    def next_disabled(self) -> bool:
        return not self.revealed

    @rx.var(cache=True)
    def loading_status_text(self) -> str:
        if self.analyzing_session:
            return translate(self.ui_locale, "analyzing_session")
        return translate(self.ui_locale, "generating_questions")

    @rx.var(cache=True)
    def lbl_start(self) -> str:
        return translate(self.ui_locale, "start")

    @rx.var(cache=True)
    def lbl_section(self) -> str:
        return translate(self.ui_locale, "section")

    @rx.var(cache=True)
    def lbl_level(self) -> str:
        return translate(self.ui_locale, "level")

    @rx.var(cache=True)
    def lbl_category(self) -> str:
        return translate(self.ui_locale, "category")

    @rx.var(cache=True)
    def lbl_num_questions(self) -> str:
        return translate(self.ui_locale, "num_questions")

    @rx.var(cache=True)
    def lbl_language(self) -> str:
        return translate(self.ui_locale, "language")

    @rx.var(cache=True)
    def lbl_check_answer(self) -> str:
        return translate(self.ui_locale, "check_answer")

    @rx.var(cache=True)
    def lbl_next(self) -> str:
        return translate(self.ui_locale, "next")

    @rx.var(cache=True)
    def lbl_finish(self) -> str:
        return translate(self.ui_locale, "finish")

    @rx.var(cache=True)
    def lbl_results(self) -> str:
        return translate(self.ui_locale, "results")

    @rx.var(cache=True)
    def lbl_score(self) -> str:
        return translate(self.ui_locale, "score")

    @rx.var(cache=True)
    def lbl_feedback(self) -> str:
        return translate(self.ui_locale, "feedback")

    @rx.var(cache=True)
    def lbl_download_pdf(self) -> str:
        return translate(self.ui_locale, "download_pdf")

    @rx.var(cache=True)
    def lbl_start_over(self) -> str:
        return translate(self.ui_locale, "start_over")

    @rx.var(cache=True)
    def lbl_back_setup(self) -> str:
        return translate(self.ui_locale, "back_setup")

    @rx.var(cache=True)
    def lbl_no_question_yet(self) -> str:
        return translate(self.ui_locale, "no_question_yet")

    @rx.var(cache=True)
    def lbl_go_setup(self) -> str:
        return translate(self.ui_locale, "go_setup")

    @rx.var(cache=True)
    def lbl_answer_prefix(self) -> str:
        return translate(self.ui_locale, "answer_prefix")

    @rx.var(cache=True)
    def lbl_app_title(self) -> str:
        return translate(self.ui_locale, "app_title")

    @rx.var(cache=True)
    def lbl_app_tagline(self) -> str:
        return translate(self.ui_locale, "app_tagline")

    @rx.var(cache=True)
    def lbl_no_analysis(self) -> str:
        return translate(self.ui_locale, "no_analysis")

    @rx.var(cache=True)
    def lbl_analyzing_short(self) -> str:
        return translate(self.ui_locale, "analyzing_short")

    @rx.var(cache=True)
    def language_select_items(self) -> list[str]:
        return language_option_labels(self.ui_locale)

    @rx.var(cache=True)
    def language_select_value(self) -> str:
        return locale_label_for_code(self.ui_locale, self.ui_locale)

    @rx.var(cache=True)
    def section_select_items(self) -> list[str]:
        return section_option_labels(self.ui_locale)

    @rx.var(cache=True)
    def section_select_value(self) -> str:
        return label_for_section(self.ui_locale, self.section)

    @rx.var(cache=True)
    def category_select_items(self) -> list[str]:
        return category_option_labels(self.ui_locale, list(self.categories))

    @rx.var(cache=True)
    def category_select_value(self) -> str:
        return label_for_category(self.ui_locale, self.category)

    @rx.var(cache=True)
    def badge_section_label(self) -> str:
        return label_for_section(self.ui_locale, self.section)

    @rx.var(cache=True)
    def badge_category_label(self) -> str:
        return label_for_category(self.ui_locale, self.category)

    @rx.var(cache=True)
    def results_score_line(self) -> str:
        total = len(self.run_attempts)
        correct = sum(1 for a in self.run_attempts if a.get("is_correct"))
        return f"{translate(self.ui_locale, 'score')} {correct}/{total}"

    def detect_browser_locale(self):
        return rx.call_script(
            "navigator.language || 'en'",
            callback=AppState.apply_browser_language,
        )

    def apply_browser_language(self, lang: str):
        if self.locale_user_locked:
            return
        if lang is None:
            return
        self.ui_locale = map_browser_language(str(lang))

    def set_ui_locale(self, value: str):
        self.locale_user_locked = True
        if value in SUPPORTED_LOCALES:
            self.ui_locale = value

    def set_ui_locale_from_label(self, label: str):
        code = parse_locale_label(self.ui_locale, label)
        if code:
            self.locale_user_locked = True
            self.ui_locale = code

    def set_section_from_label(self, label: str):
        value = parse_section_label(self.ui_locale, label)
        if value:
            self.set_section(value)

    def set_category_from_label(self, label: str):
        cats = (
            READING_CATEGORIES
            if self.section == QuestionSection.reading.value
            else LISTENING_CATEGORIES
        )
        resolved = parse_category_label(self.ui_locale, label, list(cats))
        if resolved:
            self.category = resolved

    def set_section(self, value: str):
        self.section = value
        self.category = (
            READING_CATEGORIES[0]
            if value == QuestionSection.reading.value
            else LISTENING_CATEGORIES[0]
        )

    def set_level(self, value: str):
        self.level = value

    def set_category(self, value: str):
        self.category = value

    def set_num_questions(self, value: str):
        try:
            self.num_questions = max(1, min(MAX_NUM_QUESTIONS, int(value)))
        except ValueError:
            self.num_questions = 10

    def apply_current_question(self) -> None:
        q = self.run_questions[self.current_index]
        self.current_question_id = str(q["id"])
        self.current_prompt = str(q["prompt"])
        self.current_choices = list(q["choices"])
        self.current_answer_index = int(q["answer_index"])
        self.current_explanation = str(q["explanation"])
        self.selected_index = None
        self.revealed = False

    def start(self):
        self.error = None
        self.run_questions = []
        self.run_attempts = []
        self.final_analysis = ""
        self.analysis_stream = ""
        self.analyzing_session = False
        self.current_index = 0
        self.current_question_id = ""
        self.current_prompt = ""
        self.current_choices = []
        self.current_answer_index = 0
        self.current_explanation = ""
        self.selected_index = None
        self.revealed = False
        self.loading = True
        return [AppState.prefetch_all_questions, rx.redirect("/test")]

    def prefetch_all_questions(self):
        self.loading = True
        self.error = None
        self.analyzing_session = False
        yield

        expl_name = explanation_locale_name(self.ui_locale)
        try:
            provider = _provider()
            prompt = questions_batch_generation_prompt(
                section=QuestionSection(self.section),
                level=JLPTLevel(self.level),
                category=self.category,
                num_questions=self.num_questions,
                explanation_locale=expl_name,
            )
            raw = provider.complete_text(prompt=prompt)
            parsed = parse_questions_batch_json(
                text=raw, expected_count=self.num_questions
            )
        except Exception as e:  # noqa: BLE001
            try:
                provider = _provider()
                repair = questions_batch_repair_prompt(
                    bad_output=str(e),
                    expected_count=self.num_questions,
                    section=QuestionSection(self.section),
                    level=JLPTLevel(self.level),
                    category=self.category,
                    explanation_locale=expl_name,
                )
                raw2 = provider.complete_text(prompt=repair)
                parsed = parse_questions_batch_json(
                    text=raw2, expected_count=self.num_questions
                )
            except Exception as e2:  # noqa: BLE001
                self.error = translate(self.ui_locale, "err_generate", detail=str(e2))
                self.loading = False
                return

        self.run_questions = parsed
        self.current_index = 0
        self.apply_current_question()
        self.loading = False

    def select_choice(self, value: str):
        try:
            self.selected_index = int(value)
        except ValueError:
            self.selected_index = None

    def submit_answer(self):
        if not self.current_question_id:
            return
        if self.selected_index is None:
            self.error = translate(self.ui_locale, "err_select_first")
            return

        self.error = None
        is_correct = self.selected_index == self.current_answer_index
        self.run_attempts.append(
            {
                "question_id": self.current_question_id,
                "selected_index": self.selected_index,
                "is_correct": is_correct,
            }
        )
        self.revealed = True

    def next(self):
        if not self.revealed:
            self.error = translate(self.ui_locale, "err_check_first")
            return

        if self.current_index >= self.num_questions - 1:
            return AppState.finish
        self.current_index += 1
        self.apply_current_question()

    def finish(self):
        self.loading = True
        self.analyzing_session = True
        self.error = None
        self.analysis_stream = ""
        yield

        try:
            session = SessionRun(
                section=QuestionSection(self.section),
                level=JLPTLevel(self.level),
                category=self.category,
                num_questions=self.num_questions,
                questions=[Question.model_validate(q) for q in self.run_questions],
                attempts=[
                    Attempt.model_validate(a)
                    for a in self.run_attempts
                    if a.get("question_id")
                ],
            )
            provider = _provider()
            lang = final_analysis_language_name(self.ui_locale)
            analysis_prompt = final_analysis_prompt(
                session=session, output_language_name=lang
            )
            for i, delta in enumerate(provider.stream_text(prompt=analysis_prompt)):
                self.analysis_stream += delta
                if i % 8 == 0:
                    yield
            self.final_analysis = self.analysis_stream.strip()
        except Exception as e:  # noqa: BLE001
            self.error = translate(self.ui_locale, "err_analyze", detail=str(e))
        finally:
            self.loading = False
            self.analyzing_session = False

        return rx.redirect("/results")

    def download_feedback_pdf(self):
        if not self.final_analysis.strip():
            self.error = translate(self.ui_locale, "err_no_feedback_pdf")
            return
        try:
            title = translate(self.ui_locale, "feedback")
            data = build_feedback_pdf_bytes(
                title=title,
                markdown_body=self.final_analysis,
                subtitle_line=self.results_score_line,
                generated_on=translate(
                    self.ui_locale,
                    "pdf_generated",
                    date=datetime.date.today().isoformat(),
                ),
            )
            fn = f"jlpt-feedback-{datetime.date.today().isoformat()}.pdf"
            return rx.download(data=data, filename=fn)
        except Exception as e:  # noqa: BLE001
            self.error = str(e)

    def restart(self):
        self.run_questions = []
        self.run_attempts = []
        self.final_analysis = ""
        self.analysis_stream = ""
        self.analyzing_session = False
        self.current_question_id = ""
        self.current_prompt = ""
        self.current_choices = []
        self.current_answer_index = 0
        self.current_explanation = ""
        self.selected_index = None
        self.revealed = False
        self.loading = False
        self.error = None
        return rx.redirect("/")


def _shell(*children: rx.Component) -> rx.Component:
    start_year = 2026
    current_year = datetime.date.today().year
    year_text = (
        f"© {start_year} Eri Dojo. All rights reserved."
        if current_year == start_year
        else f"© {start_year}-{current_year} Eri Dojo. All rights reserved."
    )
    return rx.box(
        rx.box(
            rx.hstack(
                rx.image(
                    src="/favicon.png",
                    alt="JLPT Mock Generator icon",
                    class_name="h-20 w-20 shrink-0",
                ),
                rx.heading(
                    AppState.lbl_app_title,
                    class_name=_TEXT_APP_TITLE,
                ),
                class_name="items-center gap-3",
            ),
            rx.text(
                AppState.lbl_app_tagline,
                class_name=_TEXT_TAGLINE,
            ),
            class_name="space-y-1",
        ),
        rx.box(*children, class_name="mt-6"),
        rx.box(
            rx.text(
                year_text,
                class_name=_TEXT_MUTED,
            ),
            class_name="mt-auto pt-10 pb-2 mx-auto",
        ),
        class_name=_SHELL_CLASS,
    )


def setup_page() -> rx.Component:
    return rx.box(
        _shell(
            rx.cond(
                AppState.loading,
                _test_loading_view(),
                rx.card(
                    rx.vstack(
                        rx.box(
                            rx.text(
                                AppState.lbl_language,
                                class_name=_TEXT_LABEL,
                            ),
                            rx.select(
                                AppState.language_select_items,
                                value=AppState.language_select_value,
                                on_change=AppState.set_ui_locale_from_label,
                                **_SETUP_SELECT_PROPS,
                            ),
                            class_name="space-y-1 w-full",
                        ),
                        rx.hstack(
                            rx.box(
                                rx.text(
                                    AppState.lbl_section,
                                    class_name=_TEXT_LABEL,
                                ),
                                rx.select(
                                    AppState.section_select_items,
                                    value=AppState.section_select_value,
                                    on_change=AppState.set_section_from_label,
                                    **_SETUP_SELECT_PROPS,
                                ),
                                class_name="w-full space-y-1",
                            ),
                            rx.box(
                                rx.text(
                                    AppState.lbl_level,
                                    class_name=_TEXT_LABEL,
                                ),
                                rx.select(
                                    [l.value for l in JLPTLevel],
                                    value=AppState.level,
                                    on_change=AppState.set_level,
                                    **_SETUP_SELECT_PROPS,
                                ),
                                class_name="w-full space-y-1",
                            ),
                            class_name="gap-4",
                        ),
                        rx.box(
                            rx.text(
                                AppState.lbl_category,
                                class_name=_TEXT_LABEL,
                            ),
                            rx.select(
                                AppState.category_select_items,
                                value=AppState.category_select_value,
                                on_change=AppState.set_category_from_label,
                                **_SETUP_SELECT_PROPS,
                            ),
                            class_name="space-y-1",
                        ),
                        rx.box(
                            rx.text(
                                AppState.lbl_num_questions,
                                class_name=_TEXT_LABEL,
                            ),
                            rx.select(
                                NUM_QUESTION_OPTIONS,
                                value=AppState.num_questions.to_string(),
                                on_change=AppState.set_num_questions,
                                **_SETUP_SELECT_PROPS,
                            ),
                            class_name="space-y-1 white",
                        ),
                        rx.cond(
                            AppState.error,
                            rx.text(AppState.error, class_name=_TEXT_ERROR),
                        ),
                        rx.button(
                            AppState.lbl_start,
                            on_click=AppState.start,
                            disabled=AppState.loading,
                            class_name=_BTN_PRIMARY,
                        ),
                        spacing="4",
                    ),
                    class_name=_CARD_CLASS,
                ),
            ),
        ),
        on_mount=AppState.detect_browser_locale,
        class_name="bg-gradient-to-br from-sky-100/90 via-sky-50 to-white",
    )


def _test_loading_view() -> rx.Component:
    return rx.center(
        rx.card(
            rx.vstack(
                rx.spinner(size="3", color_scheme="sky"),
                rx.text(
                    AppState.loading_status_text,
                    class_name=_TEXT_LABEL,
                ),
                rx.vstack(
                    rx.skeleton(class_name=f"h-6 w-full {_SKELETON_CLASS}"),
                    rx.skeleton(class_name=f"h-6 w-[92%] {_SKELETON_CLASS}"),
                    rx.skeleton(class_name=f"h-4 w-full {_SKELETON_CLASS}"),
                    rx.skeleton(class_name=f"h-4 w-4/5 {_SKELETON_CLASS}"),
                    rx.box(class_name="h-2"),
                    rx.skeleton(class_name=f"h-11 w-full {_SKELETON_CLASS}"),
                    rx.skeleton(class_name=f"h-11 w-full {_SKELETON_CLASS}"),
                    rx.skeleton(class_name=f"h-11 w-full {_SKELETON_CLASS}"),
                    rx.skeleton(class_name=f"h-11 w-full {_SKELETON_CLASS}"),
                    spacing="2",
                    class_name="mt-4 w-full",
                ),
                spacing="3",
                class_name="w-full items-center",
            ),
            class_name=f"w-full max-w-2xl {_CARD_CLASS}",
        ),
        class_name="py-10",
    )


def _test_question_card() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.badge(
                    AppState.badge_section_label,
                    variant="soft",
                    color_scheme="sky",
                ),
                rx.badge(AppState.level, variant="soft", color_scheme="sky"),
                rx.badge(
                    AppState.badge_category_label,
                    variant="soft",
                    color_scheme="sky",
                ),
                rx.spacer(),
                rx.text(
                    AppState.progress_text,
                    class_name=_TEXT_LABEL,
                ),
                class_name="items-center gap-2",
            ),
            rx.text(
                AppState.current_prompt,
                class_name=_TEXT_BODY_LG,
            ),
            rx.vstack(
                rx.button(
                    "A. " + AppState.current_choices[0],
                    on_click=AppState.select_choice("0"),
                    variant="outline",
                    class_name=rx.cond(
                        AppState.selected_value == "0",
                        _CHOICE_BTN_SELECTED,
                        _CHOICE_BTN_UNSELECTED,
                    ),
                ),
                rx.button(
                    "B. " + AppState.current_choices[1],
                    on_click=AppState.select_choice("1"),
                    variant="outline",
                    class_name=rx.cond(
                        AppState.selected_value == "1",
                        _CHOICE_BTN_SELECTED,
                        _CHOICE_BTN_UNSELECTED,
                    ),
                ),
                rx.button(
                    "C. " + AppState.current_choices[2],
                    on_click=AppState.select_choice("2"),
                    variant="outline",
                    class_name=rx.cond(
                        AppState.selected_value == "2",
                        _CHOICE_BTN_SELECTED,
                        _CHOICE_BTN_UNSELECTED,
                    ),
                ),
                rx.button(
                    "D. " + AppState.current_choices[3],
                    on_click=AppState.select_choice("3"),
                    variant="outline",
                    class_name=rx.cond(
                        AppState.selected_value == "3",
                        _CHOICE_BTN_SELECTED,
                        _CHOICE_BTN_UNSELECTED,
                    ),
                ),
                class_name="w-full gap-2",
            ),
            rx.cond(
                AppState.revealed,
                rx.box(
                    rx.divider(color_scheme="sky"),
                    rx.text(
                        AppState.lbl_answer_prefix
                        + " "
                        + AppState.correct_label
                        + " ("
                        + AppState.current_choices[AppState.current_answer_index]
                        + ")",
                        class_name=_TEXT_STRONG,
                    ),
                    rx.text(
                        AppState.current_explanation,
                        class_name=_TEXT_BODY,
                    ),
                    class_name="space-y-2",
                ),
            ),
            rx.cond(
                AppState.error,
                rx.text(AppState.error, class_name=_TEXT_ERROR),
            ),
            rx.hstack(
                rx.button(
                    AppState.lbl_check_answer,
                    on_click=AppState.submit_answer,
                    disabled=AppState.revealed,
                    variant="solid",
                    class_name=_BTN_PRIMARY,
                ),
                rx.button(
                    rx.cond(
                        AppState.is_last_question,
                        AppState.lbl_finish,
                        AppState.lbl_next,
                    ),
                    on_click=AppState.next,
                    disabled=AppState.next_disabled,
                    variant="outline",
                    class_name=_BTN_OUTLINE,
                ),
                class_name="gap-3",
            ),
            spacing="4",
        ),
        class_name=_CARD_CLASS,
    )


def test_page() -> rx.Component:
    return _shell(
        rx.cond(
            AppState.loading,
            _test_loading_view(),
            rx.cond(
                AppState.has_question,
                _test_question_card(),
                rx.center(
                    rx.vstack(
                        rx.text(
                            AppState.lbl_no_question_yet,
                            class_name=_TEXT_BODY,
                        ),
                        rx.link(
                            rx.button(
                                AppState.lbl_go_setup,
                                variant="outline",
                                class_name=_BTN_OUTLINE,
                            ),
                            href="/",
                        ),
                        spacing="3",
                    ),
                    class_name="py-20",
                ),
            ),
        ),
    )


def results_page() -> rx.Component:
    return _shell(
        rx.card(
            rx.vstack(
                rx.heading(
                    AppState.lbl_results,
                    class_name=_TEXT_HEADING,
                ),
                rx.box(
                    rx.text(
                        AppState.results_score_line,
                        class_name=_TEXT_LABEL,
                    ),
                    class_name="space-y-2",
                ),
                rx.cond(
                    AppState.final_analysis,
                    rx.box(
                        rx.text(
                            AppState.lbl_feedback,
                            class_name=_TEXT_STRONG,
                        ),
                        rx.box(
                            rx.markdown(
                                AppState.final_analysis,
                                use_raw=False,
                            ),
                            class_name=_MARKDOWN_PANEL_CLASS,
                        ),
                        rx.button(
                            AppState.lbl_download_pdf,
                            on_click=AppState.download_feedback_pdf,
                            variant="outline",
                            class_name=f"mt-2 {_BTN_OUTLINE}",
                        ),
                        class_name="space-y-2",
                    ),
                    rx.text(
                        rx.cond(
                            AppState.analysis_stream,
                            AppState.lbl_analyzing_short,
                            AppState.lbl_no_analysis,
                        ),
                        class_name=_TEXT_MUTED,
                    ),
                ),
                rx.cond(
                    AppState.error,
                    rx.text(AppState.error, class_name=_TEXT_ERROR),
                ),
                rx.hstack(
                    rx.link(
                        rx.button(
                            AppState.lbl_start_over,
                            on_click=AppState.restart,
                            class_name=_BTN_PRIMARY,
                        ),
                        href="#",
                    ),
                    rx.link(
                        rx.button(
                            AppState.lbl_back_setup,
                            variant="outline",
                            class_name=_BTN_OUTLINE,
                        ),
                        href="/",
                    ),
                    class_name="gap-3",
                ),
                spacing="4",
            ),
            class_name=_CARD_CLASS,
        ),
    )


app = rx.App(
    theme=rx.theme(
        appearance="light",
        accent_color="sky",
        gray_color="slate",
        panel_background="solid",
        radius="large",
        has_background=True,
    ),
    head_components=[
        rx.el.link(rel="icon", type="image/png", href="/favicon.png"),
        rx.el.link(rel="apple-touch-icon", href="/favicon.png"),
        rx.el.meta(name="color-scheme", content="light"),
        rx.el.meta(name="supported-color-schemes", content="light"),
        rx.script(
            """
            (function () {
              function forceLight(el) {
                if (!el) return;
                if (el.classList && el.classList.contains("dark")) el.classList.remove("dark");
                var attrs = [
                  "data-theme",
                  "data-color-scheme",
                  "data-radix-color-scheme",
                  "data-appearance",
                ];
                for (var i = 0; i < attrs.length; i++) {
                  var k = attrs[i];
                  if (el.getAttribute && el.getAttribute(k) === "dark") el.setAttribute(k, "light");
                }
              }

              function apply() {
                forceLight(document.documentElement);
                document.documentElement.style.colorScheme = "light";
                var nodes = document.querySelectorAll(".radix-themes, [data-theme], [data-color-scheme], [data-radix-color-scheme], [data-appearance]");
                for (var i = 0; i < nodes.length; i++) forceLight(nodes[i]);
              }

              apply();
              if (document.readyState === "loading") {
                document.addEventListener("DOMContentLoaded", apply, { once: true });
              }

              var obs = new MutationObserver(function () { apply(); });
              obs.observe(document.documentElement, { attributes: true, subtree: true, attributeFilter: ["class", "data-theme", "data-color-scheme", "data-radix-color-scheme", "data-appearance"] });
            })();
            """.strip()
        ),
    ],
)
app.add_page(setup_page, route="/", title="JLPT Mock Generator")
app.add_page(test_page, route="/test", title="JLPT Mock Generator - Test")
app.add_page(results_page, route="/results", title="JLPT Mock Generator - Results")

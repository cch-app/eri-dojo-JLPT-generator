from __future__ import annotations

from JLPT_generator.domain import QuestionSection

SUPPORTED_LOCALES = ("en", "ja", "zh_TW")

_STRINGS: dict[str, dict[str, str]] = {
    "en": {
        "app_title": "JLPT Mock Generator",
        "app_tagline": "Generate original JLPT-style questions (Reading/Listening) and get a strengths/weaknesses summary.",
        "language": "Language",
        "section": "Section",
        "level": "Level",
        "category": "Category",
        "num_questions": "Number of questions",
        "start": "Start",
        "generating_questions": "Generating questions…",
        "analyzing_session": "Analyzing your session…",
        "check_answer": "Check answer",
        "next": "Next",
        "finish": "Finish",
        "answer_prefix": "Answer:",
        "results": "Results",
        "score": "Score:",
        "feedback": "Feedback",
        "download_pdf": "Download PDF",
        "start_over": "Start over",
        "back_setup": "Back to setup",
        "no_question_yet": "No question yet. Start a session first.",
        "go_setup": "Go to setup",
        "err_select_first": "Select an answer first.",
        "err_check_first": "Check the answer first.",
        "err_generate": "Failed to generate questions: {detail}",
        "err_analyze": "Failed to analyze performance: {detail}",
        "err_no_feedback_pdf": "No feedback to download yet.",
        "no_analysis": "No analysis yet. (If the AI call failed, check the error on the test page.)",
        "analyzing_short": "Analyzing…",
        "lang_en": "English",
        "lang_ja": "日本語",
        "lang_zh_TW": "繁體中文",
        "section_reading": "Reading",
        "section_listening": "Listening",
        "cat_grammar": "Grammar",
        "cat_vocabulary": "Vocabulary",
        "cat_reading_comprehension": "Reading comprehension",
        "cat_task_based": "Task-based",
        "cat_point_comprehension": "Point comprehension",
        "cat_listening_comprehension": "Listening comprehension",
        "pdf_generated": "Generated: {date}",
        "stream_planned_total": "planned",
        "stream_more_coming": "More questions loading…",
        "err_wait_more_questions": "More questions are still being generated. Please wait a moment.",
        "audio": "Audio",
        "play_audio": "Play audio",
        "audio_unavailable": "Audio unavailable.",
        "transcript": "Transcript",
        "max_num_questions": "Max 10",
    },
    "ja": {
        "app_title": "JLPT模擬問題ジェネレーター",
        "app_tagline": "オリジナルのJLPT形式問題（読解・聴解）を出題し、最後に強み・弱点のフィードバックを表示します。",
        "language": "言語",
        "section": "セクション",
        "level": "レベル",
        "category": "カテゴリ",
        "num_questions": "問題数",
        "start": "開始",
        "generating_questions": "問題を生成しています…",
        "analyzing_session": "セッションを分析しています…",
        "check_answer": "答え合わせ",
        "next": "次へ",
        "finish": "終了",
        "answer_prefix": "正解:",
        "results": "結果",
        "score": "スコア:",
        "feedback": "フィードバック",
        "download_pdf": "PDFをダウンロード",
        "start_over": "最初から",
        "back_setup": "設定に戻る",
        "no_question_yet": "まだ問題がありません。セッションを開始してください。",
        "go_setup": "設定へ",
        "err_select_first": "先に選択肢を選んでください。",
        "err_check_first": "先に答え合わせをしてください。",
        "err_generate": "問題の生成に失敗しました: {detail}",
        "err_analyze": "分析に失敗しました: {detail}",
        "err_no_feedback_pdf": "ダウンロードできるフィードバックがありません。",
        "no_analysis": "まだ分析がありません。（エラーの場合はテストページを確認してください。）",
        "analyzing_short": "分析中…",
        "lang_en": "English",
        "lang_ja": "日本語",
        "lang_zh_TW": "繁體中文",
        "section_reading": "読解",
        "section_listening": "聴解",
        "cat_grammar": "文法",
        "cat_vocabulary": "語彙",
        "cat_reading_comprehension": "読解（文章）",
        "cat_task_based": "課題理解",
        "cat_point_comprehension": "ポイント理解",
        "cat_listening_comprehension": "聴解（概要）",
        "pdf_generated": "作成日: {date}",
        "stream_planned_total": "問予定",
        "stream_more_coming": "他の問題を読み込み中…",
        "err_wait_more_questions": "まだ問題を生成しています。少し待ってからお試しください。",
        "audio": "音声",
        "play_audio": "音声を再生",
        "audio_unavailable": "音声が利用できません。",
        "transcript": "写し",
        "max_num_questions": "最大10問",
    },
    "zh_TW": {
        "app_title": "JLPT 模擬試題產生器",
        "app_tagline": "產生原創 JLPT 風格題目（讀解／聽解），完成後提供強弱項回饋摘要。",
        "language": "介面語言",
        "section": "類型",
        "level": "級別",
        "category": "類別",
        "num_questions": "題數",
        "start": "開始",
        "generating_questions": "正在產生題目…",
        "analyzing_session": "正在分析作答結果…",
        "check_answer": "對答案",
        "next": "下一題",
        "finish": "完成",
        "answer_prefix": "答案：",
        "results": "結果",
        "score": "分數：",
        "feedback": "回饋",
        "download_pdf": "下載 PDF",
        "start_over": "重新開始",
        "back_setup": "返回設定",
        "no_question_yet": "尚無題目。請先開始測驗。",
        "go_setup": "前往設定",
        "err_select_first": "請先選擇一個答案。",
        "err_check_first": "請先按「對答案」。",
        "err_generate": "無法產生題目：{detail}",
        "err_analyze": "無法分析表現：{detail}",
        "err_no_feedback_pdf": "尚無可下載的回饋內容。",
        "no_analysis": "尚無分析內容。（若 AI 呼叫失敗，請至測驗頁查看錯誤訊息。）",
        "analyzing_short": "分析中…",
        "lang_en": "English",
        "lang_ja": "日本語",
        "lang_zh_TW": "繁體中文",
        "section_reading": "讀解",
        "section_listening": "聽解",
        "cat_grammar": "文法",
        "cat_vocabulary": "詞彙",
        "cat_reading_comprehension": "讀解（文章）",
        "cat_task_based": "課題理解",
        "cat_point_comprehension": "重點理解",
        "cat_listening_comprehension": "聽解（概要）",
        "pdf_generated": "產生日期：{date}",
        "stream_planned_total": "題預定",
        "stream_more_coming": "仍在載入更多題目…",
        "err_wait_more_questions": "題目仍在產生中，請稍候再試。",
        "audio": "音檔",
        "play_audio": "播放音檔",
        "audio_unavailable": "音檔無法播放。",
        "transcript": "文字記錄",
        "max_num_questions": "最多10題",
    },
}


def translate(locale: str, key: str, **kwargs: str) -> str:
    loc = locale if locale in SUPPORTED_LOCALES else "en"
    template = _STRINGS.get(loc, _STRINGS["en"]).get(key, _STRINGS["en"].get(key, key))
    if kwargs:
        return template.format(**kwargs)
    return template


def map_browser_language(raw: str | None) -> str:
    if not raw or not isinstance(raw, str):
        return "en"
    low = raw.strip().lower().replace("_", "-")
    if low.startswith("zh-tw") or "hant" in low or low.startswith("zh-hk"):
        return "zh_TW"
    if low.startswith("ja"):
        return "ja"
    return "en"


def label_for_section(locale: str, section_value: str) -> str:
    return translate(locale, f"section_{section_value}")


def label_for_category(locale: str, category_id: str) -> str:
    return translate(locale, f"cat_{category_id}")


def language_option_labels(locale: str) -> list[str]:
    loc = locale if locale in SUPPORTED_LOCALES else "en"
    return [translate(loc, f"lang_{code}") for code in SUPPORTED_LOCALES]


def locale_label_for_code(locale: str, code: str) -> str:
    return translate(locale, f"lang_{code}")


def parse_locale_label(locale: str, label: str) -> str | None:
    loc = locale if locale in SUPPORTED_LOCALES else "en"
    for code in SUPPORTED_LOCALES:
        if translate(loc, f"lang_{code}") == label:
            return code
    return None


def section_option_labels(locale: str) -> list[str]:
    loc = locale if locale in SUPPORTED_LOCALES else "en"
    return [translate(loc, f"section_{s.value}") for s in QuestionSection]


def parse_section_label(locale: str, label: str) -> str | None:
    loc = locale if locale in SUPPORTED_LOCALES else "en"
    for s in QuestionSection:
        if translate(loc, f"section_{s.value}") == label:
            return s.value
    return None


def category_option_labels(locale: str, category_ids: list[str]) -> list[str]:
    return [label_for_category(locale, c) for c in category_ids]


def parse_category_label(
    locale: str, label: str, category_ids: list[str]
) -> str | None:
    for c in category_ids:
        if label_for_category(locale, c) == label:
            return c
    return None


def explanation_locale_name(locale: str) -> str:
    match locale:
        case "ja":
            return "Japanese"
        case "zh_TW":
            return "Traditional Chinese (Taiwan)"
        case _:
            return "English"


def final_analysis_language_name(locale: str) -> str:
    match locale:
        case "ja":
            return "Japanese"
        case "zh_TW":
            return "Traditional Chinese (Taiwan standard)"
        case _:
            return "English"

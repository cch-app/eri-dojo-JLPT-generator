import pytest

from JLPT_generator.domain import QuestionSection
from JLPT_generator.i18n.strings import (
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


@pytest.mark.unit
def test_map_browser_language():
    assert map_browser_language("zh-TW") == "zh_TW"
    assert map_browser_language("ja-JP") == "ja"
    assert map_browser_language("en-US") == "en"


@pytest.mark.unit
def test_translate_fallback():
    assert "Start" in translate("en", "start")
    assert translate("bogus", "start") == translate("en", "start")


@pytest.mark.unit
def test_translate_format():
    s = translate("en", "err_generate", detail="x")
    assert "x" in s


@pytest.mark.unit
def test_language_option_labels_distinct():
    labels = language_option_labels("en")
    assert len(labels) == len(set(labels))
    assert "English" in labels


@pytest.mark.unit
def test_parse_locale_label_roundtrip():
    for loc in ("en", "ja", "zh_TW"):
        for code in ("en", "ja", "zh_TW"):
            label = locale_label_for_code(loc, code)
            assert parse_locale_label(loc, label) == code


@pytest.mark.unit
def test_section_labels_parse_roundtrip():
    for loc in ("en", "ja", "zh_TW"):
        for s in QuestionSection:
            lab = label_for_section(loc, s.value)
            assert parse_section_label(loc, lab) == s.value
        assert section_option_labels(loc) == [
            label_for_section(loc, s.value) for s in QuestionSection
        ]


@pytest.mark.unit
def test_parse_category_reading():
    ids = ["grammar", "vocabulary", "reading_comprehension"]
    for loc in ("en", "ja", "zh_TW"):
        for cid in ids:
            lab = label_for_category(loc, cid)
            assert parse_category_label(loc, lab, ids) == cid

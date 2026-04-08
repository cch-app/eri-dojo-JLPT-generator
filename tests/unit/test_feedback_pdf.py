import pytest

from JLPT_generator.adapters.pdf.feedback_pdf import build_feedback_pdf_bytes


@pytest.mark.unit
def test_build_feedback_pdf_bytes_smoke():
    data = build_feedback_pdf_bytes(
        title="Feedback",
        markdown_body="## Summary\n\nHello **world**.\n\n### Detail\n\nMore text.",
        subtitle_line="Score: 3/5",
        generated_on="Generated: 2026-01-01",
    )
    assert isinstance(data, bytes)
    assert data[:4] == b"%PDF"

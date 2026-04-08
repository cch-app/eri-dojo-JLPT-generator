from __future__ import annotations

import re
from pathlib import Path

from fpdf import FPDF
from fpdf.html import HTMLMixin

_REPO_ROOT = Path(__file__).resolve().parents[3]
_FONT_PATH = _REPO_ROOT / "assets" / "fonts" / "NotoSansTC-Regular.ttf"


def _escape_html(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _markdown_inline_to_html(text: str) -> str:
    escaped = _escape_html(text)
    # Avoid <strong>/<b> when using a single regular TTF file (no bold font variant).
    escaped = re.sub(
        r"\*\*([^*]+)\*\*", r'<font color="#0c4a6e">\1</font>', escaped
    )
    escaped = re.sub(
        r"__([^_]+)__", r'<font color="#0c4a6e">\1</font>', escaped
    )
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    return escaped


def _markdown_to_basic_html(markdown: str) -> str:
    """Convert a subset of markdown to fpdf2-friendly HTML.

    Goal: keep PDF output aligned with what the UI displays (markdown), without
    needing a full markdown engine.
    """
    md = markdown.replace("\r\n", "\n").strip("\n")
    lines = md.split("\n")

    html_parts: list[str] = []
    in_code = False
    code_buf: list[str] = []
    para_buf: list[str] = []
    in_ul = False
    in_ol = False

    def flush_para() -> None:
        nonlocal para_buf
        text = " ".join(s.strip() for s in para_buf).strip()
        if text:
            html_parts.append(f"<p>{_markdown_inline_to_html(text)}</p>")
        para_buf = []

    def close_lists() -> None:
        nonlocal in_ul, in_ol
        if in_ul:
            html_parts.append("</ul>")
            in_ul = False
        if in_ol:
            html_parts.append("</ol>")
            in_ol = False

    for raw in lines:
        line = raw.rstrip("\n")
        stripped = line.strip()

        if stripped.startswith("```"):
            if in_code:
                html_parts.append(
                    "<pre><code>" + _escape_html("\n".join(code_buf)) + "</code></pre>"
                )
                code_buf = []
                in_code = False
            else:
                flush_para()
                close_lists()
                in_code = True
            continue

        if in_code:
            code_buf.append(line)
            continue

        if not stripped:
            flush_para()
            close_lists()
            continue

        m_ol = re.match(r"^\s*(\d+)\.\s+(.*)$", line)
        m_ul = re.match(r"^\s*[-*]\s+(.*)$", line)
        if m_ol:
            flush_para()
            if in_ul:
                html_parts.append("</ul>")
                in_ul = False
            if not in_ol:
                html_parts.append("<ol>")
                in_ol = True
            # Add a little extra vertical spacing between adjacent points.
            html_parts.append(
                f"<li>{_markdown_inline_to_html(m_ol.group(2))}<br/></li>"
            )
            continue
        if m_ul:
            flush_para()
            if in_ol:
                html_parts.append("</ol>")
                in_ol = False
            if not in_ul:
                html_parts.append("<ul>")
                in_ul = True
            # Add a little extra vertical spacing between adjacent points.
            html_parts.append(
                f"<li>{_markdown_inline_to_html(m_ul.group(1))}<br/></li>"
            )
            continue

        close_lists()
        if stripped.startswith("#"):
            flush_para()
            m_h = re.match(r"^(#{1,6})\s+(.*)$", stripped)
            if m_h:
                level = len(m_h.group(1))
                tag = f"h{min(level, 6)}"
                html_parts.append(f"<{tag}>{_markdown_inline_to_html(m_h.group(2))}</{tag}>")
                continue

        para_buf.append(stripped)

    flush_para()
    close_lists()
    if in_code:
        html_parts.append(
            "<pre><code>" + _escape_html("\n".join(code_buf)) + "</code></pre>"
        )

    return "\n".join(html_parts)


class _FeedbackPDF(HTMLMixin, FPDF):
    def __init__(self, font_family: str) -> None:
        super().__init__(orientation="P", unit="mm", format="A4")
        self._ff = font_family
        self.set_auto_page_break(auto=True, margin=18)
        self.alias_nb_pages()

    def footer(self) -> None:
        self.set_y(-14)
        self.set_font(self._ff, "", 8)
        self.set_text_color(100, 116, 139)  # slate-ish
        self.cell(0, 8, f"Page {self.page_no()}/{{nb}}", align="C")


def build_feedback_pdf_bytes(
    *,
    title: str,
    markdown_body: str,
    subtitle_line: str = "",
    generated_on: str = "",
) -> bytes:
    font_family = "NotoTC"
    use_custom = _FONT_PATH.is_file()

    pdf = _FeedbackPDF(font_family)
    pdf.set_margins(18, 18, 18)
    pdf.add_page()

    if use_custom:
        pdf.add_font(font_family, "", str(_FONT_PATH))
        pdf.set_font(font_family, "", 18)
    else:
        font_family = "Helvetica"
        pdf._ff = font_family
        pdf.set_font("Helvetica", "", 18)

    pdf.set_text_color(12, 74, 110)  # sky-ish
    pdf.multi_cell(0, 9, text=title)
    pdf.ln(2)

    pdf.set_font(font_family, "", 10)
    pdf.set_text_color(71, 85, 105)  # slate-ish
    meta_lines = []
    if generated_on:
        meta_lines.append(generated_on)
    if subtitle_line:
        meta_lines.append(subtitle_line)
    for mline in meta_lines:
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(0, 5, text=mline)
    if meta_lines:
        pdf.ln(3)

    pdf.set_draw_color(186, 230, 253)  # sky-200
    pdf.set_line_width(0.3)
    y_rule = pdf.get_y()
    pdf.line(pdf.l_margin, y_rule, pdf.w - pdf.r_margin, y_rule)
    pdf.ln(5)

    pdf.set_text_color(30, 41, 59)  # slate-800-ish
    pdf.set_font(font_family, "", 10)
    pdf.write_html(_markdown_to_basic_html(markdown_body))

    out = pdf.output()
    if isinstance(out, (bytes, bytearray)):
        return bytes(out)
    return str(out).encode("utf-8")

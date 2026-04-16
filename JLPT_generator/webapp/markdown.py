from __future__ import annotations

import html
import re

from JLPT_generator.text.feedback_preprocess import preprocess_feedback_markdown


def markdown_to_safe_html(markdown: str) -> str:
    """
    Convert a small subset of markdown to safe HTML.

    - Escapes all user/model-provided text first (XSS-safe).
    - Supports: headings (#..######), unordered/ordered lists, paragraphs, fenced code.
    - Supports simple inline: **bold**, __bold__, `code`.
    """

    md = preprocess_feedback_markdown((markdown or "").replace("\r\n", "\n")).strip(
        "\n"
    )
    if not md.strip():
        return ""

    def inline(text: str) -> str:
        escaped = html.escape(text, quote=True)
        escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
        escaped = re.sub(r"__([^_]+)__", r"<strong>\1</strong>", escaped)
        escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
        return escaped

    lines = md.split("\n")
    out: list[str] = []
    in_code = False
    code_buf: list[str] = []
    para_buf: list[str] = []
    in_ul = False
    in_ol = False
    in_table = False
    table_header: list[str] = []
    table_rows: list[list[str]] = []

    def flush_para() -> None:
        nonlocal para_buf
        text = " ".join(s.strip() for s in para_buf).strip()
        if text:
            out.append(f"<p>{inline(text)}</p>")
        para_buf = []

    def close_lists() -> None:
        nonlocal in_ul, in_ol
        if in_ul:
            out.append("</ul>")
            in_ul = False
        if in_ol:
            out.append("</ol>")
            in_ol = False

    def flush_table() -> None:
        nonlocal in_table, table_header, table_rows
        if not in_table:
            return
        # Emit a simple HTML table (still safe because cells are escaped via inline()).
        out.append('<div class="overflow-x-auto"><table>')
        if table_header:
            out.append("<thead><tr>")
            for h in table_header:
                out.append(f"<th>{inline(h)}</th>")
            out.append("</tr></thead>")
        out.append("<tbody>")
        for row in table_rows:
            out.append("<tr>")
            for cell in row:
                out.append(f"<td>{inline(cell)}</td>")
            out.append("</tr>")
        out.append("</tbody></table></div>")
        in_table = False
        table_header = []
        table_rows = []

    for raw in lines:
        line = raw.rstrip("\n")
        stripped = line.strip()

        if stripped.startswith("```"):
            if in_code:
                out.append(
                    "<pre><code>"
                    + html.escape("\n".join(code_buf), quote=True)
                    + "</code></pre>"
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

        # Horizontal rule (3+ dashes/asterisks/underscores, optional spaces)
        if re.match(r"^[-─*_\s]{3,}$", stripped) and re.search(r"[-─*_]{3,}", stripped):
            flush_para()
            close_lists()
            flush_table()
            out.append('<hr class="my-4 border-sky-200"/>')
            continue

        # Blockquote
        if stripped.startswith(">"):
            flush_para()
            close_lists()
            flush_table()
            q = stripped.lstrip(">").strip()
            out.append(f"<blockquote><p>{inline(q)}</p></blockquote>")
            continue

        # Table detection: header line with pipes + separator line.
        if "|" in line and not in_table:
            # Look ahead for separator
            # We only support tables with the form:
            # | a | b |
            # |---|---|
            parts = [p.strip() for p in line.strip().strip("|").split("|")]
            if len(parts) >= 2:
                # We'll decide it's a header if the next non-empty line looks like a separator.
                # (Done by checking next raw line in the original list is complex; instead, accept
                # header and let separator line toggle into table mode below.)
                pass

        if not stripped:
            flush_para()
            close_lists()
            flush_table()
            continue

        # Table separator row: starts/ends with | and made of dashes/colons/pipes/spaces
        if "|" in line and re.match(r"^\s*\|?[\s:\-|\+]+\|?\s*$", line) and not in_code:
            # If we were buffering a potential header in para_buf, convert it to table header.
            if para_buf and "|" in para_buf[-1]:
                header_line = para_buf.pop()
                flush_para()
                close_lists()
                in_table = True
                table_header = [
                    p.strip() for p in header_line.strip().strip("|").split("|")
                ]
                table_rows = []
                continue

        if in_table and "|" in line:
            cells = [p.strip() for p in line.strip().strip("|").split("|")]
            if cells and any(cells):
                table_rows.append(cells)
                continue
            flush_table()

        m_ol = re.match(r"^\s*(\d+)\.\s+(.*)$", line)
        m_ul = re.match(r"^\s*[-*]\s+(.*)$", line)
        if m_ol:
            flush_para()
            if in_ul:
                out.append("</ul>")
                in_ul = False
            if not in_ol:
                out.append("<ol>")
                in_ol = True
            out.append(f"<li>{inline(m_ol.group(2))}</li>")
            continue
        if m_ul:
            flush_para()
            if in_ol:
                out.append("</ol>")
                in_ol = False
            if not in_ul:
                out.append("<ul>")
                in_ul = True
            out.append(f"<li>{inline(m_ul.group(1))}</li>")
            continue

        close_lists()
        flush_table()
        if stripped.startswith("#"):
            flush_para()
            m_h = re.match(r"^(#{1,6})\s+(.*)$", stripped)
            if m_h:
                level = min(len(m_h.group(1)), 6)
                out.append(f"<h{level}>{inline(m_h.group(2))}</h{level}>")
                continue

        para_buf.append(stripped)

    flush_para()
    close_lists()
    flush_table()
    if in_code:
        out.append(
            "<pre><code>"
            + html.escape("\n".join(code_buf), quote=True)
            + "</code></pre>"
        )

    return "\n".join(out)

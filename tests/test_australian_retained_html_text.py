from __future__ import annotations

from foi_o_nz.australian_retained_html_text import _extract


def test_extracts_only_correspondence_text() -> None:
    html = "<div class='navigation'>Ignore</div><div class='correspondence_text'><p>Keep <b>this</b>.</p></div>"
    assert _extract(html) == "Keep this ."


def test_extract_ignores_non_correspondence_content() -> None:
    assert _extract("<h1>Title</h1><div class='request-header'>Header</div>") == ""

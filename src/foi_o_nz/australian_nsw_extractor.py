"""Bounded candidate AU-NSW assertion extractor."""

from __future__ import annotations

import re
from typing import Any

_EXPLICIT_GIPA = re.compile(
    r"\bGIPA\s+Act\b|Government Information \(Public Access\) Act",
    re.IGNORECASE,
)
_SPAN = re.compile(
    r"\bGIPA(?:\s+Act)?\b|Government Information \(Public Access\)(?:\s+Act)?",
    re.IGNORECASE,
)


def extract_assertion(text: str) -> dict[str, Any]:
    """Extract only explicit GIPA Act evidence under codebook v0.2.1."""
    label_match = _EXPLICIT_GIPA.search(text)
    span_match = _SPAN.search(text) if label_match else None
    return {
        "label": "observed" if label_match else "unknown",
        "abstention": label_match is None,
        "span": None
        if span_match is None
        else {
            "start": span_match.start(),
            "end": span_match.end(),
            "coordinate_system": "utf8_character_half_open",
        },
    }

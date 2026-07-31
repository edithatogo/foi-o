"""Explicit interpretation of hash-pinned legacy annotation values."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any

SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


class LegacyInterpretationError(ValueError):
    """Raised when legacy evidence cannot be interpreted without invention."""


class _StrictJSONError(ValueError):
    """Internal marker for JSON extensions forbidden by this boundary."""


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise _StrictJSONError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def _reject_non_finite(constant: str) -> None:
    raise _StrictJSONError(f"non-finite JSON number: {constant}")


@dataclass(frozen=True)
class LegacyUnknownMapping:
    """Exact codebook-bound interpretation of one legacy unknown label."""

    source_codebook_sha256: str
    unknown_label: str
    normalized_label: None
    abstention_reason: str

    def __post_init__(self) -> None:
        """Reject mappings that could silently create a primary label."""
        if not SHA256_PATTERN.fullmatch(self.source_codebook_sha256):
            raise LegacyInterpretationError("source codebook SHA-256 is invalid")
        if not self.unknown_label:
            raise LegacyInterpretationError("legacy unknown label must be nonempty")
        if self.normalized_label is not None:
            raise LegacyInterpretationError("normalized label must be null")
        if not self.abstention_reason:
            raise LegacyInterpretationError("abstention reason must be nonempty")


@dataclass(frozen=True)
class LegacyInterpretationResult:
    """Original and interpreted representations kept side by side."""

    original_bytes: bytes
    original_bytes_sha256: str
    original_value: dict[str, Any]
    normalized_value: dict[str, Any]
    source_codebook_sha256: str
    was_legacy_unknown: bool


def interpret_legacy_annotation(
    raw_bytes: bytes,
    *,
    source_codebook_sha256: str,
    mapping: LegacyUnknownMapping,
) -> LegacyInterpretationResult:
    """Interpret a legacy unknown without changing its original bytes or value."""
    try:
        text = raw_bytes.decode("utf-8", errors="strict")
        value = json.loads(
            text,
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_non_finite,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, _StrictJSONError) as error:
        raise LegacyInterpretationError("annotation must be a valid UTF-8 JSON object") from error
    if not isinstance(value, dict):
        raise LegacyInterpretationError("annotation must be a valid UTF-8 JSON object")
    if "label" not in value:
        raise LegacyInterpretationError("annotation label is required")
    if source_codebook_sha256 != mapping.source_codebook_sha256:
        raise LegacyInterpretationError("source codebook SHA-256 mismatch")

    original = dict(value)
    normalized = dict(value)
    was_unknown = value["label"] == mapping.unknown_label
    if was_unknown:
        existing_reason = value.get("abstention_reason")
        if existing_reason not in (None, mapping.abstention_reason):
            raise LegacyInterpretationError("conflicting abstention reason")
        normalized["label"] = None
        normalized["abstention_reason"] = mapping.abstention_reason

    return LegacyInterpretationResult(
        original_bytes=raw_bytes,
        original_bytes_sha256=hashlib.sha256(raw_bytes).hexdigest(),
        original_value=original,
        normalized_value=normalized,
        source_codebook_sha256=source_codebook_sha256,
        was_legacy_unknown=was_unknown,
    )

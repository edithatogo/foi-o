"""Canonical byte representation used by provenance contract version 1."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Any

CANONICALIZATION_ID = "foio.sorted-compact-json.v1"


def canonical_bytes(value: Any) -> bytes:
    """Return compact, key-sorted UTF-8 JSON bytes.

    This intentionally is not advertised as RFC 8785. Contract version 1 permits
    JSON values, rejects non-finite floats, preserves array order, and serializes
    with the Python standard library using sorted keys and no insignificant
    whitespace.
    """
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def content_sha256(record: Mapping[str, Any], self_pin_field: str) -> str:
    """Hash a record after excluding its named self-pin field."""
    body = {key: value for key, value in record.items() if key != self_pin_field}
    return hashlib.sha256(canonical_bytes(body)).hexdigest()

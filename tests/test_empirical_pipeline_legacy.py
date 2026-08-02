from __future__ import annotations

import hashlib
import json
from typing import Any, cast

import pytest

from foi_o_nz.empirical_pipeline.legacy import (
    LegacyInterpretationError,
    LegacyUnknownMapping,
    interpret_legacy_annotation,
)

SOURCE_CODEBOOK_SHA = "a" * 64


def _mapping() -> LegacyUnknownMapping:
    return LegacyUnknownMapping(
        source_codebook_sha256=SOURCE_CODEBOOK_SHA,
        unknown_label="unknown",
        normalized_label=None,
        abstention_reason="insufficient_evidence",
    )


def test_unknown_is_interpreted_as_null_abstention_without_mutating_original() -> None:
    raw = b'{"label":"unknown","span":null,"unit_id":"unit-1"}\n'
    original = json.loads(raw)

    interpreted = interpret_legacy_annotation(
        raw,
        source_codebook_sha256=SOURCE_CODEBOOK_SHA,
        mapping=_mapping(),
    )

    assert interpreted.original_bytes == raw
    assert interpreted.original_bytes_sha256 == hashlib.sha256(raw).hexdigest()
    assert interpreted.original_value == original
    assert interpreted.normalized_value == {
        "label": None,
        "span": None,
        "unit_id": "unit-1",
        "abstention_reason": "insufficient_evidence",
    }
    assert interpreted.was_legacy_unknown is True
    assert json.loads(raw) == original


def test_non_unknown_label_is_preserved_exactly() -> None:
    raw = b'{"label":"requested","span":"the records","unit_id":"unit-2"}'
    interpreted = interpret_legacy_annotation(
        raw,
        source_codebook_sha256=SOURCE_CODEBOOK_SHA,
        mapping=_mapping(),
    )
    assert interpreted.normalized_value == interpreted.original_value
    assert interpreted.was_legacy_unknown is False


def test_unknown_requires_exact_source_codebook_pin() -> None:
    raw = b'{"label":"unknown","unit_id":"unit-1"}'
    with pytest.raises(LegacyInterpretationError, match="codebook SHA-256 mismatch"):
        interpret_legacy_annotation(
            raw,
            source_codebook_sha256="b" * 64,
            mapping=_mapping(),
        )


def test_invalid_json_preserves_no_silent_fallback() -> None:
    with pytest.raises(LegacyInterpretationError, match="valid UTF-8 JSON object"):
        interpret_legacy_annotation(
            b'{"label":',
            source_codebook_sha256=SOURCE_CODEBOOK_SHA,
            mapping=_mapping(),
        )


def test_missing_label_is_rejected() -> None:
    with pytest.raises(LegacyInterpretationError, match="label"):
        interpret_legacy_annotation(
            b'{"unit_id":"unit-1"}',
            source_codebook_sha256=SOURCE_CODEBOOK_SHA,
            mapping=_mapping(),
        )


def test_existing_abstention_reason_cannot_be_overwritten() -> None:
    raw = b'{"abstention_reason":"other","label":"unknown","unit_id":"unit-1"}'
    with pytest.raises(LegacyInterpretationError, match="conflicting abstention"):
        interpret_legacy_annotation(
            raw,
            source_codebook_sha256=SOURCE_CODEBOOK_SHA,
            mapping=_mapping(),
        )


def test_mapping_cannot_normalize_unknown_to_a_primary_label() -> None:
    with pytest.raises(LegacyInterpretationError, match="normalized label must be null"):
        LegacyUnknownMapping(
            source_codebook_sha256=SOURCE_CODEBOOK_SHA,
            unknown_label="unknown",
            normalized_label=cast(Any, "requested"),
            abstention_reason="insufficient_evidence",
        )


def test_mapping_requires_a_sha256_and_nonempty_reason() -> None:
    with pytest.raises(LegacyInterpretationError, match="source codebook"):
        LegacyUnknownMapping(
            source_codebook_sha256="not-a-digest",
            unknown_label="unknown",
            normalized_label=None,
            abstention_reason="insufficient_evidence",
        )
    with pytest.raises(LegacyInterpretationError, match="abstention reason"):
        LegacyUnknownMapping(
            source_codebook_sha256=SOURCE_CODEBOOK_SHA,
            unknown_label="unknown",
            normalized_label=None,
            abstention_reason="",
        )


@pytest.mark.parametrize(
    "raw",
    [
        '{"label":"unknown"}'.encode("utf-16"),
        '{"label":"unknown"}'.encode("utf-32"),
        b'{"label":"unknown","label":"requested"}',
        b'{"label":"unknown","score":NaN}',
        b'{"label":"unknown","score":Infinity}',
        b'{"label":"unknown","score":-Infinity}',
    ],
)
def test_legacy_parser_rejects_non_utf8_duplicate_and_non_finite_json(raw: bytes) -> None:
    with pytest.raises(LegacyInterpretationError, match="valid UTF-8 JSON object"):
        interpret_legacy_annotation(
            raw,
            source_codebook_sha256=SOURCE_CODEBOOK_SHA,
            mapping=_mapping(),
        )

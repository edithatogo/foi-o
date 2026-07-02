"""Deterministic redaction-candidate detection for review workflows.

This module does not redact, withhold, classify, or decide. It only emits review
candidates with hashed/masked excerpts so agents can route sensitive-looking
material to authorised humans.
"""

from __future__ import annotations

import re
from hashlib import sha256
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from foi_o_nz.io import iter_jsonl, write_jsonl

REDACTION_CANDIDATE_SCHEMA_VERSION = "foi-o-nz.redaction-candidate.v0.1.0"

_PATTERNS: tuple[tuple[str, str, float, str], ...] = (
    (
        "email_address",
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
        0.96,
        "Email-like string. Candidate personal/contact information.",
    ),
    (
        "phone_number",
        r"(?<!\d)(?:\+?64[\s-]?)?(?:0\d{1,2}[\s-]?\d{3}[\s-]?\d{3,4}|2\d[\s-]?\d{3}[\s-]?\d{3,4})(?!\d)",
        0.72,
        "NZ phone-like string. Candidate contact information.",
    ),
    (
        "possible_nhi",
        r"\b[A-HJ-NP-Z]{3}\d{4}\b",
        0.58,
        "NHI-like token. High false-positive risk; requires human review.",
    ),
    (
        "possible_ird_number",
        r"(?<!\d)(?:\d{2,3}[-\s]?\d{3}[-\s]?\d{3})(?!\d)",
        0.54,
        "IRD-like numeric pattern. High false-positive risk; requires human review.",
    ),
    (
        "postal_address_hint",
        r"\b\d{1,5}\s+[A-Za-z][A-Za-z\s.'-]{2,60}\s+(?:Street|St|Road|Rd|Avenue|Ave|Drive|Dr|Lane|Ln|Place|Pl|Terrace|Tce)\b",
        0.62,
        "Street-address-like phrase. Candidate location/contact information.",
    ),
)


class RedactionCandidate(BaseModel):
    """One non-dispositive candidate span for human review."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["foi-o-nz.redaction-candidate.v0.1.0"] = (
        REDACTION_CANDIDATE_SCHEMA_VERSION
    )
    candidate_id: str
    source_id: str
    request_id: str | None = None
    source_record_type: str | None = None
    span_type: str
    start: int = Field(ge=0)
    end: int = Field(ge=0)
    text_sha256: str
    masked_preview: str
    confidence: float = Field(ge=0, le=1)
    rationale: str
    review_required: bool = True
    decision_status: Literal["candidate_only_not_redacted", "human_reviewed"] = (
        "candidate_only_not_redacted"
    )


def mask_text(value: str) -> str:
    """Return a privacy-preserving preview of candidate text."""
    if len(value) <= 2:
        return "*" * len(value)
    if "@" in value:
        local, _, domain = value.partition("@")
        return f"{local[:1]}***@{domain[:1]}***"
    return f"{value[:1]}***{value[-1:]}"


def candidate_id(source_id: str, span_type: str, start: int, end: int, text: str) -> str:
    """Create a deterministic candidate identifier."""
    digest = sha256(f"{source_id}\0{span_type}\0{start}\0{end}\0{text}".encode()).hexdigest()
    return f"foio-nz:redaction-candidate:{digest[:24]}"


def extract_text_from_record(record: dict[str, Any], *, text_field: str = "text") -> str:
    """Extract reviewable text from common FOI-O record shapes."""
    value = record.get(text_field)
    if isinstance(value, str) and value:
        return value
    if isinstance(record.get("payload"), dict):
        payload = record["payload"]
        for key in ("text", "body", "title", "reason"):
            if isinstance(payload.get(key), str):
                return payload[key]
    return ""


def infer_source_id(record: dict[str, Any], sequence: int) -> str:
    """Infer a stable source identifier."""
    for key in ("chunk_id", "event_id", "request_id", "source_id"):
        if record.get(key) is not None:
            return str(record[key])
    return f"record-{sequence}"


def find_redaction_candidates(
    record: dict[str, Any], *, sequence: int = 0, text_field: str = "text"
) -> list[RedactionCandidate]:
    """Find candidate sensitive spans in a single record."""
    text = extract_text_from_record(record, text_field=text_field)
    if not text:
        return []
    source_id = infer_source_id(record, sequence)
    request_id = record.get("request_id")
    if request_id is None and isinstance(record.get("request_ref"), dict):
        request_id = record["request_ref"].get("source_request_id")
    candidates: list[RedactionCandidate] = []
    seen: set[tuple[int, int, str]] = set()
    for span_type, pattern, confidence, rationale in _PATTERNS:
        for match in re.finditer(pattern, text, flags=re.IGNORECASE):
            key = (match.start(), match.end(), span_type)
            if key in seen:
                continue
            seen.add(key)
            matched = match.group(0)
            candidates.append(
                RedactionCandidate(
                    candidate_id=candidate_id(
                        source_id, span_type, match.start(), match.end(), matched
                    ),
                    source_id=source_id,
                    request_id=str(request_id) if request_id is not None else None,
                    source_record_type=str(record.get("source_record_type"))
                    if record.get("source_record_type")
                    else None,
                    span_type=span_type,
                    start=match.start(),
                    end=match.end(),
                    text_sha256=sha256(matched.encode("utf-8")).hexdigest(),
                    masked_preview=mask_text(matched),
                    confidence=confidence,
                    rationale=rationale,
                )
            )
    candidates.sort(key=lambda item: (item.start, item.end, item.span_type))
    return candidates


def propose_redactions_jsonl(
    input_jsonl: Path, output_jsonl: Path, *, text_field: str = "text"
) -> dict[str, Any]:
    """Write redaction candidates for every record in a JSONL stream."""
    all_candidates: list[dict[str, Any]] = []
    source_count = 0
    for sequence, record in enumerate(iter_jsonl(input_jsonl)):
        source_count += 1
        all_candidates.extend(
            candidate.model_dump(mode="json")
            for candidate in find_redaction_candidates(
                record, sequence=sequence, text_field=text_field
            )
        )
    write_jsonl(output_jsonl, all_candidates)
    return {
        "ok": True,
        "input": str(input_jsonl),
        "output": str(output_jsonl),
        "source_record_count": source_count,
        "candidate_count": len(all_candidates),
        "decision_status": "candidate_only_not_redacted",
    }

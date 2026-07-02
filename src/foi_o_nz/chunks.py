"""Chunk request and event records into agent/vector ready text units."""

from __future__ import annotations

from collections.abc import Iterable
from hashlib import sha256
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from foi_o_nz.constants import CHUNK_SCHEMA_VERSION
from foi_o_nz.io import iter_jsonl, write_jsonl


class ChunkRecord(BaseModel):
    """Text chunk derived from a request profile or process event."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["foi-o-nz.chunk.v0.1.0"] = CHUNK_SCHEMA_VERSION
    chunk_id: str
    source_record_type: Literal["request", "event"]
    source_id: str
    request_id: str | None = None
    authority: str | None = None
    event_type: str | None = None
    text: str = Field(min_length=1)
    text_sha256: str
    token_estimate: int = Field(ge=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


def text_hash(text: str) -> str:
    """Return SHA-256 hash for chunk text."""
    return sha256(text.encode("utf-8")).hexdigest()


def estimate_tokens(text: str) -> int:
    """Cheap deterministic token estimate for planning, not billing."""
    return max(1, (len(text) + 3) // 4)


def make_chunk_id(source_record_type: str, source_id: str, text: str, ordinal: int = 0) -> str:
    """Build a content-addressed chunk ID."""
    digest = sha256(f"{source_record_type}\0{source_id}\0{ordinal}\0{text}".encode()).hexdigest()
    return f"foio-nz:chunk:{digest[:24]}"


def _stringify_payload(payload: Any) -> str:
    if isinstance(payload, dict):
        parts: list[str] = []
        for key in sorted(payload):
            value = payload[key]
            if value is None or isinstance(value, dict | list):
                continue
            parts.append(f"{key}: {value}")
        return "; ".join(parts)
    return str(payload) if payload is not None else ""


def chunk_request_record(record: dict[str, Any]) -> ChunkRecord:
    """Create one text chunk from a request profile."""
    request_id = str(record.get("request_id", "unknown"))
    title = str(record.get("title") or "Untitled request")
    authority = str(record.get("authority") or "Unknown authority")
    state = record.get("normalised_state") or record.get("source_state") or "Unknown"
    source_state = record.get("source_state") or "Unknown"
    text = f"Request {request_id}. Title: {title}. Authority: {authority}. State: {state}. Source state: {source_state}."
    if record.get("legal_clock"):
        text += f" Legal clock: {_stringify_payload(record.get('legal_clock'))}."
    digest = text_hash(text)
    return ChunkRecord(
        chunk_id=make_chunk_id("request", request_id, text),
        source_record_type="request",
        source_id=request_id,
        request_id=request_id,
        authority=authority,
        text=text,
        text_sha256=digest,
        token_estimate=estimate_tokens(text),
        metadata={
            "url_title": record.get("url_title"),
            "source_url": str(record.get("source_url")) if record.get("source_url") else None,
        },
    )


def chunk_event_record(record: dict[str, Any]) -> ChunkRecord:
    """Create one text chunk from a core event."""
    event_id = str(record.get("event_id", "unknown"))
    event_type = str(record.get("event_type", "UnknownEvent"))
    request_ref = record.get("request_ref") if isinstance(record.get("request_ref"), dict) else {}
    request_id = str(request_ref.get("source_request_id")) if request_ref else None
    lifecycle_state = record.get("lifecycle_state_after") or "Unknown"
    payload_text = _stringify_payload(record.get("payload"))
    evidence_parts: list[str] = []
    for evidence in record.get("evidence", []) if isinstance(record.get("evidence"), list) else []:
        if isinstance(evidence, dict) and evidence.get("excerpt"):
            evidence_parts.append(str(evidence["excerpt"]))
    text = (
        f"Event {event_type} for request {request_id or 'unknown'}. State after: {lifecycle_state}."
    )
    if payload_text:
        text += f" Payload: {payload_text}."
    if evidence_parts:
        text += " Evidence excerpts: " + " | ".join(evidence_parts[:3])
    digest = text_hash(text)
    return ChunkRecord(
        chunk_id=make_chunk_id("event", event_id, text),
        source_record_type="event",
        source_id=event_id,
        request_id=request_id,
        event_type=event_type,
        text=text,
        text_sha256=digest,
        token_estimate=estimate_tokens(text),
        metadata={
            "assertion_status": record.get("assertion_status"),
            "confidence": record.get("confidence"),
            "requires_human_certification": record.get("requires_human_certification"),
        },
    )


def chunk_records(
    records: Iterable[dict[str, Any]], *, kind: Literal["request", "event"]
) -> list[ChunkRecord]:
    """Chunk records of one kind."""
    if kind == "request":
        return [chunk_request_record(record) for record in records]
    return [chunk_event_record(record) for record in records]


def chunk_jsonl(
    input_jsonl: Path, output_jsonl: Path, *, kind: Literal["request", "event"]
) -> dict[str, Any]:
    """Chunk a JSONL record stream and write chunk JSONL."""
    chunks = chunk_records(iter_jsonl(input_jsonl), kind=kind)
    write_jsonl(
        output_jsonl, [chunk.model_dump(mode="json", exclude_none=True) for chunk in chunks]
    )
    return {
        "ok": True,
        "input": str(input_jsonl),
        "output": str(output_jsonl),
        "kind": kind,
        "chunk_count": len(chunks),
        "token_estimate": sum(chunk.token_estimate for chunk in chunks),
    }

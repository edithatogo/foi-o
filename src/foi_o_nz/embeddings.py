"""Deterministic local text embeddings for FOI-O NZ artefacts.

This is not a semantic model. It is a dependency-light feature-hashing baseline
that lets the repository build a vector/RAG surface before MAX or external model
embeddings are configured. The output shape is intentionally compatible with
LanceDB and other vector stores.
"""

from __future__ import annotations

import hashlib
import math
import re
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from foi_o_nz.io import iter_jsonl, write_jsonl

_TOKEN_RE = re.compile(r"[\wāēīōūĀĒĪŌŪ]+", re.UNICODE)


def tokenize(text: str) -> list[str]:
    """Tokenise text into lower-case word-ish tokens, preserving macrons."""
    return [match.group(0).lower() for match in _TOKEN_RE.finditer(text)]


def hash_embedding(text: str, *, dimensions: int = 128) -> list[float]:
    """Return a deterministic signed feature-hashing vector.

    This provides a stable local baseline for tests, indexing, and pipeline
    development. It should be replaced or supplemented by MAX/HF embeddings for
    production semantic retrieval.
    """
    if dimensions <= 0:
        raise ValueError("dimensions must be positive")
    vector = [0.0] * dimensions
    for token in tokenize(text):
        digest = hashlib.blake2b(token.encode("utf-8"), digest_size=16).digest()
        bucket = int.from_bytes(digest[:8], "big") % dimensions
        sign = 1.0 if digest[8] & 1 else -1.0
        vector[bucket] += sign
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [value / norm for value in vector]


def request_text(record: dict[str, Any]) -> str:
    """Extract indexable text from a request profile-like record."""
    parts = [
        str(record.get("title") or ""),
        str(record.get("authority") or ""),
        str(record.get("source_state") or ""),
        str(record.get("normalised_state") or ""),
    ]
    return "\n".join(part for part in parts if part)


def event_text(record: dict[str, Any]) -> str:
    """Extract indexable text from a core-event-like record."""
    payload = record.get("payload") if isinstance(record.get("payload"), dict) else {}
    evidence = record.get("evidence") if isinstance(record.get("evidence"), list) else []
    evidence_text = "\n".join(
        str(item.get("excerpt"))
        for item in evidence
        if isinstance(item, dict) and item.get("excerpt")
    )
    parts = [
        str(record.get("event_type") or ""),
        str(record.get("lifecycle_state_after") or ""),
        str(payload.get("text") or payload.get("body") or payload.get("title") or ""),
        evidence_text,
    ]
    return "\n".join(part for part in parts if part)


def embedding_record(
    record: dict[str, Any],
    *,
    kind: str,
    dimensions: int = 128,
) -> dict[str, Any]:
    """Build one vector-store-ready embedding record."""
    if kind == "request":
        text = request_text(record)
        source_id = str(record.get("request_id") or record.get("url_title") or "unknown")
    elif kind == "event":
        text = event_text(record)
        source_id = str(record.get("event_id") or "unknown")
    else:
        raise ValueError("kind must be 'request' or 'event'")
    return {
        "source_id": source_id,
        "kind": kind,
        "text": text,
        "embedding_model": f"foi-o-nz-feature-hash-v0.5.{dimensions}",
        "embedding": hash_embedding(text, dimensions=dimensions),
        "metadata": {
            "request_id": record.get("request_id")
            or (record.get("request_ref") or {}).get("source_request_id")
            if isinstance(record.get("request_ref"), dict)
            else record.get("request_id"),
            "event_type": record.get("event_type"),
            "normalised_state": record.get("normalised_state")
            or record.get("lifecycle_state_after"),
        },
    }


def iter_embedding_records(
    records: Iterable[dict[str, Any]],
    *,
    kind: str,
    dimensions: int = 128,
) -> Iterable[dict[str, Any]]:
    """Yield embedding records for an iterable of request/event records."""
    for record in records:
        yield embedding_record(record, kind=kind, dimensions=dimensions)


def embed_jsonl(
    input_path: Path,
    output_path: Path,
    *,
    kind: str,
    dimensions: int = 128,
) -> int:
    """Embed a request/event JSONL file to vector JSONL."""
    return write_jsonl(
        output_path,
        iter_embedding_records(iter_jsonl(input_path), kind=kind, dimensions=dimensions),
    )

"""Dependency-light lexical/vector retrieval over FOI-O NZ chunks.

The retrieval layer is intentionally local and deterministic. It gives agents a
bounded way to retrieve relevant process context without calling external models
or certifying legal meaning. Vector scores use the repository's feature-hashing
baseline; semantic MAX/HF embeddings can be added later behind the same output
contract.
"""

from __future__ import annotations

import math
from collections import Counter
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from foi_o_nz.embeddings import hash_embedding, tokenize
from foi_o_nz.io import iter_jsonl, write_json


class RetrievalHit(BaseModel):
    """One ranked retrieval result for an agent query."""

    model_config = ConfigDict(extra="forbid")

    rank: int = Field(ge=1)
    chunk_id: str
    source_record_type: str | None = None
    source_id: str | None = None
    request_id: str | None = None
    event_type: str | None = None
    score: float
    lexical_score: float
    vector_score: float
    matched_terms: list[str] = Field(default_factory=list)
    token_estimate: int | None = Field(default=None, ge=1)
    text: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class RetrievalReport(BaseModel):
    """A deterministic search report over a chunk stream."""

    model_config = ConfigDict(extra="forbid")

    ok: bool = True
    query: str
    input: str
    top_k: int = Field(ge=1)
    result_count: int = Field(ge=0)
    scoring: str
    dimensions: int = Field(ge=1)
    results: list[RetrievalHit]


def _normalise_chunk(record: dict[str, Any]) -> dict[str, Any]:
    text = str(record.get("text") or "")
    return {
        "chunk_id": str(record.get("chunk_id") or record.get("source_id") or "unknown"),
        "source_record_type": record.get("source_record_type"),
        "source_id": str(record.get("source_id")) if record.get("source_id") is not None else None,
        "request_id": str(record.get("request_id"))
        if record.get("request_id") is not None
        else None,
        "event_type": str(record.get("event_type"))
        if record.get("event_type") is not None
        else None,
        "token_estimate": record.get("token_estimate"),
        "text": text,
        "metadata": record.get("metadata") if isinstance(record.get("metadata"), dict) else {},
        "tokens": tokenize(text),
    }


def _idf(doc_freq: int, doc_count: int) -> float:
    return math.log(1.0 + (doc_count - doc_freq + 0.5) / (doc_freq + 0.5))


def _cosine(left: list[float], right: list[float]) -> float:
    if len(left) != len(right):
        raise ValueError("vectors must have the same dimensions")
    return sum(a * b for a, b in zip(left, right, strict=True))


def search_chunk_records(
    records: list[dict[str, Any]],
    *,
    query: str,
    top_k: int = 10,
    dimensions: int = 128,
    lexical_weight: float = 0.70,
    include_vectors: bool = True,
) -> RetrievalReport:
    """Search already-loaded chunk records using BM25-ish lexical scoring.

    Vector scoring is deterministic feature hashing. This is a local baseline,
    not a claim of semantic equivalence to a trained embedding model.
    """
    if top_k <= 0:
        raise ValueError("top_k must be positive")
    if not 0 <= lexical_weight <= 1:
        raise ValueError("lexical_weight must be between 0 and 1")
    if dimensions <= 0:
        raise ValueError("dimensions must be positive")

    chunks = [_normalise_chunk(record) for record in records if str(record.get("text") or "")]
    query_tokens = tokenize(query)
    if not chunks or not query_tokens:
        return RetrievalReport(
            query=query,
            input="<memory>",
            top_k=top_k,
            result_count=0,
            scoring="bm25+feature-hash" if include_vectors else "bm25",
            dimensions=dimensions,
            results=[],
        )

    doc_count = len(chunks)
    doc_freq: Counter[str] = Counter()
    lengths: list[int] = []
    token_counts: list[Counter[str]] = []
    for chunk in chunks:
        counts = Counter(chunk["tokens"])
        token_counts.append(counts)
        lengths.append(sum(counts.values()))
        doc_freq.update(counts.keys())
    avgdl = sum(lengths) / max(1, len(lengths))
    query_counts = Counter(query_tokens)
    query_vector = hash_embedding(query, dimensions=dimensions) if include_vectors else []

    scored: list[tuple[float, RetrievalHit]] = []
    for idx, chunk in enumerate(chunks):
        counts = token_counts[idx]
        doc_len = max(1, lengths[idx])
        lexical_score = 0.0
        matched_terms: list[str] = []
        for token in query_counts:
            tf = counts.get(token, 0)
            if tf == 0:
                continue
            matched_terms.append(token)
            k1 = 1.5
            b = 0.75
            lexical_score += _idf(doc_freq[token], doc_count) * (
                (tf * (k1 + 1.0)) / (tf + k1 * (1.0 - b + b * doc_len / avgdl))
            )
        vector_score = 0.0
        if include_vectors:
            # Convert cosine [-1, 1] into a stable [0, 1] blending range.
            vector_score = (
                _cosine(query_vector, hash_embedding(chunk["text"], dimensions=dimensions)) + 1.0
            ) / 2.0
        combined = lexical_weight * lexical_score + (1.0 - lexical_weight) * vector_score
        hit = RetrievalHit(
            rank=1,
            chunk_id=chunk["chunk_id"],
            source_record_type=chunk["source_record_type"],
            source_id=chunk["source_id"],
            request_id=chunk["request_id"],
            event_type=chunk["event_type"],
            score=round(combined, 8),
            lexical_score=round(lexical_score, 8),
            vector_score=round(vector_score, 8),
            matched_terms=sorted(matched_terms),
            token_estimate=chunk["token_estimate"]
            if isinstance(chunk["token_estimate"], int)
            else None,
            text=chunk["text"],
            metadata=chunk["metadata"],
        )
        scored.append((combined, hit))

    scored.sort(key=lambda item: (-item[0], item[1].chunk_id))
    hits: list[RetrievalHit] = []
    for rank, (_, hit) in enumerate(scored[:top_k], start=1):
        hits.append(hit.model_copy(update={"rank": rank}))
    return RetrievalReport(
        query=query,
        input="<memory>",
        top_k=top_k,
        result_count=len(hits),
        scoring="bm25+feature-hash" if include_vectors else "bm25",
        dimensions=dimensions,
        results=hits,
    )


def search_chunks_jsonl(
    input_jsonl: Path,
    output_json: Path,
    *,
    query: str,
    top_k: int = 10,
    dimensions: int = 128,
    lexical_weight: float = 0.70,
    include_vectors: bool = True,
) -> dict[str, Any]:
    """Search a chunk JSONL file and write a JSON report."""
    report = search_chunk_records(
        list(iter_jsonl(input_jsonl)),
        query=query,
        top_k=top_k,
        dimensions=dimensions,
        lexical_weight=lexical_weight,
        include_vectors=include_vectors,
    )
    data = report.model_copy(update={"input": str(input_jsonl)}).model_dump(mode="json")
    write_json(output_json, data)
    return data

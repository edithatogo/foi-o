from __future__ import annotations

from foi_o_nz.embeddings import embedding_record, hash_embedding, tokenize


def test_tokenize_preserves_macrons() -> None:
    assert tokenize("Māori OIA request") == ["māori", "oia", "request"]


def test_hash_embedding_is_deterministic_and_normalised() -> None:
    left = hash_embedding("Official information request", dimensions=16)
    right = hash_embedding("Official information request", dimensions=16)
    assert left == right
    assert len(left) == 16
    norm = sum(value * value for value in left) ** 0.5
    assert abs(norm - 1.0) < 1e-9


def test_embedding_record_request() -> None:
    record = {"request_id": "1", "title": "A request", "authority": "Agency"}
    embedded = embedding_record(record, kind="request", dimensions=8)
    assert embedded["source_id"] == "1"
    assert embedded["kind"] == "request"
    assert len(embedded["embedding"]) == 8

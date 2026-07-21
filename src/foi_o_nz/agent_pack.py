"""Build bounded agent context packs for one request.

A context pack is a portable snapshot of request/process evidence for agent
workflows. It includes constraints and provenance metadata so downstream agents
can retrieve and draft without exceeding certification boundaries.
"""

from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from foi_o_nz.constants import HUMAN_CERTIFICATION_EVENT_TYPES
from foi_o_nz.io import iter_jsonl, write_json
from foi_o_nz.ledger import canonical_record_json, sha256_text

AGENT_PACK_SCHEMA_VERSION = "foi-o-nz.agent-pack.v0.1.0"


class AgentPack(BaseModel):
    """One request-scoped context pack for bounded agent workflows."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["foi-o-nz.agent-pack.v0.1.0"] = AGENT_PACK_SCHEMA_VERSION
    pack_id: str
    request_id: str
    generated_at: datetime
    constraints: dict[str, Any]
    request: dict[str, Any] | None = None
    events: list[dict[str, Any]] = Field(default_factory=list)
    chunks: list[dict[str, Any]] = Field(default_factory=list)
    risks: list[dict[str, Any]] = Field(default_factory=list)
    retrieval_results: list[dict[str, Any]] = Field(default_factory=list)
    redaction_candidates: list[dict[str, Any]] = Field(default_factory=list)
    provenance: dict[str, Any] = Field(default_factory=dict)


def _request_id_from_record(record: dict[str, Any]) -> str | None:
    if record.get("request_id") is not None:
        return str(record["request_id"])
    ref = record.get("request_ref")
    if isinstance(ref, dict) and ref.get("source_request_id") is not None:
        return str(ref["source_request_id"])
    return None


def _profile_from_record(record: dict[str, Any]) -> tuple[str | None, str | None]:
    profile = record.get("profile")
    if isinstance(profile, dict):
        return profile.get("profile_id"), profile.get("profile_version")
    return record.get("profile_id"), record.get("profile_version")


def _load_for_request(path: Path | None, request_id: str) -> list[dict[str, Any]]:
    if path is None or not path.exists():
        return []
    return [record for record in iter_jsonl(path) if _request_id_from_record(record) == request_id]


def _load_request(path: Path, request_id: str) -> dict[str, Any] | None:
    for record in iter_jsonl(path):
        if _request_id_from_record(record) == request_id:
            return record
    return None


def _hash_records(records: list[dict[str, Any]]) -> str:
    digest = sha256()
    for record in records:
        digest.update(canonical_record_json(record).encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def build_agent_context_pack(
    *,
    request_id: str,
    requests_jsonl: Path,
    events_jsonl: Path | None = None,
    chunks_jsonl: Path | None = None,
    risks_jsonl: Path | None = None,
    retrieval_json: Path | None = None,
    redaction_candidates_jsonl: Path | None = None,
) -> AgentPack:
    """Build an in-memory agent context pack for one request ID."""
    request = _load_request(requests_jsonl, request_id)
    if request is None:
        raise ValueError(f"requested case is missing from {requests_jsonl}: {request_id}")
    request_profile = _profile_from_record(request)
    events = _load_for_request(events_jsonl, request_id)
    chunks = _load_for_request(chunks_jsonl, request_id)
    risks = _load_for_request(risks_jsonl, request_id)
    redaction_candidates = _load_for_request(redaction_candidates_jsonl, request_id)
    retrieval_results: list[dict[str, Any]] = []
    if retrieval_json is not None and retrieval_json.exists():
        import json

        data = json.loads(retrieval_json.read_text(encoding="utf-8"))
        if isinstance(data, dict) and isinstance(data.get("results"), list):
            retrieval_results = [item for item in data["results"] if isinstance(item, dict)]
    excluded_retrieval_results: list[dict[str, Any]] = []
    compatible_retrieval_results: list[dict[str, Any]] = []
    for item in retrieval_results:
        item_request = _request_id_from_record(item)
        item_profile = _profile_from_record(item)
        reasons: list[str] = []
        if item_request is not None and item_request != request_id:
            reasons.append("request_mismatch")
        profiles_present = item_profile != (None, None) and request_profile != (None, None)
        if profiles_present and item_profile != request_profile:
            reasons.append("profile_mismatch")
        if reasons:
            excluded_retrieval_results.append({"record": item, "reason": reasons})
        else:
            compatible_retrieval_results.append(item)
    retrieval_results = compatible_retrieval_results
    constraints = {
        "agent_may": [
            "retrieve_context",
            "summarise_process_history",
            "draft_search_plan",
            "draft_correspondence_for_human_review",
            "flag_candidate_risks",
            "flag_candidate_redaction_spans",
        ],
        "agent_must_not": sorted(HUMAN_CERTIFICATION_EVENT_TYPES),
        "certification_boundary": "agents may prepare or flag; authorised humans certify decisions, releases, refusals, charges, transfers, extensions, and redactions",
    }
    all_material = {
        "request": request,
        "events": events,
        "chunks": chunks,
        "risks": risks,
        "retrieval_results": retrieval_results,
        "redaction_candidates": redaction_candidates,
        "excluded_retrieval_results": excluded_retrieval_results,
    }
    material = {
        "request_id": request_id,
        "context": all_material,
        "constraints": constraints,
    }
    pack_digest = sha256_text(canonical_record_json(material))
    return AgentPack(
        pack_id=f"foio-nz:agent-pack:{pack_digest}",
        request_id=request_id,
        generated_at=datetime.now(UTC),
        constraints=constraints,
        request=request,
        events=events,
        chunks=chunks,
        risks=risks,
        retrieval_results=retrieval_results,
        redaction_candidates=redaction_candidates,
        provenance={
            "source_ids": {
                "requests": str(requests_jsonl),
                "events": str(events_jsonl) if events_jsonl else None,
                "chunks": str(chunks_jsonl) if chunks_jsonl else None,
                "risks": str(risks_jsonl) if risks_jsonl else None,
                "retrieval": str(retrieval_json) if retrieval_json else None,
                "redactions": str(redaction_candidates_jsonl)
                if redaction_candidates_jsonl
                else None,
            },
            "source_hashes": {
                "request": sha256_text(canonical_record_json(request)),
                "events": _hash_records(events),
                "chunks": _hash_records(chunks),
                "risks": _hash_records(risks),
                "retrieval": _hash_records(retrieval_results),
                "redactions": _hash_records(redaction_candidates),
            },
            "excluded_retrieval_results": excluded_retrieval_results,
            "component_counts": {
                "request": 1 if request else 0,
                "events": len(events),
                "chunks": len(chunks),
                "risks": len(risks),
                "retrieval_results": len(retrieval_results),
                "redaction_candidates": len(redaction_candidates),
            },
        },
    )


def write_agent_context_pack(
    output_json: Path,
    *,
    request_id: str,
    requests_jsonl: Path,
    events_jsonl: Path | None = None,
    chunks_jsonl: Path | None = None,
    risks_jsonl: Path | None = None,
    retrieval_json: Path | None = None,
    redaction_candidates_jsonl: Path | None = None,
) -> dict[str, Any]:
    """Write an agent context pack to JSON."""
    pack = build_agent_context_pack(
        request_id=request_id,
        requests_jsonl=requests_jsonl,
        events_jsonl=events_jsonl,
        chunks_jsonl=chunks_jsonl,
        risks_jsonl=risks_jsonl,
        retrieval_json=retrieval_json,
        redaction_candidates_jsonl=redaction_candidates_jsonl,
    )
    data = pack.model_dump(mode="json", exclude_none=True)
    write_json(output_json, data)
    return data

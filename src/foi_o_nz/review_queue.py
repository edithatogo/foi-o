"""Human-review queue builders for bounded FOI-O NZ agent workflows.

The queue is intentionally non-dispositive: it turns candidate risks, candidate
redaction spans, uncertified dispositive events, and quality findings into human
review tasks. It never records that access should be granted, refused, redacted,
charged, extended, or transferred.
"""

from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from foi_o_nz.constants import REVIEW_TASK_SCHEMA_VERSION
from foi_o_nz.io import iter_jsonl, write_jsonl

TaskType = Literal[
    "risk_review",
    "redaction_candidate_review",
    "certification_boundary_review",
    "quality_finding_review",
    "transition_review",
]
Priority = Literal["low", "medium", "high", "urgent"]


class ReviewTask(BaseModel):
    """One human-review task created from machine-generated candidate signals."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["foi-o-nz.review-task.v0.1.0"] = REVIEW_TASK_SCHEMA_VERSION
    task_id: str
    request_id: str | None = None
    task_type: TaskType
    priority: Priority
    source_record_type: str
    source_id: str
    title: str
    rationale: str
    candidate_payload: dict[str, Any] = Field(default_factory=dict)
    required_reviewer_role: str
    created_at: datetime
    agent_boundary: dict[str, Any]
    decision_status: Literal["pending_human_review", "human_reviewed"] = "pending_human_review"


def _stable_task_id(task_type: str, source_id: str, rationale: str) -> str:
    digest = sha256(f"{task_type}\0{source_id}\0{rationale}".encode()).hexdigest()
    return f"foio-nz:review-task:{digest[:24]}"


def _agent_boundary() -> dict[str, Any]:
    return {
        "machine_may": [
            "route_to_reviewer",
            "summarise_candidate_signal",
            "link_supporting_candidate_payload",
            "record_review_outcome_after_human_input",
        ],
        "machine_must_not": [
            "certify_release",
            "certify_refusal",
            "certify_redaction",
            "certify_charge",
            "certify_extension",
            "certify_transfer",
            "certify_review_or_complaint_outcome",
        ],
        "notes": [
            "Review tasks are worklist items only.",
            "Candidate payloads are not legal findings or redaction decisions.",
        ],
    }


def _priority_from_risk(level: str | None) -> Priority:
    if level == "high":
        return "high"
    if level == "medium":
        return "medium"
    return "low"


def _request_id(record: dict[str, Any]) -> str | None:
    if record.get("request_id") is not None:
        return str(record["request_id"])
    request_ref = record.get("request_ref")
    if isinstance(request_ref, dict) and request_ref.get("source_request_id") is not None:
        return str(request_ref["source_request_id"])
    return None


def _source_id(record: dict[str, Any], fallback: str) -> str:
    for key in ("assessment_id", "candidate_id", "event_id", "chunk_id", "finding_id", "source_id"):
        if record.get(key) is not None:
            return str(record[key])
    return fallback


def task_from_risk_assessment(record: dict[str, Any], *, sequence: int = 0) -> ReviewTask | None:
    """Create a review task from one risk-assessment record when review is required."""
    if not record.get("review_required"):
        return None
    source_id = _source_id(record, f"risk-{sequence}")
    hits = record.get("hits") if isinstance(record.get("hits"), list) else []
    categories = sorted(
        {str(hit.get("category")) for hit in hits if isinstance(hit, dict) and hit.get("category")}
    )
    rationale = "Review deterministic risk signals: " + (
        ", ".join(categories) if categories else "unspecified"
    )
    return ReviewTask(
        task_id=_stable_task_id("risk_review", source_id, rationale),
        request_id=_request_id(record),
        task_type="risk_review",
        priority=_priority_from_risk(str(record.get("risk_level") or "low")),
        source_record_type=str(record.get("source_record_type") or "risk_assessment"),
        source_id=source_id,
        title=f"Risk review for {source_id}",
        rationale=rationale,
        candidate_payload=record,
        required_reviewer_role="information_management_or_privacy_reviewer",
        created_at=datetime.now(UTC),
        agent_boundary=_agent_boundary(),
    )


def task_from_redaction_candidate(
    record: dict[str, Any], *, sequence: int = 0
) -> ReviewTask | None:
    """Create a human-review task from a non-dispositive redaction candidate."""
    if record.get("decision_status") == "human_reviewed":
        return None
    source_id = _source_id(record, f"redaction-{sequence}")
    span_type = str(record.get("span_type") or "candidate_span")
    confidence = float(record.get("confidence") or 0.0)
    priority: Priority = "high" if confidence >= 0.9 else "medium"
    rationale = f"Review candidate {span_type}; masked preview only, no redaction applied."
    return ReviewTask(
        task_id=_stable_task_id("redaction_candidate_review", source_id, rationale),
        request_id=_request_id(record),
        task_type="redaction_candidate_review",
        priority=priority,
        source_record_type=str(record.get("source_record_type") or "redaction_candidate"),
        source_id=source_id,
        title=f"Candidate sensitive-span review: {span_type}",
        rationale=rationale,
        candidate_payload=record,
        required_reviewer_role="authorised_foi_decision_support_reviewer",
        created_at=datetime.now(UTC),
        agent_boundary=_agent_boundary(),
    )


def task_from_core_event(record: dict[str, Any], *, sequence: int = 0) -> ReviewTask | None:
    """Create a review task for uncertified events that require human certification."""
    if not record.get("requires_human_certification"):
        return None
    certification = record.get("human_certification")
    if isinstance(certification, dict) and certification.get("certified") is True:
        return None
    source_id = _source_id(record, f"event-{sequence}")
    event_type = str(record.get("event_type") or "UnknownEvent")
    rationale = f"{event_type} requires human certification before it can be treated as certified."
    return ReviewTask(
        task_id=_stable_task_id("certification_boundary_review", source_id, rationale),
        request_id=_request_id(record),
        task_type="certification_boundary_review",
        priority="high",
        source_record_type="event",
        source_id=source_id,
        title=f"Certification boundary review: {event_type}",
        rationale=rationale,
        candidate_payload={
            "event_type": event_type,
            "assertion_status": record.get("assertion_status"),
            "quality_flags": record.get("quality_flags", []),
            "machine_generated": record.get("machine_generated"),
        },
        required_reviewer_role="authorised_oia_decision_maker_or_delegate",
        created_at=datetime.now(UTC),
        agent_boundary=_agent_boundary(),
    )


def _dedupe_tasks(tasks: list[ReviewTask]) -> list[ReviewTask]:
    seen: set[str] = set()
    deduped: list[ReviewTask] = []
    priority_order = {"urgent": 0, "high": 1, "medium": 2, "low": 3}
    for task in sorted(tasks, key=lambda item: (priority_order[item.priority], item.task_id)):
        if task.task_id in seen:
            continue
        seen.add(task.task_id)
        deduped.append(task)
    return deduped


def build_review_tasks(
    *,
    risks_jsonl: Path | None = None,
    redaction_candidates_jsonl: Path | None = None,
    events_jsonl: Path | None = None,
) -> list[ReviewTask]:
    """Build a deterministic human-review queue from optional artefact streams."""
    tasks: list[ReviewTask] = []
    if risks_jsonl is not None:
        for sequence, record in enumerate(iter_jsonl(risks_jsonl)):
            task = task_from_risk_assessment(record, sequence=sequence)
            if task is not None:
                tasks.append(task)
    if redaction_candidates_jsonl is not None:
        for sequence, record in enumerate(iter_jsonl(redaction_candidates_jsonl)):
            task = task_from_redaction_candidate(record, sequence=sequence)
            if task is not None:
                tasks.append(task)
    if events_jsonl is not None:
        for sequence, record in enumerate(iter_jsonl(events_jsonl)):
            task = task_from_core_event(record, sequence=sequence)
            if task is not None:
                tasks.append(task)
    return _dedupe_tasks(tasks)


def write_review_queue(
    output_jsonl: Path,
    *,
    risks_jsonl: Path | None = None,
    redaction_candidates_jsonl: Path | None = None,
    events_jsonl: Path | None = None,
) -> dict[str, Any]:
    """Write review tasks to JSONL and return a summary."""
    tasks = build_review_tasks(
        risks_jsonl=risks_jsonl,
        redaction_candidates_jsonl=redaction_candidates_jsonl,
        events_jsonl=events_jsonl,
    )
    records = [task.model_dump(mode="json", exclude_none=True) for task in tasks]
    write_jsonl(output_jsonl, records)
    priority_counts = {"low": 0, "medium": 0, "high": 0, "urgent": 0}
    task_type_counts: dict[str, int] = {}
    for record in records:
        priority_counts[str(record["priority"])] += 1
        task_type = str(record["task_type"])
        task_type_counts[task_type] = task_type_counts.get(task_type, 0) + 1
    return {
        "ok": True,
        "output": str(output_jsonl),
        "task_count": len(records),
        "priority_counts": priority_counts,
        "task_type_counts": task_type_counts,
    }

"""Deterministic process-advice generator for OIA workflow support.

Advice emitted here is operational and preparatory only. It can suggest next safe
steps, missing evidence, and review needs, but it cannot decide release/refusal,
redaction, charges, extensions, transfers, or review outcomes.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from foi_o_nz.io import iter_jsonl, write_json

_TERMINAL_STATES = {
    "ReleasedInFull",
    "ReleasedInPart",
    "Refused",
    "Withdrawn",
    "Closed",
    "NoRecordsFound",
}
_DISPOSITIVE_EVENTS = {
    "DecisionCommunicated",
    "ReleaseMade",
    "RefusalCommunicated",
    "ChargeNoticeSent",
    "ExtensionNotified",
    "TransferNotified",
    "HumanDecisionCertified",
}


def _request_id_from_event(event: dict[str, Any]) -> str | None:
    request_ref = event.get("request_ref")
    if isinstance(request_ref, dict) and request_ref.get("source_request_id") is not None:
        return str(request_ref["source_request_id"])
    if event.get("request_id") is not None:
        return str(event["request_id"])
    return None


def _load_request(requests_jsonl: Path, request_id: str) -> dict[str, Any]:
    for record in iter_jsonl(requests_jsonl):
        if str(record.get("request_id")) == str(request_id):
            return record
    raise ValueError(f"request_id not found: {request_id}")


def _load_events(events_jsonl: Path | None, request_id: str) -> list[dict[str, Any]]:
    if events_jsonl is None:
        return []
    return [
        record
        for record in iter_jsonl(events_jsonl)
        if _request_id_from_event(record) == str(request_id)
    ]


def _event_types(events: list[dict[str, Any]]) -> set[str]:
    return {str(event.get("event_type")) for event in events if event.get("event_type")}


def build_process_advice(
    *,
    request_id: str,
    requests_jsonl: Path,
    events_jsonl: Path | None = None,
    review_queue_jsonl: Path | None = None,
) -> dict[str, Any]:
    """Build an operational advice report for one request."""
    request = _load_request(requests_jsonl, request_id)
    events = _load_events(events_jsonl, request_id)
    types = _event_types(events)
    current_state = request.get("normalised_state") or request.get("source_state") or "Unknown"
    next_safe_actions: list[dict[str, Any]] = []
    warnings: list[str] = []
    missing_artifacts: list[str] = []
    required_human_reviews: list[dict[str, Any]] = []

    if not events:
        missing_artifacts.append("core_event_stream")
        next_safe_actions.append(
            {
                "action": "extract_events",
                "legal_effect": "none",
                "rationale": "No event stream was supplied for the request.",
            }
        )
    if "RequestObserved" not in types:
        missing_artifacts.append("RequestObserved")
    if "DeadlineCalculated" not in types:
        next_safe_actions.append(
            {
                "action": "calculate_deadline",
                "legal_effect": "preparatory",
                "rationale": "No indicative deadline event is present.",
            }
        )
    if "SearchPlanDrafted" not in types and str(current_state) not in _TERMINAL_STATES:
        next_safe_actions.append(
            {
                "action": "draft_search_plan",
                "legal_effect": "preparatory",
                "rationale": "A search plan is useful before document identification or consultation.",
            }
        )
    if "DecisionPackDrafted" not in types and any(
        t in types for t in ("RecordsIdentified", "SearchPerformed")
    ):
        next_safe_actions.append(
            {
                "action": "draft_decision_pack",
                "legal_effect": "preparatory",
                "rationale": "Search/document-identification events are present but no decision pack has been drafted.",
            }
        )

    uncertified_dispositive = []
    for event in events:
        event_type = str(event.get("event_type"))
        if event_type not in _DISPOSITIVE_EVENTS:
            continue
        certification = event.get("human_certification")
        if not isinstance(certification, dict) or certification.get("certified") is not True:
            uncertified_dispositive.append(event_type)
    if uncertified_dispositive:
        required_human_reviews.append(
            {
                "review_type": "certification_boundary",
                "event_types": sorted(set(uncertified_dispositive)),
                "rationale": "Dispositive/process-altering events require authorised human certification before being treated as certified.",
            }
        )

    if review_queue_jsonl is not None:
        queue_tasks = [
            record
            for record in iter_jsonl(review_queue_jsonl)
            if str(record.get("request_id")) == str(request_id)
        ]
        for task in queue_tasks[:20]:
            required_human_reviews.append(
                {
                    "review_type": task.get("task_type"),
                    "priority": task.get("priority"),
                    "task_id": task.get("task_id"),
                    "rationale": task.get("rationale"),
                }
            )

    if str(current_state) in _TERMINAL_STATES:
        warnings.append(
            "Request appears to be in a terminal or outcome-like state; do not infer legal correctness from platform state alone."
        )
    if request.get("state_mapping", {}).get("method") != "manual":
        warnings.append(
            "State mapping is not manually certified and should remain observed/inferred metadata."
        )

    blocked_actions = [
        {"action": "certify_release", "reason": "reserved for authorised human decision-maker"},
        {"action": "certify_refusal", "reason": "reserved for authorised human decision-maker"},
        {
            "action": "apply_redaction",
            "reason": "candidate redaction spans require authorised review against applicable law",
        },
        {
            "action": "send_correspondence",
            "reason": "outbound correspondence must be human-approved outside this workbench",
        },
    ]
    confidence = 0.82 if events else 0.55
    if required_human_reviews:
        confidence = min(confidence, 0.72)
    return {
        "schema_version": "foi-o-nz.process-advice.v0.1.0",
        "request_id": str(request_id),
        "current_state": str(current_state),
        "event_count": len(events),
        "event_types": sorted(types),
        "next_safe_actions": next_safe_actions,
        "blocked_actions": blocked_actions,
        "missing_artifacts": missing_artifacts,
        "required_human_reviews": required_human_reviews,
        "warnings": warnings,
        "confidence": confidence,
        "legal_effect": "none_preparatory_only",
    }


def write_process_advice(
    output: Path,
    *,
    request_id: str,
    requests_jsonl: Path,
    events_jsonl: Path | None = None,
    review_queue_jsonl: Path | None = None,
) -> dict[str, Any]:
    """Write process advice as JSON."""
    report = build_process_advice(
        request_id=request_id,
        requests_jsonl=requests_jsonl,
        events_jsonl=events_jsonl,
        review_queue_jsonl=review_queue_jsonl,
    )
    write_json(output, report)
    return report

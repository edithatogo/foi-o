"""Evaluation helpers for request/event extraction experiments."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from foi_o_nz.io import iter_jsonl, write_json

MatchMode = Literal["event_type", "event_type_state", "strict"]


def _request_id(event: dict[str, Any]) -> str:
    request_ref = event.get("request_ref")
    if isinstance(request_ref, dict):
        return str(request_ref.get("source_request_id") or request_ref.get("url_title") or "unknown")
    return str(event.get("request_id") or "unknown")


def event_match_key(event: dict[str, Any], *, mode: MatchMode = "event_type_state") -> tuple[str, ...]:
    """Return a comparison key for an extracted event."""
    request_id = _request_id(event)
    event_type = str(event.get("event_type") or "Unknown")
    state = str(event.get("lifecycle_state_after") or "Unknown")
    if mode == "event_type":
        return (request_id, event_type)
    if mode == "event_type_state":
        return (request_id, event_type, state)
    if mode == "strict":
        return (
            request_id,
            event_type,
            state,
            str(event.get("assertion_status") or "unknown"),
            str(round(float(event.get("confidence") or 0.0), 2)),
        )
    raise ValueError(f"unsupported match mode: {mode}")


def evaluate_event_extraction(
    predicted: list[dict[str, Any]],
    gold: list[dict[str, Any]],
    *,
    mode: MatchMode = "event_type_state",
) -> dict[str, Any]:
    """Compute set-based precision/recall/F1 for event extraction."""
    predicted_keys = {event_match_key(event, mode=mode) for event in predicted}
    gold_keys = {event_match_key(event, mode=mode) for event in gold}
    true_positive = len(predicted_keys & gold_keys)
    false_positive = len(predicted_keys - gold_keys)
    false_negative = len(gold_keys - predicted_keys)
    precision = true_positive / (true_positive + false_positive) if predicted_keys else 0.0
    recall = true_positive / (true_positive + false_negative) if gold_keys else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "mode": mode,
        "predicted_count": len(predicted_keys),
        "gold_count": len(gold_keys),
        "true_positive": true_positive,
        "false_positive": false_positive,
        "false_negative": false_negative,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "false_positive_keys": [list(key) for key in sorted(predicted_keys - gold_keys)[:100]],
        "false_negative_keys": [list(key) for key in sorted(gold_keys - predicted_keys)[:100]],
    }


def evaluate_event_jsonl(
    predicted_path: Path,
    gold_path: Path,
    *,
    mode: MatchMode = "event_type_state",
    output: Path | None = None,
) -> dict[str, Any]:
    """Evaluate predicted JSONL events against gold JSONL events."""
    result = evaluate_event_extraction(
        list(iter_jsonl(predicted_path)),
        list(iter_jsonl(gold_path)),
        mode=mode,
    )
    if output is not None:
        write_json(output, result)
    return result

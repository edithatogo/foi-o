"""Annotation export helpers for human-in-the-loop review surfaces."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from foi_o_nz.io import iter_jsonl, write_json, write_jsonl

AnnotationFormat = Literal["foio", "label-studio"]


def _task_text(task: dict[str, Any]) -> str:
    payload = task.get("candidate_payload") if isinstance(task.get("candidate_payload"), dict) else {}
    snippets: list[str] = [str(task.get("title") or "Review task"), str(task.get("rationale") or "")]
    for key in ("masked_preview", "span_type", "risk_level", "event_type"):
        if payload.get(key) is not None:
            snippets.append(f"{key}: {payload[key]}")
    return "\n".join(part for part in snippets if part)


def review_task_to_annotation(task: dict[str, Any]) -> dict[str, Any]:
    """Convert a review-task record into a neutral annotation task."""
    return {
        "schema_version": "foi-o-nz.annotation-task.v0.1.0",
        "annotation_id": f"foio-nz:annotation:{task.get('task_id')}",
        "task_id": task.get("task_id"),
        "request_id": task.get("request_id"),
        "source_id": task.get("source_id"),
        "priority": task.get("priority"),
        "task_type": task.get("task_type"),
        "text": _task_text(task),
        "labels": [],
        "annotation_status": "unlabelled",
        "instructions": [
            "Decide whether the candidate signal is relevant to workflow review.",
            "Do not record final release/refusal/redaction decisions in this annotation artefact.",
        ],
        "agent_boundary": task.get("agent_boundary", {}),
    }


def annotation_to_label_studio(annotation: dict[str, Any]) -> dict[str, Any]:
    """Convert a neutral annotation task to Label Studio JSON task shape."""
    return {
        "data": {
            "text": annotation["text"],
            "request_id": annotation.get("request_id"),
            "task_id": annotation.get("task_id"),
            "priority": annotation.get("priority"),
            "task_type": annotation.get("task_type"),
        },
        "meta": {
            "schema_version": annotation["schema_version"],
            "annotation_id": annotation["annotation_id"],
            "agent_boundary": annotation.get("agent_boundary", {}),
        },
    }


def write_annotation_tasks(
    review_queue_jsonl: Path,
    output: Path,
    *,
    fmt: AnnotationFormat = "foio",
) -> dict[str, Any]:
    """Write annotation tasks from a review queue."""
    annotations = [review_task_to_annotation(record) for record in iter_jsonl(review_queue_jsonl)]
    if fmt == "label-studio":
        data: Any = [annotation_to_label_studio(annotation) for annotation in annotations]
        write_json(output, data)
    else:
        write_jsonl(output, annotations)
    return {"ok": True, "output": str(output), "format": fmt, "annotation_count": len(annotations)}

"""Gold-set sampling and annotation task builders for FOI-O NZ."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from foi_o_nz.constants import GOLDSET_TASK_SCHEMA_VERSION
from foi_o_nz.io import iter_jsonl, write_json, write_jsonl

RecordKind = Literal["request", "event", "chunk", "risk", "review_task"]


class GoldsetTask(BaseModel):
    """One bounded annotation task for human review/evaluation."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["foi-o-nz.goldset-task.v0.1.0"] = GOLDSET_TASK_SCHEMA_VERSION
    task_id: str
    task_type: Literal[
        "state_mapping",
        "event_extraction",
        "risk_triage",
        "redaction_candidate",
        "retrieval_relevance",
    ]
    source_id: str
    request_id: str | None = None
    priority: Literal["low", "medium", "high"]
    text: str = Field(min_length=1)
    candidate_labels: list[str]
    prefilled_label: str | None = None
    evidence: dict[str, Any] = Field(default_factory=dict)
    instructions: str
    decision_boundary: str = "Annotation supports evaluation only; it does not certify an OIA decision."


def _record_id(record: dict[str, Any], sequence: int) -> str:
    for key in ("request_id", "event_id", "chunk_id", "assessment_id", "task_id", "source_id"):
        if record.get(key) is not None:
            return str(record[key])
    return f"record-{sequence}"


def _stratum(record: dict[str, Any], kind: str) -> str:
    if kind == "request":
        return f"authority={record.get('authority', 'unknown')}|state={record.get('normalised_state') or record.get('source_state') or 'unknown'}"
    if kind == "event":
        return f"event_type={record.get('event_type', 'unknown')}|assertion={record.get('assertion_status', 'unknown')}"
    if kind == "risk":
        return f"risk={record.get('risk_level', 'unknown')}|review={record.get('review_required', 'unknown')}"
    if kind == "review_task":
        return f"task={record.get('task_type', 'unknown')}|priority={record.get('priority', 'unknown')}"
    return f"kind={kind}"


def _score(seed: str, record_id: str) -> str:
    return sha256(f"{seed}\0{record_id}".encode("utf-8")).hexdigest()


def sample_goldset_records(
    input_jsonl: Path,
    *,
    kind: RecordKind,
    limit: int = 100,
    seed: str = "foi-o-nz-goldset-v0.1",
    per_stratum: int = 10,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Sample records deterministically with a light stratum cap."""
    if limit < 1:
        raise ValueError("limit must be >= 1")
    candidates: list[tuple[str, str, dict[str, Any]]] = []
    for sequence, record in enumerate(iter_jsonl(input_jsonl)):
        rid = _record_id(record, sequence)
        candidates.append((_stratum(record, kind), _score(seed, rid), record))
    selected: list[dict[str, Any]] = []
    stratum_counts: dict[str, int] = {}
    for stratum, _digest, record in sorted(candidates, key=lambda item: (item[0], item[1])):
        if len(selected) >= limit:
            break
        if stratum_counts.get(stratum, 0) >= per_stratum:
            continue
        rid = _record_id(record, len(selected))
        selected.append(
            {
                "schema_version": "foi-o-nz.goldset-item.v0.1.0",
                "record_id": rid,
                "record_kind": kind,
                "stratum": stratum,
                "sampling_seed": seed,
                "source_record": record,
                "annotation_status": "unlabelled",
                "labels": {},
            }
        )
        stratum_counts[stratum] = stratum_counts.get(stratum, 0) + 1
    manifest = {
        "schema_version": "foi-o-nz.goldset-manifest.v0.1.0",
        "input": str(input_jsonl),
        "record_kind": kind,
        "candidate_count": len(candidates),
        "selected_count": len(selected),
        "limit": limit,
        "per_stratum": per_stratum,
        "seed": seed,
        "stratum_counts": stratum_counts,
        "limitations": [
            "Deterministic sample for evaluation planning only; not statistically representative unless the source corpus and strata are externally justified.",
        ],
    }
    return selected, manifest


def write_goldset_sample(
    input_jsonl: Path,
    output_jsonl: Path,
    manifest_output: Path,
    *,
    kind: RecordKind,
    limit: int = 100,
    seed: str = "foi-o-nz-goldset-v0.1",
    per_stratum: int = 10,
) -> dict[str, Any]:
    """Write a sampled gold-set candidate JSONL and manifest."""
    records, manifest = sample_goldset_records(
        input_jsonl,
        kind=kind,
        limit=limit,
        seed=seed,
        per_stratum=per_stratum,
    )
    write_jsonl(output_jsonl, records)
    write_json(manifest_output, manifest)
    return {"ok": True, "output": str(output_jsonl), "manifest_output": str(manifest_output), **manifest}


def _task_id(kind: str, source_id: str, text: str) -> str:
    return f"foio-nz:gold:{sha256(f'{kind}\0{source_id}\0{text}'.encode('utf-8')).hexdigest()[:24]}"


def _prefilled_risk_label(risk: dict[str, Any] | None) -> str | None:
    if risk is None:
        return None
    hits = risk.get("hits") if isinstance(risk.get("hits"), list) else []
    categories = {str(hit.get("category")) for hit in hits if isinstance(hit, dict)}
    if "health_information" in categories:
        return "health"
    if "personal_information" in categories:
        return "privacy"
    if "withholding_or_redaction" in categories:
        return "withholding_language"
    if "ai_workload" in categories:
        return "ai_generated_request"
    return "no_review_trigger" if not categories else sorted(categories)[0]


def tasks_from_chunks(chunks: list[dict[str, Any]], risks: list[dict[str, Any]] | None = None) -> list[GoldsetTask]:
    """Build annotation tasks from chunks plus optional risk assessments."""
    risk_by_source = {str(item.get("source_id")): item for item in risks or []}
    tasks: list[GoldsetTask] = []
    for chunk in chunks:
        source_id = str(chunk.get("chunk_id") or chunk.get("source_id") or "unknown")
        text = str(chunk.get("text") or "")
        if not text:
            continue
        risk = risk_by_source.get(source_id)
        raw_priority = str(risk.get("risk_level", "medium")) if risk is not None else "medium"
        priority: Literal["low", "medium", "high"] = raw_priority if raw_priority in {"low", "medium", "high"} else "medium"  # type: ignore[assignment]
        tasks.append(
            GoldsetTask(
                task_id=_task_id("risk_triage", source_id, text),
                task_type="risk_triage",
                source_id=source_id,
                request_id=str(chunk.get("request_id")) if chunk.get("request_id") is not None else None,
                priority=priority,
                text=text,
                candidate_labels=[
                    "no_review_trigger",
                    "privacy",
                    "health",
                    "commercial",
                    "withholding_language",
                    "ai_generated_request",
                    "other",
                ],
                prefilled_label=_prefilled_risk_label(risk) if risk is not None else None,
                evidence={"risk_assessment": risk} if risk is not None else {},
                instructions="Select all review-trigger categories that apply. Do not decide release/refusal/redaction.",
            )
        )
    return tasks


def write_goldset_tasks(
    chunks_jsonl: Path,
    output: Path,
    *,
    risks_jsonl: Path | None = None,
    summary_output: Path | None = None,
) -> dict[str, Any]:
    """Write annotation tasks as JSONL and optional summary JSON."""
    chunks = list(iter_jsonl(chunks_jsonl))
    risks = list(iter_jsonl(risks_jsonl)) if risks_jsonl is not None else None
    tasks = tasks_from_chunks(chunks, risks)
    records = [task.model_dump(mode="json", exclude_none=True) for task in tasks]
    write_jsonl(output, records)
    priority_counts = {"low": 0, "medium": 0, "high": 0}
    for task in tasks:
        priority_counts[task.priority] += 1
    summary = {
        "ok": True,
        "output": str(output),
        "task_count": len(tasks),
        "priority_counts": priority_counts,
        "task_type_counts": {"risk_triage": len(tasks)},
        "limitations": ["Tasks are for evaluation/annotation only and do not certify OIA decisions."],
    }
    if summary_output is not None:
        write_json(summary_output, summary)
    return summary

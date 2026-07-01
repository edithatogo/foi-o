"""Deterministic trace-span helpers for agent and pipeline replay."""

from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from foi_o_nz.cas import digest_file
from foi_o_nz.constants import TRACE_SPAN_SCHEMA_VERSION
from foi_o_nz.io import write_jsonl


class TraceSpan(BaseModel):
    """A minimal OpenTelemetry/W3C-inspired span for local FOI-O runs."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["foi-o-nz.trace-span.v0.1.0"] = TRACE_SPAN_SCHEMA_VERSION
    trace_id: str = Field(min_length=32, max_length=32)
    span_id: str = Field(min_length=16, max_length=16)
    parent_span_id: str | None = Field(default=None, min_length=16, max_length=16)
    name: str
    started_at: datetime
    ended_at: datetime
    status: Literal["ok", "error", "unknown"] = "ok"
    attributes: dict[str, Any] = Field(default_factory=dict)
    links: list[dict[str, Any]] = Field(default_factory=list)


def make_trace_id(seed: str) -> str:
    """Return a deterministic 16-byte hex trace ID."""
    return sha256(seed.encode("utf-8")).hexdigest()[:32]


def make_span_id(seed: str) -> str:
    """Return a deterministic 8-byte hex span ID."""
    return sha256(seed.encode("utf-8")).hexdigest()[:16]


def build_artifact_trace_spans(paths: list[Path], *, run_name: str = "foi-o-nz-local-run") -> list[TraceSpan]:
    """Build one root span plus one artifact-observed span per file."""
    now = datetime.now(UTC)
    trace_seed = "|".join([run_name, *[str(path) for path in paths]])
    trace_id = make_trace_id(trace_seed)
    root_id = make_span_id(f"{trace_id}:root")
    spans = [
        TraceSpan(
            trace_id=trace_id,
            span_id=root_id,
            name=run_name,
            started_at=now,
            ended_at=now,
            attributes={"artifact_count": len(paths), "agent_boundary": "process-support-only"},
        )
    ]
    for ordinal, path in enumerate(sorted(paths, key=lambda value: str(value))):
        digest, byte_size = digest_file(path)
        spans.append(
            TraceSpan(
                trace_id=trace_id,
                span_id=make_span_id(f"{trace_id}:{ordinal}:{path}:{digest}"),
                parent_span_id=root_id,
                name="artifact.observed",
                started_at=now,
                ended_at=now,
                attributes={
                    "path": str(path),
                    "sha256": digest,
                    "byte_size": byte_size,
                    "sequence": ordinal,
                },
                links=[{"type": "content-address", "uri": f"sha256:{digest}"}],
            )
        )
    return spans


def write_trace_spans(paths: list[Path], output: Path, *, run_name: str = "foi-o-nz-local-run") -> dict[str, Any]:
    """Write trace spans as JSONL."""
    spans = build_artifact_trace_spans(paths, run_name=run_name)
    write_jsonl(output, [span.model_dump(mode="json", exclude_none=True) for span in spans])
    return {
        "ok": True,
        "output": str(output),
        "trace_id": spans[0].trace_id,
        "span_count": len(spans),
        "run_name": run_name,
    }

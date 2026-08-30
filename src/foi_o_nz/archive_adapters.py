"""Archive execution adapters for resilient remote crawling and pipeline execution."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@dataclass
class RetryPolicy:
    """Bounded retry policy for archive operations."""

    max_retries: int = 5
    base_delay_seconds: float = 1.0
    max_delay_seconds: float = 60.0
    backoff_multiplier: float = 2.0
    retryable_status_codes: set[int] = field(default_factory=lambda: {429, 500, 502, 503, 504})
    terminal_status_codes: set[int] = field(default_factory=lambda: {404, 410, 451})

    def is_retryable(self, status_code: int) -> bool:
        """Determine if an HTTP status code is transient and retryable."""
        return status_code in self.retryable_status_codes

    def compute_backoff(self, attempt: int) -> float:
        """Compute exponential backoff delay in seconds."""
        delay = self.base_delay_seconds * (self.backoff_multiplier ** max(0, attempt - 1))
        return min(delay, self.max_delay_seconds)


class ArchiveCheckpointManager:
    """Manage durable, content-addressed checkpoints during batch execution."""

    def __init__(self, checkpoint_dir: Path, definition_sha256: str) -> None:
        """Initialize the checkpoint manager with a root directory and definition SHA."""
        self.checkpoint_dir = checkpoint_dir
        self.definition_sha256 = definition_sha256
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def save_checkpoint(
        self,
        stage_name: str,
        processed_units: list[dict[str, Any]],
        stage_output_sha256: str,
    ) -> Path:
        """Save a deterministic checkpoint file for the current stage."""
        payload = {
            "schema_version": "foi-o.archive-checkpoint.v1",
            "stage_name": stage_name,
            "definition_sha256": self.definition_sha256,
            "stage_output_sha256": stage_output_sha256,
            "processed_count": len(processed_units),
            "units": processed_units,
        }
        raw_bytes = json.dumps(payload, sort_keys=True, indent=2).encode("utf-8")
        checkpoint_sha = _sha256_bytes(raw_bytes)
        payload["checkpoint_sha256"] = checkpoint_sha

        checkpoint_path = (
            self.checkpoint_dir / f"checkpoint_{stage_name}_{checkpoint_sha[:16]}.json"
        )
        checkpoint_path.write_text(
            json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8"
        )
        return checkpoint_path

    def load_latest_checkpoint(self, stage_name: str) -> dict[str, Any] | None:
        """Find and validate the latest checkpoint matching the stage and definition."""
        candidates = sorted(self.checkpoint_dir.glob(f"checkpoint_{stage_name}_*.json"))
        if not candidates:
            return None

        latest = candidates[-1]
        data = json.loads(latest.read_text(encoding="utf-8"))
        if data.get("definition_sha256") != self.definition_sha256:
            raise ValueError(
                f"checkpoint definition mismatch: expected {self.definition_sha256}, got {data.get('definition_sha256')}"
            )
        return data


class MetadataFirstSelector:
    """Two-stage classifier: fast metadata filtering followed by bounded fulltext selection."""

    def __init__(self, target_jurisdiction: str, max_fulltext_units: int = 500) -> None:
        """Initialize the selector with target jurisdiction and max unit limits."""
        self.target_jurisdiction = target_jurisdiction
        self.max_fulltext_units = max_fulltext_units

    def filter_metadata_rows(self, raw_cdx_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Filter metadata rows to isolate jurisdiction-eligible requests."""
        eligible = []
        for record in raw_cdx_records:
            jurisdiction = record.get("jurisdiction") or record.get("inferred_jurisdiction")
            status = record.get("http_status", 200)
            if status == 200 and (jurisdiction == self.target_jurisdiction or jurisdiction is None):
                eligible.append(record)
        return eligible

    def select_for_fulltext(
        self, eligible_records: list[dict[str, Any]]
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Split eligible metadata into selected batch and remaining backlog."""
        sorted_records = sorted(
            eligible_records,
            key=lambda r: (r.get("request_id", ""), r.get("archive_timestamp", "")),
        )
        selected = sorted_records[: self.max_fulltext_units]
        backlog = sorted_records[self.max_fulltext_units :]
        return selected, backlog

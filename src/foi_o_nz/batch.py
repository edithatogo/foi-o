"""Batch normalisation helpers for multiple FYI archive manifests."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from foi_o_nz.io import read_json_records, write_json, write_jsonl
from foi_o_nz.manifest import build_run_manifest
from foi_o_nz.normalise import normalise_records, write_optional_parquet


def discover_input_files(paths: list[Path]) -> list[Path]:
    """Resolve files/directories/globs into a stable manifest file list."""
    out: list[Path] = []
    for path in paths:
        if any(ch in str(path) for ch in "*?[]"):
            out.extend(Path().glob(str(path)))
        elif path.is_dir():
            out.extend(sorted(path.glob("*.json")))
            out.extend(sorted(path.glob("*.jsonl")))
        elif path.exists():
            out.append(path)
        else:
            raise FileNotFoundError(path)
    return sorted(dict.fromkeys(file for file in out if file.is_file()))


def normalise_manifest_batch(
    inputs: list[Path],
    *,
    requests_output: Path,
    events_output: Path,
    parquet_dir: Path | None = None,
    run_manifest_output: Path | None = None,
) -> dict[str, Any]:
    """Normalise multiple manifest files into combined request/event streams."""
    input_files = discover_input_files(inputs)
    raw_records: list[dict[str, Any]] = []
    per_input_counts: dict[str, int] = {}
    for input_file in input_files:
        records = read_json_records(input_file)
        raw_records.extend(records)
        per_input_counts[str(input_file)] = len(records)
    profiles, events = normalise_records(raw_records)
    request_dicts = [profile.model_dump(mode="json", exclude_none=True) for profile in profiles]
    event_dicts = [event.model_dump(mode="json", exclude_none=True) for event in events]
    request_count = write_jsonl(requests_output, request_dicts)
    event_count = write_jsonl(events_output, event_dicts)
    parquet_written: list[str] = []
    if parquet_dir is not None:
        parquet_written = write_optional_parquet(
            parquet_dir,
            request_dicts=request_dicts,
            event_dicts=event_dicts,
        )
    result: dict[str, Any] = {
        "input_files": [str(path) for path in input_files],
        "per_input_counts": per_input_counts,
        "requests_output": str(requests_output),
        "events_output": str(events_output),
        "request_count": request_count,
        "event_count": event_count,
        "parquet_written": parquet_written,
    }
    if run_manifest_output is not None:
        outputs = [requests_output, events_output, *[Path(path) for path in parquet_written]]
        manifest = build_run_manifest(
            input_path=input_files[0] if input_files else Path("<empty-batch>"),
            outputs=outputs,
            counts={"requests": request_count, "events": event_count},
            command="normalise-batch",
        )
        manifest["inputs"] = [str(path) for path in input_files]
        manifest["per_input_counts"] = per_input_counts
        write_json(run_manifest_output, manifest)
        result["run_manifest_output"] = str(run_manifest_output)
    return result

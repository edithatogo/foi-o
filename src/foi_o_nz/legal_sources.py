"""Legal and guidance source versioning helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from foi_o_nz.dates import parse_datetime

SOURCE_REQUIRED_FIELDS = {
    "title",
    "kind",
    "canonical_uri",
    "work_id",
    "version_id",
    "retrieved_at",
    "source_status",
}
REFERENCE_REQUIRED_FIELDS = {
    "source_id",
    "reference",
    "concept",
    "uri",
    "work_id",
    "version_id",
    "retrieved_at",
    "source_status",
    "applicability_basis",
}
ALLOWED_SOURCE_STATUS = {"official_snapshot", "external_gate", "deprecated", "unknown"}
ALLOWED_APPLICABILITY_BASIS = {
    "current_at_event_time",
    "current_at_extraction_time",
    "unknown",
}


def load_legal_source_mapping(path: Path) -> dict[str, Any]:
    """Load the source-versioned legal source mapping."""
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected mapping object in {path}")
    return data


def _missing_fields(record: dict[str, Any], required: set[str]) -> list[str]:
    return sorted(field for field in required if record.get(field) in {None, ""})


def validate_legal_source_mapping(path: Path) -> dict[str, Any]:
    """Validate source and reference records for source-version metadata."""
    mapping = load_legal_source_mapping(path)
    errors: list[str] = []
    sources = mapping.get("sources")
    if not isinstance(sources, dict):
        errors.append("sources: expected mapping")
        sources = {}
    for source_id, source in sources.items():
        if not isinstance(source, dict):
            errors.append(f"sources.{source_id}: expected mapping")
            continue
        for field in _missing_fields(source, SOURCE_REQUIRED_FIELDS):
            errors.append(f"sources.{source_id}.{field}: required")
        if source.get("source_status") not in ALLOWED_SOURCE_STATUS:
            errors.append(f"sources.{source_id}.source_status: unsupported value")
        if source.get("retrieved_at") and parse_datetime(source.get("retrieved_at")) is None:
            errors.append(f"sources.{source_id}.retrieved_at: invalid datetime")

    references = mapping.get("key_references_initial")
    if not isinstance(references, list):
        errors.append("key_references_initial: expected list")
        references = []
    for index, reference in enumerate(references):
        if not isinstance(reference, dict):
            errors.append(f"key_references_initial.{index}: expected mapping")
            continue
        for field in _missing_fields(reference, REFERENCE_REQUIRED_FIELDS):
            errors.append(f"key_references_initial.{index}.{field}: required")
        source_id = reference.get("source_id")
        if source_id not in sources:
            errors.append(f"key_references_initial.{index}.source_id: unknown source")
        if reference.get("source_status") not in ALLOWED_SOURCE_STATUS:
            errors.append(f"key_references_initial.{index}.source_status: unsupported value")
        if reference.get("applicability_basis") not in ALLOWED_APPLICABILITY_BASIS:
            errors.append(f"key_references_initial.{index}.applicability_basis: unsupported value")
        if reference.get("retrieved_at") and parse_datetime(reference.get("retrieved_at")) is None:
            errors.append(f"key_references_initial.{index}.retrieved_at: invalid datetime")

    return {
        "ok": not errors,
        "schema_version": mapping.get("schema_version"),
        "source_count": len(sources),
        "reference_count": len(references),
        "errors": errors,
    }


def build_legal_source_status(
    *,
    mapping_path: Path = Path("mappings/nz-legislation-sources.yaml"),
    live: bool = False,
    cache_dir: Path = Path("generated/legal-sources"),
) -> dict[str, Any]:
    """Report legal-source mapping status and fail closed for live-source checks."""
    mapping_report = validate_legal_source_mapping(mapping_path)
    warnings: list[str] = []
    live_source_status = "not_requested"
    ok = mapping_report["ok"]
    if live:
        if cache_dir.exists():
            live_source_status = "cache_available"
        else:
            live_source_status = "external_gate"
            ok = False
            warnings.append(
                "live_source_unavailable: no live retriever was run and no cache directory "
                "exists; use generated/legal-sources or another ignored cache path"
            )
    return {
        "ok": ok,
        "mapping_ok": mapping_report["ok"],
        "mapping_path": str(mapping_path),
        "source_count": mapping_report["source_count"],
        "reference_count": mapping_report["reference_count"],
        "errors": mapping_report["errors"],
        "live_requested": live,
        "live_source_status": live_source_status,
        "cache_dir": str(cache_dir),
        "warnings": warnings,
    }

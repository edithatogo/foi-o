"""Candidate OIA document-selection intervals for named-human legal review."""

from __future__ import annotations

from datetime import date
from hashlib import sha256
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field


class ApplicabilityIntervalCandidate(BaseModel):
    """Adjacent as-at dates, not an approved legal commencement finding."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    version_id: str = Field(min_length=1)
    valid_from_inclusive: date
    valid_to_exclusive: date | None
    derivation: Literal["adjacent_official_as_at_dates"] = "adjacent_official_as_at_dates"
    legal_applicability_approved: Literal[False] = False


class OiaApplicabilityIntervalCandidates(BaseModel):
    """Complete candidate interval sequence for the pinned OIA version index."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["foi-o.nz-oia-applicability-interval-candidates.v0.1.0"] = (
        "foi-o.nz-oia-applicability-interval-candidates.v0.1.0"
    )
    status: Literal["candidate_human_legal_review_required"] = (
        "candidate_human_legal_review_required"
    )
    source_index_path: Literal["mappings/nz-oia-version-index.yaml"] = (
        "mappings/nz-oia-version-index.yaml"
    )
    source_index_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    interval_count: int = Field(gt=0)
    intervals: tuple[ApplicabilityIntervalCandidate, ...]
    legal_applicability_approved: Literal[False] = False
    source_pack_promotion_allowed: Literal[False] = False
    required_review: Literal[
        "Verify each boundary against commencement and amendment evidence; as-at adjacency alone is not legal applicability."
    ] = "Verify each boundary against commencement and amendment evidence; as-at adjacency alone is not legal applicability."


def build_oia_interval_candidates(index_path: Path) -> OiaApplicabilityIntervalCandidates:
    """Build a deterministic adjacent-date review artifact from the pinned index."""
    index_bytes = index_path.read_bytes()
    payload = yaml.safe_load(index_bytes)
    if not isinstance(payload, dict) or payload.get("status") != "candidate":
        raise ValueError("OIA version index must remain candidate")
    versions = payload.get("versions")
    if not isinstance(versions, list) or not versions:
        raise ValueError("OIA version index must contain versions")
    parsed: list[tuple[str, date]] = []
    for version in versions:
        if not isinstance(version, dict):
            raise ValueError("OIA version entry must be an object")
        version_id = version.get("version_id")
        as_at = version.get("as_at")
        if not isinstance(version_id, str) or not isinstance(as_at, str):
            raise ValueError("OIA version requires version_id and as_at")
        parsed.append((version_id, date.fromisoformat(as_at)))
    if parsed != sorted(parsed, key=lambda item: item[1]):
        raise ValueError("OIA version dates must be strictly ordered")
    dates = [item[1] for item in parsed]
    if len(dates) != len(set(dates)):
        raise ValueError("OIA version dates must be unique")
    intervals = tuple(
        ApplicabilityIntervalCandidate(
            version_id=version_id,
            valid_from_inclusive=as_at,
            valid_to_exclusive=parsed[index + 1][1] if index + 1 < len(parsed) else None,
        )
        for index, (version_id, as_at) in enumerate(parsed)
    )
    return OiaApplicabilityIntervalCandidates(
        source_index_sha256=sha256(index_bytes).hexdigest(),
        interval_count=len(intervals),
        intervals=intervals,
    )


def write_oia_interval_candidates(index_path: Path, output_path: Path) -> Path:
    """Write stable YAML for named-human review."""
    payload = build_oia_interval_candidates(index_path).model_dump(mode="json")
    output_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return output_path

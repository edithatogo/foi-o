"""Build and verify the restricted-local AU RightToKnow immutable manifest."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from foi_o_nz.australian_cdx_completion_candidate import validate_completion_candidate
from foi_o_nz.australian_replay_candidate import validate_replay_candidate

PINNED_INPUTS = {
    "source_cdx": "954b0f80ad2a44038f364d240cc9baac815f252a43535c8403dec060ddb730bd",
    "replay_selection": "a1c2308ecc81de3754f37b3c26f7ba7fc232ff5bac930b86b36fb10463178c51",
    "normalized_replay": "3801b4b99de6152bfcaf5f093e00e137acb4ee5d636611ada75820aed55fd807",
    "classification_summary": "98eae70428e630cbd36849e5ad19c4133dbd9f01c413cf33221d2b0eef0091ab",
    "completion_candidate": "0dafc44c1b871357802282f138bf0e6e9d68f249a171c1d9627809bd928531c8",
    "completion_selection": "370a6d84e20a4bd260619209d84098458c9e72acf7e4e6f5cb3465cbaba88bb6",
}
MANIFEST_SCHEMA = "foi-o.au-rtk-restricted-immutable-manifest.v1"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_bytes(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def _assert_pin(path: Path, expected: str, label: str) -> None:
    if not path.is_file() or _sha256(path) != expected:
        raise ValueError(f"{label} SHA-256 does not match its approved pin")


def build_manifest(
    *,
    replay_selection: Path,
    normalized_replay: Path,
    classification_summary: Path,
    replay_root: Path,
    completion_candidate: Path,
    completion_selection: Path,
    query_plan: Path,
    response_bodies_root: Path,
    expected_inputs: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Build a manifest only when all approved inputs independently validate."""
    pins = expected_inputs or PINNED_INPUTS
    for key in PINNED_INPUTS:
        if key not in pins:
            raise ValueError(f"missing approved input pin: {key}")
    _assert_pin(replay_selection, pins["replay_selection"], "replay selection")
    _assert_pin(normalized_replay, pins["normalized_replay"], "normalized replay")
    _assert_pin(classification_summary, pins["classification_summary"], "classification summary")
    _assert_pin(completion_candidate, pins["completion_candidate"], "completion candidate")
    _assert_pin(completion_selection, pins["completion_selection"], "completion selection")

    replay = json.loads(replay_selection.read_text(encoding="utf-8"))
    if (
        replay.get("source_cdx_sha256") != pins["source_cdx"]
        or replay.get("record_count") != 2082
        or replay.get("json_count") != 1225
        or replay.get("html_fallback_count") != 857
    ):
        raise ValueError("replay selection does not define the approved 2,082-record population")
    replay_validation = validate_replay_candidate(classification_summary, replay_root=replay_root)
    completion_validation = validate_completion_candidate(
        completion_candidate,
        selection_path=completion_selection,
        query_plan_path=query_plan,
        response_bodies_root=response_bodies_root,
        expected_candidate_sha256=pins["completion_candidate"],
        expected_selection_sha256=pins["completion_selection"],
    )
    if (
        replay_validation["record_count"] != 2082
        or completion_validation["selected_slug_count"] != 0
        or completion_validation["no_capture_slug_count"] != 858
    ):
        raise ValueError("validated inputs would expand or alter the approved replay population")
    payload: dict[str, Any] = {
        "schema": MANIFEST_SCHEMA,
        "status": "immutable_restricted_local",
        "population": {
            "scope": "https://www.righttoknow.org.au/request/*",
            "record_count": 2082,
            "selection_rule": "latest successful canonical JSON; otherwise latest successful primary HTML",
            "json_count": 1225,
            "html_fallback_count": 857,
            "completion_additions": 0,
            "completion_no_capture_slugs": 858,
        },
        "jurisdiction_counts": replay_validation["counts"],
        "approved_inputs": pins,
        "boundaries": {
            "restricted_local": True,
            "archived_page_replay_extension_authorized": False,
            "empirical_freeze_authorized": False,
            "annotation_authorized": False,
            "publication_authorized": False,
            "redistribution_authorized": False,
            "training_authorized": False,
            "legal_certification_authorized": False,
            "profile_promotion_authorized": False,
        },
    }
    payload["manifest_sha256"] = hashlib.sha256(_canonical_bytes(payload)).hexdigest()
    return payload


def write_manifest(output: Path, **kwargs: Any) -> dict[str, Any]:
    """Create one canonical local manifest after fail-closed validation."""
    manifest = build_manifest(**kwargs)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(_canonical_bytes(manifest))
    return manifest


def validate_manifest(
    path: Path, *, expected_inputs: dict[str, str] | None = None
) -> dict[str, Any]:
    """Validate manifest structure, self-hash, pins, population, and boundaries."""
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("schema") != MANIFEST_SCHEMA:
        raise ValueError("manifest schema is invalid")
    manifest_sha256 = value.pop("manifest_sha256", None)
    if (
        not isinstance(manifest_sha256, str)
        or hashlib.sha256(_canonical_bytes(value)).hexdigest() != manifest_sha256
    ):
        raise ValueError("manifest self SHA-256 mismatch")
    if value.get("approved_inputs") != (expected_inputs or PINNED_INPUTS):
        raise ValueError("manifest input pins do not match approval")
    population = value.get("population")
    if not isinstance(population, dict) or (
        population.get("record_count"),
        population.get("completion_additions"),
        population.get("completion_no_capture_slugs"),
    ) != (2082, 0, 858):
        raise ValueError("manifest population is not the approved bounded population")
    boundaries = value.get("boundaries")
    if (
        not isinstance(boundaries, dict)
        or boundaries.get("restricted_local") is not True
        or any(value is not False for key, value in boundaries.items() if key != "restricted_local")
    ):
        raise ValueError("manifest boundaries are not restricted-local")
    return {"ok": True, "manifest_sha256": manifest_sha256, "record_count": 2082}

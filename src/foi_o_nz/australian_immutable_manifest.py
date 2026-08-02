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
FAILURE_DISPOSITION_SCHEMA = "foi-o.au-rtk-restricted-immutable-manifest.explicit-failures.v1"
FAILURE_DISPOSITION_CONFIRMATION = "FINALIZE_WITH_NINE_EXPLICIT_404_EXCLUSIONS"
EXPECTED_FAILURE_SLUGS = {
    "acting_treasurer_scott_morrisons",
    "inquiry_about_contact_tracing_ap",
    "inquiry_about_contact_tracing_ap_2",
    "inquiry_about_contact_tracing_ap_5",
    "inquiry_about_contact_tracing_ap_7",
    "masschallenge_contracts",
    "nuclear_fuel_cycle_activities_in",
    "number_of_approved_citizens_wait",
    "which_agencies_are_rbas_transact",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_bytes(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def _assert_pin(path: Path, expected: str, label: str) -> None:
    if not path.is_file() or _sha256(path) != expected:
        raise ValueError(f"{label} SHA-256 does not match its approved pin")


def validate_failure_disposition_inputs(
    *,
    replay_selection: Path,
    failure_ledger: Path,
    replay_index: Path,
    classification_summary: Path,
    approved_failure_ledger_sha256: str,
) -> dict[str, Any]:
    """Validate a complete 2,082-position population with nine explicit 404s."""
    _assert_pin(replay_selection, PINNED_INPUTS["replay_selection"], "replay selection")
    _assert_pin(
        failure_ledger,
        approved_failure_ledger_sha256,
        "approved failure ledger",
    )
    selection = json.loads(replay_selection.read_text(encoding="utf-8"))
    selected = {
        str(item["canonical_slug"]): item
        for item in selection.get("records", [])
        if isinstance(item, dict) and item.get("canonical_slug")
    }
    if (
        selection.get("source_cdx_sha256") != PINNED_INPUTS["source_cdx"]
        or selection.get("record_count") != 2082
        or len(selected) != 2082
    ):
        raise ValueError("replay selection is not the approved 2,082-position population")

    ledger = json.loads(failure_ledger.read_text(encoding="utf-8"))
    failures = ledger.get("failures")
    if (
        ledger.get("schema") != "foio.au-rtk-replay-failure-ledger.v1"
        or ledger.get("selection_sha256") != PINNED_INPUTS["replay_selection"]
        or ledger.get("failure_count") != 9
        or not isinstance(failures, list)
    ):
        raise ValueError("failure ledger contract is invalid")
    failure_slugs = {str(item.get("canonical_slug")) for item in failures}
    if failure_slugs != EXPECTED_FAILURE_SLUGS:
        raise ValueError("failure ledger membership is not the approved nine")
    for failure in failures:
        slug = str(failure["canonical_slug"])
        expected = selected[slug]
        for field in ("source_url", "archive_timestamp", "archive_digest", "media_kind"):
            if failure.get(field) != expected.get(field):
                raise ValueError(f"failure provenance mismatch for {slug}: {field}")
        if not str(failure.get("diagnostic", "")).startswith("Client error '404"):
            raise ValueError(f"failure is not an explicit HTTP 404: {slug}")

    replay_entries = [
        json.loads(line)
        for line in replay_index.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    replay_slugs = [str(item.get("canonical_slug")) for item in replay_entries]
    if (
        len(replay_slugs) != 2073
        or len(set(replay_slugs)) != 2073
        or set(replay_slugs) != set(selected) - failure_slugs
    ):
        raise ValueError("replay index does not exactly cover the successful positions")

    summary = json.loads(classification_summary.read_text(encoding="utf-8"))
    counts = summary.get("counts")
    if (
        summary.get("status") != "candidate_non_final"
        or summary.get("selection_sha256") != PINNED_INPUTS["replay_selection"]
        or summary.get("selected_record_count") != 2082
        or summary.get("captured_record_count") != 2073
        or summary.get("failure_count") != 9
        or not isinstance(counts, dict)
        or sum(counts.values()) != 2073
        or summary.get("replay_index", {}).get("sha256") != _sha256(replay_index)
    ):
        raise ValueError("classification summary does not match the failure disposition")
    return {
        "selection_count": 2082,
        "successful_count": 2073,
        "failure_count": 9,
        "failure_slugs": sorted(failure_slugs),
        "jurisdiction_counts": counts,
        "pins": {
            "replay_selection": _sha256(replay_selection),
            "failure_ledger": _sha256(failure_ledger),
            "replay_index": _sha256(replay_index),
            "classification_summary": _sha256(classification_summary),
        },
    }


def build_failure_disposition_manifest(
    *,
    replay_selection: Path,
    failure_ledger: Path,
    replay_index: Path,
    classification_summary: Path,
    approved_failure_ledger_sha256: str,
    authorization_confirmation: str,
) -> dict[str, Any]:
    """Build a restricted-local manifest with nine approved 404 exclusions."""
    if authorization_confirmation != FAILURE_DISPOSITION_CONFIRMATION:
        raise ValueError("explicit failure-disposition authorization is missing")
    validated = validate_failure_disposition_inputs(
        replay_selection=replay_selection,
        failure_ledger=failure_ledger,
        replay_index=replay_index,
        classification_summary=classification_summary,
        approved_failure_ledger_sha256=approved_failure_ledger_sha256,
    )
    payload: dict[str, Any] = {
        "schema": FAILURE_DISPOSITION_SCHEMA,
        "status": "immutable_restricted_local",
        "population": {
            "scope": "https://www.righttoknow.org.au/request/*",
            "selected_position_count": validated["selection_count"],
            "successful_capture_count": validated["successful_count"],
            "explicit_failure_count": validated["failure_count"],
            "empirical_full_text_unit_count": validated["successful_count"],
            "failure_slugs": validated["failure_slugs"],
        },
        "jurisdiction_counts": validated["jurisdiction_counts"],
        "approved_inputs": validated["pins"],
        "failure_disposition": {
            "kind": "explicit_http_404_exclusions",
            "empirical_full_text_eligible": False,
            "population_inference_eligible": False,
        },
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


def write_failure_disposition_manifest(output: Path, **kwargs: Any) -> dict[str, Any]:
    """Write a canonical failure-disposition manifest after strict validation."""
    manifest = build_failure_disposition_manifest(**kwargs)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(_canonical_bytes(manifest))
    return manifest


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

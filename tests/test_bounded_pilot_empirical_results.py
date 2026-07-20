import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from foi_o_nz.bounded_pilot_empirical_results import (
    ANALYST_IDS,
    RECONCILER_ID,
    build_analysis_set,
    build_dual_analysis_lock,
    build_reconciliation_set,
    canonical_sha256,
    compute_candidate_diagnostics,
    context_manifest_sha256,
    validate_analysis_set,
    validate_reconciliation_set,
)
from foi_o_nz.validation import validate_json_schema

ROOT = Path(__file__).parents[1]
SCHEMAS = ROOT / "schemas/json"
AUTH = {"path": "local/auth.json", "sha256": "1" * 64}
CODEBOOK = {"path": "local/codebook.json", "sha256": "2" * 64}
PATHS = ("local/analysis-a.json", "local/analysis-b.json")
LOCK_PATH = "local/analysis-lock.json"


def _sources(request_id: str) -> list[dict[str, Any]]:
    count = 7 if request_id == "11872" else 1
    result = []
    cursor = 0
    for index in range(count):
        result.append(
            {
                "source_kind": "correspondence" if index < 4 else "attachment_derived_text",
                "source_id": f"source-{request_id}-{index}",
                "source_sha256": f"{index + 1:x}" * 64,
                "start": cursor,
                "end": cursor + 10,
                "character_count": 10,
            }
        )
        cursor += 11
    return result


def _manifest() -> dict[str, Any]:
    return {
        "schema_version": "foi-o.bounded-pilot-context-manifest.v0.2.0",
        "status": "locked_local_contexts",
        "authorization_sha256": AUTH["sha256"],
        "repository_commit": "b" * 40,
        "request_ids": ["11872", "35076"],
        "contexts": [
            {
                "request_id": request_id,
                "unit_sha256": digit * 64,
                "context_sha256": context_digit * 64,
                "global_start": 0 if request_id == "11872" else 77,
                "global_end": 76 if request_id == "11872" else 87,
                "sources": _sources(request_id),
            }
            for request_id, digit, context_digit in (
                ("11872", "3", "4"),
                ("35076", "6", "7"),
            )
        ],
        "analyst_context_sha256": "c" * 64,
        "byte_count": 87,
        "codepoint_count": 87,
        "segments": [
            {
                "request_id": request_id,
                "segment_id": source["source_id"],
                "source_sha256": source["source_sha256"],
                "source_kind": source["source_kind"],
                "start": (0 if request_id == "11872" else 77) + source["start"],
                "end": (0 if request_id == "11872" else 77) + source["end"],
            }
            for request_id in ("11872", "35076")
            for source in _sources(request_id)
        ],
        "analyst_contexts_identical": True,
        "local_only": True,
        "reconciliation_allowed": False,
        "empirical_result_approved": False,
        "publication_allowed": False,
    }


def _manifest_pin(manifest: dict[str, Any]) -> dict[str, str]:
    return {
        "path": "local/context-manifest.json",
        "sha256": context_manifest_sha256(manifest),
    }


def _record(actor: str, request_id: str, *, label: str = "unknown") -> dict[str, Any]:
    context = {value["request_id"]: value for value in _manifest()["contexts"]}[request_id]
    key = "a" if actor == ANALYST_IDS[0] else "b"
    source = context["sources"][0]
    return {
        "schema_version": "foi-o.bounded-pilot-analyst-record.v0.2.0",
        "record_id": f"bounded-pilot:analyst-{key}:{request_id}",
        "status": "locked_agent_first_pass",
        "request_id": request_id,
        "analyst": {
            "actor_id": actor,
            "actor_class": "automated_agent",
            "role": "analyst",
            "runtime": {
                "provider": "OpenAI",
                "model": "Codex synthetic test runtime",
                "prompt_sha256": ("a" if key == "a" else "b") * 64,
                "session_id": f"/root/synthetic-{key}",
            },
        },
        "unit_sha256": context["unit_sha256"],
        "context_sha256": context["context_sha256"],
        "codebook_sha256": CODEBOOK["sha256"],
        "label": label,
        "source_spans": [
            {
                "source_kind": source["source_kind"],
                "source_id": source["source_id"],
                "source_sha256": source["source_sha256"],
                "start": 0,
                "end": 4,
                "coordinate_system": "zero_based_utf8_codepoint_half_open_in_materialized_unit_context",
            }
        ],
        "uncertainty": 0.25,
        "abstention": False,
        "abstention_reason": None,
        "rationale": "Synthetic contract test only.",
        "independence": {
            "blinded_to_peer_outputs": True,
            "blinded_to_candidate_labels": True,
            "blinded_to_prior_reviews": True,
        },
        "repair_attempt_count": 0,
        "created_at": "2026-07-20T00:00:00Z",
        "locked_at": "2026-07-20T00:01:00Z",
        "empirical_result_approved": False,
        "human_reviewed": False,
        "gold_eligible": False,
    }


def _sets(*, disagree: bool = True) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    manifest = _manifest()
    results = []
    for actor in ANALYST_IDS:
        records = [_record(actor, request_id) for request_id in ("11872", "35076")]
        if disagree and actor == ANALYST_IDS[1]:
            records[0]["label"] = "awaiting_response"
        results.append(
            build_analysis_set(
                analyst_id=actor,
                records=records,
                authorization=AUTH,
                codebook=CODEBOOK,
                context_manifest_pin=_manifest_pin(manifest),
                context_manifest=manifest,
            )
        )
    return results[0], results[1], manifest


def _reconciler() -> dict[str, Any]:
    return {
        "actor_id": RECONCILER_ID,
        "actor_class": "automated_agent",
        "role": "reconciler",
        "runtime": {
            "provider": "OpenAI",
            "model": "Codex synthetic test runtime",
            "prompt_sha256": "9" * 64,
            "session_id": "/root/synthetic-reconciler",
        },
    }


def _reconciliation(
    a: dict[str, Any], b: dict[str, Any], lock: dict[str, Any], manifest: dict[str, Any]
) -> dict[str, Any]:
    source = manifest["contexts"][0]["sources"][0]
    record = {
        "schema_version": "foi-o.bounded-pilot-reconciliation-record.v0.2.0",
        "record_id": "bounded-pilot:reconciler:11872",
        "status": "locked_agent_reconciliation",
        "request_id": "11872",
        "analysis_refs": [
            {"analyst_id": actor, "record_sha256": value["entries"][0]["record_sha256"]}
            for actor, value in zip(ANALYST_IDS, (a, b), strict=True)
        ],
        "reconciler": _reconciler(),
        "outcome": "resolved_disagreement",
        "label": "unknown",
        "source_spans": [
            {
                "source_kind": source["source_kind"],
                "source_id": source["source_id"],
                "source_sha256": source["source_sha256"],
                "start": 0,
                "end": 4,
                "coordinate_system": "zero_based_utf8_codepoint_half_open_in_materialized_unit_context",
            }
        ],
        "rationale": "Synthetic resolution of the sole disagreement.",
        "repair_attempt_count": 0,
        "created_at": "2026-07-20T00:02:00Z",
        "locked_at": "2026-07-20T00:03:00Z",
        "empirical_result_approved": False,
        "human_reviewed": False,
        "gold_eligible": False,
    }
    return build_reconciliation_set(
        records=[record],
        reconciler=_reconciler(),
        analysis_a=a,
        analysis_b=b,
        analysis_lock=lock,
        analysis_paths=PATHS,
        analysis_lock_path=LOCK_PATH,
        context_manifest=manifest,
    )


def test_pipeline_is_deterministic_schema_valid_and_agreements_are_mechanical(
    tmp_path: Path,
) -> None:
    a, b, manifest = _sets()
    lock = build_dual_analysis_lock(
        analysis_a=a, analysis_b=b, paths=PATHS, context_manifest=manifest
    )
    reconciliation = _reconciliation(a, b, lock, manifest)
    diagnostics = compute_candidate_diagnostics(
        analysis_a=a,
        analysis_b=b,
        analysis_lock=lock,
        analysis_paths=PATHS,
        analysis_lock_path=LOCK_PATH,
        reconciliation=reconciliation,
        context_manifest=manifest,
    )
    assert reconciliation["disagreement_request_ids"] == ["11872"]
    assert reconciliation["agreement_request_ids"] == ["35076"]
    assert reconciliation["record_count"] == len(reconciliation["entries"]) == 1
    assert diagnostics["cases"][1]["reconciliation_outcome"] == "mechanical_agreement"
    assert diagnostics["empirical_result_approved"] is False
    for value, schema in (
        (a, "bounded-pilot-analysis-set-v0.2"),
        (lock, "bounded-pilot-dual-analysis-lock-v0.2"),
        (reconciliation, "bounded-pilot-reconciliation-set-v0.2"),
        (diagnostics, "bounded-pilot-candidate-diagnostics-v0.2"),
    ):
        path = tmp_path / f"{schema}.json"
        path.write_text(json.dumps(value))
        assert not validate_json_schema(path, SCHEMAS / f"{schema}.schema.json").errors


def test_zero_disagreements_requires_no_reconciler_records() -> None:
    a, b, manifest = _sets(disagree=False)
    lock = build_dual_analysis_lock(
        analysis_a=a, analysis_b=b, paths=PATHS, context_manifest=manifest
    )
    result = build_reconciliation_set(
        records=[],
        reconciler=_reconciler(),
        analysis_a=a,
        analysis_b=b,
        analysis_lock=lock,
        analysis_paths=PATHS,
        analysis_lock_path=LOCK_PATH,
        context_manifest=manifest,
    )
    assert result["agreement_request_ids"] == ["11872", "35076"]
    assert result["entries"] == []


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("record_hash", "record hash"),
        ("set_role", "role identity"),
        ("prohibition", "policy constants"),
        ("span_bound", "source extent"),
        ("context_pin", "context-manifest pin"),
        ("runtime", "provenance mismatch"),
    ],
)
def test_analysis_set_revalidation_rejects_tampering(mutation: str, message: str) -> None:
    a, _, manifest = _sets()
    if mutation == "record_hash":
        a["entries"][0]["record_sha256"] = "0" * 64
    elif mutation == "set_role":
        a["set_id"] = "bounded-pilot-b-first-pass"
    elif mutation == "prohibition":
        a["prohibited_actions"].pop()
    elif mutation == "span_bound":
        record = a["entries"][0]["record"]
        record["source_spans"][0]["end"] = 101
        a["entries"][0]["record_sha256"] = canonical_sha256(record)
    elif mutation == "context_pin":
        a["context_manifest"]["sha256"] = "0" * 64
    else:
        a["entries"][1]["record"]["analyst"]["runtime"]["session_id"] = "/root/other"
        a["entries"][1]["record_sha256"] = canonical_sha256(a["entries"][1]["record"])
    with pytest.raises(ValueError, match=message):
        validate_analysis_set(a, context_manifest=manifest)


def test_reconciliation_rejects_agreement_injection_and_bad_lock_ref() -> None:
    a, b, manifest = _sets()
    lock = build_dual_analysis_lock(
        analysis_a=a, analysis_b=b, paths=PATHS, context_manifest=manifest
    )
    result = _reconciliation(a, b, lock, manifest)
    injected = deepcopy(result["entries"][0]["record"])
    injected["request_id"] = "35076"
    injected["record_id"] = "bounded-pilot:reconciler:35076"
    with pytest.raises(ValueError, match="verified disagreements only"):
        build_reconciliation_set(
            records=[result["entries"][0]["record"], injected],
            reconciler=_reconciler(),
            analysis_a=a,
            analysis_b=b,
            analysis_lock=lock,
            analysis_paths=PATHS,
            analysis_lock_path=LOCK_PATH,
            context_manifest=manifest,
        )
    result["analysis_lock"]["sha256"] = "0" * 64
    with pytest.raises(ValueError, match="linkage mismatch"):
        validate_reconciliation_set(
            result,
            analysis_a=a,
            analysis_b=b,
            analysis_lock=lock,
            analysis_paths=PATHS,
            analysis_lock_path=LOCK_PATH,
            context_manifest=manifest,
        )


def test_diagnostics_rejects_unrelated_or_tampered_inputs() -> None:
    a, b, manifest = _sets()
    lock = build_dual_analysis_lock(
        analysis_a=a, analysis_b=b, paths=PATHS, context_manifest=manifest
    )
    reconciliation = _reconciliation(a, b, lock, manifest)
    b["entries"][0]["record"]["label"] = "closed"
    b["entries"][0]["record_sha256"] = canonical_sha256(b["entries"][0]["record"])
    with pytest.raises(ValueError, match="set linkage mismatch"):
        compute_candidate_diagnostics(
            analysis_a=a,
            analysis_b=b,
            analysis_lock=lock,
            analysis_paths=PATHS,
            analysis_lock_path=LOCK_PATH,
            reconciliation=reconciliation,
            context_manifest=manifest,
        )

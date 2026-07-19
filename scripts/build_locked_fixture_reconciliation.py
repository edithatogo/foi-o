"""Package the governed reconciler response without changing first-pass analysis."""

from __future__ import annotations

import json
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from typing import Any, cast

from jsonschema import Draft202012Validator, FormatChecker

from foi_o_nz.analyst_packet_verification import resolve_repo_artifact

ANALYSIS_LOCK_SHA256 = "79faff0d554df7baff3e9f052dbc7f3a55d3e0e09baec95ab020fb3c4c002d1c"
RESPONSE_SHA256 = "49e63e0818de6da6a7b0f00180128bfc904864a5d36d84f9853e08f931d32393"
PROHIBITED = [
    "redistribution",
    "publication",
    "training",
    "fine_tuning",
    "release",
    "dataset_publication",
    "gold_promotion",
    "legal_certification",
    "paper_update",
    "human_reviewed_claims",
    "empirical_evidence_claims",
]
RUNTIME = {
    "actor_id": "agent:reconciler-fixture",
    "actor_class": "automated_agent",
    "role": "reconciler",
    "runtime": {
        "provider": "OpenAI",
        "model": "Codex / GPT-5; exact snapshot unavailable",
        "prompt_sha256": "80770f3b4335b7fb5b092a96265e41cef29f0c26081ae46afc9949b220661081",
        "session_id": "/root/fixture_reconciler_ready",
    },
}


def canonical_sha256(value: object) -> str:
    """Return the governed compact canonical-JSON digest."""
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode()
    return sha256(encoded).hexdigest()


def _strict_load(path: Path) -> Any:
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in items:
            if key in result:
                raise ValueError(f"{path.name}: duplicate JSON key {key}")
            result[key] = value
        return result

    return json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=pairs,
        parse_constant=lambda value: (_ for _ in ()).throw(
            ValueError(f"{path.name}: non-finite {value}")
        ),
    )


def _pin(root: Path, path: Path) -> dict[str, str]:
    return {
        "path": path.relative_to(root).as_posix(),
        "sha256": sha256(path.read_bytes()).hexdigest(),
    }


def _pretty(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n"
    ).encode()


def disagreement_ids(a: dict[str, Any], b: dict[str, Any]) -> list[str]:
    """Compute the ordered protocol-defined first-pass disagreement census."""
    if [x["unit_id"] for x in a["entries"]] != [x["unit_id"] for x in b["entries"]]:
        raise ValueError("analysis set order or membership mismatch")
    fields = ("label", "span", "abstention")
    return [
        left["unit_id"]
        for left, right in zip(a["entries"], b["entries"], strict=True)
        if tuple(left["record"][field] for field in fields)
        != tuple(right["record"][field] for field in fields)
    ]


def build(*, repository_root: Path, response_path: Path, output_path: Path) -> None:
    """Build the deterministic reconciliation-set envelope."""
    root = repository_root.resolve(strict=True)
    packet = root / "examples/v2/analyst-fixture-packet"
    lock_path = packet / "results/analysis-lock.locked.json"
    canonical_output = packet / "results/reconciliation-set.locked.json"
    if output_path.is_symlink() or output_path.absolute() != canonical_output.absolute():
        raise ValueError("output path is not canonical")
    relative_output = output_path.absolute().relative_to(root)
    cursor = root
    for part in relative_output.parts:
        cursor /= part
        if cursor.exists() and cursor.is_symlink():
            raise ValueError("output path contains a symlink")
    if sha256(lock_path.read_bytes()).hexdigest() != ANALYSIS_LOCK_SHA256:
        raise ValueError("canonical analysis lock SHA-256 mismatch")
    if response_path.is_symlink() or not response_path.resolve(strict=True).is_file():
        raise ValueError("response must be a regular non-symlink file")
    if sha256(response_path.read_bytes()).hexdigest() != RESPONSE_SHA256:
        raise ValueError("governed reconciler response SHA-256 mismatch")
    lock = _strict_load(lock_path)
    set_paths = [resolve_repo_artifact(root, pin["path"]) for pin in lock["analysis_sets"]]
    canonical_set_paths = [
        resolve_repo_artifact(
            root,
            f"examples/v2/analyst-fixture-packet/results/analysis-set.analyst-{key}.locked.json",
        )
        for key in ("a", "b")
    ]
    if set_paths != canonical_set_paths:
        raise ValueError("analysis set paths are not canonical")
    sets = [_strict_load(path) for path in set_paths]
    for pin, path in zip(lock["analysis_sets"], set_paths, strict=True):
        if sha256(path.read_bytes()).hexdigest() != pin["sha256"]:
            raise ValueError("analysis set pin mismatch")
    ids = disagreement_ids(sets[0], sets[1])
    raw = _strict_load(response_path)
    if (
        not isinstance(raw, list)
        or [record.get("record_id", "").split(":")[-1] for record in raw] != ids
    ):
        raise ValueError("response must match exact ordered disagreement census")
    records = cast("list[dict[str, Any]]", raw)
    record_schema = _strict_load(root / "schemas/json/analyst-reconciliation-record.schema.json")
    entries: list[dict[str, Any]] = []
    index = [{entry["unit_id"]: entry for entry in value["entries"]} for value in sets]
    contexts = _strict_load(root / lock["context_presentation"]["path"])["contexts"]
    units = {context["unit_id"]: context for context in contexts}
    codebook = _strict_load(resolve_repo_artifact(root, lock["codebook"]["path"]))
    labels = {item["label"] for item in codebook["labels"]}
    for unit_id, record in zip(ids, records, strict=True):
        errors = list(
            Draft202012Validator(record_schema, format_checker=FormatChecker()).iter_errors(record)
        )
        if errors:
            raise ValueError(f"{unit_id}: {errors[0].message}")
        expected_refs = [
            {
                "analyst_id": item["record"]["analyst"]["actor_id"],
                "sha256": item["record_sha256"],
                "locked_at": item["record"]["locked_at"],
            }
            for item in (index[0][unit_id], index[1][unit_id])
        ]
        if (
            record["record_id"] != f"reconciler-fixture:{unit_id}"
            or record["unit_sha256"] != units[unit_id]["unit_sha256"]
        ):
            raise ValueError(f"{unit_id}: record identity or unit mismatch")
        if record["analysis_refs"] != expected_refs or record["reconciler"] != RUNTIME:
            raise ValueError(f"{unit_id}: analysis provenance or reconciler runtime mismatch")
        if (
            record["reconciled_candidate_label"] is not None
            and record["reconciled_candidate_label"] not in labels
        ):
            raise ValueError(f"{unit_id}: reconciled label outside approved codebook")
        span = record["reconciled_candidate_span"]
        if span is not None and span["end"] <= span["start"]:
            raise ValueError(f"{unit_id}: span must be non-empty")
        created = datetime.fromisoformat(record["created_at"])
        locked = datetime.fromisoformat(record["locked_at"])
        input_locks = [datetime.fromisoformat(ref["locked_at"]) for ref in expected_refs]
        if created > locked or any(
            created < instant or locked < instant for instant in input_locks
        ):
            raise ValueError(f"{unit_id}: reconciliation timestamp ordering mismatch")
        entries.append(
            {"unit_id": unit_id, "record_sha256": canonical_sha256(record), "record": record}
        )
    document = {
        "schema_version": "foi-o.analyst-fixture-reconciliation-set.v0.1.0",
        "set_id": "local-fixture-reconciliation",
        "status": "locked_agent_reconciliation_set",
        "analysis_lock": _pin(root, lock_path),
        "analysis_sets": lock["analysis_sets"],
        "context_presentation": lock["context_presentation"],
        "codebook": lock["codebook"],
        "authorization": lock["authorization"],
        "reconciler": RUNTIME,
        "disagreement_definition": "label_span_or_abstention_differs_v1",
        "unit_count": 11,
        "disagreement_count": len(ids),
        "ordered_disagreement_unit_ids": ids,
        "ordered_disagreement_commitment_sha256": canonical_sha256(ids),
        "record_hash_algorithm": "sha256_canonical_json_utf8_sort_keys_compact_v1",
        "entries": entries,
        "local_only": True,
        "empirical_evidence": False,
        "human_reviewed": False,
        "gold_eligible": False,
        "release_qualifying": False,
        "publication_eligible": False,
        "prohibited_actions": PROHIBITED,
    }
    schema = _strict_load(root / "schemas/json/analyst-fixture-reconciliation-set.schema.json")
    errors = list(
        Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(document)
    )
    if errors:
        raise ValueError(errors[0].message)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(_pretty(document))


if __name__ == "__main__":
    raise SystemExit("invoke build() with the exact governed reconciler response")

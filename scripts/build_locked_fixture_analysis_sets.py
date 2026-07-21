"""Package two isolated analyst responses without changing their decisions."""

from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from foi_o_nz.analyst_packet_verification import ordered_unit_commitment

ROOT = Path(__file__).parents[1]
PACKET = ROOT / "examples/v2/analyst-fixture-packet"
AUTHORIZATION_SHA256 = "6b92051ae1ad1b7899f4ad102d4df4ec68267d196458f5bfbd461e89ba999d95"
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
ROLE = {
    "a": (
        "agent:analyst-fixture-a",
        "ab8cd28ea7b98eae235069555ef5d239ef47d6b8ca1fe1ee6715e67d0f045908",
        "/root/fixture_analyst_a_ready",
    ),
    "b": (
        "agent:analyst-fixture-b",
        "3bcb3b37c8d3a19e51a152c0b72aee82dba088bf822aa8cdc299cbbf029dfb6a",
        "/root/fixture_analyst_b_ready",
    ),
}
RECORD_ID = {
    "a": lambda unit_id: f"analyst-a:{unit_id}",
    "b": lambda unit_id: f"analyst-b-{unit_id}",
}


def _canonical(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode()


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


def _write(path: Path, value: object) -> None:
    path.write_bytes(_pretty(value))


def _pretty(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n"
    ).encode("utf-8")


def _pin(root: Path, path: Path) -> dict[str, str]:
    return {
        "path": path.relative_to(root).as_posix(),
        "sha256": sha256(path.read_bytes()).hexdigest(),
    }


def build(
    *, repository_root: Path, analyst_a_path: Path, analyst_b_path: Path, output: Path
) -> None:
    """Build deterministic set envelopes and their two-set lock manifest."""
    root = repository_root.resolve(strict=True)
    packet = root / "examples/v2/analyst-fixture-packet"
    context_path = packet / "context-presentation.pending.json"
    codebook_path = packet / "codebook.approved.json"
    authorization_path = packet / "execution-authorization.v0.2.pending-verification.json"
    if sha256(authorization_path.read_bytes()).hexdigest() != AUTHORIZATION_SHA256:
        raise ValueError("canonical executable authorization SHA-256 mismatch")
    resolved_output = output.resolve(strict=False)
    if root not in resolved_output.parents or output.is_symlink():
        raise ValueError("output must be a non-symlink descendant of repository root")
    relative_output = resolved_output.relative_to(root)
    cursor = root
    for part in relative_output.parts:
        cursor /= part
        if cursor.exists() and cursor.is_symlink():
            raise ValueError("output path contains a symlink")
    for path in (analyst_a_path, analyst_b_path):
        if path.is_symlink() or not path.resolve(strict=True).is_file():
            raise ValueError("analyst input must be a regular non-symlink file")
    contexts = _strict_load(context_path)["contexts"]
    codebook = _strict_load(codebook_path)
    expected_ids = [item["unit_id"] for item in contexts]
    expected_units = {item["unit_id"]: item for item in contexts}
    labels = {item["label"] for item in codebook["labels"]}
    pins = {
        "authorization": _pin(root, authorization_path),
        "codebook": _pin(root, codebook_path),
        "context_presentation": _pin(root, context_path),
    }
    set_paths: list[Path] = []
    set_documents: list[dict[str, Any]] = []
    schema = json.loads(
        (root / "schemas/json/analyst-fixture-analysis-set.schema.json").read_text()
    )
    for key, raw_path in (("a", analyst_a_path), ("b", analyst_b_path)):
        raw = _strict_load(raw_path)
        if not isinstance(raw, list) or [item.get("unit_id") for item in raw] != expected_ids:
            raise ValueError(f"analyst {key}: responses must match exact ordered census")
        actor_id, prompt_sha, session = ROLE[key]
        entries: list[dict[str, Any]] = []
        for item in raw:
            unit_id = item["unit_id"]
            record = {name: value for name, value in item.items() if name != "unit_id"}
            expected = expected_units[unit_id]
            runtime = record.get("analyst", {}).get("runtime", {})
            if record.get("analyst", {}).get("actor_id") != actor_id:
                raise ValueError(f"{unit_id}: analyst identity mismatch")
            if runtime.get("prompt_sha256") != prompt_sha or runtime.get("session_id") != session:
                raise ValueError(f"{unit_id}: governed runtime mismatch")
            if (
                record.get("unit_sha256") != expected["unit_sha256"]
                or record.get("independence", {}).get("context_sha256")
                != expected["context_sha256"]
            ):
                raise ValueError(f"{unit_id}: unit or context digest mismatch")
            if record.get("codebook_revision") != codebook["revision"]:
                raise ValueError(f"{unit_id}: codebook revision mismatch")
            if not record.get("abstention") and record.get("label") not in labels:
                raise ValueError(f"{unit_id}: label outside approved codebook")
            if record.get("record_id") != RECORD_ID[key](unit_id):
                raise ValueError(f"{unit_id}: record ID mismatch")
            span = record.get("span")
            if isinstance(span, dict) and span.get("end", 0) <= span.get("start", 0):
                raise ValueError(f"{unit_id}: span must be non-empty")
            entries.append(
                {
                    "unit_id": unit_id,
                    "record_sha256": sha256(_canonical(record)).hexdigest(),
                    "record": record,
                }
            )
        analyst = entries[0]["record"]["analyst"]
        if any(entry["record"]["analyst"] != analyst for entry in entries):
            raise ValueError(f"analyst {key}: provenance changes within set")
        document = {
            "schema_version": "foi-o.analyst-fixture-analysis-set.v0.1.0",
            "set_id": f"local-fixture-analysis-{key}",
            "status": "locked_agent_analysis_set",
            **pins,
            "analyst": analyst,
            "unit_count": 11,
            "ordered_unit_commitment_sha256": ordered_unit_commitment(
                [expected_units[i]["unit_sha256"] for i in expected_ids]
            ),
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
        errors = list(
            Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(document)
        )
        if errors:
            raise ValueError(f"analyst {key}: {errors[0].message}")
        set_documents.append(document)
    set_paths = [output / f"analysis-set.analyst-{key}.locked.json" for key in ("a", "b")]
    lock = {
        "schema_version": "foi-o.analyst-fixture-analysis-lock.v0.1.0",
        "lock_id": "local-fixture-dual-analysis",
        "status": "locked_complete_dual_analysis",
        **pins,
        "analysis_sets": [
            {
                "path": path.relative_to(root).as_posix(),
                "sha256": sha256(_pretty(document)).hexdigest(),
            }
            for path, document in zip(set_paths, set_documents, strict=True)
        ],
        "unit_count": 11,
        "ordered_unit_commitment_sha256": ordered_unit_commitment(
            [expected_units[i]["unit_sha256"] for i in expected_ids]
        ),
        "first_pass_sets_complete": True,
        "reconciliation_inputs_ready": True,
        "reconciliation_executed": False,
        "local_only": True,
        "empirical_evidence": False,
        "human_reviewed": False,
        "gold_eligible": False,
        "release_qualifying": False,
        "publication_eligible": False,
        "prohibited_actions": PROHIBITED,
    }
    lock_schema = _strict_load(root / "schemas/json/analyst-fixture-analysis-lock.schema.json")
    lock_errors = list(
        Draft202012Validator(lock_schema, format_checker=FormatChecker()).iter_errors(lock)
    )
    if lock_errors:
        raise ValueError(f"analysis lock: {lock_errors[0].message}")
    output.mkdir(parents=True, exist_ok=True)
    for path, document in zip(set_paths, set_documents, strict=True):
        _write(path, document)
    _write(output / "analysis-lock.locked.json", lock)


if __name__ == "__main__":
    raise SystemExit("invoke build() with explicit governed response paths")

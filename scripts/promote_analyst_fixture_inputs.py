"""Promote the approved analyst-fixture inputs without authorizing execution."""

from __future__ import annotations

import json
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

ROOT = Path(__file__).parents[1]
PACKET = ROOT / "examples/v2/analyst-fixture-packet"
APPROVED_ON = "2026-07-17"
RECORDED_AT = "2026-07-17T23:04:58+10:00"
BASE_READINESS_SHA256 = "de4bdf129f433373b1287c78867db51b1874bd33476dd2229e0710dfc25e03bd"
BASE_REPOSITORY_COMMIT = "948d392df7fbbf49ea9b33646a0bdbd845505811"
APPROVAL_STATEMENT = (
    "I, edithatogo, approve fixture readiness artifact SHA-256 "
    "de4bdf129f433373b1287c78867db51b1874bd33476dd2229e0710dfc25e03bd as committed in "
    "948d392df7fbbf49ea9b33646a0bdbd845505811 for bounded local rights and "
    "execution-input promotion only. This approval does not authorize analyst execution, "
    "redistribution, publication, training, fine-tuning, release, dataset publication, gold "
    "promotion, legal certification, or paper updates. Concrete analyst and reconciler runtimes "
    "and a committed v0.2 execution authorization require separate exact approval."
)
APPROVAL_STATEMENT_SHA256 = "48a0f550f6628a96a003204b6375831d440270581c4281422df778c10bb85b1a"
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
]


def _load(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected object")
    return value


def _write(output: Path, name: str, value: object) -> Path:
    path = output / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def main(
    output: Path = PACKET,
    candidate_dir: Path = PACKET,
    *,
    repository_root: Path = ROOT,
    protocol_path: Path | None = None,
    base_repository_commit: str = BASE_REPOSITORY_COMMIT,
    base_readiness_sha256: str = BASE_READINESS_SHA256,
) -> None:
    """Create deterministic approved-input derivatives; execution remains disabled."""
    readiness_path = candidate_dir / "readiness.json"
    if _digest(readiness_path) != base_readiness_sha256:
        raise ValueError("candidate readiness SHA-256 mismatch")
    repository_root = repository_root.resolve(strict=True)
    protocol = protocol_path or repository_root / "docs/42-v2-analyst-execution-protocol.md"
    protocol = protocol.resolve(strict=True)

    approval_path = _write(
        output,
        "input-approval.approved.json",
        {
            "schema_version": "foi-o.analyst-fixture-input-approval.v0.1.0",
            "approval_id": "local-fixture-inputs-2026-07-17",
            "status": "approved_bounded_local_fixture_inputs",
            "approved_by": "human:edithatogo",
            "approved_on": APPROVED_ON,
            "recorded_at": RECORDED_AT,
            "recording_note": "recorded_at is provenance only and is not claimed as approval time",
            "approval_statement": APPROVAL_STATEMENT,
            "approval_statement_sha256": APPROVAL_STATEMENT_SHA256,
            "approved_readiness": {
                "path": "examples/v2/analyst-fixture-packet/readiness.json",
                "sha256": base_readiness_sha256,
            },
            "approved_repository_commit": base_repository_commit,
            "purpose": "bounded_local_agent_analysis",
            "rights_approved": True,
            "codebook_approved": True,
            "sampling_approved": True,
            "roles_approved": False,
            "execution_authorization_approved": False,
            "execution_allowed": False,
            "local_only": True,
            "empirical_evidence": False,
            "human_reviewed": False,
            "gold_eligible": False,
            "release_qualifying": False,
            "publication_eligible": False,
            "prohibited_actions": PROHIBITED,
        },
    )

    rights = deepcopy(_load(candidate_dir / "local-rights-review.pending.json"))
    rights.update(
        schema_version="foi-o.analyst-approved-local-rights-review.v0.1.0",
        status="approved_bounded_local_use",
        local_analysis_allowed=True,
        approved_by="human:edithatogo",
        approved_on=APPROVED_ON,
        recorded_at=RECORDED_AT,
    )
    rights.pop("approved_at")
    rights_path = _write(output, "local-rights-review.approved.json", rights)

    codebook = deepcopy(_load(candidate_dir / "codebook.json"))
    codebook.update(
        schema_version="foi-o.analyst-approved-fixture-codebook.v0.1.0",
        status="approved",
        approved_by="human:edithatogo",
        approved_on=APPROVED_ON,
        recorded_at=RECORDED_AT,
    )
    codebook.pop("approved_at")
    codebook_path = _write(output, "codebook.approved.json", codebook)

    sampling = deepcopy(_load(candidate_dir / "sampling-configuration.json"))
    sampling.update(
        schema_version="foi-o.analyst-approved-sampling-configuration.v0.1.0",
        status="approved",
        approved_by="human:edithatogo",
        approved_on=APPROVED_ON,
        recorded_at=RECORDED_AT,
    )
    sampling.pop("approved_at")
    sampling_path = _write(output, "sampling-configuration.approved.json", sampling)

    units = deepcopy(_load(candidate_dir / "unit-manifest.json"))
    units["locked_at"] = RECORDED_AT
    for unit in units["units"]:  # type: ignore[index]
        unit["rights_eligible_for_local_use"] = True
    unit_path = _write(output, "unit-manifest.rights-approved.json", units)

    clusters = deepcopy(_load(candidate_dir / "cluster-registry.json"))
    clusters["locked_at"] = RECORDED_AT
    clusters["unit_manifest_sha256"] = _digest(unit_path)
    cluster_path = _write(output, "cluster-registry.rights-approved.json", clusters)

    unchanged = {
        "protocol": (protocol, "docs/42-v2-analyst-execution-protocol.md"),
        "source_population": (
            candidate_dir / "source-population.json",
            "examples/v2/analyst-fixture-packet/source-population.json",
        ),
        "redaction_manifest": (
            candidate_dir / "redaction-manifest.json",
            "examples/v2/analyst-fixture-packet/redaction-manifest.json",
        ),
    }
    approved = {
        "input_approval": approval_path,
        "local_rights_review": rights_path,
        "codebook": codebook_path,
        "sampling_configuration": sampling_path,
        "unit_manifest": unit_path,
        "duplicate_cluster_registry": cluster_path,
    }
    _write(
        output,
        "input-readiness.approved.json",
        {
            "schema_version": "foi-o.analyst-fixture-approved-input-readiness.v0.1.0",
            "status": "approved_inputs_roles_and_execution_authorization_pending",
            "approved_on": APPROVED_ON,
            "recorded_at": RECORDED_AT,
            "base_readiness": {
                "path": "examples/v2/analyst-fixture-packet/readiness.json",
                "sha256": base_readiness_sha256,
                "repository_commit": base_repository_commit,
            },
            "unchanged_artifacts": {
                role: {"path": path, "sha256": _digest(local)}
                for role, (local, path) in unchanged.items()
            },
            "approved_artifacts": {
                role: {
                    "path": f"examples/v2/analyst-fixture-packet/{path.name}",
                    "sha256": _digest(path),
                }
                for role, path in approved.items()
            },
            "transition_algorithm": "foi-o.approved-fixture-input-transition.v0.1.0",
            "rights_approved": True,
            "inputs_approved": True,
            "roles_assigned": False,
            "execution_authorization_present": False,
            "execution_allowed": False,
            "local_only": True,
            "empirical_evidence": False,
            "human_reviewed": False,
            "gold_eligible": False,
            "release_qualifying": False,
            "publication_eligible": False,
            "prohibited_actions": PROHIBITED,
        },
    )


if __name__ == "__main__":
    main()

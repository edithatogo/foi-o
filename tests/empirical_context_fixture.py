"""Production-path verified-context fixture helpers for empirical tests."""

from __future__ import annotations

import hashlib
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from foi_o_nz.empirical_pipeline.contracts import canonical_bytes, seal_record
from foi_o_nz.empirical_pipeline.execution import (
    VerifiedExecutionContext,
    approved_execution_context_sha256,
    canonical_source_bundle_sha256,
    canonical_unit_sha256,
    load_verified_execution_context,
)


@dataclass
class ContextFixture:
    """Verified context plus exact source artifacts used to issue it."""

    context: VerifiedExecutionContext
    paths: dict[str, Path]
    membership: dict[str, Any]
    units: list[dict[str, Any]]
    codebook: dict[str, Any]
    calibration: dict[str, Any]
    authorization: dict[str, Any]
    spec: dict[str, Any]


def _write_json(path: Path, value: dict[str, Any]) -> bytes:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = canonical_bytes(value)
    path.write_bytes(payload)
    return payload


def _git(repository: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repository), *args],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _commit(repository: Path, message: str) -> str:
    subprocess.run(["git", "-C", str(repository), "add", "."], check=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(repository),
            "-c",
            "user.name=Empirical test",
            "-c",
            "user.email=empirical@example.invalid",
            "commit",
            "-qm",
            message,
        ],
        check=True,
    )
    return _git(repository, "rev-parse", "HEAD")


def build_context_fixture(
    root: Path,
    *,
    run_id: str = "run:au-test",
    assessment_status: str = "candidate",
    lifecycle_disposition: str = "active",
    relationships: dict[str, list[str]] | None = None,
    labels: tuple[str, ...] = ("yes", "no", "unknown"),
    abstention_reasons: tuple[str, ...] = ("insufficient", "out_of_scope"),
    extra_stages: tuple[tuple[str, tuple[str, ...]], ...] = (),
    extra_referenced_artifacts: tuple[tuple[str, str, str], ...] = (),
) -> ContextFixture:
    """Create a tiny committed repository and issue a production verified context."""
    repository = root / "repository"
    repository.mkdir(parents=True)
    subprocess.run(["git", "-C", str(repository), "init", "-q"], check=True)
    evidence_path = repository / "examples" / "v2" / "evidence.json"
    evidence_bytes = _write_json(evidence_path, {"evidence": "test authority receipt"})
    evidence_commit = _commit(repository, "evidence")
    evidence_sha = hashlib.sha256(evidence_bytes).hexdigest()

    units = []
    for unit_id, text in (("u1", "yes!"), ("u2", "no!"), ("u3", "none")):
        unit = {"unit_id": unit_id, "text": text, "source_spans": []}
        units.append({**unit, "unit_sha256": canonical_unit_sha256(unit)})
    units.sort(key=lambda row: (row["unit_id"], row["unit_sha256"]))
    membership = seal_record(
        {
            "schema_version": "foio.empirical-sampling-membership.v1.0.0",
            "status": "candidate_membership",
            "membership": [
                {"unit_id": unit["unit_id"], "unit_sha256": unit["unit_sha256"]} for unit in units
            ],
        },
        "membership_sha256",
    )
    source_bundle_sha = canonical_source_bundle_sha256(units)
    codebook = {
        "schema_version": "foio.test-codebook.v1.0.0",
        "labels": [{"id": label} for label in labels],
        "abstention": {"reasons": list(abstention_reasons)},
    }
    codebook_bytes = canonical_bytes(codebook)
    codebook_sha = hashlib.sha256(codebook_bytes).hexdigest()

    role_ids = ["role:annotator-a", "role:annotator-b", "role:adjudicator"]
    calibration_core = {
        "schema_version": "foio.empirical-calibration-result.v1.0.0",
        "calibration_id": "calibration:test:v1",
        "status": "passed",
        "membership_sha256": membership["membership_sha256"],
        "codebook_sha256": codebook_sha,
        "role_ids": role_ids,
        "calibrator_identity": {
            "identity_id": "harness:calibrator",
            "identity_kind": "automated_calibration_harness",
        },
    }
    authorization_core = {
        "schema_version": "foio.empirical-execution-authorization.v1.0.0",
        "authorization_id": "authorization:test:v1",
        "status": "approved",
        "membership_sha256": membership["membership_sha256"],
        "codebook_sha256": codebook_sha,
        "approved_roles": role_ids,
        "capabilities": [
            "packet.generate",
            "annotation.execute",
            "adjudication.queue.prepare",
            "reliability.compute_descriptive",
            "extractor_metrics.compute",
            "maturity.compare_thresholds",
            *(capability for _, capabilities in extra_stages for capability in capabilities),
        ],
        "authorizer_identity": {
            "identity_id": "human:owner",
            "identity_kind": "external_human",
        },
    }
    context_sha = approved_execution_context_sha256(
        membership_sha256=membership["membership_sha256"],
        codebook_sha256=codebook_sha,
        source_bundle_sha256=source_bundle_sha,
        calibration=calibration_core,
        authorization=authorization_core,
    )
    calibration_approval = seal_record(
        {
            "artifact_id": "approval:calibration:test",
            "approved_context_sha256": context_sha,
            "approver_identity": {
                "identity_id": "human:owner",
                "identity_kind": "external_human",
            },
        },
        "artifact_sha256",
    )
    authorization_approval = seal_record(
        {
            "artifact_id": "approval:execution:test",
            "approved_context_sha256": context_sha,
            "approver_identity": {
                "identity_id": "human:owner",
                "identity_kind": "external_human",
            },
        },
        "artifact_sha256",
    )
    population = {
        "population_id": "population:test",
        "population_sha256": hashlib.sha256(b"population:test").hexdigest(),
        "predecessor": 3,
        "included": 3,
        "excluded": 0,
        "unresolved": 0,
    }
    stage_definitions = (
        *extra_stages,
        ("packet", ["packet.generate"]),
        ("annotation", ["annotation.execute", "adjudication.queue.prepare"]),
        ("reliability", ["reliability.compute_descriptive"]),
        ("extractor_metrics", ["extractor_metrics.compute"]),
        ("maturity", ["maturity.compare_thresholds"]),
    )
    stages = [
        {
            "stage_id": f"stage:{kind}",
            "sequence": index,
            "stage_kind": kind,
            "input_sha256": [hashlib.sha256(f"input:{kind}".encode()).hexdigest()],
            "output_sha256": [hashlib.sha256(f"output:{kind}".encode()).hexdigest()],
            "population": population,
            "allowed_capabilities": capabilities,
            "denied_capabilities": ["publication.release", "profile.promote"],
        }
        for index, (kind, capabilities) in enumerate(stage_definitions, start=1)
    ]
    referenced = [
        ("membership:test", membership["membership_sha256"], "restricted_local"),
        ("codebook:test", codebook_sha, "committed"),
        ("approval:calibration:test", calibration_approval["artifact_sha256"], "committed"),
        ("approval:execution:test", authorization_approval["artifact_sha256"], "committed"),
        *extra_referenced_artifacts,
    ]
    spec = seal_record(
        {
            "schema_version": "foio.australian-empirical-run-spec.v1.0.0",
            "run_id": run_id,
            "jurisdiction": "AU-CTH",
            "profile_id": "foi-o-au-cth",
            "assessment_status": assessment_status,
            "lifecycle_disposition": lifecycle_disposition,
            "canonicalization": "foio.sorted-compact-json.v1",
            "authority_bindings": {
                "calibration_approval": calibration_approval,
                "execution_authorization_approval": authorization_approval,
            },
            "evidence_sources": [
                {
                    "artifact_id": "evidence:test",
                    "path": "examples/v2/evidence.json",
                    "sha256": evidence_sha,
                    "size_bytes": len(evidence_bytes),
                    "git_commit": evidence_commit,
                }
            ],
            "referenced_artifacts": [
                {
                    "artifact_id": artifact_id,
                    "sha256": digest,
                    "availability": availability,
                    "evidence_source_sha256": evidence_sha,
                }
                for artifact_id, digest, availability in referenced
            ],
            "producer_provenance": {
                "status": "opaque",
                "reason": "Synthetic verified-context test fixture.",
                "evidence_source_sha256": evidence_sha,
            },
            "stages": stages,
            "relationships": relationships or {"supersedes": [], "invalidates": []},
        },
        "run_spec_sha256",
    )
    calibration = seal_record(
        {
            **calibration_core,
            "run_spec_sha256": spec["run_spec_sha256"],
            "external_approval": calibration_approval,
        },
        "calibration_sha256",
    )
    authorization = seal_record(
        {
            **authorization_core,
            "run_spec_sha256": spec["run_spec_sha256"],
            "calibration_sha256": calibration["calibration_sha256"],
            "external_approval": authorization_approval,
        },
        "authorization_sha256",
    )
    paths = {
        "run_spec": repository / "versions" / "empirical-runs" / "test.json",
        "membership": root / "restricted" / "membership.json",
        "units": root / "restricted" / "units.json",
        "codebook": root / "restricted" / "codebook.json",
        "calibration": root / "restricted" / "calibration.json",
        "authorization": root / "restricted" / "authorization.json",
    }
    _write_json(paths["run_spec"], spec)
    _commit(repository, "run specification")
    _write_json(paths["membership"], membership)
    _write_json(paths["units"], {"units": units})
    paths["codebook"].parent.mkdir(parents=True, exist_ok=True)
    paths["codebook"].write_bytes(codebook_bytes)
    _write_json(paths["calibration"], calibration)
    _write_json(paths["authorization"], authorization)
    context = load_verified_execution_context(
        run_spec_path=paths["run_spec"],
        membership_path=paths["membership"],
        units_path=paths["units"],
        codebook_path=paths["codebook"],
        calibration_path=paths["calibration"],
        authorization_path=paths["authorization"],
    )
    return ContextFixture(
        context=context,
        paths=paths,
        membership=membership,
        units=units,
        codebook=codebook,
        calibration=calibration,
        authorization=authorization,
        spec=spec,
    )

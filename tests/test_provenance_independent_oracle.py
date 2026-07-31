from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

from foi_o_nz.provenance import (
    build_envelope,
    build_pending_authorization,
    canonical_bytes,
    seal_record,
)

ROOT = Path(__file__).resolve().parents[1]
ORACLE = ROOT / "scripts" / "verify_provenance_envelope.py"


def _envelope() -> dict:
    contract = seal_record(
        {
            "schema_version": "foio.transformation-contract.v1.0.0",
            "contract_id": "foio.oracle-test",
            "contract_version": "1.0.0",
            "stage": "validation",
            "accepted_input_schema_versions": ["input.v1"],
            "output_schema_versions": ["output.v1"],
            "algorithm": {
                "id": "identity",
                "version": "1",
                "canonicalization": "foio.sorted-compact-json.v1",
            },
            "rules": {
                "ordering": "preserve",
                "duplicates": "reject",
                "missingness": "retain unresolved",
                "exclusions": "record",
            },
            "required_capabilities": [],
            "prohibited_successor_capabilities": ["publication.release"],
            "compatibility": {
                "unknown_contract_behavior": "reject",
                "supersedes": [],
            },
        },
        "contract_sha256",
    )
    run = seal_record(
        {
            "run_id": "run:oracle-test",
            "repository": "https://github.com/example/foi-o.git",
            "commit": "d" * 40,
            "dirty_worktree": False,
            "command": ["python", "identity.py"],
            "started_at": "2026-07-31T00:00:00Z",
            "completed_at": "2026-07-31T00:00:01Z",
            "implementation_sha256": "a" * 64,
            "dependency_lock_sha256": "b" * 64,
            "parameters": {},
        },
        "run_occurrence_sha256",
    )
    authorization = build_pending_authorization(
        authorization_id="auth:oracle-test",
        object_scope="local validation",
        population_scope="three positions",
        population_id="population:oracle-test",
        population_sha256="c" * 64,
        transformation_id=contract["contract_id"],
        transformation_version=contract["contract_version"],
        transformation_contract_sha256=contract["contract_sha256"],
        run_id=run["run_id"],
        run_occurrence_sha256=run["run_occurrence_sha256"],
        allowed_capabilities=[],
        denied_capabilities=["publication.release"],
        approved_input_sha256=["a" * 64],
    )
    return build_envelope(
        envelope_id="envelope:oracle-test",
        transformation_contract=contract,
        run_occurrence=run,
        authorization=authorization,
        inputs=[
            {
                "artifact_id": "input",
                "sha256": "a" * 64,
                "size_bytes": 1,
                "schema_version": "input.v1",
            }
        ],
        outputs=[
            {
                "artifact_id": "output",
                "sha256": "b" * 64,
                "size_bytes": 1,
                "schema_version": "output.v1",
            }
        ],
        population={
            "population_id": "population:oracle-test",
            "population_sha256": "c" * 64,
            "predecessor": 3,
            "included": 2,
            "excluded": 1,
            "unresolved": 0,
        },
    )


def _load_oracle():
    spec = importlib.util.spec_from_file_location("independent_provenance_oracle", ORACLE)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_oracle_source_does_not_import_producer_package() -> None:
    source = ORACLE.read_text(encoding="utf-8")
    assert "from foi_o_nz" not in source
    assert "import foi_o_nz" not in source


def test_oracle_accepts_valid_envelope_and_cli_emits_json(tmp_path: Path) -> None:
    envelope_path = tmp_path / "envelope.json"
    envelope_path.write_bytes(canonical_bytes(_envelope()) + b"\n")
    result = subprocess.run(
        [sys.executable, str(ORACLE), str(envelope_path)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert json.loads(result.stdout) == {"errors": [], "valid": True}


def test_oracle_rejects_tampering_population_and_missing_denials() -> None:
    oracle = _load_oracle()
    tampered = _envelope()
    tampered["outputs"][0]["size_bytes"] = 2
    assert "invalid envelope_sha256" in oracle.verify(tampered)

    imbalanced = _envelope()
    imbalanced["population"]["included"] = 1
    del imbalanced["envelope_sha256"]
    imbalanced = seal_record(imbalanced, "envelope_sha256")
    assert "population imbalance" in oracle.verify(imbalanced)

    no_denials = _envelope()
    del no_denials["authorization"]["denied_capabilities"]
    del no_denials["authorization"]["authorization_sha256"]
    no_denials["authorization"] = seal_record(
        no_denials["authorization"],
        "authorization_sha256",
    )
    del no_denials["envelope_sha256"]
    no_denials = seal_record(no_denials, "envelope_sha256")
    assert any("schema validation failed" in error for error in oracle.verify(no_denials))


def test_oracle_rejects_successor_activation_without_approval() -> None:
    oracle = _load_oracle()
    envelope = copy.deepcopy(_envelope())
    envelope["successor_effects"] = ["manifest.finalize"]
    del envelope["envelope_sha256"]
    envelope = seal_record(envelope, "envelope_sha256")
    errors = oracle.verify(envelope)
    assert "successor activation requires approved authorization" in errors
    assert "successor activation exceeds allowed capabilities" in errors


def _reseal_envelope(envelope: dict) -> dict:
    envelope.pop("envelope_sha256", None)
    return seal_record(envelope, "envelope_sha256")


def _reseal_authorization(envelope: dict) -> None:
    envelope["authorization"].pop("authorization_sha256", None)
    envelope["authorization"] = seal_record(
        envelope["authorization"],
        "authorization_sha256",
    )


def test_oracle_rejects_structural_and_date_format_bypasses() -> None:
    oracle = _load_oracle()
    malformed_run = _envelope()
    malformed_run["run_occurrence"] = {}
    assert any("schema validation failed" in error for error in oracle.verify(malformed_run))

    malformed_artifact = _envelope()
    malformed_artifact["inputs"][0] = {"artifact_id": "missing-fields"}
    assert any("schema validation failed" in error for error in oracle.verify(malformed_artifact))

    invalid_date = _envelope()
    invalid_date["run_occurrence"]["started_at"] = "not-a-date"
    assert any("schema validation failed" in error for error in oracle.verify(invalid_date))


def test_oracle_rejects_every_authorization_binding_bypass() -> None:
    oracle = _load_oracle()
    mutations = (
        ("population_id", "population:other", "authorization population id mismatch"),
        ("population_sha256", "e" * 64, "authorization population pin mismatch"),
        ("transformation_id", "foio.other", "authorization transformation id mismatch"),
        ("transformation_version", "2.0.0", "authorization transformation version mismatch"),
        ("run_id", "run:other", "authorization run id mismatch"),
        ("run_occurrence_sha256", "e" * 64, "authorization run occurrence pin mismatch"),
    )
    for field, value, expected in mutations:
        envelope = _envelope()
        envelope["authorization"][field] = value
        _reseal_authorization(envelope)
        errors = oracle.verify(_reseal_envelope(envelope))
        assert expected in errors

    input_mismatch = _envelope()
    input_mismatch["inputs"][0]["sha256"] = "e" * 64
    assert "authorization approved input digest set mismatch" in oracle.verify(
        _reseal_envelope(input_mismatch)
    )


def _attestation(*, passed: bool = True, independent: bool = True, valid: bool = True) -> dict:
    return seal_record(
        {
            "schema_version": "foio.validation-attestation.v1.0.0",
            "attestation_id": "attestation:oracle-test",
            "validator": {
                "implementation": "independent-oracle",
                "revision": "1",
                "independent_oracle": independent,
            },
            "validated_envelope_sha256": _envelope()["envelope_sha256"],
            "checks": [{"id": "all", "passed": passed}],
            "valid": valid,
            "limitations": ["bounded test"],
        },
        "attestation_sha256",
    )


def test_oracle_verifies_attestation_invariants_and_self_pin() -> None:
    oracle = _load_oracle()
    assert oracle.verify_attestation(_attestation()) == []
    for attestation in (
        _attestation(passed=False, valid=True),
        _attestation(independent=False, valid=True),
        _attestation(valid=False),
    ):
        assert any(
            "schema validation failed" in error for error in oracle.verify_attestation(attestation)
        )

    tampered = _attestation()
    tampered["limitations"] = ["tampered"]
    assert "invalid attestation_sha256" in oracle.verify_attestation(tampered)
    assert "attestation envelope pin mismatch" in oracle.verify_attestation(
        _attestation(),
        expected_envelope_sha256="e" * 64,
    )

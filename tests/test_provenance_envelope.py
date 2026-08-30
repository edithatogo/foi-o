from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from foi_o_nz.provenance import (
    ProvenanceValidationError,
    build_envelope,
    build_pending_authorization,
    canonical_bytes,
    render_pending_approval_packet,
    seal_record,
    validate_attestation,
    validate_envelope,
)

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "schemas" / "json"
SHA_A = "a" * 64
SHA_B = "b" * 64
POPULATION_SHA = "d" * 64


def _contract() -> dict:
    return seal_record(
        {
            "schema_version": "foio.transformation-contract.v1.0.0",
            "contract_id": "foio.test-transform",
            "contract_version": "1.0.0",
            "stage": "manifest_candidate",
            "accepted_input_schema_versions": ["foio.input.v1"],
            "output_schema_versions": ["foio.output.v1"],
            "algorithm": {
                "id": "sha256-rank",
                "version": "1",
                "canonicalization": "foio.sorted-compact-json.v1",
            },
            "rules": {
                "ordering": "ascending sha256 rank",
                "duplicates": "retain first stable artifact id",
                "missingness": "retain unresolved positions",
                "exclusions": "record every exclusion",
            },
            "parameters": {"seed": {"type": "integer"}},
            "required_capabilities": ["manifest.prepare"],
            "prohibited_successor_capabilities": ["publication.release"],
            "compatibility": {
                "unknown_contract_behavior": "reject",
                "supersedes": [],
            },
        },
        "contract_sha256",
    )


def _authorization(contract: dict, run: dict) -> dict:
    return build_pending_authorization(
        authorization_id="auth:test",
        object_scope="one local manifest candidate",
        population_scope="ten pinned positions",
        population_id="population:test",
        population_sha256=POPULATION_SHA,
        transformation_id=contract["contract_id"],
        transformation_version=contract["contract_version"],
        transformation_contract_sha256=contract["contract_sha256"],
        run_id=run["run_id"],
        run_occurrence_sha256=run["run_occurrence_sha256"],
        allowed_capabilities=["manifest.prepare"],
        denied_capabilities=["manifest.finalize", "publication.release"],
        approved_input_sha256=[SHA_A],
    )


def _run() -> dict:
    return seal_record(
        {
            "run_id": "run:test",
            "repository": "https://github.com/example/foi-o.git",
            "commit": "c" * 40,
            "dirty_worktree": False,
            "command": ["python", "transform.py", "--seed", "7"],
            "started_at": "2026-07-31T00:00:00Z",
            "completed_at": "2026-07-31T00:01:00Z",
            "implementation_sha256": SHA_A,
            "dependency_lock_sha256": SHA_B,
            "parameters": {"seed": 7},
            "environment": {"python": "3.12"},
        },
        "run_occurrence_sha256",
    )


def _artifact(artifact_id: str, digest: str) -> dict:
    return {
        "artifact_id": artifact_id,
        "sha256": digest,
        "size_bytes": 10,
        "schema_version": "foio.test.v1",
    }


def _envelope() -> dict:
    contract = _contract()
    run = _run()
    return build_envelope(
        envelope_id="envelope:test",
        transformation_contract=contract,
        run_occurrence=run,
        authorization=_authorization(contract, run),
        inputs=[_artifact("input:1", SHA_A)],
        outputs=[_artifact("output:1", SHA_B)],
        population={
            "population_id": "population:test",
            "population_sha256": POPULATION_SHA,
            "predecessor": 10,
            "included": 8,
            "excluded": 1,
            "unresolved": 1,
        },
    )


def _schema(name: str) -> dict:
    return json.loads((SCHEMA_DIR / name).read_text(encoding="utf-8"))


def test_envelope_and_component_schemas_accept_built_record() -> None:
    envelope = _envelope()
    schemas = [
        _schema("transformation-contract.schema.json"),
        _schema("authorization-record.schema.json"),
        _schema("validation-attestation.schema.json"),
        _schema("provenance-envelope.schema.json"),
    ]
    registry = Registry().with_resources([
        (schema["$id"], Resource.from_contents(schema)) for schema in schemas
    ])
    Draft202012Validator(schemas[-1], registry=registry).validate(envelope)


def test_canonical_bytes_are_stable_compact_sorted_utf8() -> None:
    assert canonical_bytes({"z": "māori", "a": [2, 1]}) == ('{"a":[2,1],"z":"māori"}'.encode())


def test_stable_contract_rejects_occurrence_fields() -> None:
    contract = _contract()
    contract["generated_at"] = "2026-07-31T00:00:00Z"
    schema = _schema("transformation-contract.schema.json")
    errors = list(Draft202012Validator(schema).iter_errors(contract))
    assert any(error.validator == "additionalProperties" for error in errors)


def test_pending_packet_is_explicit_and_cannot_render_approved_record() -> None:
    contract = _contract()
    authorization = _authorization(contract, _run())
    packet = render_pending_approval_packet(authorization)
    assert "pending_human_decision" in packet
    assert "cannot authorize itself" in packet
    assert "`publication.release`" in packet

    approved = copy.deepcopy(authorization)
    approved["status"] = "approved"
    approved["human_decision"] = {
        "approver_role": "accountable_owner",
        "decided_at": "2026-07-31T00:02:00Z",
    }
    del approved["authorization_sha256"]
    approved = seal_record(approved, "authorization_sha256")
    with pytest.raises(ValueError, match="pending_human_decision"):
        render_pending_approval_packet(approved)


def test_statement_hash_is_exact_utf8_bytes() -> None:
    authorization = _authorization(_contract(), _run())
    assert (
        authorization["approval_statement_sha256"]
        == hashlib.sha256(authorization["approval_statement"].encode("utf-8")).hexdigest()
    )


def test_packet_renderer_rejects_tampered_pending_record() -> None:
    authorization = _authorization(_contract(), _run())
    authorization["population_scope"] = "expanded population"
    with pytest.raises(ValueError, match="self-pin is invalid"):
        render_pending_approval_packet(authorization)


def test_invalid_envelope_self_pin_is_rejected() -> None:
    envelope = _envelope()
    envelope["population"]["included"] = 7
    with pytest.raises(ProvenanceValidationError, match="invalid envelope_sha256"):
        validate_envelope(envelope)


def test_population_imbalance_is_rejected_after_resealing() -> None:
    envelope = _envelope()
    envelope["population"]["included"] = 7
    del envelope["envelope_sha256"]
    envelope = seal_record(envelope, "envelope_sha256")
    with pytest.raises(ProvenanceValidationError, match="population imbalance"):
        validate_envelope(envelope)


def test_omitted_denial_set_is_rejected_after_resealing() -> None:
    envelope = _envelope()
    del envelope["authorization"]["denied_capabilities"]
    del envelope["authorization"]["authorization_sha256"]
    envelope["authorization"] = seal_record(
        envelope["authorization"],
        "authorization_sha256",
    )
    del envelope["envelope_sha256"]
    envelope = seal_record(envelope, "envelope_sha256")
    with pytest.raises(ProvenanceValidationError, match="schema validation failed"):
        validate_envelope(envelope)


def test_successor_activation_requires_human_approval() -> None:
    envelope = _envelope()
    envelope["successor_effects"] = ["manifest.prepare"]
    del envelope["envelope_sha256"]
    envelope = seal_record(envelope, "envelope_sha256")
    with pytest.raises(ProvenanceValidationError, match="requires approved"):
        validate_envelope(envelope)


def test_transformation_capability_requires_explicit_authorization() -> None:
    envelope = _envelope()
    envelope["authorization"]["allowed_capabilities"] = []
    del envelope["authorization"]["authorization_sha256"]
    envelope["authorization"] = seal_record(
        envelope["authorization"],
        "authorization_sha256",
    )
    del envelope["envelope_sha256"]
    envelope = seal_record(envelope, "envelope_sha256")
    with pytest.raises(ProvenanceValidationError, match="not authorized"):
        validate_envelope(envelope)


def test_build_does_not_mutate_legacy_or_input_records() -> None:
    contract = _contract()
    authorization = _authorization(contract, _run())
    original_contract = copy.deepcopy(contract)
    original_authorization = copy.deepcopy(authorization)
    _envelope()
    assert contract == original_contract
    assert authorization == original_authorization


def _reseal_envelope(envelope: dict) -> dict:
    envelope.pop("envelope_sha256", None)
    return seal_record(envelope, "envelope_sha256")


def _reseal_authorization(envelope: dict) -> None:
    envelope["authorization"].pop("authorization_sha256", None)
    envelope["authorization"] = seal_record(
        envelope["authorization"],
        "authorization_sha256",
    )


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("population_id", "population:other", "population id mismatch"),
        ("population_sha256", "e" * 64, "population pin mismatch"),
        ("transformation_id", "foio.other-transform", "transformation id mismatch"),
        ("transformation_version", "2.0.0", "transformation version mismatch"),
        ("run_id", "run:other", "run id mismatch"),
        ("run_occurrence_sha256", "e" * 64, "run occurrence pin mismatch"),
    ],
)
def test_authorization_exact_binding_rejects_mismatch(
    field: str,
    value: str,
    message: str,
) -> None:
    envelope = _envelope()
    envelope["authorization"][field] = value
    _reseal_authorization(envelope)
    envelope = _reseal_envelope(envelope)
    with pytest.raises(ProvenanceValidationError, match=message):
        validate_envelope(envelope)


def test_authorization_rejects_unapproved_input_digest() -> None:
    envelope = _envelope()
    envelope["inputs"][0]["sha256"] = "e" * 64
    envelope = _reseal_envelope(envelope)
    with pytest.raises(ProvenanceValidationError, match="approved input digest set mismatch"):
        validate_envelope(envelope)


@pytest.mark.parametrize(
    "mutation",
    [
        lambda envelope: envelope.update(run_occurrence={}),
        lambda envelope: envelope["run_occurrence"].update(started_at="not-a-date"),
        lambda envelope: envelope["inputs"].__setitem__(0, {"artifact_id": "malformed"}),
    ],
)
def test_structurally_invalid_envelopes_fail_closed(mutation) -> None:
    envelope = _envelope()
    mutation(envelope)
    envelope = _reseal_envelope(envelope)
    with pytest.raises(ProvenanceValidationError, match="schema validation failed"):
        validate_envelope(envelope)


def _attestation(*, passed: bool = True, independent: bool = True, valid: bool = True) -> dict:
    return seal_record(
        {
            "schema_version": "foio.validation-attestation.v1.0.0",
            "attestation_id": "attestation:test",
            "validator": {
                "implementation": "independent-test-oracle",
                "revision": "1",
                "independent_oracle": independent,
            },
            "validated_envelope_sha256": _envelope()["envelope_sha256"],
            "checks": [{"id": "schema", "passed": passed}],
            "valid": valid,
            "limitations": ["restricted-local validation only"],
        },
        "attestation_sha256",
    )


def test_valid_attestation_requires_independent_oracle_and_all_checks() -> None:
    validate_attestation(_attestation())
    for attestation in (
        _attestation(passed=False, valid=True),
        _attestation(independent=False, valid=True),
        _attestation(passed=True, independent=True, valid=False),
    ):
        with pytest.raises(ProvenanceValidationError, match="schema validation failed"):
            validate_attestation(attestation)


def test_attestation_self_pin_and_envelope_pin_are_verified() -> None:
    attestation = _attestation()
    attestation["limitations"] = ["tampered"]
    with pytest.raises(ProvenanceValidationError, match="invalid attestation_sha256"):
        validate_attestation(attestation)
    with pytest.raises(ProvenanceValidationError, match="attestation envelope pin mismatch"):
        validate_attestation(
            _attestation(),
            expected_envelope_sha256="e" * 64,
        )

from __future__ import annotations

import json
import subprocess
import sys
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

import pytest

from foi_o_nz.australian_rollout_pipeline import (
    STAGE_ORDER,
    finalize_contract,
    validate_contract,
)

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples/v2"
POSITIVE = EXAMPLES / "australian-rollout-pipeline.positive.json"


def _load_positive() -> dict:
    return json.loads(POSITIVE.read_text(encoding="utf-8"))


# Independent oracle: deliberately does not call or import the producer canonicalizer.
def _oracle_bytes(value: object) -> bytes:
    text = json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return (text + "\n").encode()


def _oracle_sha256(value: object) -> str:
    return sha256(_oracle_bytes(value)).hexdigest()


def _repin(value: dict) -> dict:
    candidate = deepcopy(value)
    candidate.pop("definition_sha256", None)
    candidate.pop("contract_sha256", None)
    checkpoint = candidate.pop("resume_checkpoint", None)
    definition = _oracle_sha256(candidate)
    candidate["definition_sha256"] = definition
    if checkpoint is not None:
        checkpoint = deepcopy(checkpoint)
        checkpoint["definition_sha256"] = definition
        checkpoint.pop("checkpoint_sha256", None)
        checkpoint["checkpoint_sha256"] = _oracle_sha256(checkpoint)
        candidate["resume_checkpoint"] = checkpoint
    candidate["contract_sha256"] = _oracle_sha256(candidate)
    return candidate


def _stage(value: dict, name: str) -> dict:
    return next(stage for stage in value["stages"] if stage["name"] == name)


def _gate(value: dict, stage_name: str) -> dict:
    return next(gate for gate in value["gates"] if gate["before_stage"] == stage_name)


def test_positive_example_validates_with_exact_stage_order() -> None:
    value = _load_positive()
    result = validate_contract(value)
    assert tuple(stage["name"] for stage in value["stages"]) == STAGE_ORDER
    assert result["last_completed_stage"] == "discover"
    assert result["stage_count"] == 13


def test_independent_hash_oracle_agrees_with_all_producer_pins() -> None:
    value = _load_positive()
    definition_payload = {
        key: item
        for key, item in value.items()
        if key not in {"definition_sha256", "contract_sha256", "resume_checkpoint"}
    }
    assert _oracle_sha256(definition_payload) == value["definition_sha256"]
    checkpoint_payload = {
        key: item for key, item in value["resume_checkpoint"].items() if key != "checkpoint_sha256"
    }
    assert _oracle_sha256(checkpoint_payload) == value["resume_checkpoint"]["checkpoint_sha256"]
    contract_payload = {key: item for key, item in value.items() if key != "contract_sha256"}
    assert _oracle_sha256(contract_payload) == value["contract_sha256"]


def test_finalize_contract_does_not_change_statuses_or_grant_gates() -> None:
    value = _load_positive()
    draft = {
        key: item
        for key, item in value.items()
        if key not in {"definition_sha256", "contract_sha256"}
    }
    draft["resume_checkpoint"].pop("checkpoint_sha256")
    statuses = [stage["status"] for stage in draft["stages"]]
    finalized = finalize_contract(draft)
    assert [stage["status"] for stage in finalized["stages"]] == statuses
    assert finalized["gates"] == draft["gates"]
    assert _gate(finalized, "replay")["authorization_state"] == "not_authorized"


def test_rejects_changed_contract_pin() -> None:
    value = _load_positive()
    value["contract_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="contract self-pin"):
        validate_contract(value)


def test_rejects_stage_order_even_when_tampered_contract_is_repinned() -> None:
    value = _load_positive()
    value["stages"][1], value["stages"][2] = value["stages"][2], value["stages"][1]
    with pytest.raises(ValueError, match="required stage order"):
        validate_contract(_repin(value))


def test_rejects_changed_artifact_pin_even_when_contract_is_repinned() -> None:
    value = _load_positive()
    _stage(value, "select")["inputs"][0]["sha256"] = "9" * 64
    with pytest.raises(ValueError, match="artifact pin changed"):
        validate_contract(_repin(value))


def test_rejects_population_expansion_even_when_contract_is_repinned() -> None:
    value = _load_positive()
    _stage(value, "select")["population"]["unit_count"] = 101
    with pytest.raises(ValueError, match="expands the bounded population"):
        validate_contract(_repin(value))


def test_rejects_unknown_population_parent_pin() -> None:
    value = _load_positive()
    _stage(value, "sample")["population"]["parent_membership_sha256"] = "9" * 64
    with pytest.raises(ValueError, match="not produced by an authorized predecessor"):
        validate_contract(_repin(value))


def test_rejects_unauthorized_stage_activation() -> None:
    value = _load_positive()
    select = _stage(value, "select")
    select["status"] = "completed"
    select["outputs"] = [
        {
            "artifact_id": "au-vic-selection",
            "sha256": "7" * 64,
            "media_type": "application/json",
        }
    ]
    replay = _stage(value, "replay")
    replay["status"] = "active"
    replay["inputs"] = deepcopy(select["outputs"])
    with pytest.raises(ValueError, match="without external authorization"):
        validate_contract(_repin(value))


def test_rejects_activated_stage_when_its_registered_gate_is_missing() -> None:
    value = _load_positive()
    value["gates"] = [gate for gate in value["gates"] if gate["before_stage"] != "discover"]
    with pytest.raises(ValueError, match="missing registered gate for stage discover"):
        validate_contract(_repin(value))


def test_rejects_duplicate_gate_ids() -> None:
    value = _load_positive()
    value["gates"][1]["gate_id"] = value["gates"][0]["gate_id"]
    with pytest.raises(ValueError, match="duplicate gate id"):
        validate_contract(_repin(value))


def test_rejects_duplicate_gates_for_one_stage() -> None:
    value = _load_positive()
    value["gates"][1]["before_stage"] = value["gates"][0]["before_stage"]
    with pytest.raises(ValueError, match="duplicate registered gate for stage"):
        validate_contract(_repin(value))


def test_accepts_activation_only_with_pinned_external_human_authorization() -> None:
    value = _load_positive()
    value.pop("resume_checkpoint")
    select = _stage(value, "select")
    select["status"] = "completed"
    select["outputs"] = [
        {
            "artifact_id": "au-vic-selection",
            "sha256": "7" * 64,
            "media_type": "application/json",
        }
    ]
    replay = _stage(value, "replay")
    replay["status"] = "active"
    replay["inputs"] = deepcopy(select["outputs"])
    _gate(value, "select").update(
        {
            "authorization_state": "externally_authorized",
            "authorized_by": "external_human",
            "authorization_evidence_sha256": "6" * 64,
        }
    )
    _gate(value, "replay").update(
        {
            "authorization_state": "externally_authorized",
            "authorized_by": "external_human",
            "authorization_evidence_sha256": "8" * 64,
        }
    )
    result = validate_contract(_repin(value))
    assert result["last_completed_stage"] == "select"


def test_rejects_invented_non_root_stage_input() -> None:
    value = _load_positive()
    select = _stage(value, "select")
    select["inputs"] = [
        {
            "artifact_id": "invented-unproduced-input",
            "sha256": "9" * 64,
            "media_type": "application/json",
        }
    ]
    with pytest.raises(ValueError, match="not produced by an authorized predecessor"):
        validate_contract(_repin(value))


def test_rejects_input_from_undeclared_non_immediate_predecessor() -> None:
    value = _load_positive()
    reconcile = _stage(value, "reconcile")
    reconcile["inputs"] = deepcopy(_stage(value, "discover")["outputs"])
    with pytest.raises(ValueError, match="not produced by an authorized predecessor"):
        validate_contract(_repin(value))


def test_accepts_input_from_explicit_earlier_predecessor() -> None:
    value = _load_positive()
    reconcile = _stage(value, "reconcile")
    reconcile["additional_predecessor_stages"] = ["discover"]
    reconcile["inputs"] = deepcopy(_stage(value, "discover")["outputs"])
    validate_contract(_repin(value))


def test_rejects_population_parent_from_undeclared_predecessor() -> None:
    value = _load_positive()
    select = _stage(value, "select")
    select["population"]["parent_membership_sha256"] = _stage(value, "calibrate")["population"][
        "membership_sha256"
    ]
    with pytest.raises(
        ValueError, match="population parent is not produced by an authorized predecessor"
    ):
        validate_contract(_repin(value))


def test_rejects_forward_declared_predecessor() -> None:
    value = _load_positive()
    _stage(value, "select")["additional_predecessor_stages"] = ["replay"]
    with pytest.raises(ValueError, match="is not an earlier stage"):
        validate_contract(_repin(value))


def test_rejects_gate_evidence_that_does_not_declare_external_human_authority() -> None:
    value = _load_positive()
    _gate(value, "replay").update(
        {
            "authorization_state": "externally_authorized",
            "authorization_evidence_sha256": "8" * 64,
        }
    )
    with pytest.raises(ValueError, match="schema validation failed"):
        validate_contract(_repin(value))


def test_rejects_resume_checkpoint_for_wrong_output() -> None:
    value = _load_positive()
    value["resume_checkpoint"]["stage_output_sha256"] = "9" * 64
    with pytest.raises(ValueError, match="output pin is not produced"):
        validate_contract(_repin(value))


def test_rejects_resume_checkpoint_for_different_definition() -> None:
    value = _load_positive()
    value["resume_checkpoint"]["definition_sha256"] = "9" * 64
    checkpoint = value["resume_checkpoint"]
    checkpoint["checkpoint_sha256"] = _oracle_sha256(
        {key: item for key, item in checkpoint.items() if key != "checkpoint_sha256"}
    )
    value["contract_sha256"] = _oracle_sha256(
        {key: item for key, item in value.items() if key != "contract_sha256"}
    )
    with pytest.raises(ValueError, match="different pipeline definition"):
        validate_contract(value)


@pytest.mark.parametrize(
    "failure_type",
    ["network_error", "unknown", "http_404"],
)
def test_rejects_untyped_failure_dispositions(failure_type: str) -> None:
    value = _load_positive()
    value["failure_dispositions"][0]["failure_type"] = failure_type
    with pytest.raises(ValueError, match="schema validation failed"):
        validate_contract(_repin(value))


def test_rejects_exclusion_without_evidence_pin() -> None:
    value = _load_positive()
    value["failure_dispositions"][0].pop("evidence_sha256")
    with pytest.raises(ValueError, match="has no evidence pin"):
        validate_contract(_repin(value))


@pytest.mark.parametrize("missing_key", ["producer", "transformation"])
def test_requires_stage_producer_and_transformation_provenance(missing_key: str) -> None:
    value = _load_positive()
    _stage(value, "select")["provenance"].pop(missing_key)
    with pytest.raises(ValueError, match="schema validation failed"):
        validate_contract(_repin(value))


def test_verifies_declared_artifact_file_with_direct_file_hash(tmp_path: Path) -> None:
    artifact = tmp_path / "discovery.json"
    artifact.write_bytes(b"bounded discovery\n")
    digest = sha256(artifact.read_bytes()).hexdigest()
    value = _load_positive()
    output_pin = _stage(value, "discover")["outputs"][0]
    input_pin = _stage(value, "select")["inputs"][0]
    output_pin["sha256"] = digest
    input_pin["sha256"] = digest
    value["resume_checkpoint"]["stage_output_sha256"] = digest
    value = _repin(value)
    validate_contract(value, artifact_files={"au-vic-discovery": artifact})
    artifact.write_bytes(b"expanded discovery\n")
    with pytest.raises(ValueError, match="artifact file pin mismatch"):
        validate_contract(value, artifact_files={"au-vic-discovery": artifact})


def test_negative_examples_describe_enforced_mutations() -> None:
    for path in sorted(EXAMPLES.glob("australian-rollout-pipeline.*.negative.json")):
        vector = json.loads(path.read_text(encoding="utf-8"))
        value = _load_positive()
        mutation = vector["mutation"]
        if mutation["kind"] == "swap_stages":
            left = next(
                i for i, stage in enumerate(value["stages"]) if stage["name"] == mutation["left"]
            )
            right = next(
                i for i, stage in enumerate(value["stages"]) if stage["name"] == mutation["right"]
            )
            value["stages"][left], value["stages"][right] = (
                value["stages"][right],
                value["stages"][left],
            )
        elif mutation["kind"] == "set_stage_population_count":
            _stage(value, mutation["stage"])["population"]["unit_count"] = mutation["unit_count"]
        else:
            select = _stage(value, "select")
            select["status"] = "completed"
            select["outputs"] = [
                {
                    "artifact_id": "au-vic-selection",
                    "sha256": "7" * 64,
                    "media_type": "application/json",
                }
            ]
            replay = _stage(value, mutation["stage"])
            replay["status"] = "active"
            replay["inputs"] = deepcopy(select["outputs"])
        with pytest.raises(ValueError, match=vector["expected_error"]):
            validate_contract(_repin(value))


def test_cli_validates_positive_example() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/build_australian_rollout_pipeline.py"),
            "--input",
            str(POSITIVE),
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr + result.stdout
    assert json.loads(result.stdout)["stage_count"] == 13


def test_rejects_duplicate_gates() -> None:
    value = _load_positive()
    dup_gate = deepcopy(value["gates"][0])
    value["gates"].append(dup_gate)
    with pytest.raises(ValueError, match="schema validation failed|duplicate gate|unique"):
        validate_contract(_repin(value))


def test_rejects_malformed_provenance_envelope() -> None:
    value = _load_positive()
    value["stages"][0]["provenance"]["producer"] = "invalid-untyped-producer"
    with pytest.raises(ValueError, match="schema validation failed"):
        validate_contract(_repin(value))


def test_rejects_unpinned_codebook_core() -> None:
    value = _load_positive()
    calibrate = _stage(value, "calibrate")
    if "codebook_sha256" in calibrate.get("provenance", {}):
        calibrate["provenance"]["codebook_sha256"] = "invalid_hash"
        with pytest.raises(ValueError, match="schema validation failed|invalid"):
            validate_contract(_repin(value))

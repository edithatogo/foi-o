"""Bounded, resumable contract for Australian jurisdiction rollout pipelines."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from copy import deepcopy
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

SCHEMA_VERSION = "foi-o.australian-rollout-pipeline.v1"
STAGE_ORDER = (
    "discover",
    "select",
    "replay",
    "reconcile",
    "classify",
    "validate",
    "manifest",
    "frame",
    "sample",
    "calibrate",
    "annotate",
    "evaluate",
    "maturity_packet",
)
TERMINAL_STAGE_STATUSES = frozenset({"completed", "skipped"})
ACTIVATED_STAGE_STATUSES = frozenset({"active", "completed", "skipped"})
SHA256_LENGTH = 64


def canonical_bytes(value: Any) -> bytes:
    """Return the producer's stable JSON representation."""
    return (
        json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n"
    ).encode()


def canonical_sha256(value: Any) -> str:
    """Return the SHA-256 of the producer's stable JSON representation."""
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def _without_keys(value: Mapping[str, Any], *keys: str) -> dict[str, Any]:
    return {key: deepcopy(item) for key, item in value.items() if key not in keys}


def definition_sha256(contract: Mapping[str, Any]) -> str:
    """Hash the immutable pipeline definition, excluding checkpoint and envelope pins."""
    return canonical_sha256(
        _without_keys(contract, "definition_sha256", "contract_sha256", "resume_checkpoint")
    )


def contract_sha256(contract: Mapping[str, Any]) -> str:
    """Hash the complete contract envelope, excluding only its self-pin."""
    return canonical_sha256(_without_keys(contract, "contract_sha256"))


def checkpoint_sha256(checkpoint: Mapping[str, Any]) -> str:
    """Hash a resume checkpoint, excluding only its self-pin."""
    return canonical_sha256(_without_keys(checkpoint, "checkpoint_sha256"))


def _schema_path() -> Path:
    return (
        Path(__file__).resolve().parents[2] / "schemas/json/australian-rollout-pipeline.schema.json"
    )


def _load_schema(schema_path: Path | None = None) -> dict[str, Any]:
    path = schema_path or _schema_path()
    return json.loads(path.read_text(encoding="utf-8"))


def _require_sha256(value: object, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != SHA256_LENGTH
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"{label} must be a lowercase SHA-256")
    return value


def _artifact_pin_index(stages: Sequence[Mapping[str, Any]]) -> dict[str, str]:
    pins: dict[str, str] = {}
    for stage in stages:
        for pin_type in ("inputs", "outputs"):
            for pin in stage[pin_type]:
                artifact_id = str(pin["artifact_id"])
                digest = _require_sha256(
                    pin["sha256"], f"{stage['name']} {pin_type} pin {artifact_id}"
                )
                prior = pins.get(artifact_id)
                if prior is not None and prior != digest:
                    raise ValueError(f"artifact pin changed for {artifact_id}")
                pins[artifact_id] = digest
    return pins


def _validate_stage_order(stages: Sequence[Mapping[str, Any]]) -> None:
    names = tuple(str(stage.get("name")) for stage in stages)
    if names != STAGE_ORDER:
        raise ValueError("pipeline stages do not match the required stage order")

    terminal_prefix = True
    for stage in stages:
        status = str(stage["status"])
        if status in ACTIVATED_STAGE_STATUSES and not terminal_prefix:
            raise ValueError(f"stage {stage['name']} activates before its predecessors complete")
        if status not in TERMINAL_STAGE_STATUSES:
            terminal_prefix = False
        if status == "completed" and not stage["outputs"]:
            raise ValueError(f"completed stage {stage['name']} has no output pin")
        if status == "pending" and stage["outputs"]:
            raise ValueError(f"pending stage {stage['name']} cannot declare produced outputs")


def _validate_artifact_lineage(stages: Sequence[Mapping[str, Any]]) -> None:
    outputs_by_stage: dict[str, dict[str, str]] = {}
    for index, stage in enumerate(stages):
        stage_name = str(stage["name"])
        additional_predecessors = [
            str(name) for name in stage.get("additional_predecessor_stages", [])
        ]
        allowed_predecessors: set[str] = set(additional_predecessors)
        if index:
            allowed_predecessors.add(str(stages[index - 1]["name"]))

        for predecessor in additional_predecessors:
            predecessor_index = STAGE_ORDER.index(predecessor)
            if predecessor_index >= index:
                raise ValueError(
                    f"declared predecessor {predecessor} for stage {stage_name} "
                    "is not an earlier stage"
                )

        allowed_outputs: dict[str, str] = {}
        for predecessor in allowed_predecessors:
            allowed_outputs.update(outputs_by_stage[predecessor])
        for pin in stage["inputs"]:
            artifact_id = str(pin["artifact_id"])
            digest = str(pin["sha256"])
            if allowed_outputs.get(artifact_id) != digest:
                raise ValueError(
                    f"input {artifact_id} for stage {stage_name} is not produced "
                    "by an authorized predecessor"
                )
        if index and stage["status"] in ACTIVATED_STAGE_STATUSES and not stage["inputs"]:
            raise ValueError(f"activated stage {stage_name} has no content-addressed input")
        stage_outputs: dict[str, str] = {}
        for pin in stage["outputs"]:
            stage_outputs[str(pin["artifact_id"])] = str(pin["sha256"])
        outputs_by_stage[stage_name] = stage_outputs


def _validate_population_lineage(
    population: Mapping[str, Any], stages: Sequence[Mapping[str, Any]]
) -> None:
    maximum = int(population["maximum_unit_count"])
    root_membership = str(population["root_membership_sha256"])
    seen: dict[str, int] = {root_membership: maximum}
    populations_by_stage: dict[str, tuple[str, int]] = {}

    for index, stage in enumerate(stages):
        stage_name = str(stage["name"])
        stage_population = stage["population"]
        membership = str(stage_population["membership_sha256"])
        parent = str(stage_population["parent_membership_sha256"])
        count = int(stage_population["unit_count"])
        if index == 0:
            allowed_parents = {root_membership: maximum}
        else:
            predecessor_names = {str(stages[index - 1]["name"])}
            predecessor_names.update(
                str(name) for name in stage.get("additional_predecessor_stages", [])
            )
            allowed_parents = {
                populations_by_stage[name][0]: populations_by_stage[name][1]
                for name in predecessor_names
            }
        if parent not in allowed_parents:
            raise ValueError(
                f"stage {stage_name} population parent is not produced by an authorized predecessor"
            )
        if count > maximum or count > seen[parent]:
            raise ValueError(f"stage {stage_name} expands the bounded population")
        prior_count = seen.get(membership)
        if prior_count is not None and prior_count != count:
            raise ValueError(f"population pin {membership} is associated with inconsistent counts")
        seen[membership] = count
        populations_by_stage[stage_name] = (membership, count)


def _validate_gates(
    gates: Sequence[Mapping[str, Any]], stages: Sequence[Mapping[str, Any]]
) -> None:
    by_stage: dict[str, Mapping[str, Any]] = {}
    gate_ids: set[str] = set()
    for gate in gates:
        gate_id = str(gate["gate_id"])
        if gate_id in gate_ids:
            raise ValueError(f"duplicate gate id: {gate_id}")
        gate_ids.add(gate_id)
        stage_name = str(gate["before_stage"])
        if stage_name in by_stage:
            raise ValueError(f"duplicate registered gate for stage {stage_name}")
        by_stage[stage_name] = gate
        if not gate["required"]:
            raise ValueError(f"registered gate for stage {stage_name} must be required")
        state = str(gate["authorization_state"])
        evidence = gate.get("authorization_evidence_sha256")
        if state == "externally_authorized":
            if gate.get("authorized_by") != "external_human":
                raise ValueError(f"gate {gate['gate_id']} is not externally authorized")
            _require_sha256(evidence, f"gate {gate['gate_id']} authorization evidence")
        elif evidence is not None or gate.get("authorized_by") is not None:
            raise ValueError(f"gate {gate['gate_id']} carries evidence without authorization")

    for stage in stages:
        stage_name = str(stage["name"])
        gate = by_stage.get(stage_name)
        if gate is None:
            raise ValueError(f"missing registered gate for stage {stage_name}")
        if (
            stage["status"] in ACTIVATED_STAGE_STATUSES
            and gate["authorization_state"] != "externally_authorized"
        ):
            raise ValueError(f"stage {stage_name} activates without external authorization")


def _validate_failures(
    failures: Sequence[Mapping[str, Any]], stages: Sequence[Mapping[str, Any]]
) -> None:
    stage_names = {str(stage["name"]) for stage in stages}
    identifiers: set[str] = set()
    for failure in failures:
        failure_id = str(failure["failure_id"])
        if failure_id in identifiers:
            raise ValueError(f"duplicate failure disposition: {failure_id}")
        identifiers.add(failure_id)
        if failure["stage"] not in stage_names:
            raise ValueError(f"failure {failure_id} references an unknown stage")
        if failure["status"] == "excluded" and not failure.get("evidence_sha256"):
            raise ValueError(f"excluded failure {failure_id} has no evidence pin")


def validate_resume_checkpoint(
    contract: Mapping[str, Any], checkpoint: Mapping[str, Any] | None = None
) -> None:
    """Validate that a checkpoint resumes this exact definition and completed stage."""
    candidate = checkpoint if checkpoint is not None else contract.get("resume_checkpoint")
    if candidate is None:
        return
    if candidate["definition_sha256"] != definition_sha256(contract):
        raise ValueError("resume checkpoint references a different pipeline definition")
    if candidate["checkpoint_sha256"] != checkpoint_sha256(candidate):
        raise ValueError("resume checkpoint self-pin is invalid")

    stages = list(contract["stages"])
    completed = [stage for stage in stages if stage["status"] in TERMINAL_STAGE_STATUSES]
    if not completed:
        raise ValueError("resume checkpoint exists without a completed stage")
    last = completed[-1]
    if candidate["last_completed_stage"] != last["name"]:
        raise ValueError("resume checkpoint does not identify the last completed stage")
    output_pins = {str(pin["sha256"]) for pin in last["outputs"]}
    if candidate["stage_output_sha256"] not in output_pins:
        raise ValueError("resume checkpoint output pin is not produced by its stage")
    if candidate["population_membership_sha256"] != last["population"]["membership_sha256"]:
        raise ValueError("resume checkpoint population pin does not match its stage")


def validate_artifact_files(
    contract: Mapping[str, Any], artifact_files: Mapping[str, Path]
) -> None:
    """Independently hash supplied artifact files against every matching contract pin."""
    pins = _artifact_pin_index(contract["stages"])
    unknown = set(artifact_files) - set(pins)
    if unknown:
        raise ValueError(f"artifact files are not declared by the contract: {sorted(unknown)}")
    for artifact_id, path in artifact_files.items():
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != pins[artifact_id]:
            raise ValueError(f"artifact file pin mismatch for {artifact_id}")


def validate_contract(
    contract: Mapping[str, Any],
    *,
    schema_path: Path | None = None,
    artifact_files: Mapping[str, Path] | None = None,
) -> dict[str, Any]:
    """Validate schema, hashes, ordering, lineage, boundedness, gates, and checkpoint."""
    schema = _load_schema(schema_path)
    errors = sorted(
        Draft202012Validator(schema).iter_errors(contract), key=lambda error: error.json_path
    )
    if errors:
        first = errors[0]
        raise ValueError(f"schema validation failed at {first.json_path}: {first.message}")
    if contract["schema_version"] != SCHEMA_VERSION:
        raise ValueError("unsupported Australian rollout pipeline schema")
    if contract["definition_sha256"] != definition_sha256(contract):
        raise ValueError("pipeline definition pin is invalid")
    if contract["contract_sha256"] != contract_sha256(contract):
        raise ValueError("pipeline contract self-pin is invalid")

    stages = list(contract["stages"])
    _validate_stage_order(stages)
    _artifact_pin_index(stages)
    _validate_artifact_lineage(stages)
    _validate_population_lineage(contract["population"], stages)
    _validate_gates(contract["gates"], stages)
    _validate_failures(contract["failure_dispositions"], stages)
    validate_resume_checkpoint(contract)
    if artifact_files:
        validate_artifact_files(contract, artifact_files)
    return {
        "pipeline_id": contract["pipeline_id"],
        "stage_count": len(stages),
        "last_completed_stage": next(
            (
                stage["name"]
                for stage in reversed(stages)
                if stage["status"] in TERMINAL_STAGE_STATUSES
            ),
            None,
        ),
        "failure_count": len(contract["failure_dispositions"]),
        "definition_sha256": contract["definition_sha256"],
        "contract_sha256": contract["contract_sha256"],
    }


def finalize_contract(draft: Mapping[str, Any]) -> dict[str, Any]:
    """Pin a draft without granting gates or changing any stage status."""
    contract = deepcopy(dict(draft))
    contract.pop("definition_sha256", None)
    contract.pop("contract_sha256", None)
    checkpoint = contract.get("resume_checkpoint")
    if checkpoint is not None:
        checkpoint = deepcopy(checkpoint)
        checkpoint.pop("checkpoint_sha256", None)
        contract["resume_checkpoint"] = checkpoint
    contract["definition_sha256"] = definition_sha256(contract)
    if checkpoint is not None:
        checkpoint["definition_sha256"] = contract["definition_sha256"]
        checkpoint["checkpoint_sha256"] = checkpoint_sha256(checkpoint)
    contract["contract_sha256"] = contract_sha256(contract)
    validate_contract(contract)
    return contract


def write_contract(output: Path, draft: Mapping[str, Any]) -> dict[str, Any]:
    """Finalize, validate, and write one canonical rollout contract."""
    contract = finalize_contract(draft)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(canonical_bytes(contract))
    return contract

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import pytest
from empirical_context_fixture import build_context_fixture

from foi_o_nz.empirical_pipeline.contracts import canonical_bytes, parse_run_spec, seal_record
from foi_o_nz.empirical_pipeline.execution import (
    ExecutionContextError,
    load_verified_execution_context,
)
from foi_o_nz.empirical_pipeline.packets import (
    PacketContractError,
    build_blinded_packets,
    validate_blinded_packets,
)


def _packets(tmp_path: Path):
    fixture = build_context_fixture(tmp_path)
    packets = build_blinded_packets(
        context=fixture.context,
        annotator_roles=("role:annotator-a", "role:annotator-b"),
        adjudicator_role="role:adjudicator",
    )
    return fixture, packets


def test_packets_are_deterministic_identical_and_context_bound(tmp_path: Path) -> None:
    fixture, packets = _packets(tmp_path)
    validate_blinded_packets(packets, context=fixture.context)
    left, right = packets.values()
    assert left["units"] == right["units"]
    assert left["role_id"] != right["role_id"]
    assert left["membership_sha256"] == fixture.context.membership_sha256
    assert left["codebook_sha256"] == fixture.context.codebook_sha256
    assert left["authorization_sha256"] == fixture.context.authorization_sha256


def test_descriptive_run_spec_cannot_execute_packets(tmp_path: Path) -> None:
    fixture = build_context_fixture(tmp_path)
    descriptive = parse_run_spec(fixture.spec)
    with pytest.raises(PacketContractError, match="verified execution context"):
        build_blinded_packets(  # type: ignore[arg-type]
            context=cast(Any, descriptive),
            annotator_roles=("role:annotator-a", "role:annotator-b"),
            adjudicator_role="role:adjudicator",
        )


@pytest.mark.parametrize(
    "mutation",
    [
        lambda packets: packets["role:annotator-a"].update(role_id="role:annotator-b"),
        lambda packets: packets["role:annotator-a"]["units"][0].update(text="substituted"),
        lambda packets: packets["role:annotator-a"].update(packet_can_authorize_execution=True),
        lambda packets: packets["role:annotator-a"]["units"][0].update(label="leakage"),
    ],
)
def test_packet_validation_rejects_resealed_or_leaking_substitution(
    tmp_path: Path, mutation
) -> None:
    fixture, packets = _packets(tmp_path)
    mutation(packets)
    with pytest.raises(PacketContractError):
        validate_blinded_packets(packets, context=fixture.context)


def test_verified_context_rejects_uncommitted_run_spec(tmp_path: Path) -> None:
    fixture = build_context_fixture(tmp_path)
    spec = json.loads(fixture.paths["run_spec"].read_text())
    spec["relationships"]["supersedes"] = ["run:au-prior"]
    fixture.paths["run_spec"].write_bytes(canonical_bytes(seal_record(spec, "run_spec_sha256")))
    with pytest.raises(ExecutionContextError, match="committed HEAD"):
        load_verified_execution_context(
            run_spec_path=fixture.paths["run_spec"],
            membership_path=fixture.paths["membership"],
            units_path=fixture.paths["units"],
            codebook_path=fixture.paths["codebook"],
            calibration_path=fixture.paths["calibration"],
            authorization_path=fixture.paths["authorization"],
        )


@pytest.mark.parametrize(
    "artifact", ["membership", "units", "codebook", "calibration", "authorization"]
)
def test_verified_context_rejects_artifact_substitution(tmp_path: Path, artifact: str) -> None:
    fixture = build_context_fixture(tmp_path)
    path = fixture.paths[artifact]
    value = json.loads(path.read_text())
    if artifact == "membership":
        value["membership"][0]["unit_id"] = "substituted"
    elif artifact == "units":
        value["units"][0]["text"] = "substituted"
    elif artifact == "codebook":
        value["labels"].append({"id": "invented"})
    elif artifact == "calibration":
        value["role_ids"][0] = "role:invented"
    else:
        value["approved_roles"][0] = "role:invented"
    path.write_text(json.dumps(value))
    with pytest.raises(ExecutionContextError):
        load_verified_execution_context(
            run_spec_path=fixture.paths["run_spec"],
            membership_path=fixture.paths["membership"],
            units_path=fixture.paths["units"],
            codebook_path=fixture.paths["codebook"],
            calibration_path=fixture.paths["calibration"],
            authorization_path=fixture.paths["authorization"],
        )


def test_context_returns_defensive_copies(tmp_path: Path) -> None:
    fixture = build_context_fixture(tmp_path)
    membership = fixture.context.membership
    membership["membership"][0]["unit_id"] = "mutated"
    authorization = fixture.context.authorization
    authorization["approved_roles"].clear()
    assert fixture.context.membership["membership"][0]["unit_id"] == "u1"
    assert len(fixture.context.authorization["approved_roles"]) == 3

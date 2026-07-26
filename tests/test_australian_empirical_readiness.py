import copy
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, cast

import pytest
import yaml
from jsonschema import Draft202012Validator
from pydantic import ValidationError

from foi_o_nz.australian_empirical_readiness import (
    AustralianEmpiricalReadiness,
    audit_australian_empirical_readiness,
)

ROOT = Path(__file__).parent.parent
MANIFEST = (
    ROOT
    / "conductor"
    / "tracks"
    / "australian_jurisdiction_profiles_20260714"
    / "phase-3-readiness.json"
)
TRACK = MANIFEST.parent
OPERATOR_PACKET = TRACK / "phase-3-operator-packet.json"
OPERATOR_PACKET_SCHEMA = (
    ROOT / "schemas" / "json" / "australian-empirical-operator-packet.schema.json"
)
AU_CTH_SOURCE_PACK_APPROVAL = (
    ROOT / "examples" / "v2" / "australian-source-pack-au-cth-2026-07-26.approved.json"
)


def _current() -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(MANIFEST.read_text(encoding="utf-8")))


def test_current_manifest_reports_exact_fail_closed_blockers() -> None:
    payload = _current()
    schema = AustralianEmpiricalReadiness.model_json_schema()
    Draft202012Validator(schema).validate(payload)
    manifest = AustralianEmpiricalReadiness.model_validate(payload)

    result = audit_australian_empirical_readiness(manifest)

    assert result.ready is False
    assert result.promotion_allowed is False
    assert set(result.profile_ids) == {"foio-au-cth", "foio-au-nsw"}
    assert set(result.blockers) == {
        "foio-au-nsw.archive.immutable_sample_missing",
        "foio-au-nsw.extraction.placeholder_or_missing",
        "foio-au-nsw.sampling.codebook_pin_missing",
        "foio-au-nsw.sampling.configuration_not_approved",
        "foio-au-nsw.sampling.reliability_thresholds_not_approved",
        "foio-au-nsw.annotation_roles.two_independent_annotators_missing",
        "foio-au-nsw.annotation_roles.adjudicator_missing",
        "foio-au-nsw.annotation_roles.assignment_not_approved",
    }


def test_current_commonwealth_inputs_are_hash_bound_and_bounded() -> None:
    payload = _current()
    commonwealth = cast(dict[str, Any], payload["profiles"][0])
    legislation = cast(dict[str, Any], commonwealth["legislation"])
    extraction = cast(dict[str, Any], commonwealth["extraction"])
    approval = json.loads(AU_CTH_SOURCE_PACK_APPROVAL.read_text(encoding="utf-8"))

    assert legislation["status"] == "approved"
    assert legislation["artifact_sha256"] == (
        "19dc7ddf07f3bcff38c13f4073f373e5545a316e8e5b922808b41415683e50d4"
    )
    assert extraction["status"] == "approved"
    assert extraction["repository_revision"] == ("e4a8cf36090be8c22106072514d9098d27445244")
    assert approval["approved_revision"] == ("5b297bcf5d3cb838e5afe40b889cc08a23a1dd66")
    assert approval["source_evidence"]["sha256"] == (
        "3f3577972a614a6a72c3eaf94a493ac52f1eb207ea0881e38a0969f771de2fce"
    )
    assert approval["authorization"] == {
        "bounded_source_pack_maturity": True,
        "publication": False,
        "redistribution": False,
        "training": False,
        "legal_certification": False,
        "unbounded_inference": False,
        "broader_profile_promotion": False,
    }


def test_operator_packet_covers_every_current_blocker_and_human_gate() -> None:
    packet = json.loads(OPERATOR_PACKET.read_text(encoding="utf-8"))
    schema = json.loads(OPERATOR_PACKET_SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(packet)

    readiness = AustralianEmpiricalReadiness.model_validate(_current())
    blockers = audit_australian_empirical_readiness(readiness).blockers
    covered = [blocker for action in packet["actions"] for blocker in action["readiness_blockers"]]
    assert sorted(covered) == blockers
    assert len(covered) == len(set(covered))
    assert [action["action_id"] for action in packet["actions"]] == [
        "AU-OP-03",
        "AU-OP-04",
        "AU-OP-05",
        "AU-OP-06",
    ]

    gates = yaml.safe_load((TRACK / "human-gates.yaml").read_text(encoding="utf-8"))
    known_gate_ids = {gate["id"] for gate in gates["gates"]}
    assert {
        gate_id for action in packet["actions"] for gate_id in action["human_gate_ids"]
    }.issubset(known_gate_ids)
    assert all(action["status"] == "pending" for action in packet["actions"])
    assert all(action["automatable"] is False for action in packet["actions"])
    assert packet["strict_validation_command"] == (
        "python scripts/validate_australian_empirical_readiness.py --require-ready"
    )
    assert packet["tranche_3_complete"] is False
    assert packet["tranche_5_expansion_allowed"] is False
    assert packet["profile_promotion_allowed"] is False


def test_complete_independent_inputs_can_be_ready_without_promoting() -> None:
    payload = _current()
    profiles = cast(list[dict[str, Any]], payload["profiles"])
    for profile_index, profile in enumerate(profiles):
        assert isinstance(profile, dict)
        for artifact_index, key in enumerate(("legislation", "archive", "extraction")):
            artifact = cast(dict[str, Any], profile[key])
            artifact.update(
                status="approved",
                artifact_path=f"manifests/{profile['profile_id']}/{key}.json",
                artifact_sha256=f"{profile_index + artifact_index + 1:064x}",
                rights_reviewed=True,
                independently_reviewed=True,
            )
        sampling = cast(dict[str, Any], profile["sampling"])
        sampling.update(
            codebook_path=f"codebooks/{profile['profile_id']}.json",
            codebook_revision="a" * 40,
            codebook_sha256=f"{profile_index + 10:064x}",
            sampling_configuration_path=f"frames/{profile['profile_id']}.json",
            sampling_configuration_sha256=f"{profile_index + 20:064x}",
            configuration_approved=True,
            reliability_thresholds_approved=True,
        )
        roles = cast(dict[str, Any], profile["annotation_roles"])
        roles.update(
            role_kind="automated_agent",
            annotator_ids=["automated-agent-role-a", "automated-agent-role-b"],
            adjudicator_id="automated-agent-role-adjudicator",
            assignment_approved=True,
            approval_ref=f"approvals/{profile['profile_id']}.json",
        )

    result = audit_australian_empirical_readiness(
        AustralianEmpiricalReadiness.model_validate(payload)
    )

    assert result.ready is True
    assert result.blockers == []
    assert result.promotion_allowed is False


def test_repeated_placeholder_digest_is_rejected_even_if_marked_approved() -> None:
    payload = _current()
    profiles = cast(list[dict[str, Any]], payload["profiles"])
    artifact = cast(dict[str, Any], profiles[0]["extraction"])
    artifact.update(
        status="approved",
        artifact_path="fixture.json",
        artifact_sha256="b" * 64,
        rights_reviewed=True,
        independently_reviewed=True,
    )

    result = audit_australian_empirical_readiness(
        AustralianEmpiricalReadiness.model_validate(payload)
    )

    assert "foio-au-cth.extraction.placeholder_or_missing" in result.blockers


def test_approved_automated_roles_must_remain_distinct() -> None:
    payload = _current()
    profiles = cast(list[dict[str, Any]], payload["profiles"])
    roles = cast(dict[str, Any], profiles[0]["annotation_roles"])
    roles["annotator_ids"] = ["automated-agent-role-a", "automated-agent-role-a"]

    result = audit_australian_empirical_readiness(
        AustralianEmpiricalReadiness.model_validate(payload)
    )

    assert "foio-au-cth.annotation_roles.two_independent_annotators_missing" in result.blockers


def test_manifest_rejects_an_unplanned_profile() -> None:
    payload = _current()
    profiles = cast(list[dict[str, Any]], payload["profiles"])
    extra = copy.deepcopy(profiles[0])
    extra.update(profile_id="foio-au-vic", jurisdiction="AU-VIC")
    profiles.append(extra)

    with pytest.raises(ValidationError, match="exactly AU-CTH and AU-NSW"):
        AustralianEmpiricalReadiness.model_validate(payload)


def test_phase_workflow_has_paired_mermaid_and_bpmn_contracts() -> None:
    workflow = (TRACK / "workflow.md").read_text(encoding="utf-8")
    assert "```mermaid" in workflow
    assert "workflow.bpmn" in workflow

    root = ET.parse(TRACK / "workflow.bpmn").getroot()
    namespace = "{http://www.omg.org/spec/BPMN/20100524/MODEL}"
    process = root.find(f"{namespace}process")
    assert process is not None
    assert process.find(f"{namespace}userTask") is not None
    assert len(process.findall(f"{namespace}sequenceFlow")) == 10

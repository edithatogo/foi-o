"""Offline conformance tests for named FOI-O extraction-contract consumers."""

from __future__ import annotations

import json
from pathlib import Path

from foi_o_nz.contract_capabilities import negotiate_extraction_contract
from foi_o_nz.empirical_contracts import ConsumerExtractionContract, ExtractionContract
from foi_o_nz.validation import validate_json_schema

ROOT = Path(__file__).parents[1]
FIXTURE_ROOT = ROOT / "examples" / "v2" / "consumer-contracts"
MATRIX = ROOT / "docs" / "compatibility" / "foi-o-v2-consumers.json"
CONSUMER_SCHEMA = ROOT / "schemas" / "json" / "consumer-extraction-contract.schema.json"
EXTRACTION_MANIFEST = ROOT / "contracts" / "foi-o-extraction-contract" / "0.1.0" / "manifest.json"


def _load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_named_consumer_fixture_set_is_complete_and_matches_matrix() -> None:
    fixtures = sorted(FIXTURE_ROOT.glob("*.json"))
    assert [fixture.stem for fixture in fixtures] == [
        "foi-o",
        "fyi-archive",
        "nlp-policy-nz",
        "read-only-mcp",
    ]
    fixture_records = [_load(fixture) for fixture in fixtures]
    matrix = _load(MATRIX)
    assert matrix["verification_scope"] == "repo_local_offline"
    assert matrix["all_upstream_verified"] is False
    assert matrix["consumers"] == fixture_records


def test_each_consumer_fixture_validates_and_negotiates_declared_versions() -> None:
    extraction = ExtractionContract.model_validate(_load(EXTRACTION_MANIFEST))
    for fixture in sorted(FIXTURE_ROOT.glob("*.json")):
        result = validate_json_schema(fixture, CONSUMER_SCHEMA)
        assert not result.errors, result.errors
        consumer = ConsumerExtractionContract.model_validate(_load(fixture))
        for version in consumer.accepted_versions:
            negotiation = negotiate_extraction_contract(
                extraction,
                requested_version=version,
                required_capability_ids=consumer.required_capability_ids,
            )
            assert negotiation.accepted is True
        for rejected in consumer.rejected_versions:
            negotiation = negotiate_extraction_contract(
                extraction,
                requested_version=rejected.version,
                required_capability_ids=consumer.required_capability_ids,
            )
            assert negotiation.accepted is False
            assert negotiation.reason == rejected.reason


def test_consumer_matrix_preserves_candidate_and_remote_approval_boundaries() -> None:
    consumers = [
        ConsumerExtractionContract.model_validate(_load(fixture))
        for fixture in sorted(FIXTURE_ROOT.glob("*.json"))
    ]
    assert all(consumer.candidate_only for consumer in consumers)
    assert all(not consumer.machine_certification_allowed for consumer in consumers)
    assert all(not consumer.upstream_verified for consumer in consumers)
    mcp = next(consumer for consumer in consumers if consumer.consumer_id == "foi-o-read-only-mcp")
    assert mcp.read_only is True

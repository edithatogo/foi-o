"""Contract tests for the versioned FOI-O extraction export."""

from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path

import pytest
from pydantic import ValidationError

from foi_o_nz.contract_capabilities import (
    discover_extraction_capabilities,
    find_extraction_migration,
    negotiate_extraction_contract,
)
from foi_o_nz.empirical_contracts import ExtractionContract
from foi_o_nz.validation import validate_json_schema

ROOT = Path(__file__).parents[1]
MANIFEST = ROOT / "contracts" / "foi-o-extraction-contract" / "0.1.0" / "manifest.json"
SCHEMA = ROOT / "schemas" / "json" / "extraction-contract.schema.json"
VALID = ROOT / "examples" / "v2" / "schema-valid" / "extraction-contract-1.json"
INVALID_ROOT = ROOT / "examples" / "v2" / "schema-invalid"


def _load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_committed_manifest_matches_schema_model_and_valid_fixture() -> None:
    manifest = _load(MANIFEST)
    assert manifest == _load(VALID)
    assert not validate_json_schema(MANIFEST, SCHEMA).errors
    contract = ExtractionContract.model_validate(manifest)
    assert contract.contract_id == "foi-o.extraction-contract"
    assert contract.contract_version == "0.1.0"
    assert contract.consumer_id == "nlp-policy-nz"


@pytest.mark.parametrize("fixture_number", [1, 2, 3])
def test_invalid_extraction_contract_fixtures_fail_schema_and_model(
    fixture_number: int,
) -> None:
    fixture = INVALID_ROOT / f"extraction-contract-{fixture_number}.json"
    assert validate_json_schema(fixture, SCHEMA).errors
    with pytest.raises(ValidationError):
        ExtractionContract.model_validate(_load(fixture))


def test_contract_pins_repo_artifacts_and_keeps_candidates_non_certified() -> None:
    contract = ExtractionContract.model_validate(_load(MANIFEST))
    pinned_paths = {artifact.path for artifact in contract.artifacts}
    assert "ontology/foi-o-nz.ttl" in pinned_paths
    assert "schemas/json/ontology-release-manifest.schema.json" in pinned_paths
    assert "codebooks/nz/oia.seed-codebook.yaml" in pinned_paths
    assert "migrations/v1-to-v2-empirical-overlay.md" in pinned_paths
    assert contract.candidate_status_vocabulary.allowed_statuses == [
        "observed",
        "inferred",
        "asserted",
        "unknown",
    ]
    assert contract.candidate_status_vocabulary.certified_status_allowed is False
    assert contract.human_promotion_required is True
    for artifact in contract.artifacts:
        content = (ROOT / artifact.path).read_bytes()
        assert sha256(content).hexdigest() == artifact.sha256


def test_extraction_negotiation_accepts_exact_and_declared_range() -> None:
    contract = ExtractionContract.model_validate(_load(MANIFEST))
    exact = negotiate_extraction_contract(
        contract,
        requested_version="0.1.0",
        required_capability_ids=["foi-o-nz.label-assertion"],
    )
    assert exact.accepted is True
    assert exact.reason == "exact_version"

    compatible = negotiate_extraction_contract(
        contract,
        requested_version="0.1.7",
        required_capability_ids=["foi-o-nz.evidence-assertion"],
    )
    assert compatible.accepted is True
    assert compatible.reason == "declared_range"


def test_extraction_negotiation_rejects_unknown_major_and_missing_capability() -> None:
    contract = ExtractionContract.model_validate(_load(MANIFEST))
    unknown_major = negotiate_extraction_contract(contract, requested_version="1.0.0")
    assert unknown_major.accepted is False
    assert unknown_major.reason == "unknown_major_rejected"

    missing_capability = negotiate_extraction_contract(
        contract,
        requested_version="0.1.0",
        required_capability_ids=["foi-o-nz.certify-legal-outcome"],
    )
    assert missing_capability.accepted is False
    assert missing_capability.reason == "missing_capability"

    unsupported_revision = negotiate_extraction_contract(contract, requested_version="0.2.0")
    assert unsupported_revision.accepted is False
    assert unsupported_revision.reason == "unsupported_revision_rejected"

    malformed = negotiate_extraction_contract(contract, requested_version="latest")
    assert malformed.accepted is False
    assert malformed.reason == "invalid_version_rejected"


def test_capability_discovery_and_migration_lookup_are_explicit() -> None:
    contract = ExtractionContract.model_validate(_load(MANIFEST))
    assert discover_extraction_capabilities(contract) == [
        "foi-o-nz.label-assertion",
        "foi-o-nz.evidence-assertion",
    ]
    migration = find_extraction_migration(contract, from_version="0.8.1")
    assert migration is not None
    assert migration.migration_id == "foi-o-nz.v1-to-v2-empirical-overlay"
    assert find_extraction_migration(contract, from_version="9.9.9") is None

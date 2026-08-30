from pathlib import Path

import pytest

from foi_o_nz.validation import validate_json_schema

ROOT = Path(__file__).parents[1]
GOVERNANCE_SCHEMA = ROOT / "schemas/json/generic-governance-metadata.schema.json"
PROVENANCE_SCHEMA = ROOT / "schemas/json/provenance-reference.schema.json"


def test_valid_generic_governance_metadata_example() -> None:
    example_path = ROOT / "examples/v2/generic-governance-metadata.valid.json"
    result = validate_json_schema(example_path, GOVERNANCE_SCHEMA)
    assert not result.errors, result.errors


def test_valid_provenance_reference_example() -> None:
    example_path = ROOT / "examples/v2/provenance-reference.valid.json"
    result = validate_json_schema(example_path, PROVENANCE_SCHEMA)
    assert not result.errors, result.errors


@pytest.mark.parametrize(
    "fixture_filename",
    [
        "generic-governance-metadata-absolute-path.json",
        "generic-governance-metadata-case-id.json",
    ],
)
def test_generic_governance_metadata_rejects_invalid_fixtures(fixture_filename: str) -> None:
    path = ROOT / "examples/v2/schema-invalid" / fixture_filename
    result = validate_json_schema(path, GOVERNANCE_SCHEMA)
    assert result.errors, f"Expected validation errors for {fixture_filename}"


def test_provenance_reference_rejects_invalid_path() -> None:
    path = ROOT / "examples/v2/schema-invalid/provenance-reference-invalid-path.json"
    result = validate_json_schema(path, PROVENANCE_SCHEMA)
    assert result.errors, "Expected validation errors for absolute path in provenance reference"


def test_python_validators_for_generic_governance() -> None:
    from foi_o_nz.generic_governance import (
        validate_generic_governance_metadata,
        validate_provenance_reference,
    )

    valid_gov = ROOT / "examples/v2/generic-governance-metadata.valid.json"
    assert validate_generic_governance_metadata(valid_gov)["ok"] is True

    valid_ref = ROOT / "examples/v2/provenance-reference.valid.json"
    assert validate_provenance_reference(valid_ref)["ok"] is True

    invalid_gov = ROOT / "examples/v2/schema-invalid/generic-governance-metadata-absolute-path.json"
    with pytest.raises(ValueError, match=r"schema validation failed|restricted location"):
        validate_generic_governance_metadata(invalid_gov)

    invalid_ref = ROOT / "examples/v2/schema-invalid/provenance-reference-invalid-path.json"
    with pytest.raises(ValueError, match=r"schema validation failed|restricted location"):
        validate_provenance_reference(invalid_ref)

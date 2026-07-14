"""Validate every FOI-O V2 empirical schema fixture through native helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

from foi_o_nz.validation import validate_json_schema

FIXTURE_ROOT = Path("examples/v2")
SCHEMA_ROOT = Path("schemas/json")


def _schema_for_fixture(path: Path) -> Path:
    """Resolve a numbered fixture name to its committed schema."""
    contract_name = path.stem.rsplit("-", maxsplit=1)[0]
    return SCHEMA_ROOT / f"{contract_name}.schema.json"


@pytest.mark.parametrize("fixture", sorted((FIXTURE_ROOT / "schema-valid").glob("*.json")))
def test_v2_valid_fixtures_pass_committed_schemas(fixture: Path) -> None:
    """Require every positive fixture to validate against its native schema."""
    result = validate_json_schema(fixture, _schema_for_fixture(fixture))
    assert not result.errors, result.errors


@pytest.mark.parametrize("fixture", sorted((FIXTURE_ROOT / "schema-invalid").glob("*.json")))
def test_v2_invalid_fixtures_fail_committed_schemas(fixture: Path) -> None:
    """Require every negative fixture to demonstrate at least one rejection."""
    result = validate_json_schema(fixture, _schema_for_fixture(fixture))
    assert result.errors, fixture

"""Contract tests for the declarative jurisdiction regime registry."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator

from foi_o_nz.agent_triangulated_medallion import JURISDICTION_REGIMES as MEDALLION_REGIMES
from foi_o_nz.jurisdiction_regimes import (
    DEFAULT_REGISTRY,
    DEFAULT_SCHEMA,
    StatutoryProfile,
    load_jurisdiction_regimes,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def registry_document() -> dict:
    document = yaml.safe_load((REPO_ROOT / DEFAULT_REGISTRY).read_text(encoding="utf-8"))
    assert isinstance(document, dict)
    return document


@pytest.fixture(scope="module")
def registry_schema() -> dict:
    return json.loads((REPO_ROOT / DEFAULT_SCHEMA).read_text(encoding="utf-8"))


def _make_profile_doc(**overrides: object) -> dict:
    base: dict = {
        "id": "XX-TEST",
        "jurisdiction": "XX-TEST",
        "regime": "TEST",
        "statute_name": "Test Act 2026",
        "statutory_timeframe_days": 20,
        "timeframe_type": "working_days",
        "default_agency_scope": "Test Agencies",
        "exemption_clauses": ["s1"],
    }
    base.update(overrides)
    return base


class TestRegistrySchemaConformance:
    def test_document_validates_against_schema(
        self, registry_document: dict, registry_schema: dict
    ) -> None:
        errors = list(Draft202012Validator(registry_schema).iter_errors(registry_document))
        assert not errors

    def test_loader_builds_strict_profiles(self) -> None:
        profiles = load_jurisdiction_regimes()
        assert profiles
        assert all(isinstance(p, StatutoryProfile) for p in profiles.values())

    def test_every_profile_id_matches_jurisdiction(self, registry_document: dict) -> None:
        for item in registry_document["profiles"]:
            assert item["id"] == item["jurisdiction"]

    def test_no_duplicate_profile_ids(self, registry_document: dict) -> None:
        ids = [item["id"] for item in registry_document["profiles"]]
        assert len(ids) == len(set(ids))

    def test_timeframes_are_positive_and_typed(self, registry_document: dict) -> None:
        for item in registry_document["profiles"]:
            assert 1 <= item["statutory_timeframe_days"] <= 365
            assert item["timeframe_type"] in {"working_days", "calendar_days"}


class TestLoaderValidationBoundaries:
    def test_missing_required_field_is_rejected(self, registry_schema: dict) -> None:
        doc = {"registry_id": "foio.jurisdiction-regimes", "version": "1.0.0",
               "profiles": [{k: v for k, v in _make_profile_doc().items() if k != "regime"}]}
        errors = list(Draft202012Validator(registry_schema).iter_errors(doc))
        assert errors

    def test_id_jurisdiction_mismatch_raises(self, tmp_path: Path) -> None:
        doc = {"registry_id": "foio.jurisdiction-regimes", "version": "1.0.0",
               "profiles": [_make_profile_doc(jurisdiction="OTHER")]}
        registry = tmp_path / "reg.yaml"
        registry.write_text(yaml.safe_dump(doc), encoding="utf-8")
        schema = REPO_ROOT / DEFAULT_SCHEMA
        with pytest.raises(ValueError, match="must match jurisdiction"):
            load_jurisdiction_regimes(registry_path=registry, schema_path=schema)

    def test_duplicate_ids_raise(self, tmp_path: Path) -> None:
        profile = _make_profile_doc()
        doc = {"registry_id": "foio.jurisdiction-regimes", "version": "1.0.0",
               "profiles": [profile, dict(profile)]}
        registry = tmp_path / "reg.yaml"
        registry.write_text(yaml.safe_dump(doc), encoding="utf-8")
        with pytest.raises(ValueError, match="duplicate jurisdiction profile id"):
            load_jurisdiction_regimes(registry_path=registry, schema_path=REPO_ROOT / DEFAULT_SCHEMA)

    def test_schema_violation_raises(self, tmp_path: Path) -> None:
        doc = {"registry_id": "foio.jurisdiction-regimes", "version": "1.0.0",
               "profiles": [_make_profile_doc(statutory_timeframe_days=0)]}
        registry = tmp_path / "reg.yaml"
        registry.write_text(yaml.safe_dump(doc), encoding="utf-8")
        with pytest.raises(ValueError, match="failed schema validation"):
            load_jurisdiction_regimes(registry_path=registry, schema_path=REPO_ROOT / DEFAULT_SCHEMA)

    def test_loader_is_cached(self) -> None:
        assert load_jurisdiction_regimes() is load_jurisdiction_regimes()


class TestMedallionIntegration:
    def test_medallion_registry_includes_canonical_registry(self) -> None:
        canonical = load_jurisdiction_regimes()
        for profile_id, profile in canonical.items():
            assert MEDALLION_REGIMES[profile_id] == profile

    def test_foundation_profiles_present(self) -> None:
        for profile_id in ("NZ", "NZ-OIA", "NZ-LGOIMA", "AU-CTH", "UK-FOIA", "US-FOIA-FED"):
            assert profile_id in MEDALLION_REGIMES

    def test_subnational_profiles_registered(self) -> None:
        assert any(pid.startswith("US-") for pid in MEDALLION_REGIMES)
        assert any(pid.startswith("CA-") for pid in MEDALLION_REGIMES)

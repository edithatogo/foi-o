"""Tests for the local-only NZ non-legislation source evidence manifest."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from foi_o_nz.validation import validate_json_schema

ROOT = Path(__file__).parents[1]
MANIFEST = ROOT / "examples/v2/nz-nonlegislation-source-manifest.2026-07-16.json"
SCHEMA = ROOT / "schemas/json/nz-nonlegislation-source-manifest.schema.json"
RIGHTS = ROOT / "mappings/nz-source-rights-registry.yaml"


def test_nonlegislation_manifest_is_schema_valid_and_local_only() -> None:
    result = validate_json_schema(MANIFEST, SCHEMA)
    assert not result.errors, result.errors
    payload = json.loads(MANIFEST.read_text())
    assert payload["source_count"] == 7
    assert payload["content_committed"] is False
    assert payload["source_pack_promotion_allowed"] is False
    assert all(not source["content_committed"] for source in payload["sources"])
    assert all(not (ROOT / source["local_filename"]).exists() for source in payload["sources"])


def test_manifest_covers_ombudsman_agency_and_reporting_materials() -> None:
    payload = json.loads(MANIFEST.read_text())
    categories = {source["category"] for source in payload["sources"]}
    assert categories == {
        "ombudsman_guidance",
        "agency_guidance",
        "reporting_guidance",
    }
    assert len({source["source_id"] for source in payload["sources"]}) == 7
    assert len({source["content_sha256"] for source in payload["sources"]}) == 7


def test_rights_and_historical_applicability_remain_fail_closed() -> None:
    payload = json.loads(MANIFEST.read_text())
    registry = yaml.safe_load(RIGHTS.read_text())
    registry_ids = {source["source_id"] for source in registry["sources"]}
    ombudsman = [
        source for source in payload["sources"] if source["provider_id"] == "nz-ombudsman"
    ]
    psc = [
        source
        for source in payload["sources"]
        if source["provider_id"] == "nz-public-service-commission"
    ]
    assert {source["rights_registry_source_id"] for source in ombudsman} == {
        "nz-ombudsman-content"
    }
    assert "nz-ombudsman-content" in registry_ids
    assert all(source["rights_status"] == "approved_personal_use_only" for source in ombudsman)
    assert all(source["rights_registry_source_id"] is None for source in psc)
    assert all(source["rights_status"] == "provider_scope_review_pending" for source in psc)
    assert all(not source["historical_applicability_approved"] for source in payload["sources"])
    assert all(not source["human_source_selection_approved"] for source in payload["sources"])


def test_ombudsman_historical_and_current_revisions_are_not_conflated() -> None:
    payload = json.loads(MANIFEST.read_text())
    revisions = {
        source["source_id"]: source["content_sha256"]
        for source in payload["sources"]
        if source["provider_id"] == "nz-ombudsman"
    }
    assert revisions == {
        "ombudsman-oia-agencies-2024-03":
            "ef2a5563a687961fdb8b6da12e409ba8e9d520b5932b29ba5a94c841103ec4f0",
        "ombudsman-oia-agencies-2025-06":
            "9226f385659c698aeb37957d6604196d1ab709ecc72e67ff8ee3729524f3df7e",
    }

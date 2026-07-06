from __future__ import annotations

import json
from pathlib import Path

from foi_o_nz.validation import validate_json_schema

MANIFEST = Path("examples/empirical-taskset-manifest.nz-first.json")
SCHEMA = Path("schemas/json/empirical-taskset-manifest.schema.json")
GOLDSET_DOC = Path("docs/20-corpus-profile-goldset.md")
METHODS_PROTOCOL = Path("docs/24-ontology-methods-protocol.md")
CLAIMS = Path("docs/24-ontology-claims-register.md")
ASSET_INDEX = Path("docs/25-generated-asset-index.md")
ASSET_MANIFEST = Path("examples/generated-asset-manifest.foi-o-publication.json")


def test_empirical_taskset_manifest_validates_and_stays_annotation_only() -> None:
    result = validate_json_schema(MANIFEST, SCHEMA)
    assert not result.errors, result.errors

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert manifest["jurisdiction"] == "NZ"
    assert manifest["claim_boundary"] == "annotation_tasks_not_gold_standard"
    assert manifest["ok"] is True
    assert {task["claim_boundary"] for task in manifest["task_sets"]} == {
        "annotation_task_until_human_reviewed"
    }
    assert {task["review_status"] for task in manifest["task_sets"]} == {"planned"}


def test_empirical_taskset_manifest_records_required_task_mix() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    task_counts = {task["task_type"]: task["planned_count"] for task in manifest["task_sets"]}

    assert task_counts == {
        "state_mapping": 100,
        "timeline_extraction": 30,
        "outcome_classification": 30,
        "legal_issue_flagging": 20,
        "attachment_characterisation": 20,
    }
    assert len(manifest["external_gates"]) >= 5
    assert "gold-standard label only applied after adjudication" in manifest["external_gates"]


def test_empirical_taskset_manifest_is_documented_and_registered() -> None:
    goldset_doc = GOLDSET_DOC.read_text(encoding="utf-8")
    methods = METHODS_PROTOCOL.read_text(encoding="utf-8")
    claims = CLAIMS.read_text(encoding="utf-8")
    index = ASSET_INDEX.read_text(encoding="utf-8")
    asset_manifest = json.loads(ASSET_MANIFEST.read_text(encoding="utf-8"))
    asset_paths = {asset["path"] for asset in asset_manifest["assets"]}

    for text in [goldset_doc, methods, claims, index]:
        assert "`examples/empirical-taskset-manifest.nz-first.json`" in text

    assert "annotation_tasks_not_gold_standard" in goldset_doc
    assert "Call them annotation task sets" in claims
    assert str(MANIFEST) in asset_paths

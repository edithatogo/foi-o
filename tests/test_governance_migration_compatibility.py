"""Test compatibility and public-safety migration for governance metadata."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from foi_o_nz.generic_governance import (
    build_public_governance_provenance_map,
    is_public_safe_manifest,
    validate_provenance_reference,
)
from foi_o_nz.validation import validate_json_schema

ROOT = Path(__file__).parents[1]
RELEASE_MANIFEST_SCHEMA = ROOT / "schemas/json/release-manifest.schema.json"


def test_historical_semantic_core_manifest_compatibility() -> None:
    manifest_path = ROOT / "conductor/release-candidate-2026-08-03/manifest.json"
    assert manifest_path.is_file()
    result = validate_json_schema(manifest_path, RELEASE_MANIFEST_SCHEMA)
    assert not result.errors, result.errors

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    safe, errors = is_public_safe_manifest(manifest)
    assert safe, errors


def test_public_safe_manifest_rejects_leakage() -> None:
    bad_manifests = [
        {"files": [{"path": "/private/tmp/secret.json", "sha256": "a" * 64}]},
        {"files": [{"path": "/opt/homebrew/bin/pdftotext", "sha256": "a" * 64}]},
        {"files": [{"path": "/Users/alice/repo/file.txt", "sha256": "a" * 64}]},
        {"files": [{"path": "data/case-35076-doc.pdf", "sha256": "a" * 64}]},
        {"description": "Extracted using /private/tmp/cache"},
    ]
    for bad in bad_manifests:
        safe, errors = is_public_safe_manifest(bad)
        assert not safe
        assert len(errors) >= 1


def test_build_public_governance_provenance_map() -> None:
    test_files = ["README.md", "pyproject.toml", "ontology/foi-o-nz.ttl"]
    refs = build_public_governance_provenance_map(ROOT, test_files)
    assert len(refs) == 3

    for ref in refs:
        validated = validate_provenance_reference(ref)
        assert validated["ok"] is True
        assert ref["schema_version"] == "foi-o.provenance-reference.v0.1.0"
        assert len(ref["content_sha256"]) == 64


def test_build_public_governance_provenance_map_rejects_unsafe_paths() -> None:
    with pytest.raises(ValueError, match="violates public governance safety"):
        build_public_governance_provenance_map(ROOT, ["/tmp/leak.txt"])

    with pytest.raises(ValueError, match="violates public governance safety"):
        build_public_governance_provenance_map(ROOT, ["examples/case-11872.json"])

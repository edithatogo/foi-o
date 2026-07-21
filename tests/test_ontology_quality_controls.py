"""Tests for ontology registry and semantic-quality controls."""

from pathlib import Path

from rdflib import Graph

from scripts.validate_ontology_quality import validate, validate_documents

ROOT = Path(__file__).resolve().parents[1]


def test_canonical_ontology_controls_validate() -> None:
    result = validate(ROOT)

    assert result["ok"] is True
    assert result["quality"]["unlabelled_terms"] == 0


def test_registry_rejects_unverified_submission_evidence() -> None:
    ledger = {
        "namespace": "https://w3id.org/foio/",
        "registries": [
            {
                "registry_id": "TEST",
                "status": "not_verified",
                "submission_evidence": "url",
                "human_gate": True,
            }
        ],
    }
    plan = {
        "prerequisites": [
            "canonical_global_namespace",
            "persistent_uri_redirect_plan",
            "version_iri_and_prior_version_metadata",
            "shacl_validation",
            "ontology_quality_report",
            "migration_from_nz_namespace",
        ],
        "status_policy": {"no_evidence_value": "not_verified"},
    }
    migration = {
        "canonical_namespace": "https://w3id.org/foio/",
        "status": "candidate",
        "policy": {"automatic_semantic_promotion": False, "require_human_approval": True},
        "aliases": [{"legacy": "x"}],
    }
    graph = Graph()

    result = validate_documents(ledger, plan, migration, graph)

    assert "TEST: unverified registry cannot carry submission evidence" in result["errors"]


def test_namespace_migration_rejects_automatic_promotion() -> None:
    result = validate(ROOT)
    assert result["ok"] is True

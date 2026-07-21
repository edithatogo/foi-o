"""Validate ontology registry readiness and deterministic RDF quality signals."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml
from rdflib import OWL, RDF, RDFS, Graph

ROOT = Path(__file__).resolve().parents[1]
CANONICAL_NAMESPACE = "https://w3id.org/foio/"
ALLOWED_REGISTRY_STATUSES = {"not_verified", "not_applicable"}
REQUIRED_PREREQUISITES = {
    "canonical_global_namespace",
    "persistent_uri_redirect_plan",
    "version_iri_and_prior_version_metadata",
    "shacl_validation",
    "ontology_quality_report",
    "migration_from_nz_namespace",
}


def _yaml(root: Path, relative: str) -> dict[str, Any]:
    value = yaml.safe_load((root / relative).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{relative} must contain a mapping")
    return value


def _quality_signals(graph: Graph) -> dict[str, int]:
    classes = set(graph.subjects(RDF.type, OWL.Class))
    object_properties = set(graph.subjects(RDF.type, OWL.ObjectProperty))
    datatype_properties = set(graph.subjects(RDF.type, OWL.DatatypeProperty))
    terms = classes | object_properties | datatype_properties
    labelled = {term for term in terms if any(graph.objects(term, RDFS.label))}
    return {
        "triples": len(graph),
        "classes": len(classes),
        "object_properties": len(object_properties),
        "datatype_properties": len(datatype_properties),
        "labelled_terms": len(labelled),
        "unlabelled_terms": len(terms - labelled),
    }


def validate_documents(
    ledger: dict[str, Any],
    plan: dict[str, Any],
    migration: dict[str, Any],
    graph: Graph,
) -> dict[str, Any]:
    """Return deterministic errors and quality signals for ontology controls."""
    errors: list[str] = []
    if ledger.get("namespace") != CANONICAL_NAMESPACE:
        errors.append("ontology registry ledger must declare the canonical global namespace")
    registries = ledger.get("registries")
    if not isinstance(registries, list) or not registries:
        errors.append("ontology registry ledger must contain registries")
        registries = []
    registry_ids: list[str] = []
    for index, entry in enumerate(registries):
        if not isinstance(entry, dict):
            errors.append(f"registry entry {index} must be a mapping")
            continue
        registry_id = str(entry.get("registry_id", index))
        registry_ids.append(registry_id)
        if entry.get("status") not in ALLOWED_REGISTRY_STATUSES:
            errors.append(f"{registry_id}: status is not fail-closed")
        if entry.get("human_gate") not in (True, "required"):
            errors.append(f"{registry_id}: human_gate must be required")
        if entry.get("status") == "not_verified" and entry.get("submission_evidence") is not None:
            errors.append(f"{registry_id}: unverified registry cannot carry submission evidence")
    if len(registry_ids) != len(set(registry_ids)):
        errors.append("ontology registry ids must be unique")

    prerequisites = set(plan.get("prerequisites", []))
    missing = sorted(REQUIRED_PREREQUISITES - prerequisites)
    errors.extend(f"ontology registry plan missing prerequisite: {item}" for item in missing)
    if plan.get("status_policy", {}).get("no_evidence_value") != "not_verified":
        errors.append("ontology registry plan must use not_verified for absent evidence")

    if migration.get("canonical_namespace") != CANONICAL_NAMESPACE:
        errors.append("namespace migration must point to the canonical global namespace")
    if migration.get("status") != "candidate":
        errors.append("namespace migration must remain candidate until human review")
    policy = migration.get("policy")
    if not isinstance(policy, dict) or policy.get("automatic_semantic_promotion") is not False:
        errors.append("namespace migration must prohibit automatic semantic promotion")
    if not isinstance(policy, dict) or policy.get("require_human_approval") is not True:
        errors.append("namespace migration must require human approval")
    if not migration.get("aliases"):
        errors.append("namespace migration must declare a legacy alias")

    signals = _quality_signals(graph)
    if signals["classes"] == 0 or signals["object_properties"] == 0:
        errors.append("ontology must contain classes and object properties")
    if signals["unlabelled_terms"]:
        errors.append("ontology terms must have labels")
    return {
        "ok": not errors,
        "registry_count": len(registry_ids),
        "quality": signals,
        "errors": errors,
    }


def validate(root: Path = ROOT) -> dict[str, Any]:
    """Validate the canonical ontology controls under *root*."""
    graph = Graph()
    graph.parse(root / "ontology/foi-o-nz.ttl", format="turtle")
    return validate_documents(
        _yaml(root, "registries/ontology-registry-ledger.yaml"),
        _yaml(root, "registries/ontology-registry-plan.yaml"),
        _yaml(root, "registries/ontology-namespace-migration.yaml"),
        graph,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = validate()
    rendered = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    if not result["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

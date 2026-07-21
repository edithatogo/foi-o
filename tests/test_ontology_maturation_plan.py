from __future__ import annotations

import json
import re
from pathlib import Path

from foi_o_nz.maturation import build_maturation_summary, write_maturation_summary
from foi_o_nz.validation import validate_json_schema

PROTOCOL = Path("docs/24-ontology-methods-protocol.md")
EVIDENCE_INVENTORY = Path("docs/24-ontology-methods-evidence-inventory.md")
CLAIMS_REGISTER = Path("docs/24-ontology-claims-register.md")
SOURCE_REGISTER = Path("docs/24-ontology-source-register.md")
TERMINOLOGY_CROSSWALK = Path("docs/24-ontology-terminology-crosswalk.md")
COVERAGE_MATRIX = Path("docs/24-schema-ontology-coverage-matrix.md")
RESULTS_DISCUSSION = Path("docs/25-ontology-results-discussion.md")
ASSET_INDEX = Path("docs/25-generated-asset-index.md")
VALIDATION_COVERAGE = Path("docs/25-validation-coverage-summary.md")
ASSET_MANIFEST = Path("examples/generated-asset-manifest.foi-o-publication.json")
ASSET_SCHEMA = Path("schemas/json/generated-asset-manifest.schema.json")
MATURATION_SUMMARY = Path("examples/maturation-summary.ontology-maturation.json")
MATURATION_SUMMARY_SCHEMA = Path("schemas/json/maturation-summary.schema.json")
EVIDENCE_GRAPH = Path("examples/graph-export.foi-o-evidence-network.json")
GRAPH_SCHEMA = Path("schemas/json/graph-export.schema.json")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _inline_code_refs(text: str) -> set[str]:
    return set(re.findall(r"`([^`]+)`", text))


def _assert_repo_path_exists(ref: str) -> None:
    if " " in ref or ref.startswith(("uv ", "FOIO_")):
        return
    if "://" in ref or ref.startswith("foio:"):
        return
    if "*" in ref:
        matches = list(Path().glob(ref))
        assert matches, ref
        return
    if "/" not in ref and not ref.endswith((".md", ".json", ".ttl", ".yaml", ".py")):
        return
    assert Path(ref).exists(), ref


def test_maturation_documents_exist_with_required_sections() -> None:
    documents = [
        PROTOCOL,
        EVIDENCE_INVENTORY,
        CLAIMS_REGISTER,
        SOURCE_REGISTER,
        TERMINOLOGY_CROSSWALK,
        COVERAGE_MATRIX,
        RESULTS_DISCUSSION,
        ASSET_INDEX,
        VALIDATION_COVERAGE,
    ]
    for path in documents:
        assert path.exists(), path
        assert _read(path).strip(), path

    protocol = _read(PROTOCOL)
    required_protocol_headings = [
        "## Core/profile boundary",
        "## Objectives",
        "## Materials",
        "## Ontology Development Method",
        "## Competency Questions",
        "## Empirical Evaluation Plan",
        "## Validation",
        "## Governance",
        "## Generated Assets",
        "## Limitations",
        "## Reproducibility",
        "## Planned Analysis",
    ]
    for heading in required_protocol_headings:
        assert heading in protocol

    results = _read(RESULTS_DISCUSSION)
    for heading in ["## Results", "## Validation Evidence", "## Discussion", "## Limitations"]:
        assert heading in results


def test_core_profile_boundary_keeps_global_claims_as_design_intent() -> None:
    combined = "\n".join(_read(path) for path in [Path("README.md"), PROTOCOL, CLAIMS_REGISTER])

    required_phrases = [
        "FOI-O is a global process-modelling method",
        "FOI-O is a global model that originated in NZ",
        "Australian adapters are candidate-only",
        "globally interchangeable",
    ]
    for phrase in required_phrases:
        assert phrase in combined

    forbidden_claims = [
        "validated profiles for other jurisdictions",
        "works across all countries",
        "global validation is complete",
    ]
    lowered = combined.lower()
    for phrase in forbidden_claims:
        assert phrase not in lowered


def test_new_maturation_docs_do_not_introduce_other_country_profiles() -> None:
    combined = "\n".join(
        _read(path)
        for path in [
            PROTOCOL,
            EVIDENCE_INVENTORY,
            CLAIMS_REGISTER,
            SOURCE_REGISTER,
            TERMINOLOGY_CROSSWALK,
            COVERAGE_MATRIX,
            RESULTS_DISCUSSION,
        ]
    )
    forbidden_country_profile_terms = [
        "Australia profile",
        "United States profile",
        "United Kingdom profile",
        "Canada profile",
        "Ireland profile",
    ]
    for term in forbidden_country_profile_terms:
        assert term not in combined


def test_competency_questions_and_empirical_task_sets_are_explicit() -> None:
    protocol = _read(PROTOCOL)

    for cq_id in [f"CQ{index}" for index in range(1, 11)]:
        assert cq_id in protocol

    required_questions = [
        "source state",
        "candidate process events",
        "autonomous machine certification",
        "public-holiday evidence",
        "source-version metadata",
        "public-data derivability",
    ]
    lowered = protocol.lower()
    for phrase in required_questions:
        assert phrase in lowered

    for task_name in [
        "State mapping",
        "Timeline extraction",
        "Outcome extraction",
        "Legal issue spotting",
        "Attachment profile",
    ]:
        assert task_name in protocol

    assert "annotation tasks" in lowered
    assert "not a completed gold standard" in lowered


def test_maturation_doc_path_references_resolve() -> None:
    docs = [
        PROTOCOL,
        EVIDENCE_INVENTORY,
        CLAIMS_REGISTER,
        SOURCE_REGISTER,
        TERMINOLOGY_CROSSWALK,
        COVERAGE_MATRIX,
        RESULTS_DISCUSSION,
        ASSET_INDEX,
        VALIDATION_COVERAGE,
    ]
    for doc in docs:
        for ref in _inline_code_refs(_read(doc)):
            _assert_repo_path_exists(ref)


def test_generated_asset_manifest_validates_and_paths_resolve() -> None:
    result = validate_json_schema(ASSET_MANIFEST, ASSET_SCHEMA)
    assert not result.errors, result.errors

    manifest = json.loads(ASSET_MANIFEST.read_text(encoding="utf-8"))
    asset_ids = {asset["asset_id"] for asset in manifest["assets"]}
    assert {
        "architecture-flow-mermaid",
        "architecture-flow-png",
        "state-machine-mermaid",
        "evidence-network-mermaid",
        "evidence-network-graph-json",
        "coverage-matrix",
        "claims-register",
        "validation-coverage-summary",
        "maturation-summary-json",
        "bpmn-process-model",
        "pnml-petri-net",
        "generated-state-machine-bpmn",
        "generated-state-machine-pnml",
        "generated-state-machine-mermaid",
        "process-model-conformance",
    } <= asset_ids

    for asset in manifest["assets"]:
        assert Path(asset["path"]).exists(), asset
        assert asset["caption"]
        assert asset["text_alternative"]
        assert asset["generation_command"]
        assert asset["provenance"]
        for source_input in asset["source_inputs"]:
            _assert_repo_path_exists(source_input)


def test_evidence_graph_validates_and_edges_reference_existing_nodes() -> None:
    result = validate_json_schema(EVIDENCE_GRAPH, GRAPH_SCHEMA)
    assert not result.errors, result.errors

    graph = json.loads(EVIDENCE_GRAPH.read_text(encoding="utf-8"))
    node_ids = {node["id"] for node in graph["nodes"]}

    assert graph["node_count"] == len(graph["nodes"])
    assert graph["edge_count"] == len(graph["edges"])
    assert "doc:protocol" in node_ids
    assert "gate:external" in node_ids

    for node in graph["nodes"]:
        path = node["properties"].get("path")
        if path:
            _assert_repo_path_exists(path)

    for edge in graph["edges"]:
        assert edge["source"] in node_ids, edge
        assert edge["target"] in node_ids, edge


def test_coverage_matrix_inventory_counts_match_repo() -> None:
    matrix = _read(COVERAGE_MATRIX)
    summary = build_maturation_summary()
    expected_counts = {
        "JSON Schema files": summary["inventory"]["json_schema_files"],
        "Example files": summary["inventory"]["example_files"],
        "Documentation files": summary["inventory"]["documentation_files"],
        "OWL ontology files": summary["inventory"]["owl_ontology_files"],
        "SHACL files": summary["inventory"]["shacl_files"],
        "SKOS vocabulary files": summary["inventory"]["skos_vocabulary_files"],
        "Mapping files": summary["inventory"]["mapping_files"],
        "Python test modules": summary["inventory"]["python_test_modules"],
    }
    for label, count in expected_counts.items():
        assert f"| {label} | {count} |" in matrix

    assert summary["inventory"]["example_files"] == sum(
        path.is_file() for path in Path("examples").rglob("*")
    )


def test_validation_coverage_summary_records_external_limits() -> None:
    summary = _read(VALIDATION_COVERAGE)
    normalized_summary = " ".join(summary.split())
    required_commands = [
        "uv run python scripts/validate_examples.py",
        "uv run foi-o-nz validate-repo",
        "uv run foi-o-nz schema-drift",
        "uv run pytest -q",
        "uv run ruff check src tests scripts",
        "pixi run mojo-test",
    ]
    for command in required_commands:
        assert command in summary

    for phrase in [
        "live FYI/archive pulls",
        "live legal-source refresh",
        "registry upload",
        "journal submission",
        "arXiv upload",
        "human legal/author approval",
    ]:
        assert phrase in normalized_summary


def test_maturation_summary_example_validates_and_matches_generator(tmp_path: Path) -> None:
    result = validate_json_schema(MATURATION_SUMMARY, MATURATION_SUMMARY_SCHEMA)
    assert not result.errors, result.errors

    fixture = json.loads(MATURATION_SUMMARY.read_text(encoding="utf-8"))
    generated = build_maturation_summary()

    assert fixture == generated
    assert fixture["ok"] is True
    assert fixture["missing_paths"] == []
    assert fixture["core_profile_boundary"]["validated_profile"] == "FOI-O NZ"
    assert fixture["core_profile_boundary"]["non_nz_validation_status"] == "design_intent_only"
    assert "human_reviewed_goldsets" in fixture["external_gates"]

    output = tmp_path / "maturation-summary.json"
    written = write_maturation_summary(output)
    assert written == generated
    assert json.loads(output.read_text(encoding="utf-8")) == generated

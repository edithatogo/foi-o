"""Repo-local evidence summaries for ontology maturation outputs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from foi_o_nz.io import write_json

MATURATION_SCHEMA_VERSION = "foi-o-nz.maturation-summary.v0.1.0"

INVENTORY_PATTERNS = {
    "json_schema_files": "schemas/json/*.schema.json",
    "example_files": "examples/**/*",
    "documentation_files": "docs/*.md",
    "owl_ontology_files": "ontology/*.ttl",
    "shacl_files": "shacl/*.ttl",
    "skos_vocabulary_files": "vocab/*.ttl",
    "mapping_files": "mappings/*",
    "python_test_modules": "tests/test_*.py",
}

MATURATION_DOCS = [
    "docs/24-ontology-methods-protocol.md",
    "docs/24-ontology-methods-evidence-inventory.md",
    "docs/24-ontology-claims-register.md",
    "docs/24-ontology-source-register.md",
    "docs/24-ontology-terminology-crosswalk.md",
    "docs/24-schema-ontology-coverage-matrix.md",
    "docs/25-generated-asset-index.md",
    "docs/25-ontology-results-discussion.md",
    "docs/25-validation-coverage-summary.md",
    "docs/31-process-models.md",
    "docs/32-process-mining-fixtures.md",
]

MATURATION_ASSETS = [
    "examples/generated-asset-manifest.foi-o-publication.json",
    "examples/graph-export.foi-o-evidence-network.json",
    "examples/empirical-taskset-manifest.nz-first.json",
    "examples/maturation-summary.ontology-maturation.json",
    "examples/process-model-conformance.ontology-maturation.json",
    "examples/process-mining-conformance.fixture.json",
    "examples/process-mining-events.fixture.jsonl",
    "examples/process-mining.fixture.ocel.json",
    "examples/process-mining.fixture.xes",
    "examples/publication-panel-review.ontology-maturation.json",
    "examples/reporting-checklist-adherence.ontology-maturation-miro.json",
    "schemas/json/generated-asset-manifest.schema.json",
    "schemas/json/empirical-taskset-manifest.schema.json",
    "schemas/json/maturation-summary.schema.json",
    "schemas/json/process-model-conformance.schema.json",
    "schemas/json/process-mining-conformance.schema.json",
    "schemas/json/process-mining-ocel.schema.json",
    "docs/assets/foi-o-evidence-network.mmd",
    "process_models/foi-o-nz-core.bpmn",
    "process_models/foi-o-nz-core.pnml",
    "process_models/foi-o-nz-state-machine.bpmn",
    "process_models/foi-o-nz-state-machine.pnml",
    "process_models/foi-o-nz-state-machine.mmd",
]

VALIDATION_COMMANDS = [
    "uv run python scripts/validate_examples.py",
    "uv run foi-o-nz validate-repo",
    "uv run foi-o-nz schema-drift",
    "uv run pytest -q tests/test_ontology_maturation_plan.py",
    "uv run pytest -q",
    "uv run ruff check src tests scripts",
    "uv run ruff format --check src tests scripts",
    "pixi run mojo-format-check",
    "pixi run mojo-test",
    "pixi run mojo-build",
]

EXTERNAL_GATES = [
    "live_fyi_archive_pulls",
    "live_legal_source_refresh",
    "human_reviewed_goldsets",
    "official_reporting_validation",
    "registry_publication",
    "journal_submission",
    "arxiv_upload",
    "human_legal_author_approval",
]


def build_maturation_summary(base_dir: Path = Path()) -> dict[str, Any]:
    """Build a deterministic summary of the global FOI-O maturation evidence surface."""
    inventory = {
        key: sum(path.is_file() for path in base_dir.glob(pattern))
        for key, pattern in INVENTORY_PATTERNS.items()
    }
    docs = [_path_status(base_dir, path) for path in MATURATION_DOCS]
    assets = [_path_status(base_dir, path) for path in MATURATION_ASSETS]
    missing = [item["path"] for item in [*docs, *assets] if not item["exists"]]
    return {
        "schema_version": MATURATION_SCHEMA_VERSION,
        "scope": "Global FOI-O maturation evidence originating in NZ with Australian jurisdiction iterations",
        "core_profile_boundary": {
            "core": "FOI-O reusable process-modelling method and conceptual frame",
            "validated_profile": "FOI-O NZ",
            "non_nz_validation_status": "design_intent_only",
        },
        "inventory": inventory,
        "maturation_documents": docs,
        "maturation_assets": assets,
        "validation_commands": VALIDATION_COMMANDS,
        "external_gates": EXTERNAL_GATES,
        "ok": not missing,
        "missing_paths": missing,
    }


def write_maturation_summary(output: Path, *, base_dir: Path = Path()) -> dict[str, Any]:
    """Write the maturation summary and return it."""
    summary = build_maturation_summary(base_dir=base_dir)
    write_json(output, summary)
    return summary


def _path_status(base_dir: Path, path: str) -> dict[str, Any]:
    resolved = base_dir / path
    return {
        "path": path,
        "exists": resolved.exists(),
        "kind": "directory" if resolved.is_dir() else "file",
    }

from __future__ import annotations

import json
from pathlib import Path

from foi_o_nz.validation import validate_json_schema

TARGET_REQUIREMENTS = Path("docs/26-journal-target-requirements.md")
MANUSCRIPT = Path("docs/27-submission-manuscript.md")
SUPPLEMENT = Path("docs/28-submission-supplement.md")
ARXIV_READINESS = Path("examples/arxiv-readiness.manuscript-planned.json")
ARXIV_SCHEMA = Path("schemas/json/arxiv-readiness.schema.json")


def test_submission_package_documents_exist() -> None:
    for path in [TARGET_REQUIREMENTS, MANUSCRIPT, SUPPLEMENT]:
        assert path.exists(), path
        assert path.read_text(encoding="utf-8").strip(), path


def test_manuscript_contains_required_submission_sections() -> None:
    text = MANUSCRIPT.read_text(encoding="utf-8")
    required_sections = [
        "# Introduction",
        "# Methods",
        "# Results",
        "# Discussion",
        "# Limitations",
        "# Conclusion",
        "# Data and Code Availability",
        "# Ethics and Legal Boundary",
        "# Author Contributions",
        "# Funding",
        "# Conflicts of Interest",
        "# References",
    ]
    for section in required_sections:
        assert section in text

    required_paths = [
        "schemas/json/core-event.schema.json",
        "shacl/foi-o-nz.shapes.ttl",
        "docs/22-semantic-alignment.md",
        "docs/26-journal-target-requirements.md",
        "docs/30-arxiv-readiness.md",
        "examples/arxiv-readiness.manuscript-planned.json",
    ]
    for path in required_paths:
        assert f"`{path}`" in text
        assert Path(path).exists(), path


def test_submission_package_preserves_human_gates() -> None:
    combined = "\n".join(
        path.read_text(encoding="utf-8") for path in [TARGET_REQUIREMENTS, MANUSCRIPT, SUPPLEMENT]
    ).lower()
    required_phrases = [
        "not legal advice",
        "not an official",
        "human approval",
        "human-only gates",
        "arxiv upload",
        "journal submission",
    ]
    for phrase in required_phrases:
        assert phrase in combined


def test_supplement_links_required_artifact_classes() -> None:
    text = SUPPLEMENT.read_text(encoding="utf-8")
    required_paths = [
        "schemas/json/",
        "examples/",
        "src/foi_o_nz/",
        "tests/",
        "ontology/foi-o-nz.ttl",
        "shacl/foi-o-nz.shapes.ttl",
        "vocab/*.skos.ttl",
        "mappings/*.yaml",
    ]
    for path in required_paths:
        assert f"`{path}`" in text

    assert "Cosmograph node data" in text
    assert "uv run pytest -q" in text


def test_arxiv_readiness_example_validates_for_submission_package() -> None:
    result = validate_json_schema(ARXIV_READINESS, ARXIV_SCHEMA)
    assert not result.errors, result.errors

    report = json.loads(ARXIV_READINESS.read_text(encoding="utf-8"))
    tools = {check["tool"]: check for check in report["tool_checks"]}
    assert tools["arxiv-latex-cleaner"]["requirement_level"] == "required"
    assert tools["latexpand"]["requirement_level"] == "conditional"
    assert tools["ALC-NG"]["requirement_level"] == "optional"
    assert report["human_gates"]

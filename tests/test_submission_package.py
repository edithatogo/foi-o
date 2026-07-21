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

    assert (
        'title: "FOI-O: A global, jurisdiction-profiled process/evidence and verification framework for Freedom of Information"'
        in text
    )
    compact_text = " ".join(text.split())
    assert "FOI-O NZ is the only implemented and validated jurisdictional profile" in compact_text
    assert "What the current package proves and does not prove" in text
    assert "Ontology, Process Model, and Interchange Artefacts" in text
    assert "finished global FOI platform" not in text
    assert "global resource for FOI processes" not in text
    assert "large gold-set performance" not in text

    forbidden_public_text = [
        "schemas/json/core-event.schema.json",
        "shacl/foi-o-nz.shapes.ttl",
        "docs/22-semantic-alignment.md",
        "docs/26-journal-target-requirements.md",
        "docs/30-arxiv-readiness.md",
        "examples/arxiv-readiness.manuscript-planned.json",
    ]
    for path in forbidden_public_text:
        assert f"`{path}`" not in text

    assert "\\usepackage{flowchart}" in text
    assert "\\begin{tikzpicture}" in text
    assert "docs/assets/foi-o-process-architecture.png" not in text
    assert "```mermaid" not in text
    assert "1. Official Information Act 1982." in text


def test_submission_package_preserves_human_gates() -> None:
    combined = "\n".join(
        path.read_text(encoding="utf-8") for path in [TARGET_REQUIREMENTS, MANUSCRIPT, SUPPLEMENT]
    ).lower()
    required_phrases = [
        "not legal advice",
        "not an official",
        "human approval",
        "human-only gates",
        "operational use",
        "foi request handling",
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
        assert f"`{path}`" in text or f"\\path{{{path}}}" in text

    assert "Cosmograph node data" in text
    assert "Process models" in text
    assert "Process-mining XES fixture" in text
    assert "Empirical task-set manifest" in text
    assert "uv run pytest -q" in text


def test_supplement_has_page_breaks_and_captioned_wrapped_tables() -> None:
    text = SUPPLEMENT.read_text(encoding="utf-8")
    for section in [
        "## S2. Repository Artefact Inventory",
        "## S3. Validation Commands",
        "## S4. Ontology and Standards Alignment",
        "## S5. Human Certification Boundary",
        "## S6. Generated Asset Plan",
        "## S7. arXiv Source-Package Readiness",
        "## S8. External Gates",
        "## S9. Reproducibility Notes",
    ]:
        assert f"\\clearpage\n\n{section}" in text

    assert "\\begin{longtable}" in text
    assert "| Artefact class |" not in text
    assert "| Asset | Source input |" not in text
    assert "Repository artefact inventory for the FOI-O NZ supplement. Abbreviations:" in text
    assert "Generated asset plan for the FOI-O NZ supplement. Abbreviations:" in text
    assert "BPMN, Business Process Model and Notation" in text
    assert "OCEL, Object-Centric Event Log" in text


def test_arxiv_readiness_example_validates_for_submission_package() -> None:
    result = validate_json_schema(ARXIV_READINESS, ARXIV_SCHEMA)
    assert not result.errors, result.errors

    report = json.loads(ARXIV_READINESS.read_text(encoding="utf-8"))
    tools = {check["tool"]: check for check in report["tool_checks"]}
    assert tools["arxiv-latex-cleaner"]["requirement_level"] == "required"
    assert tools["latexpand"]["requirement_level"] == "conditional"
    assert tools["ALC-NG"]["requirement_level"] == "optional"
    assert report["human_gates"]

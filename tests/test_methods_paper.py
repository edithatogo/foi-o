from __future__ import annotations

from pathlib import Path


METHODS_PAPER = Path("docs/23-methods-paper.md")


def _paper_text() -> str:
    return METHODS_PAPER.read_text(encoding="utf-8")


def test_methods_paper_exists_with_required_sections() -> None:
    assert METHODS_PAPER.exists()
    text = _paper_text()
    required_headings = [
        "# An agent-facing process ontology for New Zealand Official Information Act administration",
        "## Abstract",
        "## Motivation",
        "## Architecture",
        "## Data Model",
        "## Human Certification Boundary",
        "## Evaluation and Validation",
        "## Limitations",
        "## Reproducibility",
    ]
    for heading in required_headings:
        assert heading in text


def test_methods_paper_cites_existing_repo_evidence() -> None:
    text = _paper_text()
    required_paths = [
        Path("docs/11-implementation-status.md"),
        Path("docs/19-release-readiness-evidence.md"),
        Path("docs/22-semantic-alignment.md"),
        Path("docs/23-release-package.md"),
        Path("examples/release-checklist.v0.9.0.json"),
        Path("examples/repository-release-metadata.v0.9.0.json"),
        Path("schemas/json/core-event.schema.json"),
        Path("shacl/foi-o-nz.shapes.ttl"),
        Path("tests/test_publication_metadata.py"),
    ]
    for path in required_paths:
        assert path.exists(), path
        assert f"`{path}`" in text

    required_commands = [
        "uv run pytest -q",
        "uv run python scripts/validate_examples.py",
        "uv run foi-o-nz validate-repo",
        "uv run foi-o-nz schema-drift",
    ]
    for command in required_commands:
        assert f"`{command}`" in text


def test_methods_paper_avoids_official_or_legal_overclaiming() -> None:
    text = _paper_text().lower()
    required_boundary_phrases = [
        "not legal advice",
        "not an official government publication",
        "authorised humans certify",
        "process-support-only",
    ]
    for phrase in required_boundary_phrases:
        assert phrase in text

    forbidden_phrases = [
        "autonomously decides",
        "certifies release decisions",
        "official ombudsman guidance implementation",
        "official psc reporting system",
    ]
    for phrase in forbidden_phrases:
        assert phrase not in text

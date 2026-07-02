from __future__ import annotations

import json
from pathlib import Path

from foi_o_nz.validation import validate_json_schema

PANEL_DOC = Path("docs/29-publication-quality-panel.md")
SCORECARD_EXAMPLE = Path("examples/publication-panel-scorecard.editor.methods-paper.json")
REVIEW_EXAMPLE = Path("examples/publication-panel-review.methods-paper.json")
CHECKLIST_SOURCE_EXAMPLE = Path("examples/reporting-checklist-source.miro.json")
CHECKLIST_ADHERENCE_EXAMPLE = Path("examples/reporting-checklist-adherence.methods-paper-miro.json")


def test_publication_quality_panel_defines_all_required_agents() -> None:
    text = PANEL_DOC.read_text(encoding="utf-8")
    required_agent_ids = [
        "editor",
        "peer_reviewer",
        "copy_editor",
        "publisher",
        "ontology_expert",
        "public_admin_expert",
        "legal_informatics_expert",
        "economist",
        "operations_researcher",
        "reproducibility_expert",
        "visualization_expert",
        "red_team",
        "devils_advocate",
    ]
    for agent_id in required_agent_ids:
        assert f"`{agent_id}`" in text

    assert "greater than 95/100" in text
    assert "Cosmograph-compatible" in text


def test_panel_review_example_scores_every_required_agent() -> None:
    review = json.loads(REVIEW_EXAMPLE.read_text(encoding="utf-8"))
    expected_agents = {
        "editor",
        "peer_reviewer",
        "copy_editor",
        "publisher",
        "ontology_expert",
        "public_admin_expert",
        "legal_informatics_expert",
        "economist",
        "operations_researcher",
        "reproducibility_expert",
        "visualization_expert",
        "red_team",
        "devils_advocate",
    }
    actual_agents = {score["agent_id"] for score in review["scores"]}

    assert actual_agents == expected_agents
    assert review["overall_passed"] is False
    assert all(score["score"] <= 95 for score in review["scores"])
    assert all(score["passed"] is False for score in review["scores"])


def test_publication_panel_examples_validate_against_schemas() -> None:
    examples_and_schemas = [
        (SCORECARD_EXAMPLE, Path("schemas/json/publication-panel-scorecard.schema.json")),
        (REVIEW_EXAMPLE, Path("schemas/json/publication-panel-review.schema.json")),
        (
            CHECKLIST_SOURCE_EXAMPLE,
            Path("schemas/json/reporting-checklist-source.schema.json"),
        ),
        (
            CHECKLIST_ADHERENCE_EXAMPLE,
            Path("schemas/json/reporting-checklist-adherence.schema.json"),
        ),
    ]

    for example_path, schema_path in examples_and_schemas:
        assert example_path.exists(), example_path
        assert schema_path.exists(), schema_path
        result = validate_json_schema(example_path, schema_path)
        assert not result.errors, result.errors


def test_miro_adherence_report_links_existing_evidence_paths() -> None:
    adherence = json.loads(CHECKLIST_ADHERENCE_EXAMPLE.read_text(encoding="utf-8"))
    for item in adherence["items"]:
        if item["applicability"] != "required":
            continue
        assert item["evidence_paths"], item
        for evidence_path in item["evidence_paths"]:
            assert Path(evidence_path).exists(), evidence_path

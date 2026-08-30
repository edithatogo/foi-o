"""Test suite for autonomous agent-triangulated Medallion pipeline."""

from __future__ import annotations

import json
from pathlib import Path

from foi_o_nz.agent_triangulated_medallion import (
    AgentStanceProposal,
    MedallionRecord,
    run_agent_triangulated_medallion_pipeline,
    triangulate_record,
)


def test_agent_triangulation_consensus_success() -> None:
    """Verify that multi-agent consensus accepts valid event into Silver layer."""
    record = MedallionRecord(
        record_id="rec-au-nsw-001",
        jurisdiction="AU-NSW",
        regime="GIPA",
        raw_text="Notice of decision: All requested documents released in full.",
    )
    proposals = [
        AgentStanceProposal(
            agent_id="agent-1",
            model_version="v1",
            stance="supports",
            claimed_state="ReleasedInFull",
            confidence=0.95,
        ),
        AgentStanceProposal(
            agent_id="agent-2",
            model_version="v1",
            stance="supports",
            claimed_state="ReleasedInFull",
            confidence=0.92,
        ),
    ]

    event = triangulate_record(record, proposals, min_supporting=2)
    assert event is not None
    assert event.lifecycle_state_after == "ReleasedInFull"
    assert event.consensus_score == 1.0
    assert event.triangulation_status == "consensus_accepted"
    assert len(event.supporting_agents) == 2


def test_agent_triangulation_disagreement_handled() -> None:
    """Verify that split agent opinions with insufficient consensus are guarded."""
    record = MedallionRecord(
        record_id="rec-au-vic-002",
        jurisdiction="AU-VIC",
        regime="FOI",
        raw_text="Ambiguous letter regarding partial records and searching.",
    )
    proposals = [
        AgentStanceProposal(
            agent_id="agent-1",
            model_version="v1",
            stance="supports",
            claimed_state="PartiallyReleased",
            confidence=0.60,
        ),
        AgentStanceProposal(
            agent_id="agent-2",
            model_version="v1",
            stance="supports",
            claimed_state="Searching",
            confidence=0.55,
        ),
    ]

    # Requiring min_supporting=2 when opinions are split 1/1
    event = triangulate_record(record, proposals, min_supporting=2)
    assert event is None


def test_end_to_end_medallion_pipeline_execution(tmp_path: Path) -> None:
    """Test full Bronze -> Silver -> Gold medallion generation across jurisdictions."""
    records = [
        MedallionRecord(
            record_id="rec-nz-001",
            jurisdiction="NZ",
            regime="OIA",
            raw_text="Request acknowledged and searching begun.",
        ),
        MedallionRecord(
            record_id="rec-au-cth-001",
            jurisdiction="AU-CTH",
            regime="FOI",
            raw_text="Full grant of access provided in full.",
        ),
        MedallionRecord(
            record_id="rec-au-qld-001",
            jurisdiction="AU-QLD",
            regime="RTI",
            raw_text="Formal notice of refusal issued.",
        ),
    ]

    summary = run_agent_triangulated_medallion_pipeline(
        bronze_records=records,
        output_dir=tmp_path,
        min_supporting_agents=2,
    )

    assert summary.bronze_record_count == 3
    assert summary.silver_event_count == 3
    assert summary.gold_model_count >= 10  # NZ + 9 AU jurisdictions
    assert summary.agent_consensus_rate == 1.0

    # Verify Bronze artifacts
    bronze_file = tmp_path / "bronze" / "bronze_records.jsonl"
    assert bronze_file.exists()

    # Verify Silver artifacts
    silver_file = tmp_path / "silver" / "silver_events.jsonl"
    assert silver_file.exists()
    lines = silver_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 3

    # Verify Gold artifacts for NZ and AU jurisdictions
    for jur in ("nz", "au-cth", "au-qld", "au-nsw", "au-vic"):
        jur_dir = tmp_path / "gold" / jur
        assert jur_dir.exists()
        assert (jur_dir / "process_model.pnml").exists()
        assert (jur_dir / "process_model.bpmn").exists()
        assert (jur_dir / "process_model.mmd").exists()

    # Verify pipeline manifest
    manifest_file = tmp_path / "medallion_pipeline_manifest.json"
    assert manifest_file.exists()
    manifest_data = json.loads(manifest_file.read_text(encoding="utf-8"))
    assert manifest_data["schema_version"] == "foi-o.agent-triangulated-medallion-pipeline.v0.1.0"
    assert manifest_data["bronze_count"] == 3


def test_cli_run_medallion_invocation(tmp_path: Path) -> None:
    """Test CLI run-medallion command execution."""
    from typer.testing import CliRunner

    from foi_o_nz.cli import app

    runner = CliRunner()
    result = runner.invoke(app, ["run-medallion", "--output-dir", str(tmp_path)])
    assert result.exit_code == 0
    assert (tmp_path / "medallion_pipeline_manifest.json").exists()
    assert (tmp_path / "gold" / "nz" / "process_model.pnml").exists()

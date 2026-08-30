"""Test suite for autonomous agent-triangulated Medallion pipeline."""

from __future__ import annotations

import json
from pathlib import Path

from foi_o_nz.agent_triangulated_medallion import (
    AgentStanceProposal,
    MedallionRecord,
    compute_sla_and_bottlenecks,
    compute_trace_variants,
    compute_transition_matrices,
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
        received_date="2026-04-01",
        decision_date="2026-04-18",
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

    result = triangulate_record(record, proposals, min_supporting=2)
    assert result is not None
    request_entity, events = result
    assert request_entity.final_state == "ReleasedInFull"
    assert request_entity.sla_compliant is True
    assert request_entity.cycle_time_days == 17
    assert len(events) == 2
    assert events[0].event_type == "RequestReceived"
    assert events[1].lifecycle_state_after == "ReleasedInFull"
    assert events[1].triangulation_status == "consensus_accepted"


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

    result = triangulate_record(record, proposals, min_supporting=2)
    assert result is None


def test_transition_and_trace_analytics() -> None:
    """Verify Markov transition matrix and trace variant computation."""
    record_a = MedallionRecord(
        record_id="rec-a",
        jurisdiction="AU-NSW",
        regime="GIPA",
        raw_text="Full release granted.",
        received_date="2026-01-01",
        decision_date="2026-01-15",
    )
    record_b = MedallionRecord(
        record_id="rec-b",
        jurisdiction="AU-NSW",
        regime="GIPA",
        raw_text="Partial release redacted under s14 Table.",
        received_date="2026-02-01",
        decision_date="2026-02-28",
    )

    props_a = [
        AgentStanceProposal(
            agent_id="a1",
            model_version="v1",
            stance="supports",
            claimed_state="ReleasedInFull",
            confidence=0.9,
        ),
        AgentStanceProposal(
            agent_id="a2",
            model_version="v1",
            stance="supports",
            claimed_state="ReleasedInFull",
            confidence=0.9,
        ),
    ]
    props_b = [
        AgentStanceProposal(
            agent_id="b1",
            model_version="v1",
            stance="supports",
            claimed_state="ReleasedInPart",
            confidence=0.9,
        ),
        AgentStanceProposal(
            agent_id="b2",
            model_version="v1",
            stance="supports",
            claimed_state="ReleasedInPart",
            confidence=0.9,
        ),
    ]

    res_a = triangulate_record(record_a, props_a)
    res_b = triangulate_record(record_b, props_b)
    assert res_a is not None and res_b is not None

    reqs = [res_a[0], res_b[0]]
    evs = res_a[1] + res_b[1]

    matrices = compute_transition_matrices(evs)
    assert "transition_counts_global" in matrices
    assert "transition_probabilities_global" in matrices

    sla = compute_sla_and_bottlenecks(reqs)
    assert sla["overall_request_count"] == 2
    assert "AU-NSW" in sla["jurisdiction_metrics"]

    traces = compute_trace_variants(evs)
    assert traces["total_traces"] == 2
    assert traces["unique_variants"] >= 1


def test_end_to_end_medallion_pipeline_execution(tmp_path: Path) -> None:
    """Test full Bronze -> Silver -> Gold medallion generation across jurisdictions."""
    records = [
        MedallionRecord(
            record_id="rec-nz-001",
            jurisdiction="NZ",
            regime="OIA",
            raw_text="Request acknowledged and searching begun. Access granted in full.",
            received_date="2026-02-01",
            decision_date="2026-02-18",
        ),
        MedallionRecord(
            record_id="rec-au-cth-001",
            jurisdiction="AU-CTH",
            regime="FOI",
            raw_text="Full grant of access provided in full.",
            received_date="2026-03-01",
            decision_date="2026-03-20",
        ),
        MedallionRecord(
            record_id="rec-au-qld-001",
            jurisdiction="AU-QLD",
            regime="RTI",
            raw_text="Formal notice of refusal issued under schedule 3.",
            received_date="2026-06-01",
            decision_date="2026-06-15",
        ),
    ]

    summary = run_agent_triangulated_medallion_pipeline(
        bronze_records=records,
        output_dir=tmp_path,
        min_supporting_agents=2,
        export_duckdb=True,
    )

    assert summary.bronze_record_count == 3
    assert summary.silver_request_count == 3
    assert summary.silver_event_count >= 3
    assert summary.gold_model_count >= 10  # NZ + 9 AU jurisdictions
    assert summary.agent_consensus_rate == 1.0

    # Verify Bronze artifacts
    assert (tmp_path / "bronze" / "bronze_records.jsonl").exists()
    assert (tmp_path / "bronze" / "bronze_manifest.json").exists()

    # Verify Silver artifacts
    silver_reqs = tmp_path / "silver" / "silver_requests.jsonl"
    silver_evs = tmp_path / "silver" / "silver_events.jsonl"
    assert silver_reqs.exists()
    assert silver_evs.exists()

    # Verify Gold artifacts for NZ and AU jurisdictions
    for jur in ("nz", "au-cth", "au-qld", "au-nsw", "au-vic", "au-act", "au-nt"):
        jur_dir = tmp_path / "gold" / jur
        assert jur_dir.exists()
        assert (jur_dir / "process_model.pnml").exists()
        assert (jur_dir / "process_model.bpmn").exists()
        assert (jur_dir / "process_model.mmd").exists()

    # Verify Analytics artifacts
    analytics_dir = tmp_path / "analytics"
    assert (analytics_dir / "transition_matrices.json").exists()
    assert (analytics_dir / "sla_compliance_report.json").exists()
    assert (analytics_dir / "trace_variant_analysis.json").exists()

    # Verify pipeline manifest
    manifest_file = tmp_path / "medallion_pipeline_manifest.json"
    assert manifest_file.exists()
    manifest_data = json.loads(manifest_file.read_text(encoding="utf-8"))
    assert manifest_data["schema_version"] == "foi-o.agent-triangulated-medallion-pipeline.v0.2.0"
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
    assert (tmp_path / "analytics" / "transition_matrices.json").exists()

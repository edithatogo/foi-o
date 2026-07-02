from __future__ import annotations

import json
from pathlib import Path

from foi_o_nz.agent_policy import build_agent_action
from foi_o_nz.cas import build_cas_manifest, materialise_jsonl_cas, read_cas_manifest
from foi_o_nz.goldset import tasks_from_chunks, write_goldset_tasks
from foi_o_nz.io import write_jsonl
from foi_o_nz.lineage import build_lineage_graph, lineage_to_dot, write_lineage_graph
from foi_o_nz.replay import replay_guardrails, write_guardrail_replay
from foi_o_nz.traces import build_artifact_trace_spans, write_trace_spans


def test_cas_manifest_hashes_files(tmp_path: Path) -> None:
    artifact = tmp_path / "artifact.json"
    artifact.write_text('{"ok": true}\n', encoding="utf-8")
    manifest = build_cas_manifest([artifact], base_dir=tmp_path)
    assert manifest.entry_count == 1
    assert manifest.entries[0].path == "artifact.json"
    assert manifest.root_digest


def test_materialise_jsonl_cas_writes_index(tmp_path: Path) -> None:
    source = tmp_path / "records.jsonl"
    outdir = tmp_path / "cas"
    index = tmp_path / "index.jsonl"
    write_jsonl(source, [{"request_id": "1", "title": "Example"}])
    result = materialise_jsonl_cas(source, outdir, index)
    assert result["record_count"] == 1
    assert index.exists()
    index_record = json.loads(index.read_text(encoding="utf-8").splitlines()[0])
    assert index_record["uri"].startswith("sha256:")
    assert Path(index_record["path"]).exists()


def test_read_cas_manifest_roundtrip(tmp_path: Path) -> None:
    artifact = tmp_path / "artifact.json"
    output = tmp_path / "cas.json"
    artifact.write_text('{"ok": true}\n', encoding="utf-8")
    manifest = build_cas_manifest([artifact], base_dir=tmp_path)
    output.write_text(manifest.model_dump_json(), encoding="utf-8")
    parsed = read_cas_manifest(output)
    assert parsed.root_digest == manifest.root_digest


def test_lineage_graph_and_dot(tmp_path: Path) -> None:
    raw = tmp_path / "raw-manifest.jsonl"
    derived = tmp_path / "events.jsonl"
    raw.write_text('{"request_id": "1"}\n', encoding="utf-8")
    derived.write_text('{"event_id": "e1"}\n', encoding="utf-8")
    graph = build_lineage_graph([raw, derived], base_dir=tmp_path)
    assert graph.nodes
    assert graph.edges
    dot = lineage_to_dot(graph)
    assert "digraph" in dot


def test_write_lineage_graph_with_dot(tmp_path: Path) -> None:
    artifact = tmp_path / "summary.json"
    output = tmp_path / "lineage.json"
    dot = tmp_path / "lineage.dot"
    artifact.write_text('{"ok": true}\n', encoding="utf-8")
    result = write_lineage_graph([artifact], output, base_dir=tmp_path, dot_output=dot)
    assert result["node_count"] == 1
    assert output.exists()
    assert dot.exists()


def test_trace_spans_are_deterministic_shape(tmp_path: Path) -> None:
    artifact = tmp_path / "artifact.json"
    artifact.write_text('{"ok": true}\n', encoding="utf-8")
    spans = build_artifact_trace_spans([artifact], run_name="test-run")
    assert len(spans) == 2
    assert spans[0].parent_span_id is None
    assert spans[1].parent_span_id == spans[0].span_id


def test_write_trace_spans(tmp_path: Path) -> None:
    artifact = tmp_path / "artifact.json"
    output = tmp_path / "trace.jsonl"
    artifact.write_text('{"ok": true}\n', encoding="utf-8")
    result = write_trace_spans([artifact], output, run_name="test-run")
    assert result["span_count"] == 2
    assert output.read_text(encoding="utf-8").count("\n") == 2


def test_goldset_tasks_from_chunks() -> None:
    tasks = tasks_from_chunks(
        [{"chunk_id": "c1", "request_id": "1", "text": "Contact test@example.org"}],
        [{"source_id": "c1", "risk_level": "high", "hits": [{"category": "personal_information"}]}],
    )
    assert len(tasks) == 1
    assert tasks[0].priority == "high"
    assert tasks[0].prefilled_label == "privacy"


def test_write_goldset_tasks(tmp_path: Path) -> None:
    chunks = tmp_path / "chunks.jsonl"
    output = tmp_path / "tasks.jsonl"
    summary = tmp_path / "summary.json"
    write_jsonl(chunks, [{"chunk_id": "c1", "request_id": "1", "text": "Example chunk."}])
    result = write_goldset_tasks(chunks, output, summary_output=summary)
    assert result["task_count"] == 1
    assert summary.exists()


def test_replay_guardrails_accepts_policy_action(tmp_path: Path) -> None:
    actions = tmp_path / "actions.jsonl"
    action = build_agent_action("search_chunks")
    write_jsonl(actions, [action.model_dump(mode="json", exclude_none=True)])
    report = replay_guardrails(actions_jsonl=actions)
    assert report.ok
    assert report.action_count == 1


def test_replay_guardrails_flags_machine_certified_event(tmp_path: Path) -> None:
    events = tmp_path / "events.jsonl"
    write_jsonl(
        events,
        [
            {
                "event_id": "foio-nz:event:bad",
                "event_type": "ReleaseMade",
                "assertion_status": "certified",
                "machine_generated": True,
                "requires_human_certification": True,
                "human_certification": {"certified": False},
            }
        ],
    )
    report = replay_guardrails(events_jsonl=events)
    assert not report.ok
    assert any(
        finding.code == "certified_assertion_without_positive_human_certification"
        for finding in report.findings
    )


def test_write_guardrail_replay(tmp_path: Path) -> None:
    output = tmp_path / "replay.json"
    result = write_guardrail_replay(output)
    assert result["ok"] is True
    assert output.exists()

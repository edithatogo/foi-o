from __future__ import annotations

import json
from pathlib import Path

from foi_o_nz.annotation import write_annotation_tasks
from foi_o_nz.attestation import write_attestation
from foi_o_nz.goldset import write_goldset_sample, write_request_goldset_tasks
from foi_o_nz.graph_export import build_graph, graph_to_mermaid, write_graph_export
from foi_o_nz.io import write_jsonl
from foi_o_nz.process_advice import build_process_advice, write_process_advice
from foi_o_nz.review_queue import build_review_tasks, write_review_queue


def _write_fixture_streams(tmp_path: Path) -> dict[str, Path]:
    requests = tmp_path / "requests.jsonl"
    events = tmp_path / "events.jsonl"
    risks = tmp_path / "risks.jsonl"
    redactions = tmp_path / "redactions.jsonl"
    chunks = tmp_path / "chunks.jsonl"
    write_jsonl(
        requests,
        [
            {
                "schema_version": "foi-o-nz.request-profile.v0.1.0",
                "source": "fixture",
                "request_id": "12345",
                "title": "Health data request",
                "authority": "Example Ministry",
                "source_state": "waiting_response",
                "normalised_state": "AwaitingResponse",
                "state_mapping": {"method": "rule", "confidence": 0.75},
            }
        ],
    )
    write_jsonl(
        events,
        [
            {
                "event_id": "foio-nz:event:1",
                "event_type": "RequestObserved",
                "request_ref": {"source_request_id": "12345"},
                "assertion_status": "observed",
                "requires_human_certification": False,
            },
            {
                "event_id": "foio-nz:event:2",
                "event_type": "ReleaseMade",
                "request_ref": {"source_request_id": "12345"},
                "assertion_status": "inferred",
                "requires_human_certification": True,
                "human_certification": {"certified": False},
            },
        ],
    )
    write_jsonl(
        risks,
        [
            {
                "assessment_id": "foio-nz:risk:c1",
                "source_record_type": "chunk",
                "source_id": "c1",
                "request_id": "12345",
                "risk_level": "high",
                "review_required": True,
                "hits": [{"category": "health_information", "pattern_id": "nhi", "count": 1}],
            }
        ],
    )
    write_jsonl(
        redactions,
        [
            {
                "candidate_id": "foio-nz:redaction-candidate:1",
                "source_id": "c1",
                "request_id": "12345",
                "span_type": "email_address",
                "masked_preview": "t***@e***",
                "confidence": 0.96,
                "decision_status": "candidate_only_not_redacted",
            }
        ],
    )
    write_jsonl(
        chunks,
        [
            {
                "chunk_id": "c1",
                "source_record_type": "request",
                "source_id": "12345",
                "request_id": "12345",
                "text": "Health data request about email test@example.org",
                "metadata": {},
            }
        ],
    )
    return {
        "requests": requests,
        "events": events,
        "risks": risks,
        "redactions": redactions,
        "chunks": chunks,
    }


def test_review_queue_builds_risk_redaction_and_certification_tasks(tmp_path: Path) -> None:
    paths = _write_fixture_streams(tmp_path)
    tasks = build_review_tasks(
        risks_jsonl=paths["risks"],
        redaction_candidates_jsonl=paths["redactions"],
        events_jsonl=paths["events"],
    )
    assert {task.task_type for task in tasks} == {
        "risk_review",
        "redaction_candidate_review",
        "certification_boundary_review",
    }
    assert all("certify_release" in task.agent_boundary["machine_must_not"] for task in tasks)
    output = tmp_path / "review.jsonl"
    result = write_review_queue(
        output,
        risks_jsonl=paths["risks"],
        redaction_candidates_jsonl=paths["redactions"],
        events_jsonl=paths["events"],
    )
    assert result["task_count"] == 3
    assert output.read_text(encoding="utf-8")


def test_process_advice_routes_to_safe_actions_and_reviews(tmp_path: Path) -> None:
    paths = _write_fixture_streams(tmp_path)
    queue = tmp_path / "review.jsonl"
    write_review_queue(
        queue,
        risks_jsonl=paths["risks"],
        redaction_candidates_jsonl=paths["redactions"],
        events_jsonl=paths["events"],
    )
    report = build_process_advice(
        request_id="12345",
        requests_jsonl=paths["requests"],
        events_jsonl=paths["events"],
        review_queue_jsonl=queue,
    )
    assert report["legal_effect"] == "none_preparatory_only"
    assert any(item["action"] == "calculate_deadline" for item in report["next_safe_actions"])
    assert any(
        item["review_type"] == "certification_boundary" for item in report["required_human_reviews"]
    )
    output = tmp_path / "advice.json"
    written = write_process_advice(
        output, request_id="12345", requests_jsonl=paths["requests"], events_jsonl=paths["events"]
    )
    assert written["request_id"] == "12345"
    assert (
        json.loads(output.read_text(encoding="utf-8"))["schema_version"]
        == "foi-o-nz.process-advice.v0.1.0"
    )


def test_graph_export_builds_json_and_mermaid(tmp_path: Path) -> None:
    paths = _write_fixture_streams(tmp_path)
    graph = build_graph(
        requests_jsonl=paths["requests"],
        events_jsonl=paths["events"],
        chunks_jsonl=paths["chunks"],
        risks_jsonl=paths["risks"],
    )
    assert graph["node_count"] >= 4
    assert any(edge["label"] == "has_event" for edge in graph["edges"])
    mermaid = graph_to_mermaid(graph)
    assert mermaid.startswith("flowchart LR")
    output = tmp_path / "graph.mmd"
    result = write_graph_export(
        output, requests_jsonl=paths["requests"], events_jsonl=paths["events"], fmt="mermaid"
    )
    assert result["format"] == "mermaid"
    assert output.read_text(encoding="utf-8").startswith("flowchart LR")


def test_attestation_records_subject_digest(tmp_path: Path) -> None:
    artefact = tmp_path / "artifact.json"
    artefact.write_text('{"ok": true}\n', encoding="utf-8")
    output = tmp_path / "attestation.json"
    result = write_attestation([artefact], output, builder_id="test.builder", invocation_id="run-1")
    data = json.loads(output.read_text(encoding="utf-8"))
    assert result["subject_count"] == 1
    assert data["_type"] == "https://in-toto.io/Statement/v1"
    assert len(data["subject"][0]["digest"]["sha256"]) == 64
    assert data["x_foio_nz"]["signed"] is False


def test_goldset_sampling_is_deterministic_and_bounded(tmp_path: Path) -> None:
    records = tmp_path / "requests.jsonl"
    output = tmp_path / "gold.jsonl"
    manifest = tmp_path / "gold.manifest.json"
    write_jsonl(
        records,
        [
            {"request_id": "1", "authority": "A", "normalised_state": "AwaitingResponse"},
            {"request_id": "2", "authority": "A", "normalised_state": "AwaitingResponse"},
            {"request_id": "3", "authority": "B", "normalised_state": "Closed"},
        ],
    )
    first = write_goldset_sample(
        records, output, manifest, kind="request", limit=2, per_stratum=1, seed="seed"
    )
    lines_first = output.read_text(encoding="utf-8")
    second = write_goldset_sample(
        records, output, manifest, kind="request", limit=2, per_stratum=1, seed="seed"
    )
    assert first["selected_count"] == 2
    assert second["selected_count"] == 2
    assert output.read_text(encoding="utf-8") == lines_first


def test_goldset_sampling_supports_100_request_workflow(tmp_path: Path) -> None:
    records = tmp_path / "requests.jsonl"
    output = tmp_path / "gold.jsonl"
    manifest = tmp_path / "gold.manifest.json"
    write_jsonl(
        records,
        [
            {
                "request_id": str(index),
                "authority": f"Authority {index % 5}",
                "source_state": "successful" if index % 2 else "waiting_response",
                "normalised_state": "ReleasedInFull" if index % 2 else "Received",
            }
            for index in range(150)
        ],
    )

    result = write_goldset_sample(
        records,
        output,
        manifest,
        kind="request",
        limit=100,
        per_stratum=100,
        seed="track-2-fixture",
    )

    assert result["candidate_count"] == 150
    assert result["selected_count"] == 100
    sampled = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
    assert len(sampled) == 100
    assert all(item["record_kind"] == "request" for item in sampled)


def test_annotation_tasks_can_export_label_studio(tmp_path: Path) -> None:
    paths = _write_fixture_streams(tmp_path)
    queue = tmp_path / "review.jsonl"
    annotations = tmp_path / "annotations.json"
    write_review_queue(queue, risks_jsonl=paths["risks"])
    result = write_annotation_tasks(queue, annotations, fmt="label-studio")
    data = json.loads(annotations.read_text(encoding="utf-8"))
    assert result["annotation_count"] == 1
    assert data[0]["data"]["request_id"] == "12345"
    assert "agent_boundary" in data[0]["meta"]


def test_request_goldset_tasks_include_state_provenance_and_event_hints(
    tmp_path: Path,
) -> None:
    requests = tmp_path / "requests.jsonl"
    events = tmp_path / "events.jsonl"
    output = tmp_path / "request-tasks.jsonl"
    summary = tmp_path / "request-tasks.summary.json"
    write_jsonl(
        requests,
        [
            {
                "request_id": "123",
                "title": "Example request",
                "authority": "Example Ministry",
                "source_state": "successful",
                "normalised_state": "ReleasedInFull",
                "state_mapping": {
                    "method": "rule",
                    "confidence": 0.55,
                    "evidence_ids": ["evidence:fyi-archive-nz:123:manifest"],
                    "notes": "Inspect correspondence before distinguishing full versus partial release.",
                },
                "source_provenance": {
                    "input_path": "fixtures/fyi-manifest.jsonl",
                    "source_record_id": "123",
                    "raw_state_field": "state",
                    "raw_state_value": "successful",
                    "mapping_method": "rule",
                    "mapping_confidence": 0.55,
                    "evidence_id": "evidence:fyi-archive-nz:123:manifest",
                },
            }
        ],
    )
    write_jsonl(
        events,
        [
            {
                "event_id": "foio-nz:event:state-123",
                "event_type": "StateObserved",
                "assertion_status": "inferred",
                "confidence": 0.55,
                "request_ref": {"source_request_id": "123"},
                "evidence": [{"evidence_id": "evidence:fyi-archive-nz:123:manifest"}],
            }
        ],
    )

    result = write_request_goldset_tasks(
        requests,
        output,
        events_jsonl=events,
        summary_output=summary,
    )

    assert result["task_count"] == 1
    task = json.loads(output.read_text(encoding="utf-8").splitlines()[0])
    assert task["task_type"] == "state_mapping"
    assert task["prefilled_label"] == "ReleasedInFull"
    assert task["evidence"]["source_state"] == "successful"
    assert task["evidence"]["normalised_state"] == "ReleasedInFull"
    assert task["evidence"]["mapping_confidence"] == 0.55
    assert task["evidence"]["source_provenance"]["source_record_id"] == "123"
    assert task["evidence"]["event_hints"][0]["event_type"] == "StateObserved"
    assert task["evidence"]["event_hints"][0]["evidence_ids"] == [
        "evidence:fyi-archive-nz:123:manifest"
    ]

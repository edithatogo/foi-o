from __future__ import annotations

import json
from pathlib import Path

from foi_o_nz.agent_pack import write_agent_context_pack
from foi_o_nz.diff import diff_jsonl
from foi_o_nz.io import write_jsonl
from foi_o_nz.redaction import find_redaction_candidates, propose_redactions_jsonl
from foi_o_nz.reproducibility import write_reproducibility_manifest
from foi_o_nz.retrieval import search_chunk_records, search_chunks_jsonl


def test_search_chunk_records_ranks_relevant_text() -> None:
    records = [
        {
            "chunk_id": "c1",
            "source_record_type": "request",
            "source_id": "1",
            "request_id": "1",
            "text": "Request about health information and hospital policy.",
            "metadata": {},
        },
        {
            "chunk_id": "c2",
            "source_record_type": "request",
            "source_id": "2",
            "request_id": "2",
            "text": "Request about transport timetables.",
            "metadata": {},
        },
    ]
    report = search_chunk_records(records, query="health hospital", top_k=1, dimensions=16)
    assert report.result_count == 1
    assert report.results[0].chunk_id == "c1"
    assert "health" in report.results[0].matched_terms


def test_search_chunks_jsonl_writes_report(tmp_path: Path) -> None:
    input_path = tmp_path / "chunks.jsonl"
    output_path = tmp_path / "retrieval.json"
    write_jsonl(
        input_path,
        [
            {
                "chunk_id": "c1",
                "source_record_type": "request",
                "source_id": "1",
                "request_id": "1",
                "text": "Extension notice and working day calculation.",
                "metadata": {},
            }
        ],
    )
    result = search_chunks_jsonl(input_path, output_path, query="extension", top_k=3, dimensions=8)
    assert result["result_count"] == 1
    assert output_path.exists()


def test_redaction_candidates_are_masked_and_candidate_only() -> None:
    candidates = find_redaction_candidates(
        {"chunk_id": "c1", "request_id": "123", "text": "Email test@example.org about ABC1234."}
    )
    assert {candidate.span_type for candidate in candidates} >= {"email_address", "possible_nhi"}
    email_candidate = next(
        candidate for candidate in candidates if candidate.span_type == "email_address"
    )
    assert "test@example.org" not in email_candidate.masked_preview
    assert email_candidate.decision_status == "candidate_only_not_redacted"


def test_propose_redactions_jsonl(tmp_path: Path) -> None:
    input_path = tmp_path / "chunks.jsonl"
    output_path = tmp_path / "redactions.jsonl"
    write_jsonl(
        input_path, [{"chunk_id": "c1", "request_id": "123", "text": "Contact +64 21 123 4567."}]
    )
    result = propose_redactions_jsonl(input_path, output_path)
    assert result["candidate_count"] >= 1
    assert output_path.read_text(encoding="utf-8")


def test_diff_jsonl_reports_added_and_modified(tmp_path: Path) -> None:
    before = tmp_path / "before.jsonl"
    after = tmp_path / "after.jsonl"
    output = tmp_path / "diff.json"
    write_jsonl(before, [{"request_id": "1", "title": "Old"}])
    write_jsonl(after, [{"request_id": "1", "title": "New"}, {"request_id": "2", "title": "Added"}])
    result = diff_jsonl(before, after, output, key="request_id")
    assert result["counts"]["modified"] == 1
    assert result["counts"]["added"] == 1
    assert (
        json.loads(output.read_text(encoding="utf-8"))["schema_version"] == "foi-o-nz.diff.v0.1.0"
    )


def test_agent_context_pack_preserves_boundary(tmp_path: Path) -> None:
    requests = tmp_path / "requests.jsonl"
    events = tmp_path / "events.jsonl"
    chunks = tmp_path / "chunks.jsonl"
    output = tmp_path / "pack.json"
    write_jsonl(requests, [{"request_id": "123", "title": "Example", "authority": "Agency"}])
    write_jsonl(
        events,
        [
            {
                "event_id": "e1",
                "event_type": "RequestObserved",
                "request_ref": {"source_request_id": "123"},
            }
        ],
    )
    write_jsonl(chunks, [{"chunk_id": "c1", "request_id": "123", "text": "Example chunk."}])
    result = write_agent_context_pack(
        output,
        request_id="123",
        requests_jsonl=requests,
        events_jsonl=events,
        chunks_jsonl=chunks,
    )
    assert result["request_id"] == "123"
    assert "ReleaseMade" in result["constraints"]["agent_must_not"]
    assert result["provenance"]["component_counts"]["events"] == 1


def test_reproducibility_manifest_digests_files(tmp_path: Path) -> None:
    artefact = tmp_path / "artifact.json"
    artefact.write_text('{"ok": true}\n', encoding="utf-8")
    output = tmp_path / "repro.json"
    result = write_reproducibility_manifest([artefact], output, base_dir=tmp_path)
    assert result["schema_version"] == "foi-o-nz.reproducibility.v0.1.0"
    assert result["files"][0]["path"] == "artifact.json"
    assert len(result["files"][0]["sha256"]) == 64

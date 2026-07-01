from __future__ import annotations

from pathlib import Path

from foi_o_nz.batch import normalise_manifest_batch
from foi_o_nz.io import iter_jsonl, write_jsonl
from foi_o_nz.jsonld_context import write_context


def test_normalise_manifest_batch(tmp_path: Path) -> None:
    input_path = tmp_path / "manifest.jsonl"
    write_jsonl(
        input_path,
        [
            {
                "request_id": "r1",
                "title": "Request one",
                "authority": "Agency",
                "state": "waiting_response",
                "first_sent": "2026-06-01T00:00:00Z",
            }
        ],
    )
    requests = tmp_path / "requests.jsonl"
    events = tmp_path / "events.jsonl"
    result = normalise_manifest_batch([input_path], requests_output=requests, events_output=events)
    assert result["request_count"] == 1
    assert len(list(iter_jsonl(events))) >= 2


def test_write_context(tmp_path: Path) -> None:
    output = tmp_path / "context.jsonld"
    result = write_context(output)
    assert result["term_count"] > 5
    assert output.read_text(encoding="utf-8").startswith("{")

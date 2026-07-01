from __future__ import annotations

import json
from pathlib import Path

from rdflib import Graph

from foi_o_nz.rdf_export import export_rdf


def test_export_rdf_from_requests(tmp_path: Path) -> None:
    requests = tmp_path / "requests.jsonl"
    requests.write_text(
        json.dumps(
            {
                "request_id": 1,
                "title": "Example request",
                "authority": "Example Ministry",
                "normalised_state": "Received",
                "source_url": "https://fyi.org.nz/request/1_example",
                "first_sent": "2026-06-01T00:00:00Z",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    output = tmp_path / "requests.ttl"

    result = export_rdf(requests_jsonl=requests, output=output)

    assert result["request_count"] == 1
    assert output.exists()
    graph = Graph()
    graph.parse(output)
    assert len(graph) > 0

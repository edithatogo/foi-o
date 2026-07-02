from __future__ import annotations

import json
from pathlib import Path

from rdflib import Graph, Namespace, URIRef

from foi_o_nz.rdf_export import export_rdf

FOIO_EVENT = Namespace("https://w3id.org/foio-nz/event-type/")
FOIO_ASSERT = Namespace("https://w3id.org/foio-nz/assertion-status/")
FOIO_STATE = Namespace("https://w3id.org/foio-nz/state/")


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


def test_export_rdf_uses_skos_identifier_uris_for_event_terms(tmp_path: Path) -> None:
    events = tmp_path / "events.jsonl"
    events.write_text(
        json.dumps(
            {
                "event_id": "foio-nz:event:decision",
                "event_type": "DecisionCommunicated",
                "event_time": "2026-06-10T00:00:00Z",
                "assertion_status": "inferred",
                "lifecycle_state_after": "ReleasedInFull",
                "request_ref": {"source_request_id": "123"},
                "requires_human_certification": True,
                "evidence": [{"evidence_id": "evidence:1"}],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    output = tmp_path / "events.ttl"

    export_rdf(events_jsonl=events, output=output)

    graph = Graph()
    graph.parse(output)
    event_uri = URIRef("https://w3id.org/foio-nz/event/foio-nz:event:decision")
    assert (event_uri, URIRef("https://w3id.org/foio-nz/ontology#eventType"), FOIO_EVENT.DecisionCommunicated) in graph
    assert (event_uri, URIRef("https://w3id.org/foio-nz/ontology#assertionStatus"), FOIO_ASSERT.inferred) in graph
    assert (event_uri, URIRef("https://w3id.org/foio-nz/ontology#lifecycleStateAfter"), FOIO_STATE.released_in_full) in graph

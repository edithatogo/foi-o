"""RDF export helpers for request profiles and process events."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from rdflib import Graph, Literal, Namespace, RDF, URIRef
from rdflib.namespace import DCTERMS, PROV, XSD

from foi_o_nz.io import iter_jsonl

FOIO = Namespace("https://w3id.org/foio-nz/ontology#")
REQ = Namespace("https://w3id.org/foio-nz/request/")
EVT = Namespace("https://w3id.org/foio-nz/event/")


def _uri_fragment(value: Any) -> str:
    text = str(value).strip().replace("/", "_").replace(" ", "_")
    return "".join(ch for ch in text if ch.isalnum() or ch in "_-.:" ) or "unknown"


def graph_from_request_profiles(records: list[dict[str, Any]]) -> Graph:
    """Create a small RDF graph from request-profile dictionaries."""
    graph = Graph()
    graph.bind("foio", FOIO)
    graph.bind("dcterms", DCTERMS)
    graph.bind("prov", PROV)
    for record in records:
        request_uri = REQ[_uri_fragment(record.get("request_id"))]
        graph.add((request_uri, RDF.type, FOIO.AccessRequest))
        graph.add((request_uri, DCTERMS.identifier, Literal(str(record.get("request_id")))))
        if title := record.get("title"):
            graph.add((request_uri, DCTERMS.title, Literal(str(title))))
        if authority := record.get("authority"):
            authority_uri = URIRef(f"https://w3id.org/foio-nz/authority/{_uri_fragment(authority)}")
            graph.add((authority_uri, RDF.type, FOIO.Agency))
            graph.add((authority_uri, DCTERMS.title, Literal(str(authority))))
            graph.add((request_uri, FOIO.hasAuthority, authority_uri))
        if state := record.get("normalised_state"):
            graph.add((request_uri, FOIO.lifecycleState, Literal(str(state))))
        if source_url := record.get("source_url"):
            graph.add((request_uri, PROV.wasDerivedFrom, URIRef(str(source_url))))
        if first_sent := record.get("first_sent"):
            graph.add((request_uri, FOIO.firstSentAt, Literal(str(first_sent), datatype=XSD.dateTime)))
    return graph


def graph_from_events(records: list[dict[str, Any]]) -> Graph:
    """Create a small RDF graph from core-event dictionaries."""
    graph = Graph()
    graph.bind("foio", FOIO)
    graph.bind("dcterms", DCTERMS)
    graph.bind("prov", PROV)
    for record in records:
        event_id = str(record.get("event_id") or "")
        event_uri = URIRef(event_id) if event_id.startswith("urn:") else EVT[_uri_fragment(event_id)]
        graph.add((event_uri, RDF.type, FOIO.ProcessEvent))
        graph.add((event_uri, FOIO.eventType, Literal(str(record.get("event_type")))))
        graph.add((event_uri, PROV.generatedAtTime, Literal(str(record.get("event_time")), datatype=XSD.dateTime)))
        graph.add((event_uri, FOIO.assertionStatus, Literal(str(record.get("assertion_status")))))
        if state := record.get("lifecycle_state_after"):
            graph.add((event_uri, FOIO.lifecycleStateAfter, Literal(str(state))))
        request_ref = record.get("request_ref")
        if isinstance(request_ref, dict) and request_ref.get("source_request_id") is not None:
            request_uri = REQ[_uri_fragment(request_ref.get("source_request_id"))]
            graph.add((event_uri, FOIO.aboutRequest, request_uri))
        for evidence in record.get("evidence") or []:
            if isinstance(evidence, dict) and evidence.get("evidence_id"):
                evidence_uri = URIRef(f"https://w3id.org/foio-nz/evidence/{_uri_fragment(evidence['evidence_id'])}")
                graph.add((evidence_uri, RDF.type, PROV.Entity))
                graph.add((event_uri, PROV.wasDerivedFrom, evidence_uri))
    return graph


def export_rdf(
    *,
    requests_jsonl: Path | None = None,
    events_jsonl: Path | None = None,
    output: Path,
    fmt: str = "turtle",
) -> dict[str, Any]:
    """Export request/event JSONL into RDF."""
    graph = Graph()
    graph.bind("foio", FOIO)
    request_count = 0
    event_count = 0
    if requests_jsonl is not None:
        request_records = list(iter_jsonl(requests_jsonl))
        request_count = len(request_records)
        graph += graph_from_request_profiles(request_records)
    if events_jsonl is not None:
        event_records = list(iter_jsonl(events_jsonl))
        event_count = len(event_records)
        graph += graph_from_events(event_records)
    output.parent.mkdir(parents=True, exist_ok=True)
    graph.serialize(destination=str(output), format=fmt)
    return {
        "output": str(output),
        "format": fmt,
        "triple_count": len(graph),
        "request_count": request_count,
        "event_count": event_count,
    }

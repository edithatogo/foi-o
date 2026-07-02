"""Portable graph export for request/event/chunk/risk artefacts."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from foi_o_nz.io import iter_jsonl, write_json

GraphFormat = Literal["json", "mermaid"]
FOIO_BASE = "https://w3id.org/foio-nz/"


def _node(node_id: str, label: str, kind: str, **properties: Any) -> dict[str, Any]:
    return {
        "id": node_id,
        "label": label,
        "kind": kind,
        "properties": {k: v for k, v in properties.items() if v is not None},
    }


def _edge(source: str, target: str, label: str, **properties: Any) -> dict[str, Any]:
    return {
        "source": source,
        "target": target,
        "label": label,
        "properties": {k: v for k, v in properties.items() if v is not None},
    }


def _request_id_from_event(event: dict[str, Any]) -> str | None:
    request_ref = event.get("request_ref")
    if isinstance(request_ref, dict) and request_ref.get("source_request_id") is not None:
        return str(request_ref["source_request_id"])
    return str(event["request_id"]) if event.get("request_id") is not None else None


def _safe_mermaid_id(value: str) -> str:
    return "n" + "".join(ch if ch.isalnum() else "_" for ch in value)[:80]


def build_graph(
    *,
    requests_jsonl: Path | None = None,
    events_jsonl: Path | None = None,
    chunks_jsonl: Path | None = None,
    risks_jsonl: Path | None = None,
) -> dict[str, Any]:
    """Build a portable property graph representation."""
    nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, Any]] = []
    if requests_jsonl is not None:
        for record in iter_jsonl(requests_jsonl):
            request_id = str(record.get("request_id"))
            request_node = f"request:{request_id}"
            nodes[request_node] = _node(
                request_node,
                str(record.get("title") or request_id),
                "request",
                request_id=request_id,
                authority=record.get("authority"),
                state=record.get("normalised_state") or record.get("source_state"),
                semantic_type="foio:AccessRequest",
            )
            authority = record.get("authority")
            if authority:
                authority_node = f"authority:{authority}"
                nodes.setdefault(
                    authority_node,
                    _node(
                        authority_node,
                        str(authority),
                        "authority",
                        semantic_type="foio:Agency",
                    ),
                )
                edges.append(_edge(request_node, authority_node, "made_to"))
    if events_jsonl is not None:
        previous_by_request: dict[str, str] = {}
        for record in iter_jsonl(events_jsonl):
            event_id = str(record.get("event_id"))
            request_id = _request_id_from_event(record)
            event_node = f"event:{event_id}"
            nodes[event_node] = _node(
                event_node,
                str(record.get("event_type") or event_id),
                "event",
                event_type=record.get("event_type"),
                assertion_status=record.get("assertion_status"),
                requires_human_certification=record.get("requires_human_certification"),
                semantic_type="foio:ProcessEvent",
                event_type_uri=f"{FOIO_BASE}event-type/{record.get('event_type')}",
            )
            if request_id is not None:
                request_node = f"request:{request_id}"
                nodes.setdefault(
                    request_node,
                    _node(
                        request_node,
                        request_id,
                        "request",
                        request_id=request_id,
                        semantic_type="foio:AccessRequest",
                    ),
                )
                edges.append(_edge(request_node, event_node, "has_event"))
                previous = previous_by_request.get(request_id)
                if previous is not None:
                    edges.append(_edge(previous, event_node, "next_event"))
                previous_by_request[request_id] = event_node
    if chunks_jsonl is not None:
        for record in iter_jsonl(chunks_jsonl):
            chunk_id = str(record.get("chunk_id"))
            chunk_node = f"chunk:{chunk_id}"
            nodes[chunk_node] = _node(
                chunk_node,
                chunk_id,
                "chunk",
                token_estimate=record.get("token_estimate"),
                source_record_type=record.get("source_record_type"),
                semantic_type="foio:Chunk",
            )
            request_id = record.get("request_id")
            if request_id is not None:
                request_node = f"request:{request_id}"
                nodes.setdefault(
                    request_node,
                    _node(
                        request_node,
                        str(request_id),
                        "request",
                        request_id=str(request_id),
                        semantic_type="foio:AccessRequest",
                    ),
                )
                edges.append(_edge(request_node, chunk_node, "has_chunk"))
    if risks_jsonl is not None:
        for record in iter_jsonl(risks_jsonl):
            risk_id = str(record.get("assessment_id") or record.get("source_id"))
            risk_node = f"risk:{risk_id}"
            nodes[risk_node] = _node(
                risk_node,
                str(record.get("risk_level") or "risk"),
                "risk_assessment",
                risk_level=record.get("risk_level"),
                review_required=record.get("review_required"),
                semantic_type="foio:RiskAssessment",
            )
            request_id = record.get("request_id")
            if request_id is not None:
                request_node = f"request:{request_id}"
                nodes.setdefault(
                    request_node,
                    _node(
                        request_node,
                        str(request_id),
                        "request",
                        request_id=str(request_id),
                        semantic_type="foio:AccessRequest",
                    ),
                )
                edges.append(_edge(request_node, risk_node, "has_risk_assessment"))
    return {
        "schema_version": "foi-o-nz.graph.v0.1.0",
        "node_count": len(nodes),
        "edge_count": len(edges),
        "nodes": sorted(nodes.values(), key=lambda item: item["id"]),
        "edges": sorted(edges, key=lambda item: (item["source"], item["target"], item["label"])),
    }


def graph_to_mermaid(graph: dict[str, Any]) -> str:
    """Render a small Mermaid flowchart from a graph export."""
    labels = {
        node["id"]: str(node.get("label") or node["id"]).replace('"', "'")
        for node in graph.get("nodes", [])
    }
    lines = ["flowchart LR"]
    for edge in graph.get("edges", []):
        source = str(edge["source"])
        target = str(edge["target"])
        label = str(edge.get("label") or "relates_to").replace('"', "'")
        lines.append(
            f'  {_safe_mermaid_id(source)}["{labels.get(source, source)}"] -- "{label}" --> {_safe_mermaid_id(target)}["{labels.get(target, target)}"]'
        )
    if len(lines) == 1:
        lines.append('  empty["No graph records"]')
    return "\n".join(lines) + "\n"


def write_graph_export(
    output: Path,
    *,
    requests_jsonl: Path | None = None,
    events_jsonl: Path | None = None,
    chunks_jsonl: Path | None = None,
    risks_jsonl: Path | None = None,
    fmt: GraphFormat = "json",
) -> dict[str, Any]:
    """Write graph JSON or Mermaid and return summary."""
    graph = build_graph(
        requests_jsonl=requests_jsonl,
        events_jsonl=events_jsonl,
        chunks_jsonl=chunks_jsonl,
        risks_jsonl=risks_jsonl,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    if fmt == "mermaid":
        output.write_text(graph_to_mermaid(graph), encoding="utf-8")
    else:
        write_json(output, graph)
    return {
        "ok": True,
        "output": str(output),
        "format": fmt,
        "node_count": graph["node_count"],
        "edge_count": graph["edge_count"],
    }

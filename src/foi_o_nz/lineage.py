"""Small provenance/lineage graph builder for FOI-O NZ artifacts."""

from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from foi_o_nz.cas import digest_file, infer_media_type
from foi_o_nz.constants import LINEAGE_GRAPH_SCHEMA_VERSION
from foi_o_nz.encoding import dumps_json
from foi_o_nz.io import write_json


class LineageNode(BaseModel):
    """One artifact node in a provenance graph."""

    model_config = ConfigDict(extra="forbid")

    node_id: str
    kind: Literal["raw", "derived", "schema", "ontology", "report", "unknown"]
    path: str
    sha256: str
    media_type: str
    byte_size: int = Field(ge=0)
    role: str


class LineageEdge(BaseModel):
    """Directed provenance relation between artifacts."""

    model_config = ConfigDict(extra="forbid")

    edge_id: str
    source: str
    target: str
    relation: Literal["derived_from", "validated_by", "documents", "summarises", "unknown"]
    rationale: str


class LineageGraph(BaseModel):
    """A compact dependency graph for generated FOI-O NZ artifacts."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["foi-o-nz.lineage-graph.v0.1.0"] = LINEAGE_GRAPH_SCHEMA_VERSION
    generated_at: datetime
    graph_id: str
    nodes: list[LineageNode]
    edges: list[LineageEdge]
    limitations: list[str] = Field(default_factory=list)


def classify_path(
    path: Path,
) -> tuple[Literal["raw", "derived", "schema", "ontology", "report", "unknown"], str]:
    """Classify an artifact by path conventions."""
    parts = set(path.parts)
    name = path.name.lower()
    if "schemas" in parts or name.endswith(".schema.json"):
        return "schema", "validation_contract"
    if "ontology" in parts or "shacl" in parts or "vocab" in parts or path.suffix == ".ttl":
        return "ontology", "semantic_contract"
    if "raw" in parts or ("manifest" in name and "run" not in name):
        return "raw", "source_or_manifest"
    if any(
        term in name
        for term in ["summary", "risk", "quality", "audit", "diff", "repro", "metadata"]
    ):
        return "report", "analysis_report"
    if path.suffix in {".jsonl", ".json", ".parquet", ".ttl", ".duckdb"}:
        return "derived", "derived_artifact"
    return "unknown", "unclassified"


def node_id_for_path(path: Path, digest: str) -> str:
    """Build a stable node ID."""
    return f"foio-nz:artifact:{sha256(f'{path}\0{digest}'.encode()).hexdigest()[:24]}"


def build_lineage_graph(paths: list[Path], *, base_dir: Path | None = None) -> LineageGraph:
    """Build a heuristic lineage graph over supplied artifacts."""
    nodes: list[LineageNode] = []
    for path in sorted(paths, key=str):
        digest, size = digest_file(path)
        kind, role = classify_path(path)
        rel = (
            str(path.relative_to(base_dir))
            if base_dir is not None and path.is_relative_to(base_dir)
            else str(path)
        )
        nodes.append(
            LineageNode(
                node_id=node_id_for_path(path, digest),
                kind=kind,
                path=rel,
                sha256=digest,
                media_type=infer_media_type(path),
                byte_size=size,
                role=role,
            )
        )
    raw_nodes = [node for node in nodes if node.kind == "raw"]
    schema_nodes = [node for node in nodes if node.kind == "schema"]
    derived_nodes = [node for node in nodes if node.kind in {"derived", "report", "ontology"}]
    edges: list[LineageEdge] = []
    for raw in raw_nodes:
        for derived in derived_nodes:
            if raw.node_id == derived.node_id:
                continue
            edges.append(
                LineageEdge(
                    edge_id=f"foio-nz:edge:{sha256(f'{raw.node_id}>{derived.node_id}'.encode()).hexdigest()[:24]}",
                    source=raw.node_id,
                    target=derived.node_id,
                    relation="derived_from",
                    rationale="Heuristic: raw/manifest artifact supplied with derived/report artifact in the same lineage run.",
                )
            )
    for schema in schema_nodes:
        for derived in derived_nodes:
            edges.append(
                LineageEdge(
                    edge_id=f"foio-nz:edge:{sha256(f'{schema.node_id}>{derived.node_id}'.encode()).hexdigest()[:24]}",
                    source=schema.node_id,
                    target=derived.node_id,
                    relation="validated_by",
                    rationale="Heuristic: schema artifact is available to validate derived artifact family.",
                )
            )
    graph_digest = sha256(
        dumps_json([node.model_dump(mode="json") for node in nodes], sort_keys=True).encode("utf-8")
    ).hexdigest()
    return LineageGraph(
        generated_at=datetime.now(UTC),
        graph_id=f"foio-nz:lineage:{graph_digest[:24]}",
        nodes=nodes,
        edges=edges,
        limitations=[
            "Edges are convention-derived unless an upstream run manifest supplies explicit dependencies.",
            "Lineage describes artifact production and validation context; it does not certify legal correctness.",
        ],
    )


def write_lineage_graph(
    paths: list[Path],
    output: Path,
    *,
    base_dir: Path | None = None,
    dot_output: Path | None = None,
) -> dict[str, Any]:
    """Write a JSON lineage graph and optional Graphviz DOT file."""
    graph = build_lineage_graph(paths, base_dir=base_dir)
    write_json(output, graph.model_dump(mode="json", exclude_none=True))
    if dot_output is not None:
        dot_output.parent.mkdir(parents=True, exist_ok=True)
        dot_output.write_text(lineage_to_dot(graph), encoding="utf-8")
    return {
        "ok": True,
        "output": str(output),
        "dot_output": str(dot_output) if dot_output is not None else None,
        "node_count": len(graph.nodes),
        "edge_count": len(graph.edges),
        "graph_id": graph.graph_id,
    }


def lineage_to_dot(graph: LineageGraph) -> str:
    """Render a lineage graph as Graphviz DOT."""
    lines = ["digraph foi_o_nz_lineage {", '  rankdir="LR";']
    for node in graph.nodes:
        label = f"{node.role}\\n{node.path}"
        lines.append(f'  "{node.node_id}" [label="{label}"];')
    for edge in graph.edges:
        lines.append(f'  "{edge.source}" -> "{edge.target}" [label="{edge.relation}"];')
    lines.append("}")
    return "\n".join(lines) + "\n"

"""SHACL validation helpers with optional pySHACL support."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from rdflib import Graph


def validate_with_shacl(
    data_graph: Path,
    shapes_graph: Path,
    *,
    data_format: str = "turtle",
    shapes_format: str = "turtle",
) -> dict[str, Any]:
    """Validate RDF data against SHACL shapes.

    If pySHACL is unavailable, this performs parse-only validation and returns a
    clear degraded-mode status instead of failing the whole repository workflow.
    """
    data = Graph()
    data.parse(data_graph, format=data_format)
    shapes = Graph()
    shapes.parse(shapes_graph, format=shapes_format)
    try:
        from pyshacl import validate  # type: ignore[import-not-found]
    except ModuleNotFoundError:
        return {
            "ok": True,
            "mode": "parse_only_pyshacl_not_installed",
            "data_triples": len(data),
            "shape_triples": len(shapes),
            "warning": "install pyshacl for full SHACL constraint validation",
        }
    conforms, report_graph, report_text = validate(
        data,
        shacl_graph=shapes,
        inference="rdfs",
        abort_on_first=False,
        allow_infos=True,
        allow_warnings=True,
    )
    return {
        "ok": bool(conforms),
        "mode": "pyshacl",
        "data_triples": len(data),
        "shape_triples": len(shapes),
        "report_triples": len(report_graph),
        "report_text": report_text,
    }

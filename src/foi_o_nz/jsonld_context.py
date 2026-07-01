"""JSON-LD context exports for FOI-O NZ event/profile JSON."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from foi_o_nz.io import write_json

FOIO_CONTEXT: dict[str, Any] = {
    "@version": 1.1,
    "foio": "https://w3id.org/foi-o-nz/ontology#",
    "schema": "https://schema.org/",
    "prov": "http://www.w3.org/ns/prov#",
    "skos": "http://www.w3.org/2004/02/skos/core#",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "event_id": "@id",
    "event_type": {"@id": "foio:eventType", "@type": "@id"},
    "event_time": {"@id": "prov:generatedAtTime", "@type": "xsd:dateTime"},
    "source_system": "foio:sourceSystem",
    "lifecycle_state_after": "foio:lifecycleStateAfter",
    "assertion_status": "foio:assertionStatus",
    "confidence": {"@id": "foio:confidence", "@type": "xsd:decimal"},
    "machine_generated": {"@id": "foio:machineGenerated", "@type": "xsd:boolean"},
    "requires_human_certification": {
        "@id": "foio:requiresHumanCertification",
        "@type": "xsd:boolean",
    },
    "request_ref": "foio:aboutRequest",
    "evidence": "foio:hasEvidence",
    "payload": "foio:payload",
}


def write_context(path: Path) -> dict[str, Any]:
    """Write the FOI-O NZ JSON-LD context."""
    data = {"@context": FOIO_CONTEXT}
    write_json(path, data)
    return {"output": str(path), "term_count": len(FOIO_CONTEXT)}

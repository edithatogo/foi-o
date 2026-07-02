"""JSON-LD context exports for FOI-O NZ event/profile JSON."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from foi_o_nz.io import write_json

FOIO_CONTEXT: dict[str, Any] = {
    "@version": 1.1,
    "foio": "https://w3id.org/foio-nz/ontology#",
    "schema": "https://schema.org/",
    "prov": "http://www.w3.org/ns/prov#",
    "dcat": "http://www.w3.org/ns/dcat#",
    "odrl": "http://www.w3.org/ns/odrl/2/",
    "skos": "http://www.w3.org/2004/02/skos/core#",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "event_id": "@id",
    "event_type": {"@id": "foio:eventType", "@type": "@id"},
    "event_time": {"@id": "prov:generatedAtTime", "@type": "xsd:dateTime"},
    "source_system": "foio:sourceSystem",
    "source_url": {"@id": "foio:sourceUrl", "@type": "xsd:anyURI"},
    "source_provenance": "prov:wasDerivedFrom",
    "source_record_id": "foio:sourceRecordId",
    "raw_state_field": "foio:rawStateField",
    "raw_state_value": "foio:rawStateValue",
    "content_sha256": "foio:contentSha256",
    "lifecycle_state_after": "foio:lifecycleStateAfter",
    "assertion_status": "foio:assertionStatus",
    "confidence": {"@id": "foio:confidence", "@type": "xsd:decimal"},
    "machine_generated": {"@id": "foio:machineGenerated", "@type": "xsd:boolean"},
    "requires_human_certification": {
        "@id": "foio:requiresHumanCertification",
        "@type": "xsd:boolean",
    },
    "human_review_required": {"@id": "foio:humanReviewRequired", "@type": "xsd:boolean"},
    "legal_effect": "foio:legalEffect",
    "machine_certification_allowed": {
        "@id": "foio:machineCertificationAllowed",
        "@type": "xsd:boolean",
    },
    "generated_output_included": {
        "@id": "foio:generatedOutputIncluded",
        "@type": "xsd:boolean",
    },
    "request_ref": "foio:aboutRequest",
    "evidence": "foio:hasEvidence",
    "legal_references": "foio:hasLegalReference",
    "dataset_resources": "foio:hasDistribution",
    "publication_caveats": "foio:publicationCaveat",
    "source_version_id": "foio:sourceVersionId",
    "payload": "foio:payload",
}


def write_context(path: Path) -> dict[str, Any]:
    """Write the FOI-O NZ JSON-LD context."""
    data = {"@context": FOIO_CONTEXT}
    write_json(path, data)
    return {"output": str(path), "term_count": len(FOIO_CONTEXT)}

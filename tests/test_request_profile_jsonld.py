from __future__ import annotations

import json
from pathlib import Path

import pytest
from rdflib import Graph

from foi_o_nz.validation import validate_json_schema

REQUEST_EXAMPLE = Path("examples/request-record.jsonld")
REQUEST_SCHEMA = Path("schemas/json/request-profile.schema.json")
CONTEXT = Path("contexts/foi-o-nz.context.jsonld")


@pytest.mark.filterwarnings("ignore:ConjunctiveGraph is deprecated:DeprecationWarning")
def test_request_profile_jsonld_example_validates_and_parses() -> None:
    validation = validate_json_schema(REQUEST_EXAMPLE, REQUEST_SCHEMA)
    assert validation.ok, validation.errors

    data = json.loads(REQUEST_EXAMPLE.read_text(encoding="utf-8"))
    graph = Graph().parse(data=json.dumps(data), format="json-ld")

    assert len(graph) > 0
    assert data["source_state"] == "successful"
    assert data["normalised_state"] == "ReleasedInFull"
    assert data["source_provenance"]["source_record_id"] == "20001"
    assert data["source_provenance"]["raw_state_field"] == "state"
    assert data["source_provenance"]["mapping_method"] == "rule"
    assert data["state_mapping"]["evidence_ids"] == [data["source_provenance"]["evidence_id"]]


def test_request_profile_context_covers_provenance_terms() -> None:
    context = json.loads(CONTEXT.read_text(encoding="utf-8"))["@context"]

    for term in [
        "source_provenance",
        "source_record_id",
        "raw_state_field",
        "raw_state_value",
        "confidence",
    ]:
        assert term in context

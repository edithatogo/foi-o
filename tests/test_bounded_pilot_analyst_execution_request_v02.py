import json
from hashlib import sha256
from pathlib import Path

from foi_o_nz.validation import validate_json_schema

ROOT = Path(__file__).parents[1]
REQUEST = ROOT / "examples/v2/bounded-pilot-analyst-execution-request.v0.2.pending.json"
SCHEMA = ROOT / "schemas/json/bounded-pilot-analyst-execution-request-v0.2.schema.json"


def test_bounded_pilot_execution_request_is_inert_and_pinned() -> None:
    result = validate_json_schema(REQUEST, SCHEMA)
    assert not result.errors, result.errors
    request = json.loads(REQUEST.read_text())
    for key in ("protocol", "readiness", "codebook", "derivation_result"):
        pin = request[key]
        assert sha256((ROOT / pin["path"]).read_bytes()).hexdigest() == pin["sha256"]
    roles = request["roles"]
    assert len({role["actor_id"] for role in roles.values()}) == 3
    assert len({role["canonical_locator"] for role in roles.values()}) == 3
    for role in roles.values():
        pin = role["prompt"]
        assert sha256((ROOT / pin["path"]).read_bytes()).hexdigest() == pin["sha256"]
    for key in (
        "authorization_present",
        "derived_text_read_allowed",
        "context_materialization_allowed",
        "context_presentation_allowed",
        "analyst_execution_allowed",
        "reconciliation_allowed",
        "execution_allowed",
        "empirical_claims_allowed",
        "empirical_result_approval_allowed",
        "population_inference_allowed",
        "archive_wide_claim_allowed",
        "human_reviewed",
        "gold_eligible",
        "publication_allowed",
        "release_allowed",
        "paper_updates_allowed",
    ):
        assert request[key] is False

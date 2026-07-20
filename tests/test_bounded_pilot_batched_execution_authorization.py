import json
from hashlib import sha256
from pathlib import Path

from foi_o_nz.validation import validate_json_schema

ROOT = Path(__file__).parents[1]
AUTH = ROOT / "examples/v2/bounded-pilot-batched-execution-authorization.approved.json"
SCHEMA = ROOT / "schemas/json/bounded-pilot-batched-execution-authorization.schema.json"


def test_batched_authorization_is_exact_stage_ordered_and_candidate_only() -> None:
    result = validate_json_schema(AUTH, SCHEMA)
    assert not result.errors, result.errors
    authorization = json.loads(AUTH.read_text(encoding="utf-8"))
    assert [stage["id"] for stage in authorization["ordered_stages"]] == [
        f"S{i}" for i in range(2, 9)
    ]
    for pin in authorization["implementation_contracts"].values():
        assert sha256((ROOT / pin["path"]).read_bytes()).hexdigest() == pin["sha256"]
    assert authorization["candidate_manuscript_preparation_authorized"] is True
    assert authorization["local_package_validation_authorized"] is True
    for key in (
        "empirical_result_approved",
        "human_reviewed",
        "gold_eligible",
        "publication_allowed",
        "arxiv_submission_allowed",
        "external_action_allowed",
    ):
        assert authorization[key] is False

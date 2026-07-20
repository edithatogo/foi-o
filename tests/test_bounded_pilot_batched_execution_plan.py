import json
from hashlib import sha256
from pathlib import Path

from foi_o_nz.validation import validate_json_schema

ROOT = Path(__file__).parents[1]
PLAN = ROOT / "examples/v2/bounded-pilot-batched-execution-plan.pending.json"
SCHEMA = ROOT / "schemas/json/bounded-pilot-batched-execution-plan.schema.json"


def test_batched_plan_is_valid_pinned_and_inert() -> None:
    result = validate_json_schema(PLAN, SCHEMA)
    assert not result.errors, result.errors
    plan = json.loads(PLAN.read_text())
    for pin in plan["governed_inputs"].values():
        assert sha256((ROOT / pin["path"]).read_bytes()).hexdigest() == pin["sha256"]
    assert [stage["id"] for stage in plan["stages"]] == [f"S{i}" for i in range(1, 9)]
    for key in (
        "authorization_present",
        "execution_allowed",
        "empirical_result_approved",
        "human_reviewed",
        "gold_eligible",
        "population_inference_allowed",
        "archive_wide_claim_allowed",
        "redistribution_allowed",
        "publication_allowed",
        "release_allowed",
        "dataset_publication_allowed",
        "arxiv_submission_allowed",
        "external_action_allowed",
    ):
        assert plan[key] is False
    assert plan["final_exact_results_and_package_approval_required"] is True

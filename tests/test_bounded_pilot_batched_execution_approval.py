import json
import subprocess
from hashlib import sha256
from pathlib import Path

from foi_o_nz.validation import validate_json_schema

ROOT = Path(__file__).parents[1]
APPROVAL = ROOT / "examples/v2/bounded-pilot-batched-execution-approval.approved.json"
SCHEMA = ROOT / "schemas/json/bounded-pilot-batched-execution-approval.schema.json"


def test_exact_batched_execution_approval_is_plan_bound_and_downstream_inert() -> None:
    result = validate_json_schema(APPROVAL, SCHEMA)
    assert not result.errors, result.errors
    approval = json.loads(APPROVAL.read_text(encoding="utf-8"))
    assert (
        sha256(approval["approval_statement"].encode("utf-8")).hexdigest()
        == approval["approval_statement_sha256"]
    )
    pin = approval["approved_plan"]
    committed = subprocess.run(
        ["git", "show", f"{pin['repository_commit']}:{pin['path']}"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    ).stdout
    assert sha256(committed).hexdigest() == pin["sha256"]
    for key in (
        "empirical_result_approved",
        "human_reviewed",
        "gold_eligible",
        "publication_allowed",
        "external_action_allowed",
    ):
        assert approval[key] is False

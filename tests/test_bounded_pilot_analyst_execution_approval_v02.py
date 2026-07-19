import json
import subprocess
from hashlib import sha256
from pathlib import Path

from foi_o_nz.validation import validate_json_schema

ROOT = Path(__file__).parents[1]
APPROVAL = ROOT / "examples/v2/bounded-pilot-analyst-execution-approval.approved.json"
SCHEMA = ROOT / "schemas/json/bounded-pilot-analyst-execution-approval-v0.2.schema.json"


def test_exact_analyst_execution_approval_is_request_bound_and_inert() -> None:
    result = validate_json_schema(APPROVAL, SCHEMA)
    assert not result.errors, result.errors
    approval = json.loads(APPROVAL.read_text())
    assert (
        sha256(approval["approval_statement"].encode()).hexdigest()
        == approval["approval_statement_sha256"]
    )
    pin = approval["approved_request"]
    committed = subprocess.run(
        ["git", "show", f"{pin['repository_commit']}:{pin['path']}"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    ).stdout
    assert sha256(committed).hexdigest() == pin["sha256"]
    assert approval["reconciliation_authorized"] is False
    assert approval["empirical_result_approval_authorized"] is False

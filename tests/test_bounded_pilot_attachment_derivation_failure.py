import json
import subprocess
from hashlib import sha256
from pathlib import Path

from foi_o_nz.validation import validate_json_schema

ROOT = Path(__file__).parents[1]
ARTIFACT = ROOT / "examples/v2/bounded-pilot-attachment-derivation-attempt-failure.1.json"
SCHEMA = ROOT / "schemas/json/bounded-pilot-attachment-derivation-attempt-failure.schema.json"


def _digest(data: bytes) -> str:
    return sha256(data).hexdigest()


def test_failure_evidence_is_valid_and_pins_exact_attempt_commit() -> None:
    result = validate_json_schema(ARTIFACT, SCHEMA)
    assert not result.errors, result.errors
    evidence = json.loads(ARTIFACT.read_text(encoding="utf-8"))

    commit = evidence["repository_commit"]
    subprocess.run(
        ["git", "cat-file", "-e", f"{commit}^{{commit}}"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    for field in ("authorization", "execution_request", "wrapper"):
        pin = evidence[field]
        historical = subprocess.run(
            ["git", "show", f"{commit}:{pin['path']}"],
            cwd=ROOT,
            check=True,
            capture_output=True,
        ).stdout
        assert _digest(historical) == pin["sha256"]


def test_failure_evidence_records_only_observed_stderr_boundary() -> None:
    evidence = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    failure = evidence["failure"]
    assert evidence["pre_execution_verifier_passed"] is True
    assert evidence["tool_invoked"] is True
    assert failure["exception_message"] == "attachment derivation tool emitted stderr"
    assert failure["stderr_retained"] is False
    assert failure["stderr_sha256"] is None
    assert failure["stderr_byte_count"] is None


def test_failure_evidence_is_fail_closed_and_contains_no_derived_content() -> None:
    evidence = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    assert evidence["derivation_complete"] is False
    assert evidence["outputs_installed"] is False
    assert evidence["result_manifest_created"] is False
    assert evidence["restricted_outputs_committed"] is False
    for field in (
        "context_presentation_allowed",
        "analyst_execution_allowed",
        "reconciliation_allowed",
        "empirical_evidence",
        "human_reviewed",
        "gold_eligible",
    ):
        assert evidence[field] is False

    tracked = subprocess.run(
        ["git", "ls-files", "examples/v2"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    assert not any(
        path.startswith("examples/v2/bounded-pilot") and path.endswith(".txt") for path in tracked
    )

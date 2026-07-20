import json
import subprocess
from hashlib import sha256
from pathlib import Path

from foi_o_nz.validation import validate_json_schema

ROOT = Path(__file__).parents[1]
RESULT = ROOT / "examples/v2/bounded-pilot-attachment-mutool-derivation-result.1.json"
SCHEMA = ROOT / "schemas/json/bounded-pilot-attachment-mutool-derivation-result.schema.json"


def test_mutool_result_is_metadata_only_and_exactly_pinned() -> None:
    validation = validate_json_schema(RESULT, SCHEMA)
    assert not validation.errors, validation.errors
    result = json.loads(RESULT.read_text())
    for key in ("authorization", "execution_request", "wrapper"):
        pin = result[key]
        path = ROOT / pin["path"]
        assert sha256(path.read_bytes()).hexdigest() == pin["sha256"]
        committed = subprocess.run(
            ["git", "show", f"{pin['repository_commit']}:{pin['path']}"],
            cwd=ROOT,
            check=True,
            capture_output=True,
        ).stdout
        assert sha256(committed).hexdigest() == pin["sha256"]
    assert len(result["outputs"]) == 3
    assert all(output["repeat_outputs_match"] is True for output in result["outputs"])
    assert all("content" not in output for output in result["outputs"])


def test_mutool_result_preserves_all_downstream_prohibitions() -> None:
    result = json.loads(RESULT.read_text())
    assert result["local_only"] is True
    for key in (
        "stderr_retained",
        "stderr_review_authorized",
        "derivation_retry_authorized",
        "temporary_workspace_remaining",
        "restricted_outputs_committed",
        "context_presentation_allowed",
        "analyst_execution_allowed",
        "reconciliation_allowed",
        "empirical_evidence",
        "human_reviewed",
        "gold_eligible",
        "legal_certification",
        "redistribution_allowed",
        "publication_allowed",
        "release_allowed",
        "dataset_publication_allowed",
        "paper_updates_allowed",
    ):
        assert result[key] is False

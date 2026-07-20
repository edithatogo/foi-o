import json
import subprocess
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

from foi_o_nz.validation import validate_json_schema

ROOT = Path(__file__).parents[1]
CANDIDATE = ROOT / "examples/v2/bounded-pilot-execution-input-readiness.v0.2.pending.json"
SCHEMA = ROOT / "schemas/json/bounded-pilot-execution-input-readiness-v0.2.schema.json"


def test_v02_readiness_candidate_is_closed_and_commit_pinned() -> None:
    validation = validate_json_schema(CANDIDATE, SCHEMA)
    assert not validation.errors, validation.errors
    candidate = json.loads(CANDIDATE.read_text())
    for key in ("derived_from_readiness", "attachment_derivation_result"):
        pin = candidate[key]
        assert sha256((ROOT / pin["path"]).read_bytes()).hexdigest() == pin["sha256"]
        committed = subprocess.run(
            ["git", "show", f"{pin['repository_commit']}:{pin['path']}"],
            cwd=ROOT,
            check=True,
            capture_output=True,
        ).stdout
        assert sha256(committed).hexdigest() == pin["sha256"]
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", pin["repository_commit"], "HEAD"],
            cwd=ROOT,
            check=True,
        )
    base = json.loads((ROOT / candidate["derived_from_readiness"]["path"]).read_text())
    assert [unit["request_id"] for unit in base["units"]] == ["11872", "35076"]
    assert base["sampling"]["claim_scope"] == (
        "case_level_feasibility_for_requests_11872_and_35076_only"
    )
    assert base["inputs_ready"] is False
    assert base["context_presentation_allowed"] is False
    assert base["execution_allowed"] is False


def test_v02_readiness_uses_result_metadata_without_content() -> None:
    candidate = json.loads(CANDIDATE.read_text())
    result = json.loads((ROOT / candidate["attachment_derivation_result"]["path"]).read_text())
    summary = candidate["attachment_derivation_summary"]
    assert summary["outputs"] == [
        {
            key: output[key]
            for key in ("output_name", "source_sha256", "output_sha256", "byte_count")
        }
        for output in result["outputs"]
    ]
    assert summary["manifest_sha256"] == result["manifest_sha256"]
    assert summary["content_embedded"] is False
    assert summary["content_decoded_for_readiness"] is False
    assert summary["content_presented"] is False
    assert result["status"] == "bounded_local_derivation_complete_context_still_prohibited"
    assert result["local_only"] is True
    assert result["restricted_outputs_committed"] is False
    assert result["pass_count"] == 2
    assert result["source_count"] == result["output_count"] == 3
    assert result["nonempty_stderr_observed"] is False
    for key in (
        "context_presentation_allowed",
        "analyst_execution_allowed",
        "reconciliation_allowed",
        "empirical_evidence",
        "human_reviewed",
        "gold_eligible",
    ):
        assert result[key] is False


def test_v02_readiness_candidate_remains_inert() -> None:
    candidate = json.loads(CANDIDATE.read_text())
    assert candidate["candidate_components_complete"] is True
    assert candidate["separate_context_and_execution_authorization_required"] is True
    assert candidate["clean_head_pre_execution_verification_required"] is True
    for key in (
        "exact_readiness_approval_present",
        "inputs_ready",
        "derived_text_read_allowed",
        "context_materialization_allowed",
        "context_presentation_allowed",
        "analyst_execution_allowed",
        "reconciliation_allowed",
        "execution_allowed",
        "population_inference_allowed",
        "archive_wide_claim_allowed",
        "empirical_claims_allowed",
        "empirical_evidence",
        "human_reviewed",
        "gold_eligible",
        "legal_certified",
        "redistribution_allowed",
        "training_allowed",
        "fine_tuning_allowed",
        "publication_allowed",
        "release_allowed",
        "dataset_publication_allowed",
        "paper_updates_allowed",
    ):
        assert candidate[key] is False
    assert candidate["local_only"] is True


def test_v02_schema_rejects_provenance_and_output_substitution(tmp_path: Path) -> None:
    candidate = json.loads(CANDIDATE.read_text())
    mutations = []
    wrong_pin = deepcopy(candidate)
    wrong_pin["attachment_derivation_result"]["path"] = "attacker.json"
    mutations.append(wrong_pin)
    duplicate_output = deepcopy(candidate)
    duplicate_output["attachment_derivation_summary"]["outputs"][1] = deepcopy(
        duplicate_output["attachment_derivation_summary"]["outputs"][0]
    )
    mutations.append(duplicate_output)
    enabled = deepcopy(candidate)
    enabled["context_presentation_allowed"] = True
    mutations.append(enabled)
    for index, mutation in enumerate(mutations):
        path = tmp_path / f"mutation-{index}.json"
        path.write_text(json.dumps(mutation), encoding="utf-8")
        assert validate_json_schema(path, SCHEMA).errors

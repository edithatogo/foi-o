from __future__ import annotations

import copy
import hashlib
import json
import subprocess
from pathlib import Path

import pytest
from empirical_context_fixture import build_context_fixture
from jsonschema import Draft202012Validator

from foi_o_nz.empirical_pipeline.contracts import (
    EmpiricalContractError,
    canonical_bytes,
    content_sha256,
    load_run_spec,
    parse_run_spec,
    seal_record,
    validate_executable_run,
    validate_run_spec,
    validate_stage_result,
)

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "schemas" / "json"
SHA_A = "a" * 64
SHA_B = "b" * 64
SHA_C = "c" * 64
SHA_D = "d" * 64


def _authority_bindings() -> dict:
    approver = {
        "identity_id": "human:owner",
        "identity_kind": "external_human",
    }
    return {
        "calibration_approval": {
            "artifact_id": "approval:calibration:au-test",
            "artifact_sha256": "e" * 64,
            "approved_context_sha256": SHA_A,
            "approver_identity": approver,
        },
        "execution_authorization_approval": {
            "artifact_id": "approval:execution:au-test",
            "artifact_sha256": "f" * 64,
            "approved_context_sha256": SHA_A,
            "approver_identity": approver,
        },
    }


def _population() -> dict:
    return {
        "population_id": "population:au-test",
        "population_sha256": SHA_A,
        "predecessor": 10,
        "included": 8,
        "excluded": 1,
        "unresolved": 1,
    }


def _stage() -> dict:
    return {
        "stage_id": "stage:sample",
        "sequence": 1,
        "stage_kind": "sample",
        "input_sha256": [SHA_A],
        "output_sha256": [SHA_B],
        "population": _population(),
        "allowed_capabilities": ["sampling.membership.prepare"],
        "denied_capabilities": [
            "annotation.execute",
            "publication.release",
        ],
    }


def _run_spec() -> dict:
    return seal_record(
        {
            "schema_version": "foio.australian-empirical-run-spec.v1.0.0",
            "run_id": "run:au-test",
            "jurisdiction": "AU-CTH",
            "profile_id": "foi-o-au-cth",
            "assessment_status": "active",
            "lifecycle_disposition": "opaque_producer",
            "canonicalization": "foio.sorted-compact-json.v1",
            "authority_bindings": _authority_bindings(),
            "evidence_sources": [
                {
                    "artifact_id": "evidence:test",
                    "path": "examples/v2/test.json",
                    "sha256": SHA_C,
                    "size_bytes": 123,
                    "git_commit": "d" * 40,
                }
            ],
            "referenced_artifacts": [
                {
                    "artifact_id": "membership:test",
                    "sha256": SHA_A,
                    "availability": "restricted_local",
                    "evidence_source_sha256": SHA_C,
                }
            ],
            "producer_provenance": {
                "status": "opaque",
                "reason": "The committed evidence does not pin the producing command.",
                "evidence_source_sha256": SHA_C,
            },
            "stages": [_stage()],
            "legacy_interpretation": {
                "source_codebook_sha256": SHA_D,
                "unknown_label": "unknown",
                "normalized_label": None,
                "abstention_reason": "insufficient_evidence",
                "preserves_original_bytes": True,
                "preserves_original_value": True,
            },
            "relationships": {"supersedes": [], "invalidates": []},
        },
        "run_spec_sha256",
    )


def _stage_result(spec: dict) -> dict:
    stage = spec["stages"][0]
    return seal_record(
        {
            "schema_version": "foio.australian-empirical-stage-result.v1.0.0",
            "run_id": spec["run_id"],
            "run_spec_sha256": spec["run_spec_sha256"],
            "stage_id": stage["stage_id"],
            "stage_sequence": stage["sequence"],
            "stage_spec_sha256": hashlib.sha256(canonical_bytes(stage)).hexdigest(),
            "result_status": "completed",
            "input_sha256": copy.deepcopy(stage["input_sha256"]),
            "output_sha256": copy.deepcopy(stage["output_sha256"]),
            "population": copy.deepcopy(stage["population"]),
            "allowed_capabilities": copy.deepcopy(stage["allowed_capabilities"]),
            "denied_capabilities": copy.deepcopy(stage["denied_capabilities"]),
        },
        "stage_result_sha256",
    )


def _reseal(value: dict, field: str) -> dict:
    value.pop(field, None)
    value.update(seal_record(value, field))
    return value


def test_run_spec_and_stage_result_validate() -> None:
    spec = _run_spec()
    validate_run_spec(spec)
    validate_stage_result(_stage_result(spec), spec)


def test_published_schemas_accept_valid_records() -> None:
    spec = _run_spec()
    result = _stage_result(spec)
    run_schema = json.loads((SCHEMA_DIR / "australian-empirical-run-spec.schema.json").read_text())
    result_schema = json.loads(
        (SCHEMA_DIR / "australian-empirical-stage-result.schema.json").read_text()
    )
    Draft202012Validator(run_schema).validate(spec)
    Draft202012Validator(result_schema).validate(result)


def test_run_spec_schema_rejects_malformed_authority_bindings() -> None:
    spec = _run_spec()
    spec["authority_bindings"]["calibration_approval"]["unexpected"] = True
    _reseal(spec, "run_spec_sha256")

    with pytest.raises(EmpiricalContractError, match="schema validation failed"):
        validate_run_spec(spec)


def test_run_spec_rejects_population_imbalance() -> None:
    spec = _run_spec()
    spec["stages"][0]["population"]["included"] = 7
    _reseal(spec, "run_spec_sha256")
    with pytest.raises(EmpiricalContractError, match="population imbalance"):
        validate_run_spec(spec)


def test_run_spec_rejects_overlapping_capabilities() -> None:
    spec = _run_spec()
    spec["stages"][0]["allowed_capabilities"].append("publication.release")
    _reseal(spec, "run_spec_sha256")
    with pytest.raises(EmpiricalContractError, match="capabilities overlap"):
        validate_run_spec(spec)


def test_run_spec_rejects_missing_denial_boundary() -> None:
    spec = _run_spec()
    spec["stages"][0]["denied_capabilities"] = []
    _reseal(spec, "run_spec_sha256")
    with pytest.raises(EmpiricalContractError, match="schema validation failed"):
        validate_run_spec(spec)


def test_run_spec_rejects_duplicate_stage_identity_and_sequence() -> None:
    spec = _run_spec()
    spec["stages"].append(copy.deepcopy(spec["stages"][0]))
    _reseal(spec, "run_spec_sha256")
    with pytest.raises(EmpiricalContractError, match="duplicate stage"):
        validate_run_spec(spec)


def test_run_spec_rejects_unpinned_or_unreferenced_opaque_provenance() -> None:
    spec = _run_spec()
    spec["producer_provenance"]["evidence_source_sha256"] = SHA_B
    _reseal(spec, "run_spec_sha256")
    with pytest.raises(EmpiricalContractError, match="evidence source"):
        validate_run_spec(spec)


def test_run_spec_rejects_unpinned_referenced_artifact() -> None:
    spec = _run_spec()
    spec["referenced_artifacts"][0]["evidence_source_sha256"] = SHA_B
    _reseal(spec, "run_spec_sha256")
    with pytest.raises(EmpiricalContractError, match="evidence source"):
        validate_run_spec(spec)


def test_run_spec_rejects_self_pin_tampering() -> None:
    spec = _run_spec()
    spec["profile_id"] = "foi-o-au-nsw"
    with pytest.raises(EmpiricalContractError, match="run_spec_sha256"):
        validate_run_spec(spec)


def test_stage_result_is_bound_to_exact_run_and_stage() -> None:
    spec = _run_spec()
    result = _stage_result(spec)
    result["stage_id"] = "stage:invented"
    _reseal(result, "stage_result_sha256")
    with pytest.raises(EmpiricalContractError, match="unknown stage"):
        validate_stage_result(result, spec)


@pytest.mark.parametrize(
    ("field", "replacement", "message"),
    [
        ("run_spec_sha256", SHA_B, "run specification"),
        ("stage_spec_sha256", SHA_B, "stage specification"),
        ("input_sha256", [SHA_B], "input"),
        ("output_sha256", [SHA_C], "output"),
        ("population", {**_population(), "included": 7}, "population"),
        ("allowed_capabilities", [], "allowed capabilities"),
        ("denied_capabilities", ["release.merge"], "denied capabilities"),
    ],
)
def test_stage_result_rejects_contract_drift(field: str, replacement: object, message: str) -> None:
    spec = _run_spec()
    result = _stage_result(spec)
    result[field] = replacement
    _reseal(result, "stage_result_sha256")
    with pytest.raises(EmpiricalContractError, match=message):
        validate_stage_result(result, spec)


def test_stage_result_rejects_population_imbalance_independently() -> None:
    spec = _run_spec()
    result = _stage_result(spec)
    result["population"]["included"] = 7
    _reseal(result, "stage_result_sha256")
    with pytest.raises(EmpiricalContractError, match="population imbalance"):
        validate_stage_result(result, spec)


def test_catalog_specs_are_self_pinned_and_source_files_are_exact() -> None:
    catalog = ROOT / "versions" / "empirical-runs"
    specs = sorted(catalog.glob("*.json"))
    assert specs
    for path in specs:
        spec = load_run_spec(path)
        for source in spec.evidence_sources:
            source_path = ROOT / source.path
            assert source_path.is_file()
            assert hashlib.sha256(source_path.read_bytes()).hexdigest() == source.sha256
            assert source.size_bytes == source_path.stat().st_size


def _init_repository(tmp_path: Path) -> tuple[Path, str]:
    repository = tmp_path / "repository"
    repository.mkdir()
    subprocess.run(["git", "init", "-q", str(repository)], check=True)
    subprocess.run(
        ["git", "-C", str(repository), "config", "user.email", "test@example.invalid"], check=True
    )
    subprocess.run(["git", "-C", str(repository), "config", "user.name", "Test"], check=True)
    evidence = repository / "examples" / "v2" / "test.json"
    evidence.parent.mkdir(parents=True)
    evidence.write_bytes(b'{"evidence":"pinned"}\n')
    subprocess.run(["git", "-C", str(repository), "add", "examples/v2/test.json"], check=True)
    subprocess.run(["git", "-C", str(repository), "commit", "-qm", "add evidence"], check=True)
    commit = subprocess.run(
        ["git", "-C", str(repository), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    return repository, commit


def _write_loadable_spec(repository: Path, commit: str) -> Path:
    evidence = repository / "examples" / "v2" / "test.json"
    spec = _run_spec()
    spec["evidence_sources"][0].update(
        sha256=hashlib.sha256(evidence.read_bytes()).hexdigest(),
        size_bytes=evidence.stat().st_size,
        git_commit=commit,
    )
    source_sha = spec["evidence_sources"][0]["sha256"]
    spec["referenced_artifacts"][0]["evidence_source_sha256"] = source_sha
    spec["producer_provenance"]["evidence_source_sha256"] = source_sha
    _reseal(spec, "run_spec_sha256")
    spec_path = repository / "versions" / "empirical-runs" / "test.json"
    spec_path.parent.mkdir(parents=True)
    spec_path.write_text(json.dumps(spec), encoding="utf-8")
    return spec_path


def test_load_run_spec_verifies_current_and_committed_evidence_bytes(tmp_path: Path) -> None:
    repository, commit = _init_repository(tmp_path)
    spec_path = _write_loadable_spec(repository, commit)

    loaded = load_run_spec(spec_path)

    assert loaded.evidence_sources[0].git_commit == commit
    assert loaded.authority_bindings is not None
    assert (
        loaded.authority_bindings.calibration_approval.artifact_id == "approval:calibration:au-test"
    )
    assert loaded.authority_bindings.execution_authorization_approval.artifact_sha256 == "f" * 64


@pytest.mark.parametrize("tamper", [b"different", b'{"evidence":"pinned"}\nextra'])
def test_load_run_spec_rejects_tampered_current_evidence(tmp_path: Path, tamper: bytes) -> None:
    repository, commit = _init_repository(tmp_path)
    spec_path = _write_loadable_spec(repository, commit)
    (repository / "examples" / "v2" / "test.json").write_bytes(tamper)

    with pytest.raises(EmpiricalContractError, match=r"current evidence (size|SHA-256) mismatch"):
        load_run_spec(spec_path)


def test_load_run_spec_rejects_commit_blob_that_differs_from_declared_pin(tmp_path: Path) -> None:
    repository, first_commit = _init_repository(tmp_path)
    evidence = repository / "examples" / "v2" / "test.json"
    evidence.write_bytes(b'{"evidence":"new"}\n')
    subprocess.run(["git", "-C", str(repository), "add", "examples/v2/test.json"], check=True)
    subprocess.run(["git", "-C", str(repository), "commit", "-qm", "change evidence"], check=True)
    second_commit = subprocess.run(
        ["git", "-C", str(repository), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    spec_path = _write_loadable_spec(repository, first_commit)
    assert first_commit != second_commit

    with pytest.raises(EmpiricalContractError, match=r"committed evidence (size|SHA-256) mismatch"):
        load_run_spec(spec_path)


def test_load_run_spec_rejects_unverifiable_non_git_evidence(tmp_path: Path) -> None:
    evidence = tmp_path / "examples" / "v2" / "test.json"
    evidence.parent.mkdir(parents=True)
    evidence.write_bytes(b'{"evidence":"restricted-local"}\n')
    spec = _run_spec()
    spec["evidence_sources"][0].update(
        sha256=hashlib.sha256(evidence.read_bytes()).hexdigest(),
        size_bytes=evidence.stat().st_size,
    )
    source_sha = spec["evidence_sources"][0]["sha256"]
    spec["referenced_artifacts"][0]["evidence_source_sha256"] = source_sha
    spec["producer_provenance"]["evidence_source_sha256"] = source_sha
    _reseal(spec, "run_spec_sha256")
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps(spec), encoding="utf-8")

    with pytest.raises(EmpiricalContractError, match="restricted-local payloads must remain"):
        load_run_spec(spec_path)


@pytest.mark.parametrize(
    ("assessment_status", "lifecycle_disposition"),
    [
        ("active", "invalidated"),
        ("active", "superseded"),
        ("invalidated", "active"),
        ("superseded", "opaque_producer"),
    ],
)
def test_run_spec_rejects_incompatible_lifecycle_states(
    assessment_status: str, lifecycle_disposition: str
) -> None:
    spec = _run_spec()
    spec["assessment_status"] = assessment_status
    spec["lifecycle_disposition"] = lifecycle_disposition
    _reseal(spec, "run_spec_sha256")

    with pytest.raises(EmpiricalContractError, match="lifecycle"):
        validate_run_spec(spec)


@pytest.mark.parametrize("relationship", ["supersedes", "invalidates"])
def test_run_spec_rejects_self_relationships(relationship: str) -> None:
    spec = _run_spec()
    spec["relationships"][relationship] = [spec["run_id"]]
    _reseal(spec, "run_spec_sha256")

    with pytest.raises(EmpiricalContractError, match="self-reference"):
        validate_run_spec(spec)


def test_run_spec_rejects_overlapping_relationships() -> None:
    spec = _run_spec()
    related = "run:au-related"
    spec["relationships"] = {"supersedes": [related], "invalidates": [related]}
    _reseal(spec, "run_spec_sha256")

    with pytest.raises(EmpiricalContractError, match="relationships overlap"):
        validate_run_spec(spec)


@pytest.mark.parametrize(
    ("assessment_status", "lifecycle_disposition"),
    [("superseded", "superseded"), ("invalidated", "invalidated")],
)
def test_stage_execution_rejects_inactive_runs(
    assessment_status: str, lifecycle_disposition: str
) -> None:
    spec = _run_spec()
    spec["assessment_status"] = assessment_status
    spec["lifecycle_disposition"] = lifecycle_disposition
    _reseal(spec, "run_spec_sha256")

    with pytest.raises(EmpiricalContractError, match="cannot execute"):
        validate_stage_result(_stage_result(spec), spec)


@pytest.mark.parametrize(
    ("assessment_status", "lifecycle_disposition"),
    [("superseded", "superseded"), ("invalidated", "invalidated")],
)
def test_shared_executable_lifecycle_api_rejects_inactive_mappings_and_parsed_specs(
    assessment_status: str, lifecycle_disposition: str
) -> None:
    spec = _run_spec()
    spec["assessment_status"] = assessment_status
    spec["lifecycle_disposition"] = lifecycle_disposition
    _reseal(spec, "run_spec_sha256")

    with pytest.raises(EmpiricalContractError, match="cannot execute"):
        validate_executable_run(spec)
    with pytest.raises(EmpiricalContractError, match="verified context"):
        validate_executable_run(parse_run_spec(spec))


def test_shared_executable_lifecycle_api_rejects_active_descriptive_spec() -> None:
    with pytest.raises(EmpiricalContractError, match="verified context"):
        validate_executable_run(parse_run_spec(_run_spec()))


@pytest.mark.parametrize(
    ("stage_kind", "capability"),
    [
        ("frame", "frame.finalize"),
        ("sample", "sampling.membership.prepare"),
        ("packet", "packet.generate"),
        ("annotation", "annotation.execute"),
        ("reliability", "reliability.compute_descriptive"),
        ("extractor_metrics", "extractor_metrics.compute"),
        ("maturity", "maturity.compare_thresholds"),
    ],
)
def test_each_inactive_stage_capability_fails_closed(
    tmp_path: Path, stage_kind: str, capability: str
) -> None:
    context = build_context_fixture(
        tmp_path,
        extra_stages=(
            ("frame", ("frame.finalize",)),
            ("sample", ("sampling.membership.prepare",)),
        ),
    ).context
    internal = object.__getattribute__(context, "_run_spec")
    internal.raw["assessment_status"] = "invalidated"
    internal.raw["lifecycle_disposition"] = "invalidated"
    internal.raw["run_spec_sha256"] = content_sha256(internal.raw, "run_spec_sha256")

    with pytest.raises(EmpiricalContractError, match="cannot execute"):
        context.require_capability(stage_kind, capability)

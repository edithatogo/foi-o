"""Fail-closed contracts for versioned Australian empirical runs."""

from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

CANONICALIZATION_ID = "foio.sorted-compact-json.v1"
RUN_SPEC_VERSION = "foio.australian-empirical-run-spec.v1.0.0"
STAGE_RESULT_VERSION = "foio.australian-empirical-stage-result.v1.0.0"
SCHEMA_DIR = Path(__file__).resolve().parents[3] / "schemas" / "json"


class EmpiricalContractError(ValueError):
    """Raised when an empirical contract fails closed."""


@dataclass(frozen=True)
class ArtifactPin:
    """Exact committed evidence-source identity."""

    artifact_id: str
    path: str
    sha256: str
    size_bytes: int
    git_commit: str


@dataclass(frozen=True)
class AuthorityIdentity:
    """Named external identity attached to an approved authority artifact."""

    identity_id: str
    identity_kind: str


@dataclass(frozen=True)
class ExternalApprovalBinding:
    """Exact external approval artifact bound into a run specification."""

    artifact_id: str
    artifact_sha256: str
    approved_context_sha256: str
    approver_identity: AuthorityIdentity


@dataclass(frozen=True)
class AuthorityBindings:
    """Execution authorities registered by an immutable run specification."""

    calibration_approval: ExternalApprovalBinding
    execution_authorization_approval: ExternalApprovalBinding


@dataclass(frozen=True)
class PopulationSpecification:
    """Conserved population counts for one empirical stage."""

    population_id: str
    population_sha256: str
    predecessor: int
    included: int
    excluded: int
    unresolved: int


@dataclass(frozen=True)
class StageSpecification:
    """Immutable identity and capability boundary for one stage."""

    stage_id: str
    sequence: int
    stage_kind: str
    population: PopulationSpecification


@dataclass(frozen=True)
class RunSpecification:
    """Descriptive parsed run specification; never an execution authority."""

    run_id: str
    jurisdiction: str
    profile_id: str
    assessment_status: str
    lifecycle_disposition: str
    evidence_sources: tuple[ArtifactPin, ...]
    stages: tuple[StageSpecification, ...]
    run_spec_sha256: str
    raw: dict[str, Any]
    authority_bindings: AuthorityBindings | None = None


def canonical_bytes(value: Any) -> bytes:
    """Return stable compact UTF-8 JSON bytes."""
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def content_sha256(record: dict[str, Any], self_pin_field: str) -> str:
    """Hash a record after excluding its named self-pin."""
    body = {key: value for key, value in record.items() if key != self_pin_field}
    return hashlib.sha256(canonical_bytes(body)).hexdigest()


def seal_record(record: dict[str, Any], self_pin_field: str) -> dict[str, Any]:
    """Return a copy with its content-addressed self-pin populated."""
    sealed = dict(record)
    sealed[self_pin_field] = content_sha256(sealed, self_pin_field)
    return sealed


def _schema_errors(value: dict[str, Any], filename: str) -> list[str]:
    schema = json.loads((SCHEMA_DIR / filename).read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    return [
        f"{'/'.join(str(part) for part in error.absolute_path) or '<root>'}: {error.message}"
        for error in sorted(validator.iter_errors(value), key=lambda item: list(item.absolute_path))
    ]


def _require_schema(value: dict[str, Any], filename: str) -> None:
    errors = _schema_errors(value, filename)
    if errors:
        raise EmpiricalContractError("schema validation failed: " + "; ".join(errors))


def _require_self_pin(record: dict[str, Any], field: str) -> None:
    if record.get(field) != content_sha256(record, field):
        raise EmpiricalContractError(f"invalid {field}")


def _validate_population(population: dict[str, Any]) -> None:
    predecessor = population["predecessor"]
    accounted = population["included"] + population["excluded"] + population["unresolved"]
    if predecessor != accounted:
        raise EmpiricalContractError("population imbalance")


def _validate_capabilities(stage: dict[str, Any]) -> None:
    allowed = set(stage["allowed_capabilities"])
    denied = set(stage["denied_capabilities"])
    if allowed & denied:
        raise EmpiricalContractError("allowed and denied capabilities overlap")


def _validate_lifecycle_values(assessment_status: str, lifecycle_disposition: str) -> None:
    allowed_dispositions = {
        "active": {"active", "opaque_producer"},
        "candidate": {"active", "opaque_producer"},
        "superseded": {"superseded"},
        "invalidated": {"invalidated"},
    }
    if lifecycle_disposition not in allowed_dispositions[assessment_status]:
        raise EmpiricalContractError("assessment status and lifecycle disposition are incompatible")


def _validate_lifecycle(spec: dict[str, Any]) -> None:
    _validate_lifecycle_values(spec["assessment_status"], spec["lifecycle_disposition"])


def _require_executable_lifecycle(assessment_status: str, lifecycle_disposition: str) -> None:
    if assessment_status in {"superseded", "invalidated"} or lifecycle_disposition in {
        "superseded",
        "invalidated",
    }:
        raise EmpiricalContractError(f"{assessment_status} empirical run cannot execute stages")


def _validate_relationships(spec: dict[str, Any]) -> None:
    run_id = spec["run_id"]
    supersedes = set(spec["relationships"]["supersedes"])
    invalidates = set(spec["relationships"]["invalidates"])
    if run_id in supersedes or run_id in invalidates:
        raise EmpiricalContractError("run relationship cannot contain a self-reference")
    if supersedes & invalidates:
        raise EmpiricalContractError("supersedes and invalidates relationships overlap")


def _run_git(repository: Path, *arguments: str) -> bytes:
    try:
        completed = subprocess.run(
            ["git", "-C", str(repository), *arguments],
            check=True,
            capture_output=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError) as error:
        raise EmpiricalContractError("evidence source Git pin cannot be verified") from error
    return completed.stdout


def _repository_root(spec_path: Path) -> Path:
    try:
        output = _run_git(spec_path.parent, "rev-parse", "--show-toplevel")
    except EmpiricalContractError as error:
        raise EmpiricalContractError(
            "evidence sources require a Git repository; restricted-local payloads must remain "
            "hash-pinned referenced_artifacts"
        ) from error
    return Path(output.decode("utf-8").strip()).resolve()


def _verify_evidence_sources(spec: dict[str, Any], repository: Path) -> None:
    for source in spec["evidence_sources"]:
        relative = Path(source["path"])
        current_path = (repository / relative).resolve()
        if not current_path.is_relative_to(repository) or not current_path.is_file():
            raise EmpiricalContractError(
                "evidence source path is outside or missing from repository"
            )

        current_bytes = current_path.read_bytes()
        if len(current_bytes) != source["size_bytes"]:
            raise EmpiricalContractError("current evidence size mismatch")
        if hashlib.sha256(current_bytes).hexdigest() != source["sha256"]:
            raise EmpiricalContractError("current evidence SHA-256 mismatch")

        commit = source["git_commit"]
        _run_git(repository, "cat-file", "-e", f"{commit}^{{commit}}")
        committed_bytes = _run_git(repository, "show", f"{commit}:{relative.as_posix()}")
        if len(committed_bytes) != source["size_bytes"]:
            raise EmpiricalContractError("committed evidence size mismatch")
        if hashlib.sha256(committed_bytes).hexdigest() != source["sha256"]:
            raise EmpiricalContractError("committed evidence SHA-256 mismatch")


def validate_run_spec(spec: dict[str, Any]) -> None:
    """Validate structure, identity, evidence pins, and stage invariants."""
    _require_schema(spec, "australian-empirical-run-spec.schema.json")
    _require_self_pin(spec, "run_spec_sha256")
    if spec["canonicalization"] != CANONICALIZATION_ID:
        raise EmpiricalContractError("unsupported canonicalization")
    _validate_lifecycle(spec)
    _validate_relationships(spec)

    source_digests = {source["sha256"] for source in spec["evidence_sources"]}
    producer_source = spec["producer_provenance"]["evidence_source_sha256"]
    if producer_source not in source_digests:
        raise EmpiricalContractError("producer provenance evidence source is not pinned")
    for artifact in spec["referenced_artifacts"]:
        if artifact["evidence_source_sha256"] not in source_digests:
            raise EmpiricalContractError("referenced artifact evidence source is not pinned")

    stage_ids: set[str] = set()
    sequences: set[int] = set()
    for stage in spec["stages"]:
        if stage["stage_id"] in stage_ids:
            raise EmpiricalContractError("duplicate stage identity")
        if stage["sequence"] in sequences:
            raise EmpiricalContractError("duplicate stage sequence")
        stage_ids.add(stage["stage_id"])
        sequences.add(stage["sequence"])
        _validate_population(stage["population"])
        _validate_capabilities(stage)


def validate_stage_result(result: dict[str, Any], spec: dict[str, Any]) -> None:
    """Validate a stage result against the exact immutable run specification."""
    validate_executable_run(spec)
    _require_schema(result, "australian-empirical-stage-result.schema.json")
    _require_self_pin(result, "stage_result_sha256")
    _validate_population(result["population"])
    _validate_capabilities(result)
    if result["run_id"] != spec["run_id"] or result["run_spec_sha256"] != (spec["run_spec_sha256"]):
        raise EmpiricalContractError("stage result is bound to a different run specification")

    stages = {stage["stage_id"]: stage for stage in spec["stages"]}
    stage = stages.get(result["stage_id"])
    if stage is None:
        raise EmpiricalContractError("unknown stage identity")
    expected_stage_pin = hashlib.sha256(canonical_bytes(stage)).hexdigest()
    if result["stage_spec_sha256"] != expected_stage_pin:
        raise EmpiricalContractError("stage specification pin mismatch")
    comparisons = (
        ("stage_sequence", stage["sequence"], "stage sequence"),
        ("input_sha256", stage["input_sha256"], "stage input"),
        ("output_sha256", stage["output_sha256"], "stage output"),
        ("population", stage["population"], "stage population"),
        ("allowed_capabilities", stage["allowed_capabilities"], "allowed capabilities"),
        ("denied_capabilities", stage["denied_capabilities"], "denied capabilities"),
    )
    for field, expected, label in comparisons:
        if result[field] != expected:
            raise EmpiricalContractError(f"{label} mismatch")


def validate_executable_run(spec: dict[str, Any] | RunSpecification) -> None:
    """Validate lifecycle on a raw mapping during verified-context construction only."""
    if isinstance(spec, RunSpecification):
        raise EmpiricalContractError(
            "descriptive RunSpecification cannot execute; verified context is required"
        )
    validate_run_spec(spec)
    _require_executable_lifecycle(spec["assessment_status"], spec["lifecycle_disposition"])


def _parse_external_approval(value: dict[str, Any]) -> ExternalApprovalBinding:
    identity = AuthorityIdentity(**value["approver_identity"])
    return ExternalApprovalBinding(
        artifact_id=value["artifact_id"],
        artifact_sha256=value["artifact_sha256"],
        approved_context_sha256=value["approved_context_sha256"],
        approver_identity=identity,
    )


def parse_run_spec(spec: dict[str, Any]) -> RunSpecification:
    """Parse an untrusted mapping into an immutable run specification."""
    validate_run_spec(spec)
    sources = tuple(ArtifactPin(**source) for source in spec["evidence_sources"])
    stages = tuple(
        StageSpecification(
            stage_id=stage["stage_id"],
            sequence=stage["sequence"],
            stage_kind=stage["stage_kind"],
            population=PopulationSpecification(**stage["population"]),
        )
        for stage in spec["stages"]
    )
    raw_bindings = spec.get("authority_bindings")
    authority_bindings = (
        AuthorityBindings(
            calibration_approval=_parse_external_approval(raw_bindings["calibration_approval"]),
            execution_authorization_approval=_parse_external_approval(
                raw_bindings["execution_authorization_approval"]
            ),
        )
        if raw_bindings is not None
        else None
    )
    return RunSpecification(
        run_id=spec["run_id"],
        jurisdiction=spec["jurisdiction"],
        profile_id=spec["profile_id"],
        assessment_status=spec["assessment_status"],
        lifecycle_disposition=spec["lifecycle_disposition"],
        evidence_sources=sources,
        stages=stages,
        run_spec_sha256=spec["run_spec_sha256"],
        raw=spec,
        authority_bindings=authority_bindings,
    )


def load_run_spec(path: Path) -> RunSpecification:
    """Load one descriptive run specification and verify its evidence sources."""
    resolved = path.resolve()
    repository = _repository_root(resolved)
    try:
        current = resolved.read_bytes()
    except OSError as error:
        raise EmpiricalContractError("run specification cannot be read") from error
    value = json.loads(current.decode("utf-8"))
    if not isinstance(value, dict):
        raise EmpiricalContractError("run specification must be a JSON object")
    parsed = parse_run_spec(value)
    _verify_evidence_sources(value, repository)
    return parsed

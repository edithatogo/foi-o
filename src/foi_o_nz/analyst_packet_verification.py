"""Fail-closed verification helpers for local automated-analyst packets."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
from itertools import pairwise
from pathlib import Path, PurePosixPath
from subprocess import CalledProcessError, run
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

FORBIDDEN_CONTEXT_KEYS = frozenset({"assertion_status", "confidence"})
SCHEMA_DIR = Path(__file__).parents[2] / "schemas" / "json"
CANDIDATE_PACKET_NAMES = frozenset(
    {
        "source-population.json",
        "codebook.json",
        "sampling-configuration.json",
        "unit-manifest.json",
        "cluster-registry.json",
        "redaction-manifest.json",
        "local-rights-review.pending.json",
    }
)


@dataclass(frozen=True, slots=True)
class AnalystPacketVerificationResult:
    """Verified pre-execution packet facts; never a promotion decision."""

    repository_commit: str
    authorization_sha256: str
    unit_count: int
    cluster_count: int
    redacted_context_count: int
    source_counts: dict[str, int]
    execution_allowed: bool


@dataclass(frozen=True, slots=True)
class ApprovedFixtureInputsVerificationResult:
    """Verified approved inputs; never an execution authorization."""

    base_readiness_sha256: str
    approval_sha256: str
    approved_input_readiness_sha256: str
    unit_count: int
    execution_allowed: bool = False


@dataclass(frozen=True, slots=True)
class FixtureRoleAuthorizationRequestVerificationResult:
    """Verified preparation evidence that cannot authorize execution."""

    request_sha256: str
    preparation_commit: str
    role_count: int
    context_count: int
    execution_allowed: bool = False


@dataclass(frozen=True, slots=True)
class FixtureRuntimeHandshakeAuthorizationVerificationResult:
    """Verified authorization for provenance handshakes only, never analysis."""

    authorization_sha256: str
    repository_commit: str
    request_sha256: str
    role_count: int
    runtime_handshake_allowed: bool = True
    context_presentation_allowed: bool = False
    analysis_execution_allowed: bool = False
    reconciliation_allowed: bool = False


@dataclass(frozen=True, slots=True)
class FixtureRuntimeHandshakeEvidenceVerificationResult:
    """Verified four-role handshake evidence that cannot authorize analysis."""

    bundle_sha256: str
    repository_commit: str
    authorization_sha256: str
    role_count: int
    runtime_handshakes_complete: bool = True
    execution_allowed: bool = False


@dataclass(frozen=True, slots=True)
class FixtureExecutionAuthorizationCandidateVerificationResult:
    """Verified inert v0.2 candidate that is not an execution authorization."""

    candidate_sha256: str
    repository_commit: str
    handshake_evidence_sha256: str
    role_count: int
    human_approval_present: bool = False
    authorization_effective: bool = False
    execution_allowed: bool = False


@dataclass(frozen=True, slots=True)
class FixturePreExecutionVerificationResult:
    """Effective bounded permission emitted only after exact pre-execution verification."""

    authorization_sha256: str
    repository_commit: str
    candidate_sha256: str
    role_count: int
    context_presentation_allowed: bool = True
    analysis_execution_allowed: bool = True
    reconciliation_allowed: bool = False
    execution_allowed: bool = True


@dataclass(frozen=True, slots=True)
class DerivedFixtureUnit:
    """A source-derived fixture unit; never an empirical or gold assertion."""

    unit_id: str
    source_path: str
    source_span: tuple[int, int]
    source_artifact_sha256: str
    unit_sha256: str
    context_sha256: str
    observed_date: str
    request_linkage_group: str
    removed_keys: tuple[str, ...]


def ordered_unit_commitment(unit_sha256_values: list[str]) -> str:
    """Hash unit digests in declared source order with an explicit final newline."""
    if not unit_sha256_values or any(
        len(value) != 64 or any(character not in "0123456789abcdef" for character in value)
        for value in unit_sha256_values
    ):
        raise ValueError("ordered commitment requires lowercase SHA-256 values")
    encoded = ("\n".join(unit_sha256_values) + "\n").encode("ascii")
    return sha256(encoded).hexdigest()


def canonical_redacted_context(value: dict[str, Any]) -> tuple[bytes, tuple[str, ...]]:
    """Recursively remove forbidden keys and return canonical JSON bytes."""
    removed: set[str] = set()

    def redact(item: Any) -> Any:
        if isinstance(item, dict):
            result: dict[str, Any] = {}
            for key, child in item.items():
                if key in FORBIDDEN_CONTEXT_KEYS:
                    removed.add(key)
                else:
                    result[key] = redact(child)
            return result
        if isinstance(item, list):
            return [redact(child) for child in item]
        return item

    redacted = redact(value)
    encoded = json.dumps(
        redacted,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return encoded, tuple(sorted(removed))


def _derived_unit(
    *,
    unit_id: str,
    source_path: str,
    source_bytes: bytes,
    source_text: str,
    start: int,
    end: int,
    value: dict[str, Any],
) -> DerivedFixtureUnit:
    raw_text = source_text[start:end]
    if json.loads(raw_text) != value:
        raise ValueError(f"{unit_id}: source span does not match parsed event")
    context, removed = canonical_redacted_context(value)
    request_id = value.get("request_ref", {}).get("source_request_id") or value.get("request_id")
    if not isinstance(request_id, str) or not request_id:
        raise ValueError(f"{unit_id}: request linkage missing")
    event_time = value.get("event_time")
    if not isinstance(event_time, str) or len(event_time) < 10:
        raise ValueError(f"{unit_id}: observed date missing")
    return DerivedFixtureUnit(
        unit_id=unit_id,
        source_path=source_path,
        source_span=(start, end),
        source_artifact_sha256=sha256(source_bytes).hexdigest(),
        unit_sha256=sha256(raw_text.encode("utf-8")).hexdigest(),
        context_sha256=sha256(context).hexdigest(),
        observed_date=event_time[:10],
        request_linkage_group=f"fixture:{request_id}",
        removed_keys=removed,
    )


def derive_fixture_units(repository_root: Path) -> list[DerivedFixtureUnit]:
    """Derive the exact 9+2 local engineering-fixture census from source text."""
    root = repository_root.resolve(strict=True)
    process_relative = "examples/process-mining-events.fixture.jsonl"
    timeline_relative = "examples/event-timeline.small.json"
    process_path = resolve_repo_artifact(root, process_relative)
    timeline_path = resolve_repo_artifact(root, timeline_relative)
    units: list[DerivedFixtureUnit] = []

    process_bytes = process_path.read_bytes()
    process_text = process_bytes.decode("utf-8")
    offset = 0
    records = process_text.splitlines(keepends=True)
    if len(records) != 9 or any(not line.strip() for line in records):
        raise ValueError("process fixture must contain exactly nine nonblank records")
    for index, line in enumerate(records, 1):
        raw = line.removesuffix("\n").removesuffix("\r")
        start, end = offset, offset + len(raw)
        value = json.loads(raw)
        if not isinstance(value, dict):
            raise ValueError("process fixture record is not an object")
        units.append(
            _derived_unit(
                unit_id=f"pm-{index:02d}",
                source_path=process_relative,
                source_bytes=process_bytes,
                source_text=process_text,
                start=start,
                end=end,
                value=value,
            )
        )
        offset += len(line)

    timeline_bytes = timeline_path.read_bytes()
    timeline_text = timeline_bytes.decode("utf-8")
    timeline = json.loads(timeline_text)
    events = timeline.get("events")
    if timeline.get("event_count") != 2 or not isinstance(events, list) or len(events) != 2:
        raise ValueError("timeline fixture must contain exactly two events")
    search_from = timeline_text.index('"events"')
    decoder = json.JSONDecoder()
    for index, expected in enumerate(events, 1):
        start = timeline_text.index("{", search_from)
        value, length = decoder.raw_decode(timeline_text[start:])
        if value != expected or not isinstance(value, dict):
            raise ValueError("timeline lexical event does not match parsed event")
        end = start + length
        units.append(
            _derived_unit(
                unit_id=f"tl-{index:02d}",
                source_path=timeline_relative,
                source_bytes=timeline_bytes,
                source_text=timeline_text,
                start=start,
                end=end,
                value=value,
            )
        )
        search_from = end
    return units


def verify_fixture_manifests(
    derived_units: list[DerivedFixtureUnit],
    unit_manifest: dict[str, Any],
    redaction_manifest: dict[str, Any],
    cluster_registry: dict[str, Any],
) -> None:
    """Cross-check the exact 11-unit census, redaction, and cluster bijections."""
    if len(derived_units) != 11:
        raise ValueError("derived fixture census must contain exactly 11 units")
    manifest_units = unit_manifest["units"]
    if len(manifest_units) != 11:
        raise ValueError("unit manifest must contain exactly 11 units")
    expected_commitment = ordered_unit_commitment([unit.unit_sha256 for unit in derived_units])
    if (
        unit_manifest["ordered_unit_commitment_algorithm"]
        != "sha256_lowercase_hex_lines_final_newline_v1"
    ):
        raise ValueError("ordered unit commitment algorithm mismatch")
    if unit_manifest["ordered_unit_commitment_sha256"] != expected_commitment:
        raise ValueError("ordered unit commitment mismatch")

    expected_by_id = {unit.unit_id: unit for unit in derived_units}
    if len(expected_by_id) != 11 or {unit["unit_id"] for unit in manifest_units} != set(
        expected_by_id
    ):
        raise ValueError("unit manifest membership mismatch")
    seen_raw: set[str] = set()
    seen_context: set[str] = set()
    for manifest_unit in manifest_units:
        expected = expected_by_id[manifest_unit["unit_id"]]
        actual_span = manifest_unit["source_span"]
        comparisons = {
            "source_path": expected.source_path,
            "source_artifact_sha256": expected.source_artifact_sha256,
            "unit_sha256": expected.unit_sha256,
            "context_sha256": expected.context_sha256,
            "observed_date": expected.observed_date,
            "request_linkage_group": expected.request_linkage_group,
            "duplicate_cluster_id": f"exact:{expected.context_sha256}",
            "split": "annotation_only",
            "inclusion_probability": 1.0,
            "sampling_weight": 1.0,
            "rights_eligible_for_local_use": True,
        }
        if any(manifest_unit.get(key) != value for key, value in comparisons.items()):
            raise ValueError(f"{expected.unit_id}: unit manifest value mismatch")
        if (actual_span["start"], actual_span["end"]) != expected.source_span:
            raise ValueError(f"{expected.unit_id}: source span mismatch")
        if expected.unit_sha256 in seen_raw or expected.context_sha256 in seen_context:
            raise ValueError("unit or context digest is not unique")
        seen_raw.add(expected.unit_sha256)
        seen_context.add(expected.context_sha256)

    entries = redaction_manifest["entries"]
    if len(entries) != 11 or {entry["unit_id"] for entry in entries} != set(expected_by_id):
        raise ValueError("redaction manifest membership mismatch")
    for entry in entries:
        expected = expected_by_id[entry["unit_id"]]
        if (
            entry["unit_sha256"] != expected.unit_sha256
            or entry["context_sha256"] != expected.context_sha256
            or tuple(entry["removed_keys"]) != expected.removed_keys
            or entry["forbidden_keys_absent"] is not True
        ):
            raise ValueError(f"{expected.unit_id}: redaction evidence mismatch")

    clusters = cluster_registry["clusters"]
    if len(clusters) != 11 or any(len(cluster["member_unit_sha256"]) != 1 for cluster in clusters):
        raise ValueError("clusters must be singleton and total 11")
    members = [cluster["member_unit_sha256"][0] for cluster in clusters]
    if len(set(members)) != 11 or set(members) != seen_raw:
        raise ValueError("cluster membership is not an exact unit bijection")
    context_by_raw = {unit.unit_sha256: unit.context_sha256 for unit in derived_units}
    for cluster in clusters:
        member = cluster["member_unit_sha256"][0]
        if (
            cluster["cluster_id"] != f"exact:{context_by_raw[member]}"
            or cluster["split"] != "annotation_only"
        ):
            raise ValueError("cluster identifier or split mismatch")


def resolve_repo_artifact(repository_root: Path, relative_path: str) -> Path:
    """Resolve a regular artifact beneath a repository without path escape."""
    pure_path = PurePosixPath(relative_path)
    if (
        not relative_path
        or pure_path.is_absolute()
        or "." in pure_path.parts
        or ".." in pure_path.parts
        or "\\" in relative_path
        or "\x00" in relative_path
    ):
        raise ValueError("unsafe repository-relative path")

    root = repository_root.resolve(strict=True)
    candidate = (root / Path(*pure_path.parts)).resolve(strict=True)
    if root not in candidate.parents:
        raise ValueError("artifact escapes repository root")
    if not candidate.is_file():
        raise ValueError("artifact is not a regular file")
    return candidate


def verify_authorized_actor_separation(authorization: dict[str, Any]) -> None:
    """Require distinct actor identities and isolated sessions for all three roles."""
    actors = [*authorization["analysts"], authorization["reconciler"]]
    actor_ids = [actor["actor_id"] for actor in actors]
    session_ids = [actor["runtime"]["session_id"] for actor in actors]
    if len(set(actor_ids)) != 3:
        raise ValueError("actor identities are not distinct")
    if len(set(session_ids)) != 3:
        raise ValueError("actor sessions are not distinct")


def verify_git_anchor(
    repository_root: Path,
    expected_repository_commit: str,
    artifact_paths: list[Path],
) -> None:
    """Require a Git HEAD anchor and tracked artifacts identical to that commit."""
    root = repository_root.resolve(strict=True)
    top_level = run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if Path(top_level).resolve() != root:
        raise ValueError("repository root is not the Git top level")
    head = run(
        ["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True
    ).stdout.strip()
    if head != expected_repository_commit:
        raise ValueError("repository commit mismatch")

    for artifact in artifact_paths:
        resolved = artifact.resolve(strict=True)
        if root not in resolved.parents or not resolved.is_file():
            raise ValueError("anchored artifact escapes repository root")
        relative = resolved.relative_to(root).as_posix()
        try:
            run(
                ["git", "ls-files", "--error-unmatch", "--", relative],
                cwd=root,
                check=True,
                capture_output=True,
            )
            committed = run(
                ["git", "show", f"{expected_repository_commit}:{relative}"],
                cwd=root,
                check=True,
                capture_output=True,
            ).stdout
        except CalledProcessError as error:
            raise ValueError(f"{relative}: not tracked at anchored commit") from error
        if committed != resolved.read_bytes():
            raise ValueError(f"{relative}: differs from anchored commit")


def verify_git_artifacts_at_commit(
    repository_root: Path, expected_repository_commit: str, artifact_paths: list[Path]
) -> None:
    """Match current artifact bytes to a historical commit without requiring HEAD."""
    root = repository_root.resolve(strict=True)
    for artifact in artifact_paths:
        resolved = artifact.resolve(strict=True)
        if root not in resolved.parents or not resolved.is_file():
            raise ValueError("historical artifact escapes repository root")
        relative = resolved.relative_to(root).as_posix()
        try:
            committed = run(
                ["git", "show", f"{expected_repository_commit}:{relative}"],
                cwd=root,
                check=True,
                capture_output=True,
            ).stdout
        except CalledProcessError as error:
            raise ValueError(f"{relative}: not present at base commit") from error
        if committed != resolved.read_bytes():
            raise ValueError(f"{relative}: differs from base commit")


def _load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path.name}: expected JSON object")
    return value


def _validate_object(value: dict[str, Any], schema_name: str, label: str) -> None:
    schema = _load_object(SCHEMA_DIR / schema_name)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(value), key=lambda error: list(error.absolute_path))
    if errors:
        location = ".".join(str(part) for part in errors[0].absolute_path) or "<root>"
        raise ValueError(f"{label}.{location}: {errors[0].message}")


def _without(value: dict[str, Any], names: set[str]) -> dict[str, Any]:
    return {key: child for key, child in value.items() if key not in names}


def verify_approved_fixture_inputs(
    *,
    repository_root: Path,
    packet_dir: Path,
    expected_approval_sha256: str,
    expected_approved_input_readiness_sha256: str,
    expected_base_repository_commit: str,
    expected_promotion_repository_commit: str,
) -> ApprovedFixtureInputsVerificationResult:
    """Verify the deterministic input promotion while keeping execution disabled."""
    root = repository_root.resolve(strict=True)
    packet = packet_dir.resolve(strict=True)
    if root not in packet.parents:
        raise ValueError("approved-input packet escapes repository root")

    names = {
        "candidate_readiness": "readiness.json",
        "candidate_source_population": "source-population.json",
        "candidate_rights": "local-rights-review.pending.json",
        "candidate_codebook": "codebook.json",
        "candidate_sampling": "sampling-configuration.json",
        "candidate_units": "unit-manifest.json",
        "candidate_clusters": "cluster-registry.json",
        "candidate_redaction": "redaction-manifest.json",
        "approval": "input-approval.approved.json",
        "rights": "local-rights-review.approved.json",
        "codebook": "codebook.approved.json",
        "sampling": "sampling-configuration.approved.json",
        "units": "unit-manifest.rights-approved.json",
        "clusters": "cluster-registry.rights-approved.json",
        "approved_readiness": "input-readiness.approved.json",
    }
    paths = {role: packet / name for role, name in names.items()}
    values = {role: _load_object(path) for role, path in paths.items()}

    candidate_schemas = {
        "candidate_readiness": "analyst-fixture-readiness.schema.json",
        "candidate_source_population": "analyst-fixture-source-population.schema.json",
        "candidate_rights": "analyst-local-rights-review.schema.json",
        "candidate_codebook": "analyst-fixture-codebook.schema.json",
        "candidate_sampling": "sampling-configuration.schema.json",
        "candidate_units": "analyst-fixture-unit-manifest.schema.json",
        "candidate_clusters": "analyst-fixture-cluster-registry.schema.json",
        "candidate_redaction": "analyst-redaction-manifest.schema.json",
    }
    for role, schema in candidate_schemas.items():
        _validate_object(values[role], schema, role)

    if sha256(paths["candidate_readiness"].read_bytes()).hexdigest() != (
        "de4bdf129f433373b1287c78867db51b1874bd33476dd2229e0710dfc25e03bd"
    ):
        raise ValueError("approved base readiness SHA-256 mismatch")
    if sha256(paths["approval"].read_bytes()).hexdigest() != expected_approval_sha256:
        raise ValueError("input approval SHA-256 mismatch")
    if (
        sha256(paths["approved_readiness"].read_bytes()).hexdigest()
        != expected_approved_input_readiness_sha256
    ):
        raise ValueError("approved-input readiness SHA-256 mismatch")

    schemas = {
        "approval": "analyst-fixture-input-approval.schema.json",
        "rights": "analyst-approved-local-rights-review.schema.json",
        "codebook": "analyst-approved-fixture-codebook.schema.json",
        "sampling": "analyst-approved-sampling-configuration.schema.json",
        "units": "analyst-fixture-unit-manifest.schema.json",
        "clusters": "analyst-fixture-cluster-registry.schema.json",
        "approved_readiness": "analyst-fixture-approved-input-readiness.schema.json",
    }
    for role, schema in schemas.items():
        _validate_object(values[role], schema, role)

    approval = values["approval"]
    statement_digest = sha256(approval["approval_statement"].encode("utf-8")).hexdigest()
    if approval["approval_statement_sha256"] != statement_digest:
        raise ValueError("approval statement SHA-256 mismatch")
    if approval["approved_repository_commit"] != expected_base_repository_commit:
        raise ValueError("approval base repository commit mismatch")
    if approval["execution_allowed"] is not False:
        raise ValueError("input approval cannot authorize execution")

    candidate_rights = values["candidate_rights"]
    rights = values["rights"]
    if _without(
        rights,
        {
            "schema_version",
            "status",
            "local_analysis_allowed",
            "approved_by",
            "approved_on",
            "recorded_at",
        },
    ) != _without(
        candidate_rights,
        {"schema_version", "status", "local_analysis_allowed", "approved_by", "approved_at"},
    ):
        raise ValueError("approved rights transition changed candidate content")

    candidate_codebook = values["candidate_codebook"]
    codebook = values["codebook"]
    if _without(
        codebook, {"schema_version", "status", "approved_by", "approved_on", "recorded_at"}
    ) != _without(candidate_codebook, {"schema_version", "status", "approved_by", "approved_at"}):
        raise ValueError("approved codebook transition changed candidate content")

    candidate_sampling = values["candidate_sampling"]
    sampling = values["sampling"]
    if _without(
        sampling, {"schema_version", "status", "approved_by", "approved_on", "recorded_at"}
    ) != _without(candidate_sampling, {"schema_version", "status", "approved_by", "approved_at"}):
        raise ValueError("approved sampling transition changed candidate content")

    candidate_units = values["candidate_units"]
    units = values["units"]
    expected_units = json.loads(json.dumps(candidate_units))
    expected_units["locked_at"] = approval["recorded_at"]
    for unit in expected_units["units"]:
        if unit["rights_eligible_for_local_use"] is not False:
            raise ValueError("candidate unit rights must be false")
        unit["rights_eligible_for_local_use"] = True
    if units != expected_units:
        raise ValueError("approved unit transition changed non-rights content")

    candidate_clusters = values["candidate_clusters"]
    clusters = values["clusters"]
    expected_clusters = dict(candidate_clusters)
    expected_clusters["unit_manifest_sha256"] = sha256(paths["units"].read_bytes()).hexdigest()
    expected_clusters["locked_at"] = approval["recorded_at"]
    if clusters != expected_clusters:
        raise ValueError("approved cluster transition changed non-pin content")

    readiness = values["approved_readiness"]
    if readiness["base_readiness"]["repository_commit"] != expected_base_repository_commit:
        raise ValueError("approved readiness base commit mismatch")
    if readiness["execution_allowed"] is not False:
        raise ValueError("approved inputs cannot authorize execution")
    expected_pins = {
        "input_approval": paths["approval"],
        "local_rights_review": paths["rights"],
        "codebook": paths["codebook"],
        "sampling_configuration": paths["sampling"],
        "unit_manifest": paths["units"],
        "duplicate_cluster_registry": paths["clusters"],
    }
    for role, path in expected_pins.items():
        pin = readiness["approved_artifacts"][role]
        relative = path.relative_to(root).as_posix()
        if pin["path"] != relative or pin["sha256"] != sha256(path.read_bytes()).hexdigest():
            raise ValueError(f"approved readiness {role} pin mismatch")
    unchanged = {
        "protocol": root / "docs/42-v2-analyst-execution-protocol.md",
        "source_population": packet / "source-population.json",
        "redaction_manifest": packet / "redaction-manifest.json",
    }
    for role, path in unchanged.items():
        pin = readiness["unchanged_artifacts"][role]
        if (
            pin["path"] != path.relative_to(root).as_posix()
            or pin["sha256"] != sha256(path.read_bytes()).hexdigest()
        ):
            raise ValueError(f"approved readiness {role} pin mismatch")

    candidate_readiness = values["candidate_readiness"]
    if candidate_readiness["protocol"] != {
        "path": "docs/42-v2-analyst-execution-protocol.md",
        "sha256": sha256(unchanged["protocol"].read_bytes()).hexdigest(),
    }:
        raise ValueError("candidate readiness protocol pin mismatch")
    declared = {pin["path"]: pin["sha256"] for pin in candidate_readiness["artifacts"]}
    candidate_paths = [packet / name for name in names.values() if name in CANDIDATE_PACKET_NAMES]
    expected_declared = {
        path.relative_to(root).as_posix(): sha256(path.read_bytes()).hexdigest()
        for path in candidate_paths
    }
    if declared != expected_declared:
        raise ValueError("candidate readiness artifact pins mismatch")

    historical_paths = [
        paths["candidate_readiness"],
        *candidate_paths,
        unchanged["protocol"],
        root / "examples/process-mining-events.fixture.jsonl",
        root / "examples/event-timeline.small.json",
        root / "LICENSE.md",
    ]
    verify_git_artifacts_at_commit(root, expected_base_repository_commit, historical_paths)
    final_paths = [paths["approved_readiness"], *expected_pins.values(), *unchanged.values()]
    verify_git_artifacts_at_commit(root, expected_promotion_repository_commit, final_paths)

    return ApprovedFixtureInputsVerificationResult(
        base_readiness_sha256=readiness["base_readiness"]["sha256"],
        approval_sha256=expected_approval_sha256,
        approved_input_readiness_sha256=expected_approved_input_readiness_sha256,
        unit_count=len(units["units"]),
    )


def _instant(value: str, label: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise ValueError(f"{label}: timezone required")
    return parsed


def _contains_forbidden_context_key(value: Any) -> bool:
    if isinstance(value, dict):
        return any(
            key in FORBIDDEN_CONTEXT_KEYS or _contains_forbidden_context_key(child)
            for key, child in value.items()
        )
    if isinstance(value, list):
        return any(_contains_forbidden_context_key(child) for child in value)
    return False


def _verify_fixture_role_authorization_request(
    *,
    repository_root: Path,
    request_path: Path,
    expected_request_sha256: str,
    expected_preparation_repository_commit: str,
    expected_base_repository_commit: str,
    expected_promotion_repository_commit: str,
    require_head_anchor: bool,
) -> FixtureRoleAuthorizationRequestVerificationResult:
    root = repository_root.resolve(strict=True)
    request = request_path.resolve(strict=True)
    if root not in request.parents:
        raise ValueError("role authorization request escapes repository root")
    request_digest = sha256(request.read_bytes()).hexdigest()
    if request_digest != expected_request_sha256:
        raise ValueError("role authorization request SHA-256 mismatch")
    document = _load_object(request)
    _validate_object(
        document, "fixture-role-authorization-request.schema.json", "role_authorization_request"
    )
    if document["execution_allowed"] is not False:
        raise ValueError("pending role authorization request cannot enable execution")

    paths: dict[str, Path] = {"request": request}

    def resolve_pin(label: str, pin: dict[str, Any]) -> Path:
        path = resolve_repo_artifact(root, pin["path"])
        if sha256(path.read_bytes()).hexdigest() != pin["sha256"]:
            raise ValueError(f"{label}: SHA-256 mismatch")
        paths[label] = path
        return path

    readiness_path = resolve_pin("approved_input_readiness", document["approved_input_readiness"])
    readiness = _load_object(readiness_path)
    verify_approved_fixture_inputs(
        repository_root=root,
        packet_dir=readiness_path.parent,
        expected_approval_sha256=readiness["approved_artifacts"]["input_approval"]["sha256"],
        expected_approved_input_readiness_sha256=document["approved_input_readiness"]["sha256"],
        expected_base_repository_commit=expected_base_repository_commit,
        expected_promotion_repository_commit=expected_promotion_repository_commit,
    )

    handshake = resolve_pin("handshake_prompt", document["handshake_prompt"])
    if sha256(handshake.read_bytes()).hexdigest() != (
        "6fb5386e21364f172289d563c17b7c93ea17b7a2eea454ff1affa8767d1bea77"
    ):
        raise ValueError("handshake_prompt: not the canonical governed prompt")
    role_values: dict[str, dict[str, Any]] = {}
    expected_roles = {
        "orchestrator": (
            "agent:orchestrator-fixture-stream",
            "orchestrator_non_labeling",
            "/root/fixture_stream_ready",
            False,
            "c817ee25c74ea08ebdecf28ad52d126bbc6e8debfd3a9d32f7c8f02c3571112a",
        ),
        "analyst_a": (
            "agent:analyst-fixture-a",
            "analyst",
            "/root/fixture_analyst_a_ready",
            True,
            "ab8cd28ea7b98eae235069555ef5d239ef47d6b8ca1fe1ee6715e67d0f045908",
        ),
        "analyst_b": (
            "agent:analyst-fixture-b",
            "analyst",
            "/root/fixture_analyst_b_ready",
            True,
            "3bcb3b37c8d3a19e51a152c0b72aee82dba088bf822aa8cdc299cbbf029dfb6a",
        ),
        "reconciler": (
            "agent:reconciler-fixture",
            "reconciler",
            "/root/fixture_reconciler_ready",
            False,
            "80770f3b4335b7fb5b092a96265e41cef29f0c26081ae46afc9949b220661081",
        ),
    }
    for name, (actor_id, role, locator, may_label, prompt_sha256) in expected_roles.items():
        prompt_path = resolve_pin(
            f"future_execution_prompt.{name}", document["future_execution_prompts"][name]
        )
        if sha256(prompt_path.read_bytes()).hexdigest() != prompt_sha256:
            raise ValueError(f"future_execution_prompt.{name}: not the canonical governed prompt")
        provenance_path = resolve_pin(f"role_provenance.{name}", document["role_provenance"][name])
        value = _load_object(provenance_path)
        _validate_object(value, "fixture-role-provenance.schema.json", f"role_provenance.{name}")
        if (
            value["actor_id"] != actor_id
            or value["role"] != role
            or value["canonical_session_locator"] != locator
            or value["may_label"] is not may_label
            or value["handshake_prompt"] != document["handshake_prompt"]
            or value["future_execution_prompt"] != document["future_execution_prompts"][name]
            or value["handshake_completed"] is not False
            or value["execution_allowed"] is not False
        ):
            raise ValueError(f"role_provenance.{name}: role or prompt alignment mismatch")
        if value["runtime"] != {
            "provider_family": None,
            "model_runtime_family": None,
            "exact_snapshot_available": False,
            "exact_snapshot": None,
        }:
            raise ValueError(f"role_provenance.{name}: runtime must remain unavailable")
        role_values[name] = value
        paths[f"future_execution_prompt.{name}"] = prompt_path
    if (
        len({value["actor_id"] for value in role_values.values()}) != 4
        or len({value["canonical_session_locator"] for value in role_values.values()}) != 4
    ):
        raise ValueError("role actors and locators must be unique")

    isolation_path = resolve_pin("isolation_plan", document["isolation_plan"])
    _validate_object(
        _load_object(isolation_path), "fixture-role-isolation-plan.schema.json", "isolation_plan"
    )
    context_path = resolve_pin("context_presentation", document["context_presentation"])
    context_document = _load_object(context_path)
    _validate_object(
        context_document, "fixture-context-presentation.schema.json", "context_presentation"
    )
    expected_contexts = []
    for unit in derive_fixture_units(root):
        source_text = resolve_repo_artifact(root, unit.source_path).read_text(encoding="utf-8")
        value = json.loads(source_text[unit.source_span[0] : unit.source_span[1]])
        encoded, removed = canonical_redacted_context(value)
        presented = json.loads(encoded)
        if _contains_forbidden_context_key(presented):
            raise ValueError(f"{unit.unit_id}: forbidden context key remains")
        expected_contexts.append(
            {
                "unit_id": unit.unit_id,
                "unit_sha256": unit.unit_sha256,
                "context_sha256": unit.context_sha256,
                "source_path": unit.source_path,
                "source_span": {"start": unit.source_span[0], "end": unit.source_span[1]},
                "removed_keys": list(removed),
                "presented_context": presented,
            }
        )
    if context_document["contexts"] != expected_contexts:
        raise ValueError("context presentation is not the exact ordered redacted census")
    if handshake.read_bytes() == b"":
        raise ValueError("handshake prompt is empty")

    if require_head_anchor:
        verify_git_anchor(root, expected_preparation_repository_commit, list(paths.values()))
    else:
        verify_git_artifacts_at_commit(
            root, expected_preparation_repository_commit, list(paths.values())
        )
    return FixtureRoleAuthorizationRequestVerificationResult(
        request_sha256=request_digest,
        preparation_commit=expected_preparation_repository_commit,
        role_count=4,
        context_count=11,
    )


def verify_fixture_role_authorization_request(
    *,
    repository_root: Path,
    request_path: Path,
    expected_request_sha256: str,
    expected_preparation_repository_commit: str,
    expected_base_repository_commit: str,
    expected_promotion_repository_commit: str,
) -> FixtureRoleAuthorizationRequestVerificationResult:
    """Verify pending role preparation at the exact repository HEAD."""
    return _verify_fixture_role_authorization_request(
        repository_root=repository_root,
        request_path=request_path,
        expected_request_sha256=expected_request_sha256,
        expected_preparation_repository_commit=expected_preparation_repository_commit,
        expected_base_repository_commit=expected_base_repository_commit,
        expected_promotion_repository_commit=expected_promotion_repository_commit,
        require_head_anchor=True,
    )


def _verify_commit_ancestry(repository_root: Path, commits: list[str]) -> None:
    """Require each commit to be an ancestor of the next declared commit."""
    root = repository_root.resolve(strict=True)
    for ancestor, descendant in pairwise(commits):
        try:
            run(
                ["git", "merge-base", "--is-ancestor", ancestor, descendant],
                cwd=root,
                check=True,
                capture_output=True,
            )
        except CalledProcessError as error:
            raise ValueError("fixture authorization commit ancestry mismatch") from error


def _verify_fixture_runtime_handshake_authorization(
    *,
    repository_root: Path,
    authorization_path: Path,
    expected_authorization_sha256: str,
    expected_repository_commit: str,
    expected_request_sha256: str,
    expected_preparation_repository_commit: str,
    expected_base_repository_commit: str,
    expected_promotion_repository_commit: str,
    require_head_anchor: bool,
) -> FixtureRuntimeHandshakeAuthorizationVerificationResult:
    root = repository_root.resolve(strict=True)
    authorization = authorization_path.resolve(strict=True)
    if root not in authorization.parents:
        raise ValueError("runtime handshake authorization escapes repository root")
    authorization_digest = sha256(authorization.read_bytes()).hexdigest()
    if authorization_digest != expected_authorization_sha256:
        raise ValueError("runtime handshake authorization SHA-256 mismatch")
    document = _load_object(authorization)
    _validate_object(
        document,
        "fixture-runtime-handshake-authorization.schema.json",
        "runtime_handshake_authorization",
    )

    if document["preparation_commit"] != expected_preparation_repository_commit:
        raise ValueError("runtime handshake preparation commit mismatch")
    if document["request"]["sha256"] != expected_request_sha256:
        raise ValueError("runtime handshake request SHA-256 mismatch")
    expected_prohibitions = [
        "redistribution",
        "publication",
        "training",
        "fine_tuning",
        "release",
        "dataset_publication",
        "gold_promotion",
        "legal_certification",
        "paper_update",
        "human_reviewed_claims",
        "empirical_evidence_claims",
    ]
    if document["prohibited_actions"] != expected_prohibitions:
        raise ValueError("runtime handshake prohibitions are not exact")
    if (
        document["runtime_handshake_allowed"] is not True
        or document["context_presentation_allowed"] is not False
        or document["analysis_execution_allowed"] is not False
        or document["reconciliation_allowed"] is not False
        or document["final_execution_wrapper_required"] is not True
        or document["local_only"] is not True
        or any(
            document[key] is not False
            for key in (
                "empirical_evidence",
                "human_reviewed",
                "gold_eligible",
                "release_qualifying",
                "publication_eligible",
            )
        )
    ):
        raise ValueError("runtime handshake authorization enables a prohibited state")

    paths: dict[str, Path] = {"authorization": authorization}

    def resolve_pin(label: str, pin: dict[str, Any]) -> Path:
        path = resolve_repo_artifact(root, pin["path"])
        if sha256(path.read_bytes()).hexdigest() != pin["sha256"]:
            raise ValueError(f"{label}: SHA-256 mismatch")
        paths[label] = path
        return path

    request_path = resolve_pin("request", document["request"])
    request = _load_object(request_path)
    approval_path = resolve_pin("approval_review", document["approval_review"])
    approval = _load_object(approval_path)
    _validate_object(approval, "fixture-role-authorization-approval.schema.json", "approval_review")
    expected_statement = (
        "I, edithatogo, approve pending fixture role-authorization request SHA-256 "
        "232396d06812e6158a86aec38454d7e3ea8484ed906bf510c39976993c29a98c "
        "as committed in 91013a0f69d3a376ec749bbad83902e7ac4dd2a7 for the bounded "
        "local fixture analyst execution described by that exact request. This approval "
        "authorizes creation of the final execution wrapper and subsequent execution only "
        "after that wrapper is committed and the pre-execution verifier passes against its "
        "exact SHA-256 and commit. Redistribution, publication, training, fine-tuning, "
        "release, dataset publication, gold promotion, legal certification, paper updates, "
        "human-reviewed claims, and empirical-evidence claims remain prohibited."
    )
    if (
        approval["approval_statement"] != expected_statement
        or approval["approval_statement_sha256"]
        != sha256(expected_statement.encode("utf-8")).hexdigest()
        or approval["approved_request"] != document["request"]
        or approval["approved_repository_commit"] != expected_preparation_repository_commit
        or approval["handshake_approved"] is not True
        or approval["context_delivery_approved"] is not False
        or approval["analyst_execution_approved"] is not False
        or approval["execution_allowed"] is not False
        or approval["final_execution_wrapper_required"] is not True
        or approval["prohibited_actions"] != expected_prohibitions
    ):
        raise ValueError("approval review does not preserve the exact bounded approval")

    for key in (
        "approved_input_readiness",
        "handshake_prompt",
        "future_execution_prompts",
        "role_provenance",
        "context_presentation",
        "isolation_plan",
    ):
        if document[key] != request[key]:
            raise ValueError(f"{key}: differs from the approved pending request")

    _verify_commit_ancestry(
        root,
        [
            expected_base_repository_commit,
            expected_promotion_repository_commit,
            expected_preparation_repository_commit,
            expected_repository_commit,
        ],
    )
    _verify_fixture_role_authorization_request(
        repository_root=root,
        request_path=request_path,
        expected_request_sha256=expected_request_sha256,
        expected_preparation_repository_commit=expected_preparation_repository_commit,
        expected_base_repository_commit=expected_base_repository_commit,
        expected_promotion_repository_commit=expected_promotion_repository_commit,
        require_head_anchor=False,
    )
    if require_head_anchor:
        verify_git_anchor(root, expected_repository_commit, [authorization, approval_path])
    else:
        verify_git_artifacts_at_commit(
            root, expected_repository_commit, [authorization, approval_path]
        )
    return FixtureRuntimeHandshakeAuthorizationVerificationResult(
        authorization_sha256=authorization_digest,
        repository_commit=expected_repository_commit,
        request_sha256=expected_request_sha256,
        role_count=4,
    )


def verify_fixture_runtime_handshake_authorization(
    *,
    repository_root: Path,
    authorization_path: Path,
    expected_authorization_sha256: str,
    expected_repository_commit: str,
    expected_request_sha256: str,
    expected_preparation_repository_commit: str,
    expected_base_repository_commit: str,
    expected_promotion_repository_commit: str,
) -> FixtureRuntimeHandshakeAuthorizationVerificationResult:
    """Verify the committed gate that permits only runtime-provenance handshakes."""
    return _verify_fixture_runtime_handshake_authorization(
        repository_root=repository_root,
        authorization_path=authorization_path,
        expected_authorization_sha256=expected_authorization_sha256,
        expected_repository_commit=expected_repository_commit,
        expected_request_sha256=expected_request_sha256,
        expected_preparation_repository_commit=expected_preparation_repository_commit,
        expected_base_repository_commit=expected_base_repository_commit,
        expected_promotion_repository_commit=expected_promotion_repository_commit,
        require_head_anchor=True,
    )


def _verify_fixture_runtime_handshake_evidence(
    *,
    repository_root: Path,
    bundle_path: Path,
    expected_bundle_sha256: str,
    expected_repository_commit: str,
    expected_authorization_sha256: str,
    expected_authorization_repository_commit: str,
    expected_request_sha256: str,
    expected_preparation_repository_commit: str,
    expected_base_repository_commit: str,
    expected_promotion_repository_commit: str,
    require_head_anchor: bool,
) -> FixtureRuntimeHandshakeEvidenceVerificationResult:
    root = repository_root.resolve(strict=True)
    bundle_file = bundle_path.resolve(strict=True)
    if root not in bundle_file.parents:
        raise ValueError("runtime handshake evidence bundle escapes repository root")
    expected_bundle_path = resolve_repo_artifact(
        root, "examples/v2/analyst-fixture-packet/runtime-handshake-readiness.locked.json"
    )
    if bundle_file != expected_bundle_path:
        raise ValueError("runtime handshake evidence bundle path is not canonical")
    bundle_digest = sha256(bundle_file.read_bytes()).hexdigest()
    if bundle_digest != expected_bundle_sha256:
        raise ValueError("runtime handshake evidence bundle SHA-256 mismatch")
    bundle = _load_object(bundle_file)
    _validate_object(
        bundle,
        "fixture-runtime-handshake-readiness.schema.json",
        "runtime_handshake_readiness",
    )
    expected_prohibitions = [
        "redistribution",
        "publication",
        "training",
        "fine_tuning",
        "release",
        "dataset_publication",
        "gold_promotion",
        "legal_certification",
        "paper_update",
        "human_reviewed_claims",
        "empirical_evidence_claims",
    ]
    if bundle["prohibited_actions"] != expected_prohibitions:
        raise ValueError("runtime handshake evidence prohibitions are not exact")
    if (
        bundle["runtime_handshakes_complete"] is not True
        or bundle["role_count"] != 4
        or bundle["exact_model_snapshots_available"] is not False
        or bundle["immutable_session_agent_uuids_available"] is not False
        or bundle["context_presentation_allowed"] is not False
        or bundle["analysis_execution_allowed"] is not False
        or bundle["reconciliation_allowed"] is not False
        or bundle["final_execution_wrapper_present"] is not False
        or bundle["execution_allowed"] is not False
        or bundle["local_only"] is not True
        or any(
            bundle[key] is not False
            for key in (
                "empirical_evidence",
                "human_reviewed",
                "gold_eligible",
                "release_qualifying",
                "publication_eligible",
            )
        )
    ):
        raise ValueError("runtime handshake evidence enables a prohibited state")

    authorization_pin = bundle["handshake_authorization"]
    if (
        authorization_pin["sha256"] != expected_authorization_sha256
        or authorization_pin["repository_commit"] != expected_authorization_repository_commit
    ):
        raise ValueError("runtime handshake authorization pin mismatch")
    authorization_path = resolve_repo_artifact(root, authorization_pin["path"])
    if sha256(authorization_path.read_bytes()).hexdigest() != expected_authorization_sha256:
        raise ValueError("runtime handshake authorization artifact mismatch")
    _verify_commit_ancestry(
        root,
        [expected_authorization_repository_commit, expected_repository_commit],
    )
    _verify_fixture_runtime_handshake_authorization(
        repository_root=root,
        authorization_path=authorization_path,
        expected_authorization_sha256=expected_authorization_sha256,
        expected_repository_commit=expected_authorization_repository_commit,
        expected_request_sha256=expected_request_sha256,
        expected_preparation_repository_commit=expected_preparation_repository_commit,
        expected_base_repository_commit=expected_base_repository_commit,
        expected_promotion_repository_commit=expected_promotion_repository_commit,
        require_head_anchor=False,
    )

    expected_roles = {
        "orchestrator": (
            "agent:orchestrator-fixture-stream",
            "orchestrator_non_labeling",
            "/root/fixture_stream_ready",
            "GPT-5 / Codex",
            """1. Canonical task/session locator: `/root/fixture_stream_ready`
2. Provider family: OpenAI
3. Model/runtime family: GPT-5 / Codex
4. Exact model snapshot: unavailable
5. Immutable session or agent UUID: unavailable
""",
        ),
        "analyst_a": (
            "agent:analyst-fixture-a",
            "analyst",
            "/root/fixture_analyst_a_ready",
            "Codex / GPT-5",
            """1. Canonical task locator: `/root/fixture_analyst_a_ready`
2. Provider family: OpenAI
3. Model/runtime family: Codex / GPT-5
4. Exact model snapshot: unavailable
5. Immutable session or agent UUID: unavailable
""",
        ),
        "analyst_b": (
            "agent:analyst-fixture-b",
            "analyst",
            "/root/fixture_analyst_b_ready",
            "Codex, GPT-5",
            """1. Canonical task/session locator: `/root/fixture_analyst_b_ready`
2. Provider family: OpenAI
3. Model/runtime family: Codex, GPT-5
4. Exact model snapshot: unavailable
5. Immutable session/agent UUID: unavailable
""",
        ),
        "reconciler": (
            "agent:reconciler-fixture",
            "reconciler",
            "/root/fixture_reconciler_ready",
            "Codex, GPT-5",
            """1. Canonical task or session locator: `/root/fixture_reconciler_ready`
2. Provider family: OpenAI
3. Model or runtime family: Codex, GPT-5
4. Exact model snapshot: unavailable
5. Immutable session or agent UUID: unavailable
""",
        ),
    }
    if set(bundle["evidence_records"]) != set(expected_roles):
        raise ValueError("runtime handshake evidence role membership mismatch")
    anchored_paths = [bundle_file]
    actors: set[str] = set()
    locators: set[str] = set()
    recorded_at = _instant(bundle["recorded_at"], "runtime_handshake_readiness.recorded_at")
    forbidden_payload_keys = {
        "context",
        "contexts",
        "fixture_units",
        "label",
        "labels",
        "outputs",
        "peer_outputs",
        "codebook",
        "future_execution_prompt",
        "future_execution_prompts",
    }
    for name, (actor_id, role, locator, reported_runtime, raw_text) in expected_roles.items():
        record_pin = bundle["evidence_records"][name]
        expected_record_relative = (
            f"examples/v2/analyst-fixture-packet/runtime-handshake-evidence.{name}.json"
        )
        if record_pin["path"] != expected_record_relative:
            raise ValueError(f"runtime handshake evidence {name}: record path is not canonical")
        record_path = resolve_repo_artifact(root, record_pin["path"])
        if sha256(record_path.read_bytes()).hexdigest() != record_pin["sha256"]:
            raise ValueError(f"runtime handshake evidence {name}: record SHA-256 mismatch")
        record = _load_object(record_path)
        _validate_object(
            record,
            "fixture-runtime-handshake-evidence.schema.json",
            f"runtime_handshake_evidence.{name}",
        )
        if forbidden_payload_keys.intersection(record):
            raise ValueError(f"runtime handshake evidence {name}: prohibited payload field")
        if (
            record["evidence_id"] != f"local-fixture-runtime-handshake-{name}-2026-07-19"
            or record["role_key"] != name
            or record["actor_id"] != actor_id
            or record["role"] != role
            or record["canonical_session_locator"] != locator
            or record["provider_family"] != "OpenAI"
            or record["reported_runtime_family"] != reported_runtime
            or record["normalized_runtime_family"] != "Codex / GPT-5"
            or record["handshake_authorization"] != authorization_pin
            or record["handshake_prompt"]["sha256"]
            != "6fb5386e21364f172289d563c17b7c93ea17b7a2eea454ff1affa8767d1bea77"
        ):
            raise ValueError(f"runtime handshake evidence {name}: provenance mismatch")
        if (
            record["exact_model_snapshot_available"] is not False
            or record["exact_model_snapshot"] is not None
            or record["immutable_session_agent_uuid_available"] is not False
            or record["immutable_session_agent_uuid"] is not None
            or record["delivery_time_available"] is not False
            or record["delivered_at"] is not None
            or record["reply_time_available"] is not False
            or record["reply_at"] is not None
        ):
            raise ValueError(f"runtime handshake evidence {name}: unavailable value mismatch")
        if (
            record["handshake_prompt_delivered"] is not True
            or record["fixture_context_delivered_with_handshake"] is not False
            or record["label_material_delivered_with_handshake"] is not False
            or record["peer_output_delivered_with_handshake"] is not False
            or record["context_presentation_allowed"] is not False
            or record["analysis_execution_allowed"] is not False
            or record["reconciliation_allowed"] is not False
            or record["local_only"] is not True
            or any(
                record[key] is not False
                for key in (
                    "empirical_evidence",
                    "human_reviewed",
                    "gold_eligible",
                    "release_qualifying",
                    "publication_eligible",
                )
            )
        ):
            raise ValueError(f"runtime handshake evidence {name}: prohibited state")
        expected_raw_relative = (
            f"examples/v2/analyst-fixture-packet/runtime-handshake-reply.{name}.txt"
        )
        if record["raw_reply"]["path"] != expected_raw_relative:
            raise ValueError(f"runtime handshake evidence {name}: raw reply path is not canonical")
        raw_path = resolve_repo_artifact(root, record["raw_reply"]["path"])
        raw_bytes = raw_path.read_bytes()
        if (
            sha256(raw_bytes).hexdigest() != record["raw_reply"]["sha256"]
            or raw_bytes.decode("utf-8") != raw_text
            or record["raw_reply_text"] != raw_text
        ):
            raise ValueError(f"runtime handshake evidence {name}: raw reply mismatch")
        if (
            _instant(record["recorded_at"], f"runtime_handshake_evidence.{name}.recorded_at")
            != recorded_at
            or record["recording_note"]
            != "recorded_at is repository provenance and is not a delivery or reply time"
        ):
            raise ValueError(f"runtime handshake evidence {name}: chronology mismatch")
        actors.add(record["actor_id"])
        locators.add(record["canonical_session_locator"])
        anchored_paths.extend([record_path, raw_path])
    if len(actors) != 4 or len(locators) != 4:
        raise ValueError("runtime handshake actors and locators must be distinct")
    if require_head_anchor:
        verify_git_anchor(root, expected_repository_commit, anchored_paths)
    else:
        verify_git_artifacts_at_commit(root, expected_repository_commit, anchored_paths)
    return FixtureRuntimeHandshakeEvidenceVerificationResult(
        bundle_sha256=bundle_digest,
        repository_commit=expected_repository_commit,
        authorization_sha256=expected_authorization_sha256,
        role_count=4,
    )


def verify_fixture_runtime_handshake_evidence(
    *,
    repository_root: Path,
    bundle_path: Path,
    expected_bundle_sha256: str,
    expected_repository_commit: str,
    expected_authorization_sha256: str,
    expected_authorization_repository_commit: str,
    expected_request_sha256: str,
    expected_preparation_repository_commit: str,
    expected_base_repository_commit: str,
    expected_promotion_repository_commit: str,
) -> FixtureRuntimeHandshakeEvidenceVerificationResult:
    """Verify a committed four-role handshake bundle without enabling analysis."""
    return _verify_fixture_runtime_handshake_evidence(
        repository_root=repository_root,
        bundle_path=bundle_path,
        expected_bundle_sha256=expected_bundle_sha256,
        expected_repository_commit=expected_repository_commit,
        expected_authorization_sha256=expected_authorization_sha256,
        expected_authorization_repository_commit=expected_authorization_repository_commit,
        expected_request_sha256=expected_request_sha256,
        expected_preparation_repository_commit=expected_preparation_repository_commit,
        expected_base_repository_commit=expected_base_repository_commit,
        expected_promotion_repository_commit=expected_promotion_repository_commit,
        require_head_anchor=True,
    )


def _verify_fixture_execution_authorization_candidate(
    *,
    repository_root: Path,
    candidate_path: Path,
    expected_candidate_sha256: str,
    expected_repository_commit: str,
    expected_handshake_evidence_sha256: str,
    expected_handshake_evidence_repository_commit: str,
    expected_authorization_sha256: str,
    expected_authorization_repository_commit: str,
    expected_request_sha256: str,
    expected_preparation_repository_commit: str,
    expected_base_repository_commit: str,
    expected_promotion_repository_commit: str,
    require_head_anchor: bool,
) -> FixtureExecutionAuthorizationCandidateVerificationResult:
    root = repository_root.resolve(strict=True)
    candidate_file = candidate_path.resolve(strict=True)
    canonical_candidate = resolve_repo_artifact(
        root,
        "examples/v2/analyst-fixture-packet/execution-authorization-candidate.v0.2.pending.json",
    )
    if candidate_file != canonical_candidate:
        raise ValueError("fixture execution authorization candidate path is not canonical")
    candidate_digest = sha256(candidate_file.read_bytes()).hexdigest()
    if candidate_digest != expected_candidate_sha256:
        raise ValueError("fixture execution authorization candidate SHA-256 mismatch")
    document = _load_object(candidate_file)
    _validate_object(
        document,
        "fixture-execution-authorization-candidate.v0.2.schema.json",
        "fixture_execution_authorization_candidate",
    )
    expected_prohibitions = [
        "redistribution",
        "publication",
        "training",
        "fine_tuning",
        "release",
        "dataset_publication",
        "gold_promotion",
        "legal_certification",
        "paper_update",
        "human_reviewed_claims",
        "empirical_evidence_claims",
    ]
    if document["prohibited_actions"] != expected_prohibitions:
        raise ValueError("fixture execution authorization candidate prohibitions are not exact")
    if (
        document["human_approval_present"] is not False
        or document["approved_by"] is not None
        or document["approved_at"] is not None
        or document["authorization_effective"] is not False
        or document["pre_execution_verification_passed"] is not False
        or document["context_presentation_allowed"] is not False
        or document["analysis_execution_allowed"] is not False
        or document["reconciliation_allowed"] is not False
        or document["execution_allowed"] is not False
        or document["local_only"] is not True
        or any(
            document[key] is not False
            for key in (
                "empirical_evidence",
                "human_reviewed",
                "gold_eligible",
                "release_qualifying",
                "publication_eligible",
            )
        )
    ):
        raise ValueError("fixture execution authorization candidate enables a prohibited state")
    _instant(document["recorded_at"], "fixture_execution_authorization_candidate.recorded_at")
    if document["handshake_evidence_commit"] != expected_handshake_evidence_repository_commit:
        raise ValueError("fixture execution authorization candidate evidence commit mismatch")

    expected_single_pins = {
        "approved_input_readiness": (
            "examples/v2/analyst-fixture-packet/input-readiness.approved.json",
            "814409acac7401118428bcad2d73df1b1eb8b1bf79c2fa8ce3ea0bdb560b8b6e",
        ),
        "protocol": (
            "docs/42-v2-analyst-execution-protocol.md",
            "ac3785bd823d43a43c7830e34f4f3b380472f271e21f19446cbc575f4b49eca0",
        ),
        "role_authorization_request": (
            "examples/v2/analyst-fixture-packet/role-authorization-request.pending.json",
            expected_request_sha256,
        ),
        "role_authorization_approval": (
            "examples/v2/analyst-fixture-packet/role-authorization-approval.approved.json",
            "9290ac2d3934ff844cf98b1e5c39b42aa960b7f086279dc9bd652767252312b4",
        ),
        "runtime_handshake_authorization": (
            "examples/v2/analyst-fixture-packet/runtime-handshake-authorization.approved.json",
            expected_authorization_sha256,
        ),
        "runtime_handshake_readiness": (
            "examples/v2/analyst-fixture-packet/runtime-handshake-readiness.locked.json",
            expected_handshake_evidence_sha256,
        ),
        "handshake_prompt": (
            "examples/v2/analyst-fixture-packet/prompts/runtime-provenance-handshake.v1.txt",
            "6fb5386e21364f172289d563c17b7c93ea17b7a2eea454ff1affa8767d1bea77",
        ),
        "context_presentation": (
            "examples/v2/analyst-fixture-packet/context-presentation.pending.json",
            "72b75eb688541a712a62bea2569fb84353930c089ebaf8fc1082128aa3ef0e63",
        ),
        "isolation_plan": (
            "examples/v2/analyst-fixture-packet/role-isolation-plan.pending.json",
            "fe2558b57c6a44b20fcde235c79ccc2a7517f6f774450a2f01e176a19cee18b9",
        ),
    }
    anchored_paths = [candidate_file]
    resolved_single: dict[str, Path] = {}
    for name, (relative, digest) in expected_single_pins.items():
        pin = document[name]
        if pin != {"path": relative, "sha256": digest}:
            raise ValueError(f"fixture execution authorization candidate {name} pin mismatch")
        path = resolve_repo_artifact(root, relative)
        if sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError(f"fixture execution authorization candidate {name} artifact mismatch")
        resolved_single[name] = path
        anchored_paths.append(path)

    expected_role_hashes = {
        "orchestrator": (
            "c817ee25c74ea08ebdecf28ad52d126bbc6e8debfd3a9d32f7c8f02c3571112a",
            "b08dedc5f0c2f48f106f92aab5185d7decddea9a8995c5744ac8371ad68dc9c8",
            "5fd5a148c76344021679aa478d74d2d88334bff2cc5c78508649abbe46bbce8b",
        ),
        "analyst_a": (
            "ab8cd28ea7b98eae235069555ef5d239ef47d6b8ca1fe1ee6715e67d0f045908",
            "899bfc9a6a70fa916b5d65e21aa3b64cf31b02bc82ab319c94555a722c0b0b35",
            "f61a108759139dd4cefa1179936cc4f8cbacf13380b588bd8f81f1f89cbd72ed",
        ),
        "analyst_b": (
            "3bcb3b37c8d3a19e51a152c0b72aee82dba088bf822aa8cdc299cbbf029dfb6a",
            "9be881edce63ef461e91d7bc785fdf9fe23a97cbe3bee12ec35de98374bec208",
            "b8012b39cf099015ad226c76814c4c2a96868e25345d113e20fa664f4062d024",
        ),
        "reconciler": (
            "80770f3b4335b7fb5b092a96265e41cef29f0c26081ae46afc9949b220661081",
            "5df3c98f2c3535ddbfc3df0abb42fd668fa3a40b35982494c9fbc6cd20c990f7",
            "e293e4eb036890b32d246bb4b123dae4f72636cb305da1fcf6a4982051e1671a",
        ),
    }
    groups = {
        "future_execution_prompts": ("prompts/{role}.future-execution.v1.txt", 0),
        "role_provenance": ("role-provenance.{role}.pending.json", 1),
        "runtime_evidence": ("runtime-handshake-evidence.{role}.json", 2),
    }
    for group, (template, digest_index) in groups.items():
        if set(document[group]) != set(expected_role_hashes):
            raise ValueError(
                f"fixture execution authorization candidate {group} membership mismatch"
            )
        for role, digests in expected_role_hashes.items():
            relative = "examples/v2/analyst-fixture-packet/" + template.format(role=role)
            expected_pin = {"path": relative, "sha256": digests[digest_index]}
            if document[group][role] != expected_pin:
                raise ValueError(
                    f"fixture execution authorization candidate {group}.{role} pin mismatch"
                )
            path = resolve_repo_artifact(root, relative)
            if sha256(path.read_bytes()).hexdigest() != digests[digest_index]:
                raise ValueError(
                    f"fixture execution authorization candidate {group}.{role} artifact mismatch"
                )
            anchored_paths.append(path)

    _verify_commit_ancestry(
        root,
        [
            expected_preparation_repository_commit,
            expected_authorization_repository_commit,
            expected_handshake_evidence_repository_commit,
            expected_repository_commit,
        ],
    )
    _verify_fixture_runtime_handshake_evidence(
        repository_root=root,
        bundle_path=resolved_single["runtime_handshake_readiness"],
        expected_bundle_sha256=expected_handshake_evidence_sha256,
        expected_repository_commit=expected_handshake_evidence_repository_commit,
        expected_authorization_sha256=expected_authorization_sha256,
        expected_authorization_repository_commit=expected_authorization_repository_commit,
        expected_request_sha256=expected_request_sha256,
        expected_preparation_repository_commit=expected_preparation_repository_commit,
        expected_base_repository_commit=expected_base_repository_commit,
        expected_promotion_repository_commit=expected_promotion_repository_commit,
        require_head_anchor=False,
    )
    if require_head_anchor:
        verify_git_anchor(root, expected_repository_commit, anchored_paths)
    else:
        verify_git_artifacts_at_commit(root, expected_repository_commit, anchored_paths)
    return FixtureExecutionAuthorizationCandidateVerificationResult(
        candidate_sha256=candidate_digest,
        repository_commit=expected_repository_commit,
        handshake_evidence_sha256=expected_handshake_evidence_sha256,
        role_count=4,
    )


def verify_fixture_execution_authorization_candidate(
    *,
    repository_root: Path,
    candidate_path: Path,
    expected_candidate_sha256: str,
    expected_repository_commit: str,
    expected_handshake_evidence_sha256: str,
    expected_handshake_evidence_repository_commit: str,
    expected_authorization_sha256: str,
    expected_authorization_repository_commit: str,
    expected_request_sha256: str,
    expected_preparation_repository_commit: str,
    expected_base_repository_commit: str,
    expected_promotion_repository_commit: str,
) -> FixtureExecutionAuthorizationCandidateVerificationResult:
    """Verify an inert candidate that still requires exact human approval."""
    return _verify_fixture_execution_authorization_candidate(
        repository_root=repository_root,
        candidate_path=candidate_path,
        expected_candidate_sha256=expected_candidate_sha256,
        expected_repository_commit=expected_repository_commit,
        expected_handshake_evidence_sha256=expected_handshake_evidence_sha256,
        expected_handshake_evidence_repository_commit=expected_handshake_evidence_repository_commit,
        expected_authorization_sha256=expected_authorization_sha256,
        expected_authorization_repository_commit=expected_authorization_repository_commit,
        expected_request_sha256=expected_request_sha256,
        expected_preparation_repository_commit=expected_preparation_repository_commit,
        expected_base_repository_commit=expected_base_repository_commit,
        expected_promotion_repository_commit=expected_promotion_repository_commit,
        require_head_anchor=True,
    )


def verify_fixture_pre_execution_authorization(
    *,
    repository_root: Path,
    authorization_path: Path,
    expected_authorization_sha256: str,
    expected_repository_commit: str,
    expected_candidate_sha256: str,
    expected_candidate_repository_commit: str,
    expected_handshake_evidence_sha256: str,
    expected_handshake_evidence_repository_commit: str,
    expected_handshake_authorization_sha256: str,
    expected_handshake_authorization_repository_commit: str,
    expected_request_sha256: str,
    expected_preparation_repository_commit: str,
    expected_base_repository_commit: str,
    expected_promotion_repository_commit: str,
) -> FixturePreExecutionVerificationResult:
    """Verify the exact committed wrapper and emit bounded execution permission."""
    root = repository_root.resolve(strict=True)
    authorization_file = authorization_path.resolve(strict=True)
    canonical_authorization = resolve_repo_artifact(
        root,
        "examples/v2/analyst-fixture-packet/execution-authorization.v0.2.pending-verification.json",
    )
    if authorization_file != canonical_authorization:
        raise ValueError("fixture pre-execution authorization path is not canonical")
    authorization_digest = sha256(authorization_file.read_bytes()).hexdigest()
    if authorization_digest != expected_authorization_sha256:
        raise ValueError("fixture pre-execution authorization SHA-256 mismatch")
    document = _load_object(authorization_file)
    _validate_object(
        document,
        "fixture-execution-authorization.v0.2.schema.json",
        "fixture_pre_execution_authorization",
    )
    expected_prohibitions = [
        "redistribution",
        "publication",
        "training",
        "fine_tuning",
        "release",
        "dataset_publication",
        "gold_promotion",
        "legal_certification",
        "paper_update",
        "human_reviewed_claims",
        "empirical_evidence_claims",
    ]
    if document["prohibited_actions"] != expected_prohibitions:
        raise ValueError("fixture pre-execution authorization prohibitions are not exact")
    if (
        document["status"] != "approved_pending_pre_execution_verification"
        or document["execution_authorization_present"] is not True
        or document["authorization_effective"] is not False
        or document["pre_execution_verification_required"] is not True
        or document["pre_execution_verification_passed"] is not False
        or document["context_presentation_authorized_conditionally"] is not True
        or document["analysis_execution_authorized_conditionally"] is not True
        or document["reconciliation_authorized_conditionally"] is not True
        or document["execution_authorized_conditionally"] is not True
        or document["context_presentation_allowed"] is not False
        or document["analysis_execution_allowed"] is not False
        or document["reconciliation_allowed"] is not False
        or document["execution_allowed"] is not False
        or document["local_only"] is not True
        or any(
            document[key] is not False
            for key in (
                "empirical_evidence",
                "human_reviewed",
                "gold_eligible",
                "release_qualifying",
                "publication_eligible",
            )
        )
    ):
        raise ValueError("fixture pre-execution authorization has an invalid state transition")
    _instant(document["recorded_at"], "fixture_pre_execution_authorization.recorded_at")

    candidate_pin = document["derived_from_candidate"]
    expected_candidate_pin = {
        "path": (
            "examples/v2/analyst-fixture-packet/execution-authorization-candidate.v0.2.pending.json"
        ),
        "sha256": expected_candidate_sha256,
        "repository_commit": expected_candidate_repository_commit,
    }
    if candidate_pin != expected_candidate_pin:
        raise ValueError("fixture pre-execution candidate pin mismatch")
    candidate_path = resolve_repo_artifact(root, candidate_pin["path"])
    if sha256(candidate_path.read_bytes()).hexdigest() != expected_candidate_sha256:
        raise ValueError("fixture pre-execution candidate artifact mismatch")

    approval_pin = document["candidate_approval"]
    expected_approval_path = (
        "examples/v2/analyst-fixture-packet/"
        "execution-authorization-candidate-approval.approved.json"
    )
    if approval_pin["path"] != expected_approval_path:
        raise ValueError("fixture pre-execution candidate approval path is not canonical")
    approval_path = resolve_repo_artifact(root, approval_pin["path"])
    if sha256(approval_path.read_bytes()).hexdigest() != approval_pin["sha256"]:
        raise ValueError("fixture pre-execution candidate approval SHA-256 mismatch")
    approval = _load_object(approval_path)
    _validate_object(
        approval,
        "fixture-execution-authorization-candidate-approval.schema.json",
        "fixture_execution_authorization_candidate_approval",
    )
    expected_statement = (
        "I, edithatogo, approve pending fixture execution-authorization candidate SHA-256 "
        "a1aab22f6f7870497f639e871cc4aa13d209ca35b72f8da89559bcf9940dab1d as "
        "committed in 5cbfbe80beee96c67cdcabbf352b97d5dffd6cbf for derivation of the "
        "bounded local executable v0.2 fixture authorization described by that exact candidate. "
        "This approval does not itself authorize context presentation or analysis; those remain "
        "prohibited until the separately derived executable authorization is committed and its "
        "pre-execution verifier passes against its exact SHA-256 and commit. Redistribution, "
        "publication, training, fine-tuning, release, dataset publication, gold promotion, legal "
        "certification, paper updates, human-reviewed claims, and empirical-evidence claims remain "
        "prohibited."
    )
    if (
        approval["approval_statement"] != expected_statement
        or approval["approval_statement_sha256"]
        != sha256(expected_statement.encode("utf-8")).hexdigest()
        or approval["approved_candidate"] != expected_candidate_pin
        or approval["derivation_approved"] is not True
        or approval["context_presentation_approved"] is not False
        or approval["analysis_execution_approved"] is not False
        or approval["committed_executable_required"] is not True
        or approval["pre_execution_verification_required"] is not True
        or approval["execution_allowed"] is not False
        or approval["local_only"] is not True
        or approval["prohibited_actions"] != expected_prohibitions
    ):
        raise ValueError("fixture pre-execution candidate approval is not exact")

    candidate = _load_object(candidate_path)
    inherited_keys = (
        "handshake_evidence_commit",
        "approved_input_readiness",
        "protocol",
        "role_authorization_request",
        "role_authorization_approval",
        "runtime_handshake_authorization",
        "runtime_handshake_readiness",
        "handshake_prompt",
        "context_presentation",
        "isolation_plan",
        "future_execution_prompts",
        "role_provenance",
        "runtime_evidence",
    )
    for key in inherited_keys:
        if document[key] != candidate[key]:
            raise ValueError(f"fixture pre-execution authorization {key} differs from candidate")
    expected_conditions = {
        "orchestrator": {
            "actor_id": "agent:orchestrator-fixture-stream",
            "may_coordinate": True,
            "may_label": False,
            "condition": "after_exact_pre_execution_verification",
        },
        "analyst_a": {
            "actor_id": "agent:analyst-fixture-a",
            "may_coordinate": False,
            "may_label": True,
            "condition": "after_exact_pre_execution_verification",
        },
        "analyst_b": {
            "actor_id": "agent:analyst-fixture-b",
            "may_coordinate": False,
            "may_label": True,
            "condition": "after_exact_pre_execution_verification",
        },
        "reconciler": {
            "actor_id": "agent:reconciler-fixture",
            "may_coordinate": False,
            "may_label": False,
            "condition": (
                "after_exact_pre_execution_verification_and_both_analyst_result_sets_locked"
            ),
        },
    }
    if document["role_execution_conditions"] != expected_conditions:
        raise ValueError("fixture pre-execution role conditions are not exact")

    _verify_commit_ancestry(
        root,
        [expected_candidate_repository_commit, expected_repository_commit],
    )
    _verify_fixture_execution_authorization_candidate(
        repository_root=root,
        candidate_path=candidate_path,
        expected_candidate_sha256=expected_candidate_sha256,
        expected_repository_commit=expected_candidate_repository_commit,
        expected_handshake_evidence_sha256=expected_handshake_evidence_sha256,
        expected_handshake_evidence_repository_commit=expected_handshake_evidence_repository_commit,
        expected_authorization_sha256=expected_handshake_authorization_sha256,
        expected_authorization_repository_commit=(
            expected_handshake_authorization_repository_commit
        ),
        expected_request_sha256=expected_request_sha256,
        expected_preparation_repository_commit=expected_preparation_repository_commit,
        expected_base_repository_commit=expected_base_repository_commit,
        expected_promotion_repository_commit=expected_promotion_repository_commit,
        require_head_anchor=False,
    )
    verify_git_anchor(
        root,
        expected_repository_commit,
        [authorization_file, approval_path],
    )
    return FixturePreExecutionVerificationResult(
        authorization_sha256=authorization_digest,
        repository_commit=expected_repository_commit,
        candidate_sha256=expected_candidate_sha256,
        role_count=4,
    )


def verify_analyst_execution_packet(
    *,
    repository_root: Path,
    authorization_path: Path,
    expected_authorization_sha256: str,
    expected_repository_commit: str,
) -> AnalystPacketVerificationResult:
    """Verify a committed, approved, bounded local analyst packet before execution."""
    root = repository_root.resolve(strict=True)
    authorization = authorization_path.resolve(strict=True)
    pending = _load_object(authorization)
    if pending.get("schema_version") == "foi-o.analyst-execution-authorization.v0.2.0":
        raise ValueError("legacy three-role analyst authorization is retired")
    preparation_only_versions = {
        "foi-o.fixture-role-authorization-request.v0.1.0": "pending role authorization request",
        "foi-o.fixture-runtime-handshake-authorization.v0.1.0": ("runtime handshake authorization"),
        "foi-o.fixture-runtime-handshake-readiness.v0.1.0": ("runtime handshake evidence bundle"),
        "foi-o.fixture-runtime-handshake-evidence.v0.1.0": "runtime handshake evidence record",
        "foi-o.fixture-execution-authorization-candidate.v0.2.0": (
            "fixture execution authorization candidate"
        ),
    }
    if pending.get("schema_version") in preparation_only_versions:
        label = preparation_only_versions[pending["schema_version"]]
        raise ValueError(f"{label} cannot be used for execution")
    verify_git_anchor(root, expected_repository_commit, [authorization])
    authorization_digest = sha256(authorization.read_bytes()).hexdigest()
    if authorization_digest != expected_authorization_sha256:
        raise ValueError("authorization SHA-256 mismatch")

    document = _load_object(authorization)
    _validate_object(
        document,
        "analyst-execution-authorization.v0.2.schema.json",
        "authorization",
    )
    schema_by_role = {
        "source_population": "analyst-fixture-source-population.schema.json",
        "codebook": "analyst-approved-fixture-codebook.schema.json",
        "sampling_configuration": "analyst-approved-sampling-configuration.schema.json",
        "unit_manifest": "analyst-fixture-unit-manifest.schema.json",
        "duplicate_cluster_registry": "analyst-fixture-cluster-registry.schema.json",
        "redaction_manifest": "analyst-redaction-manifest.schema.json",
        "local_rights_review": "analyst-approved-local-rights-review.schema.json",
    }
    artifact_paths: dict[str, Path] = {}
    for role, pin in document["artifacts"].items():
        path = resolve_repo_artifact(root, pin["path"])
        if path in artifact_paths.values():
            raise ValueError("artifact path reused across roles")
        if sha256(path.read_bytes()).hexdigest() != pin["sha256"]:
            raise ValueError(f"{role}: artifact SHA-256 mismatch")
        artifact_paths[role] = path
    approved_readiness_path = artifact_paths["approved_input_readiness"]
    approved_readiness = _load_object(approved_readiness_path)
    verify_approved_fixture_inputs(
        repository_root=root,
        packet_dir=approved_readiness_path.parent,
        expected_approval_sha256=approved_readiness["approved_artifacts"]["input_approval"][
            "sha256"
        ],
        expected_approved_input_readiness_sha256=document["artifacts"]["approved_input_readiness"][
            "sha256"
        ],
        expected_base_repository_commit=approved_readiness["base_readiness"]["repository_commit"],
        expected_promotion_repository_commit=expected_repository_commit,
    )
    verify_authorized_actor_separation(document)
    expected_protocol = (root / "docs/42-v2-analyst-execution-protocol.md").resolve(strict=True)
    if artifact_paths["protocol"] != expected_protocol:
        raise ValueError("protocol artifact is not the active analyst protocol")
    verify_git_anchor(root, expected_repository_commit, list(artifact_paths.values()))

    for role, schema_name in schema_by_role.items():
        _validate_object(_load_object(artifact_paths[role]), schema_name, role)

    rights = _load_object(artifact_paths["local_rights_review"])
    if (
        rights["status"] != "approved_bounded_local_use"
        or rights["local_analysis_allowed"] is not True
    ):
        raise ValueError("bounded local rights review is not approved")

    derived = derive_fixture_units(root)
    source_hashes = {unit.source_path: unit.source_artifact_sha256 for unit in derived}
    source_paths = [resolve_repo_artifact(root, path) for path in sorted(source_hashes)]
    license_path = resolve_repo_artifact(root, "LICENSE.md")
    verify_git_anchor(root, expected_repository_commit, [*source_paths, license_path])
    unit_manifest = _load_object(artifact_paths["unit_manifest"])
    redaction_manifest = _load_object(artifact_paths["redaction_manifest"])
    cluster_registry = _load_object(artifact_paths["duplicate_cluster_registry"])
    verify_fixture_manifests(derived, unit_manifest, redaction_manifest, cluster_registry)

    source_population = _load_object(artifact_paths["source_population"])
    source_counts = {
        "examples/process-mining-events.fixture.jsonl": 9,
        "examples/event-timeline.small.json": 2,
    }
    declared_counts = {
        item["path"]: item["expected_units"] for item in source_population["sources"]
    }
    if declared_counts != source_counts:
        raise ValueError("source population is not the exact 9+2 census")
    declared_source_hashes = {item["path"]: item["sha256"] for item in source_population["sources"]}
    if declared_source_hashes != source_hashes:
        raise ValueError("source population SHA-256 set mismatch")
    rights_source_hashes = {item["path"]: item["sha256"] for item in rights["sources"]}
    if rights_source_hashes != source_hashes:
        raise ValueError("rights-review source SHA-256 set mismatch")
    if (
        rights["license_placeholder"]["path"] != "LICENSE.md"
        or rights["license_placeholder"]["sha256"] != sha256(license_path.read_bytes()).hexdigest()
    ):
        raise ValueError("rights-review license placeholder mismatch")

    protocol_digest = sha256(expected_protocol.read_bytes()).hexdigest()
    codebook = _load_object(artifact_paths["codebook"])
    if (
        codebook["status"] != "approved"
        or codebook["protocol_sha256"] != protocol_digest
        or codebook["task_type"] != source_population["task"]
    ):
        raise ValueError("codebook protocol pin mismatch")
    sampling = _load_object(artifact_paths["sampling_configuration"])
    if (
        sampling["status"] != "approved"
        or sampling["protocol_sha256"] != protocol_digest
        or sampling["source_population_sha256"]
        != sha256(artifact_paths["source_population"].read_bytes()).hexdigest()
        or sampling["codebook_revision"] != codebook["revision"]
    ):
        raise ValueError("sampling cross-artifact pin mismatch")
    if (
        cluster_registry["unit_manifest_sha256"]
        != sha256(artifact_paths["unit_manifest"].read_bytes()).hexdigest()
    ):
        raise ValueError("cluster unit-manifest pin mismatch")

    authorization_time = _instant(document["approved_at"], "authorization.approved_at")
    for label, artifact in {
        "source_population": source_population,
        "unit_manifest": unit_manifest,
        "cluster_registry": cluster_registry,
        "redaction_manifest": redaction_manifest,
    }.items():
        created = _instant(artifact["created_at"], f"{label}.created_at")
        locked = _instant(artifact["locked_at"], f"{label}.locked_at")
        if created > locked or locked > authorization_time:
            raise ValueError(f"{label}: invalid lock chronology")
    for label, artifact in {
        "rights": rights,
        "codebook": codebook,
        "sampling": sampling,
    }.items():
        created = _instant(artifact["created_at"], f"{label}.created_at")
        recorded = _instant(artifact["recorded_at"], f"{label}.recorded_at")
        if created > recorded or recorded > authorization_time:
            raise ValueError(f"{label}: invalid recording chronology")
    if (
        sampling["random_seed"] != 20260717
        or sampling["probability_sample_size"] != 11
        or sampling["enrichment_sample_size"] != 0
        or sampling["split_policy"]["splits"] != ["annotation_only"]
    ):
        raise ValueError("sampling configuration is not the locked fixture census")

    return AnalystPacketVerificationResult(
        repository_commit=expected_repository_commit,
        authorization_sha256=authorization_digest,
        unit_count=11,
        cluster_count=11,
        redacted_context_count=11,
        source_counts=source_counts,
        execution_allowed=True,
    )

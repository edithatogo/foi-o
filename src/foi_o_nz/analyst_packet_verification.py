"""Fail-closed verification helpers for local automated-analyst packets."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
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


def verify_fixture_role_authorization_request(
    *,
    repository_root: Path,
    request_path: Path,
    expected_request_sha256: str,
    expected_preparation_repository_commit: str,
    expected_base_repository_commit: str,
    expected_promotion_repository_commit: str,
) -> FixtureRoleAuthorizationRequestVerificationResult:
    """Verify pending role preparation without enabling execution."""
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

    verify_git_anchor(root, expected_preparation_repository_commit, list(paths.values()))
    return FixtureRoleAuthorizationRequestVerificationResult(
        request_sha256=request_digest,
        preparation_commit=expected_preparation_repository_commit,
        role_count=4,
        context_count=11,
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
    if pending.get("schema_version") == "foi-o.fixture-role-authorization-request.v0.1.0":
        raise ValueError("pending role authorization request cannot be used for execution")
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

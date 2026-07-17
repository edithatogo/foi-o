"""Fail-closed verification helpers for local automated-analyst packets."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
from pathlib import Path, PurePosixPath
from subprocess import run
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

FORBIDDEN_CONTEXT_KEYS = frozenset({"assertion_status", "confidence"})
SCHEMA_DIR = Path(__file__).parents[2] / "schemas" / "json"


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
        if committed != resolved.read_bytes():
            raise ValueError(f"{relative}: differs from anchored commit")


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


def _instant(value: str, label: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise ValueError(f"{label}: timezone required")
    return parsed


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
    verify_authorized_actor_separation(document)

    schema_by_role = {
        "source_population": "analyst-fixture-source-population.schema.json",
        "codebook": "analyst-fixture-codebook.schema.json",
        "sampling_configuration": "sampling-configuration.schema.json",
        "unit_manifest": "analyst-fixture-unit-manifest.schema.json",
        "duplicate_cluster_registry": "analyst-fixture-cluster-registry.schema.json",
        "redaction_manifest": "analyst-redaction-manifest.schema.json",
        "local_rights_review": "analyst-local-rights-review.schema.json",
    }
    artifact_paths: dict[str, Path] = {}
    for role, pin in document["artifacts"].items():
        path = resolve_repo_artifact(root, pin["path"])
        if path in artifact_paths.values():
            raise ValueError("artifact path reused across roles")
        if sha256(path.read_bytes()).hexdigest() != pin["sha256"]:
            raise ValueError(f"{role}: artifact SHA-256 mismatch")
        artifact_paths[role] = path
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
        approved = _instant(artifact["approved_at"], f"{label}.approved_at")
        if created > approved or approved > authorization_time:
            raise ValueError(f"{label}: invalid approval chronology")
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

"""Repository-verified execution context for governed empirical operations."""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any

from .contracts import (
    EmpiricalContractError,
    RunSpecification,
    _require_schema,
    canonical_bytes,
    content_sha256,
    load_run_spec,
    parse_run_spec,
    validate_executable_run,
)

_CONSTRUCTION_TOKEN = object()


class ExecutionContextError(ValueError):
    """Raised when immutable execution evidence cannot be verified."""


@dataclass(frozen=True)
class VerifiedCodebook:
    """Vocabulary derived from exact pinned codebook bytes."""

    sha256: str
    labels: frozenset[str]
    abstention_reasons: frozenset[str]
    raw: Mapping[str, Any]


class VerifiedExecutionContext:
    """Opaque execution authority issued only after complete verification."""

    __slots__ = (
        "_authorization",
        "_calibration",
        "_codebook",
        "_membership",
        "_repository",
        "_run_spec",
        "_source_bundle_sha256",
        "_units",
        "_verification_receipt_sha256",
    )

    def __init__(
        self,
        token: object,
        *,
        run_spec: RunSpecification,
        repository: Path,
        membership: dict[str, Any],
        units: tuple[dict[str, Any], ...],
        codebook: VerifiedCodebook,
        calibration: dict[str, Any],
        authorization: dict[str, Any],
        source_bundle_sha256: str,
        verification_receipt_sha256: str,
    ) -> None:
        """Reject direct construction and retain verified immutable inputs."""
        if token is not _CONSTRUCTION_TOKEN:
            raise ExecutionContextError(
                "verified execution contexts can only be issued by repository verification"
            )
        self._run_spec = parse_run_spec(deepcopy(run_spec.raw))
        self._repository = repository
        self._membership = deepcopy(membership)
        self._units = tuple(deepcopy(unit) for unit in units)
        self._codebook = codebook
        self._calibration = deepcopy(calibration)
        self._authorization = deepcopy(authorization)
        self._source_bundle_sha256 = source_bundle_sha256
        self._verification_receipt_sha256 = verification_receipt_sha256

    @property
    def run_spec(self) -> RunSpecification:
        """Return the descriptive specification verified for this context."""
        return parse_run_spec(deepcopy(self._run_spec.raw))

    @property
    def repository(self) -> Path:
        """Return the repository root used for verification."""
        return self._repository

    @property
    def membership(self) -> dict[str, Any]:
        """Return the exact verified membership."""
        return deepcopy(self._membership)

    @property
    def units(self) -> tuple[dict[str, Any], ...]:
        """Return exact canonical source units."""
        return tuple(deepcopy(unit) for unit in self._units)

    @property
    def codebook(self) -> VerifiedCodebook:
        """Return the verified parsed codebook."""
        return self._codebook

    @property
    def calibration(self) -> dict[str, Any]:
        """Return exact approved calibration evidence."""
        return deepcopy(self._calibration)

    @property
    def authorization(self) -> dict[str, Any]:
        """Return exact approved execution authorization."""
        return deepcopy(self._authorization)

    @property
    def source_bundle_sha256(self) -> str:
        """Return the canonical source bundle digest."""
        return self._source_bundle_sha256

    @property
    def verification_receipt_sha256(self) -> str:
        """Return the deterministic verification receipt digest."""
        return self._verification_receipt_sha256

    @property
    def run_id(self) -> str:
        """Return the verified run identity."""
        return self._run_spec.run_id

    @property
    def run_spec_sha256(self) -> str:
        """Return the verified run-spec digest."""
        return self._run_spec.run_spec_sha256

    @property
    def membership_sha256(self) -> str:
        """Return the verified membership digest."""
        return str(self._membership["membership_sha256"])

    @property
    def codebook_sha256(self) -> str:
        """Return the verified codebook byte digest."""
        return self._codebook.sha256

    @property
    def calibration_sha256(self) -> str:
        """Return the verified calibration digest."""
        return str(self._calibration["calibration_sha256"])

    @property
    def authorization_sha256(self) -> str:
        """Return the verified authorization digest."""
        return str(self._authorization["authorization_sha256"])

    @property
    def calibration_artifact_sha256(self) -> str:
        """Return the external calibration-approval artifact digest."""
        return str(self._calibration["external_approval"]["artifact_sha256"])

    @property
    def authorization_artifact_sha256(self) -> str:
        """Return the external authorization-approval artifact digest."""
        return str(self._authorization["external_approval"]["artifact_sha256"])

    def require_capability(self, stage_kind: str, capability: str) -> dict[str, Any]:
        """Return the unique stage authorizing a capability or fail closed."""
        validate_executable_run(self._run_spec.raw)
        stages = [
            stage
            for stage in self._run_spec.raw.get("stages", [])
            if stage.get("stage_kind") == stage_kind
        ]
        if (
            len(stages) != 1
            or capability not in stages[0].get("allowed_capabilities", [])
            or capability in stages[0].get("denied_capabilities", [])
        ):
            raise ExecutionContextError(f"verified context does not authorize {capability}")
        return stages[0]

    def require_registered_approval(
        self,
        *,
        stage_kind: str,
        capability: str,
        artifact_prefix: str,
        artifact_sha256: str,
    ) -> dict[str, Any]:
        """Require one exact stage capability and one registered approval artifact."""
        stage = self.require_capability(stage_kind, capability)
        if (
            not artifact_prefix
            or not isinstance(artifact_sha256, str)
            or len(artifact_sha256) != 64
            or any(character not in "0123456789abcdef" for character in artifact_sha256)
        ):
            raise ExecutionContextError("stage approval artifact identity is invalid")
        matches = [
            artifact
            for artifact in self._run_spec.raw.get("referenced_artifacts", [])
            if str(artifact.get("artifact_id", "")).startswith(artifact_prefix)
            and artifact.get("sha256") == artifact_sha256
        ]
        if len(matches) != 1:
            raise ExecutionContextError("stage approval artifact is not uniquely registered")
        return stage

    def population_sha256(self, stage_kind: str) -> str:
        """Return the verified population digest for a governed stage."""
        stage = self.require_capability(stage_kind, _CAPABILITY_BY_STAGE[stage_kind])
        value = stage.get("population", {}).get("population_sha256")
        if not isinstance(value, str) or len(value) != 64:
            raise ExecutionContextError("stage population SHA-256 is invalid")
        return value


_CAPABILITY_BY_STAGE = {
    "packet": "packet.generate",
    "annotation": "annotation.execute",
    "reliability": "reliability.compute_descriptive",
    "extractor_metrics": "extractor_metrics.compute",
    "maturity": "maturity.compare_thresholds",
}


def canonical_unit_sha256(unit: Mapping[str, Any]) -> str:
    """Hash the content-bearing canonical unit representation."""
    preimage = {
        "unit_id": unit["unit_id"],
        "text": unit["text"],
        "source_spans": unit.get("source_spans", []),
    }
    return hashlib.sha256(canonical_bytes(preimage)).hexdigest()


def canonical_units(units: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Validate, normalize, and deterministically order source units."""
    parsed: list[dict[str, Any]] = []
    for unit in units:
        if not isinstance(unit, dict) or set(unit) not in (
            {"unit_id", "unit_sha256", "text"},
            {"unit_id", "unit_sha256", "text", "source_spans"},
        ):
            raise ExecutionContextError("source unit violates the strict field contract")
        if not isinstance(unit.get("unit_id"), str) or not unit["unit_id"]:
            raise ExecutionContextError("source unit identity is invalid")
        if not isinstance(unit.get("text"), str):
            raise ExecutionContextError("source unit text is invalid")
        spans = unit.get("source_spans", [])
        if not isinstance(spans, list):
            raise ExecutionContextError("source spans must be an array")
        normalized = {
            "unit_id": unit["unit_id"],
            "unit_sha256": unit["unit_sha256"],
            "text": unit["text"],
            "source_spans": spans,
        }
        if canonical_unit_sha256(normalized) != unit.get("unit_sha256"):
            raise ExecutionContextError("source unit SHA-256 does not bind canonical content")
        parsed.append(normalized)
    parsed.sort(key=lambda row: (row["unit_id"], row["unit_sha256"]))
    if len({row["unit_id"] for row in parsed}) != len(parsed):
        raise ExecutionContextError("source unit identities must be unique")
    return parsed


def canonical_source_bundle_sha256(units: list[dict[str, Any]]) -> str:
    """Hash an ordered canonical source bundle."""
    return hashlib.sha256(canonical_bytes(units)).hexdigest()


def _json_object(path: Path, label: str) -> tuple[dict[str, Any], bytes]:
    try:
        payload = path.read_bytes()
        value = json.loads(payload.decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ExecutionContextError(f"cannot read {label}: {path}") from error
    if not isinstance(value, dict):
        raise ExecutionContextError(f"{label} must be a JSON object")
    return value, payload


def _registered_artifact(spec: RunSpecification, prefix: str, digest: str) -> None:
    matches = [
        artifact
        for artifact in spec.raw.get("referenced_artifacts", [])
        if str(artifact.get("artifact_id", "")).startswith(prefix)
        and artifact.get("sha256") == digest
    ]
    if len(matches) != 1:
        raise ExecutionContextError(f"{prefix.rstrip(':')} artifact is not uniquely registered")


def _parse_codebook(value: dict[str, Any], digest: str) -> VerifiedCodebook:
    raw_labels = value.get("labels")
    labels = (
        {
            item.get("id")
            for item in raw_labels
            if isinstance(raw_labels, list) and isinstance(item, dict)
        }
        if isinstance(raw_labels, list)
        else set()
    )
    abstention = value.get("abstention")
    reasons = (
        abstention.get("reasons", [])
        if isinstance(abstention, dict)
        else value.get("abstention_reasons", [])
    )
    if (
        not labels
        or None in labels
        or any(not isinstance(label, str) or not label for label in labels)
        or not isinstance(reasons, list)
        or not reasons
        or any(not isinstance(reason, str) or not reason for reason in reasons)
    ):
        raise ExecutionContextError("codebook does not define executable label vocabularies")
    parsed_labels = frozenset(label for label in labels if isinstance(label, str))
    parsed_reasons = frozenset(reason for reason in reasons if isinstance(reason, str))
    return VerifiedCodebook(
        sha256=digest,
        labels=parsed_labels,
        abstention_reasons=parsed_reasons,
        raw=MappingProxyType(value),
    )


def _approval_content_sha256(record: dict[str, Any], excluded: set[str]) -> str:
    return hashlib.sha256(
        canonical_bytes({key: value for key, value in record.items() if key not in excluded})
    ).hexdigest()


def approved_execution_context_sha256(
    *,
    membership_sha256: str,
    codebook_sha256: str,
    source_bundle_sha256: str,
    calibration: dict[str, Any],
    authorization: dict[str, Any],
) -> str:
    """Hash approval-independent execution inputs without a hash cycle."""
    context = {
        "schema_version": "foio.empirical-approved-execution-context.v1.0.0",
        "membership_sha256": membership_sha256,
        "codebook_sha256": codebook_sha256,
        "source_bundle_sha256": source_bundle_sha256,
        "calibration_content_sha256": _approval_content_sha256(
            calibration, {"calibration_sha256", "external_approval", "run_spec_sha256"}
        ),
        "authorization_content_sha256": _approval_content_sha256(
            authorization,
            {
                "authorization_sha256",
                "calibration_sha256",
                "external_approval",
                "run_spec_sha256",
            },
        ),
    }
    return hashlib.sha256(canonical_bytes(context)).hexdigest()


def _require_authority(
    spec: RunSpecification,
    membership: dict[str, Any],
    codebook_sha256: str,
    source_bundle_sha256: str,
    calibration: dict[str, Any],
    authorization: dict[str, Any],
) -> None:
    if spec.authority_bindings is None:
        raise ExecutionContextError("run specification has no authority bindings")
    try:
        _require_schema(calibration, "australian-empirical-calibration-result.schema.json")
        _require_schema(authorization, "australian-empirical-execution-authorization.schema.json")
    except EmpiricalContractError as error:
        raise ExecutionContextError(str(error)) from error
    if calibration.get("calibration_sha256") != content_sha256(calibration, "calibration_sha256"):
        raise ExecutionContextError("calibration self-pin is invalid")
    if authorization.get("authorization_sha256") != content_sha256(
        authorization, "authorization_sha256"
    ):
        raise ExecutionContextError("authorization self-pin is invalid")
    membership_sha = membership["membership_sha256"]
    expected = {
        "run_spec_sha256": spec.run_spec_sha256,
        "membership_sha256": membership_sha,
        "codebook_sha256": codebook_sha256,
    }
    if any(calibration.get(field) != value for field, value in expected.items()):
        raise ExecutionContextError("calibration lineage differs from verified context")
    if any(authorization.get(field) != value for field, value in expected.items()):
        raise ExecutionContextError("authorization lineage differs from verified context")
    if authorization.get("calibration_sha256") != calibration["calibration_sha256"]:
        raise ExecutionContextError("authorization calibration binding mismatch")
    if calibration.get("status") != "passed" or authorization.get("status") != "approved":
        raise ExecutionContextError("execution authority is not approved and calibrated")
    roles = set(calibration.get("role_ids", []))
    if len(roles) != 3 or roles != set(authorization.get("approved_roles", [])):
        raise ExecutionContextError("authority role bindings differ")
    if calibration.get("calibrator_identity") == authorization.get("authorizer_identity"):
        raise ExecutionContextError("calibrator and authorizer must be distinct")
    approved_context = approved_execution_context_sha256(
        membership_sha256=membership_sha,
        codebook_sha256=codebook_sha256,
        source_bundle_sha256=source_bundle_sha256,
        calibration=calibration,
        authorization=authorization,
    )
    pairs = (
        (calibration["external_approval"], spec.authority_bindings.calibration_approval),
        (
            authorization["external_approval"],
            spec.authority_bindings.execution_authorization_approval,
        ),
    )
    for artifact, binding in pairs:
        if artifact.get("artifact_sha256") != content_sha256(artifact, "artifact_sha256"):
            raise ExecutionContextError("external approval self-pin is invalid")
        expected_binding = {
            "artifact_id": binding.artifact_id,
            "artifact_sha256": binding.artifact_sha256,
            "approved_context_sha256": binding.approved_context_sha256,
            "approver_identity": {
                "identity_id": binding.approver_identity.identity_id,
                "identity_kind": binding.approver_identity.identity_kind,
            },
        }
        if artifact != expected_binding or artifact["approved_context_sha256"] != approved_context:
            raise ExecutionContextError("external approval differs from immutable run binding")
        _registered_artifact(spec, "approval:", artifact["artifact_sha256"])


def load_verified_execution_context(
    *,
    run_spec_path: Path,
    membership_path: Path,
    units_path: Path,
    codebook_path: Path,
    calibration_path: Path,
    authorization_path: Path,
) -> VerifiedExecutionContext:
    """Issue an execution context after repository, evidence, and authority verification."""
    try:
        spec = load_run_spec(run_spec_path)
        validate_executable_run(spec.raw)
    except EmpiricalContractError as error:
        raise ExecutionContextError(str(error)) from error
    try:
        repository = Path(
            subprocess.run(
                ["git", "-C", str(run_spec_path.parent), "rev-parse", "--show-toplevel"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
        ).resolve()
    except (OSError, subprocess.CalledProcessError) as error:
        raise ExecutionContextError("run specification repository cannot be verified") from error
    try:
        relative_spec = run_spec_path.resolve().relative_to(repository)
        committed_spec = subprocess.run(
            ["git", "-C", str(repository), "show", f"HEAD:{relative_spec.as_posix()}"],
            check=True,
            capture_output=True,
        ).stdout
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        raise ExecutionContextError("run specification is not a committed HEAD artifact") from error
    if run_spec_path.resolve().read_bytes() != committed_spec:
        raise ExecutionContextError("run specification differs from its committed HEAD artifact")
    membership, _ = _json_object(membership_path, "membership")
    if membership.get("membership_sha256") != content_sha256(membership, "membership_sha256"):
        raise ExecutionContextError("membership self-pin is invalid")
    if membership.get("status") != "candidate_membership":
        raise ExecutionContextError("membership is not an approved candidate membership")
    _registered_artifact(spec, "membership:", membership["membership_sha256"])
    units_value, _ = _json_object(units_path, "source bundle")
    raw_units = units_value.get("units")
    if not isinstance(raw_units, list):
        raise ExecutionContextError("source bundle must contain a units array")
    units = canonical_units(raw_units)
    membership_rows = membership.get("membership")
    identities = [
        {"unit_id": unit["unit_id"], "unit_sha256": unit["unit_sha256"]} for unit in units
    ]
    if membership_rows != identities:
        raise ExecutionContextError("source bundle differs from exact membership")
    source_bundle_sha = canonical_source_bundle_sha256(units)
    codebook_value, codebook_bytes = _json_object(codebook_path, "codebook")
    codebook_sha = hashlib.sha256(codebook_bytes).hexdigest()
    _registered_artifact(spec, "codebook:", codebook_sha)
    codebook = _parse_codebook(codebook_value, codebook_sha)
    calibration, _ = _json_object(calibration_path, "calibration")
    authorization, _ = _json_object(authorization_path, "authorization")
    _require_authority(
        spec,
        membership,
        codebook_sha,
        source_bundle_sha,
        calibration,
        authorization,
    )
    receipt = hashlib.sha256(
        canonical_bytes(
            {
                "schema_version": "foio.empirical-verification-receipt.v1.0.0",
                "run_spec_sha256": spec.run_spec_sha256,
                "membership_sha256": membership["membership_sha256"],
                "source_bundle_sha256": source_bundle_sha,
                "codebook_sha256": codebook_sha,
                "calibration_sha256": calibration["calibration_sha256"],
                "authorization_sha256": authorization["authorization_sha256"],
                "repository_head": subprocess.run(
                    ["git", "-C", str(repository), "rev-parse", "HEAD"],
                    check=True,
                    capture_output=True,
                    text=True,
                ).stdout.strip(),
            }
        )
    ).hexdigest()
    return VerifiedExecutionContext(
        _CONSTRUCTION_TOKEN,
        run_spec=spec,
        repository=repository,
        membership=membership,
        units=tuple(units),
        codebook=codebook,
        calibration=calibration,
        authorization=authorization,
        source_bundle_sha256=source_bundle_sha,
        verification_receipt_sha256=receipt,
    )

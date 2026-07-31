"""Deterministic blinded packets for the shared empirical pipeline."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from .contracts import RunSpecification, canonical_bytes, content_sha256, seal_record
from .execution import ExecutionContextError, VerifiedExecutionContext

SHA256 = re.compile(r"^[0-9a-f]{64}$")
UNIT_FIELDS = frozenset({"unit_id", "unit_sha256", "text", "source_spans"})
REQUIRED_UNIT_FIELDS = frozenset({"unit_id", "unit_sha256", "text"})
LEAKAGE_MARKERS = ("annotation", "candidate", "extractor", "gold", "label", "prediction")
SCHEMA_DIR = Path(__file__).resolve().parents[3] / "schemas" / "json"
PACKET_FIELDS = frozenset(
    {
        "schema_version",
        "status",
        "run_id",
        "run_spec_sha256",
        "membership_sha256",
        "codebook_sha256",
        "calibration_sha256",
        "authorization_sha256",
        "source_bundle_sha256",
        "role_id",
        "blinded_to_peer_outputs",
        "blinded_to_candidate_extractor",
        "packet_can_authorize_execution",
        "units",
        "packet_sha256",
    }
)


class PacketContractError(ValueError):
    """Raised when blinded packet construction or validation fails closed."""


def _require_sha256(value: object, label: str) -> str:
    if not isinstance(value, str) or SHA256.fullmatch(value) is None:
        raise PacketContractError(f"{label} must be a lowercase SHA-256")
    return value


def _require_self_pin(record: dict[str, Any], field: str, label: str) -> None:
    if record.get(field) != content_sha256(record, field):
        raise PacketContractError(f"invalid {label} self-pin")


def _require_schema(record: dict[str, Any], filename: str, label: str) -> None:
    schema = json.loads((SCHEMA_DIR / filename).read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(record), key=lambda item: list(item.absolute_path))
    if errors:
        detail = "; ".join(
            f"{'/'.join(str(part) for part in error.absolute_path) or '<root>'}: {error.message}"
            for error in errors
        )
        raise PacketContractError(f"{label} schema validation failed: {detail}")


def canonical_unit_sha256(unit: dict[str, Any]) -> str:
    """Hash the canonical content-bearing identity of one packet unit."""
    preimage = {
        "unit_id": unit["unit_id"],
        "text": unit["text"],
        "source_spans": unit.get("source_spans", []),
    }
    return hashlib.sha256(canonical_bytes(preimage)).hexdigest()


def canonical_source_bundle_sha256(units: list[dict[str, Any]]) -> str:
    """Hash an ordered canonical packet-unit bundle."""
    return hashlib.sha256(canonical_bytes(units)).hexdigest()


def _approval_independent_content_sha256(
    record: dict[str, Any], *, excluded_fields: frozenset[str]
) -> str:
    content = {key: value for key, value in record.items() if key not in excluded_fields}
    return hashlib.sha256(canonical_bytes(content)).hexdigest()


def approved_execution_context_sha256(
    *,
    membership_sha256: str,
    codebook_sha256: str,
    source_bundle_sha256: str,
    calibration: dict[str, Any],
    authorization: dict[str, Any],
) -> str:
    """Bind approval-independent execution inputs without creating hash cycles."""
    context = {
        "schema_version": "foio.empirical-approved-execution-context.v1.0.0",
        "membership_sha256": membership_sha256,
        "codebook_sha256": codebook_sha256,
        "source_bundle_sha256": source_bundle_sha256,
        "calibration_content_sha256": _approval_independent_content_sha256(
            calibration,
            excluded_fields=frozenset(
                {"calibration_sha256", "external_approval", "run_spec_sha256"}
            ),
        ),
        "authorization_content_sha256": _approval_independent_content_sha256(
            authorization,
            excluded_fields=frozenset(
                {
                    "authorization_sha256",
                    "calibration_sha256",
                    "external_approval",
                    "run_spec_sha256",
                }
            ),
        ),
    }
    return hashlib.sha256(canonical_bytes(context)).hexdigest()


def _require_external_approval(
    approval: dict[str, Any], *, expected_context_sha256: str, label: str
) -> None:
    if approval.get("artifact_sha256") != content_sha256(approval, "artifact_sha256"):
        raise PacketContractError(f"invalid {label} external approval artifact self-pin")
    if approval.get("approved_context_sha256") != expected_context_sha256:
        raise PacketContractError(f"{label} does not bind the approved execution context")


def _require_run_spec_approval_binding(
    run_spec: RunSpecification, *, approval: dict[str, Any], label: str
) -> None:
    bindings = run_spec.authority_bindings
    if bindings is None:
        raise PacketContractError("run specification omits schema-loaded authority bindings")
    binding = (
        bindings.calibration_approval
        if label == "calibration"
        else bindings.execution_authorization_approval
    )
    expected = {
        "artifact_id": binding.artifact_id,
        "artifact_sha256": binding.artifact_sha256,
        "approved_context_sha256": binding.approved_context_sha256,
        "approver_identity": {
            "identity_id": binding.approver_identity.identity_id,
            "identity_kind": binding.approver_identity.identity_kind,
        },
    }
    if approval != expected:
        raise PacketContractError(f"run specification {label} approval binding mismatch")


def _require_capability(
    context: VerifiedExecutionContext, stage_kind: str, capability: str
) -> None:
    if not isinstance(context, VerifiedExecutionContext):
        raise PacketContractError("verified execution context is required")
    try:
        context.require_capability(stage_kind, capability)
    except ExecutionContextError as error:
        raise PacketContractError(str(error)) from error


def _membership_rows(membership: dict[str, Any]) -> list[dict[str, str]]:
    _require_self_pin(membership, "membership_sha256", "membership")
    if membership.get("status") != "candidate_membership":
        raise PacketContractError("membership must be a candidate membership")
    rows = membership.get("membership")
    if not isinstance(rows, list) or not rows:
        raise PacketContractError("membership must contain units")
    parsed: list[dict[str, str]] = []
    identities: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            raise PacketContractError("membership row must be an object")
        unit_id = row.get("unit_id")
        digest = row.get("unit_sha256")
        if not isinstance(unit_id, str) or not unit_id:
            raise PacketContractError("membership unit identity is invalid")
        _require_sha256(digest, "membership unit SHA-256")
        if unit_id in identities:
            raise PacketContractError("duplicate membership unit identity")
        identities.add(unit_id)
        parsed.append({"unit_id": unit_id, "unit_sha256": digest})
    return sorted(parsed, key=lambda row: (row["unit_id"], row["unit_sha256"]))


def _canonical_units(units: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not isinstance(units, list) or not units:
        raise PacketContractError("packet units must be a nonempty list")
    parsed: list[dict[str, Any]] = []
    identities: set[str] = set()
    for unit in units:
        if not isinstance(unit, dict):
            raise PacketContractError("packet unit must be an object")
        extras = set(unit) - UNIT_FIELDS
        if extras:
            if any(marker in key.lower() for key in extras for marker in LEAKAGE_MARKERS):
                raise PacketContractError("candidate or extractor leakage field rejected")
            raise PacketContractError("packet unit violates the strict field allowlist")
        if set(unit) < REQUIRED_UNIT_FIELDS:
            raise PacketContractError("packet unit is missing an allowlisted required field")
        unit_id = unit["unit_id"]
        if not isinstance(unit_id, str) or not unit_id:
            raise PacketContractError("packet unit identity is invalid")
        if unit_id in identities:
            raise PacketContractError("duplicate packet unit identity")
        identities.add(unit_id)
        _require_sha256(unit["unit_sha256"], "packet unit SHA-256")
        if not isinstance(unit["text"], str):
            raise PacketContractError("packet unit text must be a string")
        source_spans = unit.get("source_spans", [])
        if not isinstance(source_spans, list):
            raise PacketContractError("source spans must be an array")
        parsed_spans = []
        for span in source_spans:
            if not isinstance(span, dict) or set(span) != {"start", "end"}:
                raise PacketContractError("source span violates the strict field allowlist")
            start, end = span.get("start"), span.get("end")
            if (
                not isinstance(start, int)
                or isinstance(start, bool)
                or not isinstance(end, int)
                or isinstance(end, bool)
                or start < 0
                or end <= start
                or end > len(unit["text"])
            ):
                raise PacketContractError("source span is outside packet text")
            parsed_spans.append({"start": start, "end": end})
        if parsed_spans != sorted(parsed_spans, key=lambda item: (item["start"], item["end"])):
            raise PacketContractError("source spans must be sorted")
        parsed_unit = {
            "unit_id": unit_id,
            "unit_sha256": unit["unit_sha256"],
            "text": unit["text"],
            "source_spans": parsed_spans,
        }
        if canonical_unit_sha256(parsed_unit) != unit["unit_sha256"]:
            raise PacketContractError("packet unit SHA-256 does not bind canonical content")
        parsed.append(parsed_unit)
    return sorted(parsed, key=lambda row: (row["unit_id"], row["unit_sha256"]))


def _validate_execution_evidence(
    *,
    run_spec: RunSpecification,
    membership_sha256: str,
    codebook_sha256: str,
    roles: set[str],
    required_capability: str,
    source_bundle_sha256: str,
    calibration: dict[str, Any],
    authorization: dict[str, Any],
) -> None:
    _require_sha256(codebook_sha256, "codebook SHA-256")
    _require_schema(
        calibration,
        "australian-empirical-calibration-result.schema.json",
        "calibration",
    )
    _require_self_pin(calibration, "calibration_sha256", "calibration")
    if calibration.get("status") != "passed":
        raise PacketContractError("calibration status must be passed")
    expected = {
        "run_spec_sha256": run_spec.run_spec_sha256,
        "membership_sha256": membership_sha256,
        "codebook_sha256": codebook_sha256,
    }
    for field, value in expected.items():
        if calibration.get(field) != value:
            raise PacketContractError(f"calibration {field} mismatch")
    if set(calibration.get("role_ids", [])) != roles:
        raise PacketContractError("calibration roles mismatch")

    _require_schema(
        authorization,
        "australian-empirical-execution-authorization.schema.json",
        "authorization",
    )
    _require_self_pin(authorization, "authorization_sha256", "authorization")
    if authorization.get("status") != "approved":
        raise PacketContractError("external authorization status must be approved")
    expected["calibration_sha256"] = calibration["calibration_sha256"]
    for field, value in expected.items():
        if authorization.get(field) != value:
            raise PacketContractError(f"authorization {field} mismatch")
    if set(authorization.get("approved_roles", [])) != roles:
        raise PacketContractError("authorization roles mismatch")
    if required_capability not in authorization.get("capabilities", []):
        raise PacketContractError(f"authorization omits {required_capability}")

    expected_context_sha256 = approved_execution_context_sha256(
        membership_sha256=membership_sha256,
        codebook_sha256=codebook_sha256,
        source_bundle_sha256=source_bundle_sha256,
        calibration=calibration,
        authorization=authorization,
    )
    for label, approval in (
        ("calibration", calibration["external_approval"]),
        ("execution authorization", authorization["external_approval"]),
    ):
        _require_external_approval(
            approval,
            expected_context_sha256=expected_context_sha256,
            label=label,
        )
        _require_run_spec_approval_binding(run_spec, approval=approval, label=label)
    if calibration["calibrator_identity"] == authorization["authorizer_identity"]:
        raise PacketContractError("calibrator and external authorizer identities must be distinct")


def build_blinded_packets(
    *,
    context: VerifiedExecutionContext,
    annotator_roles: tuple[str, str],
    adjudicator_role: str,
) -> dict[str, dict[str, Any]]:
    """Build two identical-unit, role-specific packets under external approval."""
    _require_capability(context, "packet", "packet.generate")
    run_spec = context.run_spec
    membership = context.membership
    units = list(context.units)
    codebook_sha256 = context.codebook_sha256
    calibration = context.calibration
    authorization = context.authorization
    roles = {*annotator_roles, adjudicator_role}
    if len(roles) != 3 or any(not role for role in roles):
        raise PacketContractError("annotator and adjudicator roles must be distinct")
    membership_rows = _membership_rows(membership)
    canonical_units = _canonical_units(units)
    source_bundle_sha256 = canonical_source_bundle_sha256(canonical_units)
    if [
        {"unit_id": unit["unit_id"], "unit_sha256": unit["unit_sha256"]} for unit in canonical_units
    ] != membership_rows:
        raise PacketContractError("packet units differ from exact membership")
    _validate_execution_evidence(
        run_spec=run_spec,
        membership_sha256=membership["membership_sha256"],
        codebook_sha256=codebook_sha256,
        roles=roles,
        required_capability="packet.generate",
        source_bundle_sha256=source_bundle_sha256,
        calibration=calibration,
        authorization=authorization,
    )
    packets = {}
    for role in annotator_roles:
        packets[role] = seal_record(
            {
                "schema_version": "foio.empirical-blinded-packet.v1.0.0",
                "status": "blinded_packet",
                "run_id": run_spec.run_id,
                "run_spec_sha256": run_spec.run_spec_sha256,
                "membership_sha256": membership["membership_sha256"],
                "codebook_sha256": codebook_sha256,
                "calibration_sha256": calibration["calibration_sha256"],
                "authorization_sha256": authorization["authorization_sha256"],
                "source_bundle_sha256": source_bundle_sha256,
                "role_id": role,
                "blinded_to_peer_outputs": True,
                "blinded_to_candidate_extractor": True,
                "packet_can_authorize_execution": False,
                "units": canonical_units,
            },
            "packet_sha256",
        )
    return packets


def validate_blinded_packets(
    packets: dict[str, dict[str, Any]],
    *,
    context: VerifiedExecutionContext,
) -> None:
    """Validate pins, role isolation, membership, and identical blinded content."""
    run_spec = context.run_spec
    membership = context.membership
    units = list(context.units)
    codebook_sha256 = context.codebook_sha256
    calibration = context.calibration
    authorization = context.authorization
    if not isinstance(packets, dict) or len(packets) != 2:
        raise PacketContractError("exactly two annotator packets are required")
    membership_rows = _membership_rows(membership)
    role_set = set(packets)
    approved_roles = set(authorization.get("approved_roles", []))
    adjudicators = approved_roles - role_set
    if len(adjudicators) != 1:
        raise PacketContractError("annotator and adjudicator roles must be distinct")
    _require_capability(context, "packet", "packet.generate")
    _validate_execution_evidence(
        run_spec=run_spec,
        membership_sha256=membership["membership_sha256"],
        codebook_sha256=codebook_sha256,
        roles=approved_roles,
        required_capability="packet.generate",
        source_bundle_sha256=canonical_source_bundle_sha256(_canonical_units(units)),
        calibration=calibration,
        authorization=authorization,
    )
    canonical_source = _canonical_units(units)
    source_bundle_sha256 = canonical_source_bundle_sha256(canonical_source)
    common_units: list[dict[str, Any]] | None = None
    for role, packet in packets.items():
        if set(packet) != PACKET_FIELDS:
            raise PacketContractError("packet fields violate the strict field allowlist")
        _require_self_pin(packet, "packet_sha256", "packet")
        if packet.get("role_id") != role:
            raise PacketContractError("packet role mismatch")
        if packet.get("packet_can_authorize_execution") is not False:
            raise PacketContractError("generated packet cannot self-authorize")
        if (
            packet.get("blinded_to_peer_outputs") is not True
            or packet.get("blinded_to_candidate_extractor") is not True
        ):
            raise PacketContractError("packet is not fully blinded")
        for field, expected in (
            ("run_id", run_spec.run_id),
            ("run_spec_sha256", run_spec.run_spec_sha256),
            ("membership_sha256", membership["membership_sha256"]),
            ("codebook_sha256", codebook_sha256),
            ("calibration_sha256", calibration["calibration_sha256"]),
            ("authorization_sha256", authorization["authorization_sha256"]),
            ("source_bundle_sha256", source_bundle_sha256),
        ):
            if packet.get(field) != expected:
                raise PacketContractError(f"packet {field} mismatch")
        raw_packet_units = packet.get("units")
        if not isinstance(raw_packet_units, list):
            raise PacketContractError("packet units must be an array")
        packet_units = _canonical_units(raw_packet_units)
        identities = [
            {"unit_id": unit["unit_id"], "unit_sha256": unit["unit_sha256"]}
            for unit in packet_units
        ]
        if identities != membership_rows:
            raise PacketContractError("packet units differ from exact membership")
        if packet_units != canonical_source:
            raise PacketContractError("packet content differs from authorized source units")
        if common_units is not None and packet_units != common_units:
            raise PacketContractError(
                "annotator packets do not contain identical blinded unit sets"
            )
        common_units = packet_units

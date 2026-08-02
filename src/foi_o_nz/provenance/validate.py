"""Semantic validation for provenance envelopes."""

from __future__ import annotations

import hashlib
from typing import Any

from .canonical import CANONICALIZATION_ID, content_sha256
from .schema import schema_errors


class ProvenanceValidationError(ValueError):
    """Raised when a provenance invariant fails closed."""


def _require_self_pin(record: dict[str, Any], field: str) -> None:
    expected = content_sha256(record, field)
    if record.get(field) != expected:
        raise ProvenanceValidationError(f"invalid {field}")


def validate_envelope(envelope: dict[str, Any]) -> None:
    """Validate content identity, authorization, and population conservation."""
    structural_errors = schema_errors(envelope, "provenance-envelope.schema.json")
    if structural_errors:
        raise ProvenanceValidationError(
            "provenance envelope schema validation failed: " + "; ".join(structural_errors)
        )
    if envelope.get("schema_version") != "foio.provenance-envelope.v1.0.0":
        raise ProvenanceValidationError("unsupported provenance envelope version")
    if envelope.get("canonicalization") != CANONICALIZATION_ID:
        raise ProvenanceValidationError("unsupported canonicalization contract")

    contract = envelope.get("transformation_contract")
    authorization = envelope.get("authorization")
    if not isinstance(contract, dict) or not isinstance(authorization, dict):
        raise ProvenanceValidationError("contract and authorization records are required")
    _require_self_pin(contract, "contract_sha256")
    _require_self_pin(authorization, "authorization_sha256")
    occurrence = envelope["run_occurrence"]
    _require_self_pin(occurrence, "run_occurrence_sha256")
    _require_self_pin(envelope, "envelope_sha256")

    if authorization.get("transformation_contract_sha256") != contract["contract_sha256"]:
        raise ProvenanceValidationError("authorization contract pin mismatch")
    if authorization.get("transformation_id") != contract["contract_id"]:
        raise ProvenanceValidationError("authorization transformation id mismatch")
    if authorization.get("transformation_version") != contract["contract_version"]:
        raise ProvenanceValidationError("authorization transformation version mismatch")
    if authorization.get("run_id") != occurrence["run_id"]:
        raise ProvenanceValidationError("authorization run id mismatch")
    if authorization.get("run_occurrence_sha256") != occurrence["run_occurrence_sha256"]:
        raise ProvenanceValidationError("authorization run occurrence pin mismatch")

    approved_inputs = sorted(authorization["approved_input_sha256"])
    actual_inputs = sorted(item["sha256"] for item in envelope["inputs"])
    if approved_inputs != actual_inputs:
        raise ProvenanceValidationError("authorization approved input digest set mismatch")

    population = envelope["population"]
    if authorization.get("population_id") != population["population_id"]:
        raise ProvenanceValidationError("authorization population id mismatch")
    if authorization.get("population_sha256") != population["population_sha256"]:
        raise ProvenanceValidationError("authorization population pin mismatch")
    denied = authorization.get("denied_capabilities")
    allowed = authorization.get("allowed_capabilities")
    if not isinstance(denied, list) or not denied:
        raise ProvenanceValidationError("authorization must include a non-empty denial set")
    if not isinstance(allowed, list):
        raise ProvenanceValidationError("authorization allowed capabilities must be an array")
    if set(allowed) & set(denied):
        raise ProvenanceValidationError("allowed and denied capabilities overlap")
    missing_required = set(contract.get("required_capabilities", [])) - set(allowed)
    if missing_required:
        raise ProvenanceValidationError("transformation capabilities are not authorized")
    statement = authorization.get("approval_statement")
    if not isinstance(statement, str) or hashlib.sha256(statement.encode()).hexdigest() != (
        authorization.get("approval_statement_sha256")
    ):
        raise ProvenanceValidationError("approval statement hash mismatch")

    values = [population.get(key) for key in ("predecessor", "included", "excluded", "unresolved")]
    if any(not isinstance(value, int) or isinstance(value, bool) or value < 0 for value in values):
        raise ProvenanceValidationError("population counts must be non-negative integers")
    predecessor, included, excluded, unresolved = values
    if predecessor != included + excluded + unresolved:
        raise ProvenanceValidationError("population imbalance")

    effects = envelope.get("successor_effects")
    if not isinstance(effects, list):
        raise ProvenanceValidationError("successor effects must be an array")
    if effects and authorization.get("status") != "approved":
        raise ProvenanceValidationError("successor activation requires approved authorization")
    unauthorized = set(effects) - set(allowed)
    if unauthorized:
        raise ProvenanceValidationError("successor activation exceeds allowed capabilities")
    prohibited = set(contract.get("prohibited_successor_capabilities", []))
    if set(effects) & prohibited:
        raise ProvenanceValidationError("transformation contract prohibits successor activation")


def validate_attestation(
    attestation: dict[str, Any],
    *,
    expected_envelope_sha256: str | None = None,
) -> None:
    """Validate a structurally sound, content-addressed independent attestation."""
    structural_errors = schema_errors(attestation, "validation-attestation.schema.json")
    if structural_errors:
        raise ProvenanceValidationError(
            "validation attestation schema validation failed: " + "; ".join(structural_errors)
        )
    _require_self_pin(attestation, "attestation_sha256")
    checks_pass = all(check["passed"] for check in attestation["checks"])
    independently_valid = attestation["validator"]["independent_oracle"] and checks_pass
    if attestation["valid"] != independently_valid:
        raise ProvenanceValidationError(
            "attestation valid must equal independent-oracle status and all checks passing"
        )
    if (
        expected_envelope_sha256 is not None
        and attestation["validated_envelope_sha256"] != expected_envelope_sha256
    ):
        raise ProvenanceValidationError("attestation envelope pin mismatch")

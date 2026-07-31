"""Independent stdlib verifier for FOI-O provenance envelopes.

This program deliberately does not import the producer package, its builders,
or its canonicalization helper.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

SCHEMA_DIR = Path(__file__).resolve().parents[1] / "schemas" / "json"
SCHEMA_FILES = (
    "transformation-contract.schema.json",
    "authorization-record.schema.json",
    "validation-attestation.schema.json",
    "provenance-envelope.schema.json",
)


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _digest_without(record: dict[str, Any], field: str) -> str:
    body = {key: value for key, value in record.items() if key != field}
    return hashlib.sha256(_canonical_bytes(body)).hexdigest()


def _load_schemas() -> dict[str, dict[str, Any]]:
    return {
        name: json.loads((SCHEMA_DIR / name).read_text(encoding="utf-8")) for name in SCHEMA_FILES
    }


def _schema_errors(instance: Any, schema_name: str) -> list[str]:
    schemas = _load_schemas()
    registry = Registry().with_resources(
        [(schema["$id"], Resource.from_contents(schema)) for schema in schemas.values()]
    )
    validator = Draft202012Validator(
        schemas[schema_name],
        registry=registry,
        format_checker=FormatChecker(),
    )
    errors = sorted(validator.iter_errors(instance), key=lambda error: list(error.absolute_path))
    rendered: list[str] = []
    for error in errors:
        path = "/".join(str(part) for part in error.absolute_path) or "<root>"
        rendered.append(f"schema validation failed at {path}: {error.message}")
    return rendered


def verify(envelope: dict[str, Any]) -> list[str]:
    """Return fail-closed semantic errors without producer imports."""
    errors = _schema_errors(envelope, "provenance-envelope.schema.json")
    if errors:
        return errors
    if envelope.get("schema_version") != "foio.provenance-envelope.v1.0.0":
        errors.append("unsupported provenance envelope version")
    if envelope.get("canonicalization") != "foio.sorted-compact-json.v1":
        errors.append("unsupported canonicalization contract")

    contract = envelope.get("transformation_contract")
    auth = envelope.get("authorization")
    if not isinstance(contract, dict):
        errors.append("missing transformation contract")
        contract = {}
    if not isinstance(auth, dict):
        errors.append("missing authorization")
        auth = {}
    for record, field in (
        (contract, "contract_sha256"),
        (auth, "authorization_sha256"),
        (envelope["run_occurrence"], "run_occurrence_sha256"),
        (envelope, "envelope_sha256"),
    ):
        if record.get(field) != _digest_without(record, field):
            errors.append(f"invalid {field}")

    if auth.get("transformation_contract_sha256") != contract.get("contract_sha256"):
        errors.append("authorization contract pin mismatch")
    if auth.get("transformation_id") != contract.get("contract_id"):
        errors.append("authorization transformation id mismatch")
    if auth.get("transformation_version") != contract.get("contract_version"):
        errors.append("authorization transformation version mismatch")
    occurrence = envelope["run_occurrence"]
    if auth.get("run_id") != occurrence.get("run_id"):
        errors.append("authorization run id mismatch")
    if auth.get("run_occurrence_sha256") != occurrence.get("run_occurrence_sha256"):
        errors.append("authorization run occurrence pin mismatch")
    approved_inputs = sorted(auth["approved_input_sha256"])
    actual_inputs = sorted(item["sha256"] for item in envelope["inputs"])
    if approved_inputs != actual_inputs:
        errors.append("authorization approved input digest set mismatch")
    population = envelope["population"]
    if auth.get("population_id") != population.get("population_id"):
        errors.append("authorization population id mismatch")
    if auth.get("population_sha256") != population.get("population_sha256"):
        errors.append("authorization population pin mismatch")
    denied = auth.get("denied_capabilities")
    allowed = auth.get("allowed_capabilities")
    if not isinstance(denied, list) or not denied:
        errors.append("authorization must include a non-empty denial set")
        denied = []
    if not isinstance(allowed, list):
        errors.append("authorization allowed capabilities must be an array")
        allowed = []
    if set(allowed) & set(denied):
        errors.append("allowed and denied capabilities overlap")
    if set(contract.get("required_capabilities", [])) - set(allowed):
        errors.append("transformation capabilities are not authorized")
    statement = auth.get("approval_statement")
    if not isinstance(statement, str) or hashlib.sha256(statement.encode()).hexdigest() != auth.get(
        "approval_statement_sha256"
    ):
        errors.append("approval statement hash mismatch")

    values = [population.get(key) for key in ("predecessor", "included", "excluded", "unresolved")]
    if any(not isinstance(value, int) or isinstance(value, bool) or value < 0 for value in values):
        errors.append("population counts must be non-negative integers")
    elif values[0] != sum(values[1:]):
        errors.append("population imbalance")

    effects = envelope.get("successor_effects")
    if not isinstance(effects, list):
        errors.append("successor effects must be an array")
        effects = []
    if effects and auth.get("status") != "approved":
        errors.append("successor activation requires approved authorization")
    if set(effects) - set(allowed):
        errors.append("successor activation exceeds allowed capabilities")
    if set(effects) & set(contract.get("prohibited_successor_capabilities", [])):
        errors.append("transformation contract prohibits successor activation")
    return errors


def verify_attestation(
    attestation: dict[str, Any],
    *,
    expected_envelope_sha256: str | None = None,
) -> list[str]:
    """Independently validate one validation attestation."""
    errors = _schema_errors(attestation, "validation-attestation.schema.json")
    if errors:
        return errors
    if attestation.get("attestation_sha256") != _digest_without(
        attestation,
        "attestation_sha256",
    ):
        errors.append("invalid attestation_sha256")
    checks_pass = all(check["passed"] for check in attestation["checks"])
    independently_valid = attestation["validator"]["independent_oracle"] and checks_pass
    if attestation["valid"] != independently_valid:
        errors.append("attestation validity invariant failed")
    if (
        expected_envelope_sha256 is not None
        and attestation["validated_envelope_sha256"] != expected_envelope_sha256
    ):
        errors.append("attestation envelope pin mismatch")
    return errors


def main() -> int:
    """Verify one envelope and emit a machine-readable result."""
    parser = argparse.ArgumentParser()
    parser.add_argument("envelope", type=Path)
    parser.add_argument("--attestation", type=Path)
    args = parser.parse_args()
    envelope = json.loads(args.envelope.read_text(encoding="utf-8"))
    errors = verify(envelope)
    if args.attestation is not None:
        attestation = json.loads(args.attestation.read_text(encoding="utf-8"))
        expected = envelope.get("envelope_sha256") if not errors else None
        errors.extend(verify_attestation(attestation, expected_envelope_sha256=expected))
    print(json.dumps({"valid": not errors, "errors": errors}, sort_keys=True))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

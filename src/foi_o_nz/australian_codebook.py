"""Deterministic composition of shared Australian codebooks and overlays."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from datetime import date
from typing import Any

CORE_SCHEMA_VERSION = "foi-o.australian-codebook-core.v1"
OVERLAY_SCHEMA_VERSION = "foi-o.australian-codebook-overlay.v1"
RESOLVED_SCHEMA_VERSION = "foi-o.australian-resolved-codebook.v1"
CANONICALIZATION = "json-sort-keys-compact-utf8-v1"
ALLOWED_OVERRIDES = frozenset({"span_policy", "terminology", "calibration_examples"})
PRIMARY_LABELS = frozenset({"observed", "inferred", "candidate"})
ABSTENTION_REASONS = frozenset(
    {"missing_evidence", "insufficient_evidence", "out_of_scope", "other"}
)
PROTECTED_CORE_FIELDS = frozenset(
    {
        "label_semantics",
        "abstention_semantics",
        "evidence_boundaries",
        "serialization",
        "adjudication_trigger",
    }
)


def canonical_json_bytes(value: Any) -> bytes:
    """Serialize a JSON value using the codebook canonicalization contract."""
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    """Return the SHA-256 of canonical UTF-8 JSON."""
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _require_sha256(pin: Any, name: str) -> None:
    if not isinstance(pin, dict):
        raise ValueError(f"{name} pin is required")
    if not isinstance(pin.get("artifact_id"), str) or not pin["artifact_id"]:
        raise ValueError(f"{name} artifact_id is required")
    digest = pin.get("sha256")
    if (
        not isinstance(digest, str)
        or len(digest) != 64
        or any(character not in "0123456789abcdef" for character in digest)
    ):
        raise ValueError(f"{name} SHA-256 pin is required")


def _parse_date(value: Any, field: str) -> date:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be an ISO date")
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise ValueError(f"{field} must be an ISO date") from error


def _validate_core(core: dict[str, Any]) -> None:
    if core.get("schema_version") != CORE_SCHEMA_VERSION:
        raise ValueError("unsupported Australian core schema version")
    if not isinstance(core.get("core_id"), str) or not core["core_id"]:
        raise ValueError("core_id is required")
    if not isinstance(core.get("version"), str) or not core["version"]:
        raise ValueError("core version is required")
    if core.get("canonicalization") != CANONICALIZATION:
        raise ValueError("unsupported core canonicalization")
    if set(core.get("overlay_override_allowlist", [])) != ALLOWED_OVERRIDES:
        raise ValueError("core overlay override allowlist is incompatible")
    labels = core.get("label_semantics")
    if not isinstance(labels, list) or not labels:
        raise ValueError("core label semantics are required")
    label_ids = [label.get("id") for label in labels if isinstance(label, dict)]
    if len(label_ids) != len(labels) or len(set(label_ids)) != len(label_ids):
        raise ValueError("core label IDs must be present and unique")
    if set(label_ids) != PRIMARY_LABELS:
        raise ValueError(
            "primary labels must be observed, inferred, and candidate; "
            "unknown evidence must use null-label abstention"
        )
    span_policy = core.get("span_policy")
    if not isinstance(span_policy, dict):
        raise ValueError("core span policy is required")
    if set(span_policy.get("required_for", [])) != PRIMARY_LABELS:
        raise ValueError("spans must be required for every primary label")
    if span_policy.get("forbidden_for") != ["abstention"]:
        raise ValueError("spans must be forbidden for abstention")
    abstention = core.get("abstention_semantics")
    if not isinstance(abstention, dict):
        raise ValueError("core abstention semantics are required")
    if set(abstention.get("reasons", [])) != ABSTENTION_REASONS:
        raise ValueError("core abstention reasons are incompatible")
    serialization = core.get("serialization")
    if (
        not isinstance(serialization, dict)
        or serialization.get("null_label_means") != "abstention_only"
        or serialization.get("abstention_reason_required_when_null") is not True
    ):
        raise ValueError("null labels must unambiguously encode a reasoned abstention")

    legacy = core.get("legacy_compatibility")
    if legacy is not None:
        if not isinstance(legacy, dict):
            raise ValueError("legacy compatibility must be an object")
        _require_sha256(legacy.get("source_codebook"), "legacy source_codebook")
        mapping = legacy.get("label_mapping")
        expected_mapping = {
            "unknown": {
                "primary_label": None,
                "abstention_reason": "insufficient_evidence",
            }
        }
        if mapping != expected_mapping:
            raise ValueError(
                "legacy unknown compatibility requires an exact mapping to "
                "null-label insufficient_evidence abstention"
            )


def _validate_overlay(core: dict[str, Any], overlay: dict[str, Any]) -> None:
    if overlay.get("schema_version") != OVERLAY_SCHEMA_VERSION:
        raise ValueError("unsupported Australian overlay schema version")
    core_reference = overlay.get("core")
    if not isinstance(core_reference, dict):
        raise ValueError("overlay core reference is required")
    if (
        core_reference.get("core_id") != core["core_id"]
        or core_reference.get("version") != core["version"]
    ):
        raise ValueError("overlay references an incompatible core version")
    if core_reference.get("sha256") != canonical_sha256(core):
        raise ValueError("overlay core SHA-256 does not match the supplied core")

    jurisdiction = overlay.get("jurisdiction")
    profile = overlay.get("profile")
    regime = overlay.get("regime")
    if not isinstance(jurisdiction, str) or not jurisdiction.startswith("AU-"):
        raise ValueError("Australian jurisdiction is required")
    if not isinstance(profile, dict) or profile.get("jurisdiction") != jurisdiction:
        raise ValueError("profile jurisdiction does not match overlay jurisdiction")
    if not isinstance(regime, dict) or regime.get("jurisdiction") != jurisdiction:
        raise ValueError("regime jurisdiction does not match overlay jurisdiction")

    interval = overlay.get("effective_interval")
    if not isinstance(interval, dict):
        raise ValueError("effective interval is required")
    start = _parse_date(interval.get("start"), "effective_interval.start")
    end_value = interval.get("end")
    if end_value is not None and _parse_date(end_value, "effective_interval.end") < start:
        raise ValueError("effective interval end precedes start")

    pins = overlay.get("pins")
    if not isinstance(pins, dict):
        raise ValueError("source and ontology pins are required")
    _require_sha256(pins.get("source_pack"), "source_pack")
    _require_sha256(pins.get("ontology"), "ontology")

    assertions = overlay.get("assertions")
    if not isinstance(assertions, list) or not assertions:
        raise ValueError("at least one jurisdiction assertion is required")
    assertion_ids: list[str] = []
    for assertion in assertions:
        if not isinstance(assertion, dict):
            raise ValueError("assertions must be objects")
        assertion_id = assertion.get("id")
        if not isinstance(assertion_id, str) or not assertion_id:
            raise ValueError("assertion ID is required")
        assertion_ids.append(assertion_id)
        if assertion.get("jurisdiction") != jurisdiction:
            raise ValueError("assertion jurisdiction does not match overlay jurisdiction")
    if len(set(assertion_ids)) != len(assertion_ids):
        raise ValueError("duplicate assertion IDs are not allowed")

    overrides = overlay.get("overrides", {})
    if not isinstance(overrides, dict):
        raise ValueError("overrides must be an object")
    keys = set(overrides)
    protected = keys & PROTECTED_CORE_FIELDS
    if protected:
        raise ValueError(f"overlay cannot override core semantics: {sorted(protected)}")
    unknown = keys - ALLOWED_OVERRIDES
    if unknown:
        raise ValueError(f"overlay override is not allowlisted: {sorted(unknown)}")

    calibration_examples = overrides.get("calibration_examples", [])
    if not isinstance(calibration_examples, list):
        raise ValueError("calibration examples must be an array")
    for example in calibration_examples:
        if not isinstance(example, dict):
            raise ValueError("calibration examples must be objects")
        label = example.get("label")
        if label is None:
            if example.get("abstention_reason") not in ABSTENTION_REASONS:
                raise ValueError(
                    "null-label calibration examples require a registered abstention reason"
                )
        elif label not in PRIMARY_LABELS:
            raise ValueError(
                "calibration example labels must be primary labels or null abstentions"
            )
        elif "abstention_reason" in example:
            raise ValueError("labeled calibration examples cannot include an abstention reason")


def compose_australian_codebook(
    core: dict[str, Any],
    overlay: dict[str, Any],
) -> dict[str, Any]:
    """Validate and deterministically resolve one core and jurisdiction overlay."""
    _validate_core(core)
    _validate_overlay(core, overlay)

    core_copy = deepcopy(core)
    overlay_copy = deepcopy(overlay)
    resolved: dict[str, Any] = {
        "schema_version": RESOLVED_SCHEMA_VERSION,
        "canonicalization": CANONICALIZATION,
        "core": {
            "core_id": core_copy["core_id"],
            "version": core_copy["version"],
            "sha256": canonical_sha256(core_copy),
        },
        "overlay": {
            "overlay_id": overlay_copy["overlay_id"],
            "version": overlay_copy["version"],
            "sha256": canonical_sha256(overlay_copy),
        },
        "jurisdiction": overlay_copy["jurisdiction"],
        "profile": overlay_copy["profile"],
        "regime": overlay_copy["regime"],
        "effective_interval": overlay_copy["effective_interval"],
        "pins": overlay_copy["pins"],
        "label_semantics": core_copy["label_semantics"],
        "evidence_boundaries": core_copy["evidence_boundaries"],
        "span_policy": {
            **core_copy["span_policy"],
            **overlay_copy.get("overrides", {}).get("span_policy", {}),
        },
        "abstention_semantics": core_copy["abstention_semantics"],
        "serialization": core_copy["serialization"],
        "adjudication_trigger": core_copy["adjudication_trigger"],
        "terminology": overlay_copy.get("overrides", {}).get("terminology", {}),
        "calibration_examples": overlay_copy.get("overrides", {}).get("calibration_examples", []),
        "assertions": overlay_copy["assertions"],
    }
    if "legacy_compatibility" in core_copy:
        resolved["legacy_compatibility"] = core_copy["legacy_compatibility"]
    resolved["self_sha256"] = canonical_sha256(resolved)
    return resolved


def verify_resolved_codebook(value: dict[str, Any]) -> None:
    """Fail if a resolved bundle's self-pin does not match its canonical body."""
    claimed = value.get("self_sha256")
    body = {key: item for key, item in value.items() if key != "self_sha256"}
    if claimed != canonical_sha256(body):
        raise ValueError("resolved codebook self-pin mismatch")

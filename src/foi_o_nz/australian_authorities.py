"""Registry-driven Australian authority classification without legal inference."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from copy import deepcopy
from datetime import date
from typing import Any, cast

SCHEMA_VERSION = "foi-o.australian-authority-registry.v1"
RESULT_SCHEMA_VERSION = "foi-o.australian-authority-classification.v1"
CANONICALIZATION = "json-sort-keys-compact-utf8-v1"
AUSTRALIAN_JURISDICTIONS = frozenset(
    {
        "AU-CTH",
        "AU-NSW",
        "AU-VIC",
        "AU-QLD",
        "AU-SA",
        "AU-WA",
        "AU-TAS",
        "AU-ACT",
        "AU-NT",
    }
)
PROFILE_IDENTITIES = {
    "AU-CTH": ("foi-o-au-cth", "au-cth-foi"),
    "AU-NSW": ("foi-o-au-nsw", "au-nsw-gipa"),
    "AU-VIC": ("foi-o-au-vic", "au-vic-foi"),
    "AU-QLD": ("foi-o-au-qld", "au-qld-rti"),
    "AU-SA": ("foi-o-au-sa", "au-sa-foi"),
    "AU-WA": ("foi-o-au-wa", "au-wa-foi"),
    "AU-TAS": ("foi-o-au-tas", "au-tas-rti"),
    "AU-ACT": ("foi-o-au-act", "au-act-foi"),
    "AU-NT": ("foi-o-au-nt", "au-nt-information"),
}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def canonical_json_bytes(value: Any) -> bytes:
    """Serialize JSON using the registry's explicit canonicalization contract."""
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    """Return the SHA-256 digest of canonical JSON bytes."""
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def registry_self_sha256(registry: dict[str, Any]) -> str:
    """Calculate the registry self-pin over the body excluding the self-pin."""
    return canonical_sha256({key: value for key, value in registry.items() if key != "self_sha256"})


def _normalise(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def _parse_date(value: Any, field: str) -> date:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be an ISO date")
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise ValueError(f"{field} must be an ISO date") from error


def _validate_interval(value: Any, field: str) -> tuple[date, date | None]:
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be an object")
    start = _parse_date(value.get("start"), f"{field}.start")
    end_raw = value.get("end")
    end = None if end_raw is None else _parse_date(end_raw, f"{field}.end")
    if end is not None and end < start:
        raise ValueError(f"{field}.end precedes start")
    return start, end


def _active(interval: dict[str, Any], as_of: date) -> bool:
    start, end = _validate_interval(interval, "effective_interval")
    return start <= as_of and (end is None or as_of <= end)


def _interval_contains(
    parent: tuple[date, date | None],
    child: tuple[date, date | None],
) -> bool:
    parent_start, parent_end = parent
    child_start, child_end = child
    if child_start < parent_start:
        return False
    if parent_end is None:
        return True
    return child_end is not None and child_end <= parent_end


def _validate_pin(value: Any, field: str) -> None:
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be an evidence pin")
    if not isinstance(value.get("artifact_id"), str) or not value["artifact_id"]:
        raise ValueError(f"{field}.artifact_id is required")
    if not isinstance(value.get("sha256"), str) or not SHA256_RE.fullmatch(value["sha256"]):
        raise ValueError(f"{field}.sha256 must be lowercase SHA-256")


def validate_registry(registry: dict[str, Any]) -> None:
    """Validate semantic invariants and the canonical registry self-pin."""
    if registry.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("unsupported Australian authority registry schema version")
    if registry.get("canonicalization") != CANONICALIZATION:
        raise ValueError("unsupported authority registry canonicalization")
    if not isinstance(registry.get("registry_id"), str) or not registry["registry_id"]:
        raise ValueError("registry_id is required")
    if not isinstance(registry.get("version"), str) or not registry["version"]:
        raise ValueError("registry version is required")

    profiles = registry.get("profiles")
    if not isinstance(profiles, list):
        raise ValueError("profiles must be an array")
    profile_jurisdictions: set[str] = set()
    profile_ids: set[str] = set()
    regime_ids: set[str] = set()
    profiles_by_jurisdiction: dict[str, dict[str, Any]] = {}
    for index, profile in enumerate(profiles):
        if not isinstance(profile, dict):
            raise ValueError(f"profiles[{index}] must be an object")
        profile = cast("dict[str, Any]", profile)
        jurisdiction = profile.get("jurisdiction")
        profile_id = profile.get("profile_id")
        if not isinstance(jurisdiction, str) or jurisdiction not in AUSTRALIAN_JURISDICTIONS:
            raise ValueError(f"profiles[{index}] has unsupported jurisdiction")
        if not isinstance(profile_id, str) or not profile_id:
            raise ValueError(f"profiles[{index}].profile_id is required")
        regime_id = profile.get("regime_id")
        if not isinstance(regime_id, str) or not regime_id:
            raise ValueError(f"profiles[{index}].regime_id is required")
        if (profile_id, regime_id) != PROFILE_IDENTITIES[jurisdiction]:
            raise ValueError(f"profiles[{index}] jurisdiction/profile/regime identity mismatch")
        if (
            jurisdiction in profile_jurisdictions
            or profile_id in profile_ids
            or regime_id in regime_ids
        ):
            raise ValueError("profile jurisdictions, IDs, and regimes must be unique")
        _validate_interval(
            profile.get("effective_interval"),
            f"profiles[{index}].effective_interval",
        )
        _validate_pin(profile.get("source_pin"), f"profiles[{index}].source_pin")
        profile_jurisdictions.add(jurisdiction)
        profile_ids.add(profile_id)
        regime_ids.add(regime_id)
        profiles_by_jurisdiction[jurisdiction] = profile
    if profile_jurisdictions != AUSTRALIAN_JURISDICTIONS:
        missing = sorted(AUSTRALIAN_JURISDICTIONS - profile_jurisdictions)
        extra = sorted(profile_jurisdictions - AUSTRALIAN_JURISDICTIONS)
        raise ValueError(f"registry profile coverage mismatch: missing={missing}, extra={extra}")

    authorities = registry.get("authorities")
    if not isinstance(authorities, list) or not authorities:
        raise ValueError("authorities must be a non-empty array")
    authority_ids: set[str] = set()
    for index, authority in enumerate(authorities):
        if not isinstance(authority, dict):
            raise ValueError(f"authorities[{index}] must be an object")
        authority_id = authority.get("authority_id")
        jurisdiction = authority.get("jurisdiction")
        canonical_name = authority.get("canonical_name")
        if not isinstance(authority_id, str) or not authority_id:
            raise ValueError(f"authorities[{index}].authority_id is required")
        if not isinstance(jurisdiction, str) or jurisdiction not in profile_jurisdictions:
            raise ValueError(f"authorities[{index}] references an unknown jurisdiction")
        profile = profiles_by_jurisdiction[jurisdiction]
        expected_profile_id, expected_regime_id = PROFILE_IDENTITIES[jurisdiction]
        if (
            authority.get("profile_id") != expected_profile_id
            or authority.get("regime_id") != expected_regime_id
            or authority_id.split(":", maxsplit=1)[0] != jurisdiction.casefold()
        ):
            raise ValueError(f"authorities[{index}] jurisdiction/profile/regime identity mismatch")
        if authority_id in authority_ids:
            raise ValueError(f"duplicate authority_id: {authority_id}")
        if not isinstance(canonical_name, str) or not canonical_name:
            raise ValueError(f"authorities[{index}].canonical_name is required")
        authority_interval = _validate_interval(
            authority.get("effective_interval"),
            f"authorities[{index}].effective_interval",
        )
        profile_interval = _validate_interval(
            profile["effective_interval"],
            f"profiles[{jurisdiction}].effective_interval",
        )
        if not _interval_contains(profile_interval, authority_interval):
            raise ValueError(
                f"authorities[{index}] effective interval is outside its profile effective interval"
            )
        _validate_pin(authority.get("source_pin"), f"authorities[{index}].source_pin")
        for history_field in ("aliases", "tag_history"):
            history = authority.get(history_field)
            if not isinstance(history, list):
                raise ValueError(f"authorities[{index}].{history_field} must be an array")
            for item_index, item in enumerate(history):
                if not isinstance(item, dict) or not isinstance(item.get("value"), str):
                    raise ValueError(
                        f"authorities[{index}].{history_field}[{item_index}] is invalid"
                    )
                history_interval = _validate_interval(
                    item.get("effective_interval"),
                    (f"authorities[{index}].{history_field}[{item_index}].effective_interval"),
                )
                if not _interval_contains(authority_interval, history_interval):
                    raise ValueError(
                        f"authorities[{index}].{history_field}[{item_index}] effective "
                        "interval is outside its authority effective interval"
                    )
                _validate_pin(
                    item.get("source_pin"),
                    f"authorities[{index}].{history_field}[{item_index}].source_pin",
                )
        authority_ids.add(authority_id)

    if registry.get("self_sha256") != registry_self_sha256(registry):
        raise ValueError("authority registry self-pin mismatch")


def _profile_map(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {profile["jurisdiction"]: profile for profile in registry["profiles"]}


def _candidate(authority: dict[str, Any], *, basis: str, matched_value: str) -> dict[str, str]:
    return {
        "authority_id": authority["authority_id"],
        "jurisdiction": authority["jurisdiction"],
        "profile_id": authority["profile_id"],
        "basis": basis,
        "matched_value": matched_value,
    }


def classify_authority(
    evidence: dict[str, Any],
    registry: dict[str, Any],
    *,
    as_of: str,
) -> dict[str, Any]:
    """Classify authority evidence, preserving ambiguity and all source evidence.

    Stable authority identity and names take precedence over platform tags. This
    function classifies evidence provenance only; it does not infer a legal
    outcome, entitlement, deadline, exemption, or decision.
    """
    validate_registry(registry)
    when = _parse_date(as_of, "as_of")
    preserved = deepcopy(evidence)
    result: dict[str, Any] = {
        "schema_version": RESULT_SCHEMA_VERSION,
        "registry": {
            "registry_id": registry["registry_id"],
            "version": registry["version"],
            "sha256": registry["self_sha256"],
        },
        "as_of": as_of,
        "input_evidence": preserved,
        "disposition": "unresolved",
        "authority_id": None,
        "jurisdiction": None,
        "profile_id": None,
        "basis": [],
        "candidates": [],
        "conflicts": [],
        "legal_outcome_inferred": False,
    }

    scope = evidence.get("scope_disposition")
    if isinstance(scope, dict) and scope.get("status") == "out_of_scope":
        _validate_pin(scope.get("source_pin"), "scope_disposition.source_pin")
        result["disposition"] = "out_of_scope"
        result["basis"] = ["explicit_scope_disposition"]
        result["result_sha256"] = canonical_sha256(result)
        return result

    active_authorities = [
        authority
        for authority in registry["authorities"]
        if _active(authority["effective_interval"], when)
    ]
    authority_id = evidence.get("authority_id")
    authority_name = evidence.get("authority_name")
    tags_raw = evidence.get("tags", [])
    tags = tags_raw if isinstance(tags_raw, list) else []

    identity_matches: list[dict[str, str]] = []
    if isinstance(authority_id, str) and authority_id:
        identity_matches.extend(
            _candidate(
                authority,
                basis="canonical_authority_id",
                matched_value=authority_id,
            )
            for authority in active_authorities
            if authority["authority_id"] == authority_id
        )
    if not identity_matches and isinstance(authority_name, str) and authority_name:
        wanted = _normalise(authority_name)
        for authority in active_authorities:
            if _normalise(authority["canonical_name"]) == wanted:
                identity_matches.append(
                    _candidate(
                        authority,
                        basis="canonical_authority_name",
                        matched_value=authority_name,
                    )
                )
                continue
            for alias in authority["aliases"]:
                if (
                    _active(alias["effective_interval"], when)
                    and _normalise(alias["value"]) == wanted
                ):
                    identity_matches.append(
                        _candidate(
                            authority,
                            basis="authority_alias",
                            matched_value=authority_name,
                        )
                    )
                    break

    tag_matches: list[dict[str, str]] = []
    for tag in tags:
        if not isinstance(tag, str):
            continue
        wanted_tag = _normalise(tag)
        for authority in active_authorities:
            for history in authority["tag_history"]:
                if (
                    _active(history["effective_interval"], when)
                    and _normalise(history["value"]) == wanted_tag
                ):
                    tag_matches.append(
                        _candidate(
                            authority,
                            basis="platform_tag",
                            matched_value=tag,
                        )
                    )

    def unique_candidates(values: list[dict[str, str]]) -> list[dict[str, str]]:
        unique: dict[tuple[str, str], dict[str, str]] = {}
        for value in values:
            unique[(value["authority_id"], value["basis"])] = value
        return sorted(
            unique.values(),
            key=lambda item: (
                item["jurisdiction"],
                item["authority_id"],
                item["basis"],
            ),
        )

    identity_matches = unique_candidates(identity_matches)
    tag_matches = unique_candidates(tag_matches)
    identity_ids = {item["authority_id"] for item in identity_matches}
    tag_jurisdictions = {item["jurisdiction"] for item in tag_matches}
    profiles = _profile_map(registry)

    if len(identity_ids) == 1:
        selected = identity_matches[0]
        result.update(
            {
                "disposition": "classified",
                "authority_id": selected["authority_id"],
                "jurisdiction": selected["jurisdiction"],
                "profile_id": selected["profile_id"],
                "basis": sorted({item["basis"] for item in identity_matches}),
                "candidates": identity_matches,
            }
        )
        contradictory = sorted(tag_jurisdictions - {selected["jurisdiction"]})
        if contradictory:
            result["conflicts"] = [
                {
                    "kind": "identity_tag_jurisdiction_conflict",
                    "identity_jurisdiction": selected["jurisdiction"],
                    "tag_jurisdictions": contradictory,
                    "disposition": "identity_precedence_tags_retained",
                }
            ]
    elif len(identity_ids) > 1:
        result["disposition"] = "conflict"
        result["basis"] = sorted({item["basis"] for item in identity_matches})
        result["candidates"] = identity_matches
        result["conflicts"] = [
            {
                "kind": "ambiguous_identity_evidence",
                "authority_ids": sorted(identity_ids),
                "disposition": "human_registry_resolution_required",
            }
        ]
    elif len(tag_jurisdictions) == 1:
        jurisdiction = next(iter(tag_jurisdictions))
        result.update(
            {
                "disposition": "classified",
                "jurisdiction": jurisdiction,
                "profile_id": profiles[jurisdiction]["profile_id"],
                "basis": ["platform_tag"],
                "candidates": tag_matches,
            }
        )
    elif len(tag_jurisdictions) > 1:
        result["disposition"] = "conflict"
        result["basis"] = ["platform_tag"]
        result["candidates"] = tag_matches
        result["conflicts"] = [
            {
                "kind": "ambiguous_tag_only_jurisdiction",
                "jurisdictions": sorted(tag_jurisdictions),
                "disposition": "identity_evidence_required",
            }
        ]

    result["result_sha256"] = canonical_sha256(result)
    return result


def verify_classification_result(value: dict[str, Any]) -> None:
    """Verify a classification result's canonical content pin."""
    claimed = value.get("result_sha256")
    body = {key: item for key, item in value.items() if key != "result_sha256"}
    if claimed != canonical_sha256(body):
        raise ValueError("authority classification result pin mismatch")

"""Validate jurisdiction-profile lifecycle and promotion boundaries."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
REQUIRED_PROFILE_FIELDS = {
    "id",
    "jurisdiction",
    "regime",
    "version",
    "stage",
    "status",
    "source_pack",
    "capabilities",
    "human_gates",
}
REQUIRED_MATURITY_LEVELS = {
    "unassessed",
    "discovered",
    "candidate",
    "implemented_candidate",
    "independently_evaluated",
    "human_promoted",
    "stable",
    "blocked",
}
REQUIRED_PACK_FIELDS = {
    "platform",
    "archive",
    "normative",
    "nlp",
    "process",
    "conformance",
    "promotion",
}


def _load(root: Path, name: str) -> dict[str, Any]:
    value = yaml.safe_load((root / name).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{name} must contain a mapping")
    return value


def validate_documents(
    registry: dict[str, Any],
    maturity: dict[str, Any],
    pack_template: dict[str, Any],
    access_policy: dict[str, Any],
) -> list[str]:
    """Return deterministic errors for the four jurisdiction control documents."""
    errors: list[str] = []
    stages = registry.get("stages")
    profiles = registry.get("profiles")
    if not isinstance(stages, list) or not stages:
        errors.append("profiles/registry.yaml: stages must be a non-empty list")
        stages = []
    if not isinstance(profiles, list) or not profiles:
        errors.append("profiles/registry.yaml: profiles must be a non-empty list")
        profiles = []

    profile_ids: list[str] = []
    for index, profile in enumerate(profiles):
        if not isinstance(profile, dict):
            errors.append(f"profiles[{index}] must be a mapping")
            continue
        profile_id = str(profile.get("id", index))
        profile_ids.append(profile_id)
        missing = sorted(REQUIRED_PROFILE_FIELDS - set(profile))
        errors.extend(f"{profile_id}: missing {field}" for field in missing)
        if not SEMVER.fullmatch(str(profile.get("version", ""))):
            errors.append(f"{profile_id}: version must be semantic x.y.z")
        if profile.get("stage") not in stages:
            errors.append(f"{profile_id}: unknown lifecycle stage")
        source_pack = profile.get("source_pack")
        if not isinstance(source_pack, dict) or not source_pack.get("id"):
            errors.append(f"{profile_id}: source_pack.id is required")
        gates = profile.get("human_gates")
        if not isinstance(gates, list) or not gates:
            errors.append(f"{profile_id}: human_gates must be non-empty")
        if not isinstance(profile.get("capabilities"), dict):
            errors.append(f"{profile_id}: capabilities must be a mapping")
    errors.extend(
        f"duplicate profile id: {profile_id}"
        for profile_id in sorted({item for item in profile_ids if profile_ids.count(item) > 1})
    )

    dimensions = maturity.get("dimensions")
    levels = set(maturity.get("levels", []))
    maturity_profiles = maturity.get("profiles")
    if not isinstance(dimensions, list) or not dimensions:
        errors.append("profiles/capability-maturity.yaml: dimensions must be non-empty")
        dimensions = []
    if levels != REQUIRED_MATURITY_LEVELS:
        errors.append("profiles/capability-maturity.yaml: maturity levels are incomplete")
    if not isinstance(maturity_profiles, dict):
        errors.append("profiles/capability-maturity.yaml: profiles must be a mapping")
        maturity_profiles = {}
    for profile_id in profile_ids:
        if profile_id not in maturity_profiles:
            errors.append(f"{profile_id}: missing capability maturity entry")
    for profile_id, values in maturity_profiles.items():
        if profile_id not in profile_ids:
            errors.append(f"{profile_id}: maturity entry has no registry profile")
        if not isinstance(values, dict):
            errors.append(f"{profile_id}: maturity entry must be a mapping")
            continue
        for dimension, level in values.items():
            if dimension not in dimensions:
                errors.append(f"{profile_id}: unknown capability dimension {dimension}")
            if level not in levels:
                errors.append(f"{profile_id}: invalid maturity level for {dimension}")
    if maturity.get("aggregate_readiness_score") != "prohibited":
        errors.append("profiles/capability-maturity.yaml: aggregate scoring must be prohibited")

    if set(pack_template) < REQUIRED_PACK_FIELDS:
        errors.append("profiles/jurisdiction-pack-template.yaml: required pack sections missing")
    promotion = pack_template.get("promotion")
    if not isinstance(promotion, dict) or promotion.get("status") != "blocked":
        errors.append("profiles/jurisdiction-pack-template.yaml: promotion must start blocked")
    if not isinstance(promotion, dict) or not promotion.get("missing"):
        errors.append(
            "profiles/jurisdiction-pack-template.yaml: promotion missing-gates list required"
        )

    if access_policy.get("default_mode") != "offline_fixture_replay":
        errors.append("operations/access-policy.yaml: default mode must be offline_fixture_replay")
    network = access_policy.get("network_capture")
    if not isinstance(network, dict):
        errors.append("operations/access-policy.yaml: network_capture must be a mapping")
    else:
        required_conditions = {
            "robots_reviewed",
            "terms_reviewed",
            "rate_limits_recorded",
            "operator_approval_recorded",
        }
        if not required_conditions.issubset(set(network.get("allowed_only_when", []))):
            errors.append("operations/access-policy.yaml: live capture conditions are incomplete")
        prohibited = set(network.get("prohibited", []))
        for action in ("access_control_bypass", "unbounded_scraping", "autonomous_live_capture"):
            if action not in prohibited:
                errors.append(f"operations/access-policy.yaml: missing prohibition {action}")
    archive = access_policy.get("archive")
    if not isinstance(archive, dict) or archive.get("immutable_digest_required") is not True:
        errors.append("operations/access-policy.yaml: immutable archive digest is required")
    foio = access_policy.get("foio")
    if not isinstance(foio, dict) or foio.get("legal_interpretation") != "prohibited":
        errors.append(
            "operations/access-policy.yaml: FOI-O legal interpretation must be prohibited"
        )
    return errors


def validate(root: Path = ROOT) -> dict[str, Any]:
    """Validate the canonical profile controls under *root*."""
    registry = _load(root, "profiles/registry.yaml")
    errors = validate_documents(
        registry,
        _load(root, "profiles/capability-maturity.yaml"),
        _load(root, "profiles/jurisdiction-pack-template.yaml"),
        _load(root, "operations/access-policy.yaml"),
    )
    return {"ok": not errors, "profile_count": len(registry.get("profiles", [])), "errors": errors}


def main() -> None:
    result = validate()
    print(json.dumps(result, indent=2))
    if not result["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

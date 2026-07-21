"""Runtime reader for the canonical FOI-O capability registry.

The registry is deliberately a small policy boundary: exact profile context is
validated before a capability can be resolved, and descriptors generated from
it remain candidate/preparatory only.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field

DEFAULT_REGISTRY = Path("capabilities/registry.yaml")


class CapabilityContext(BaseModel):
    """Exact jurisdiction/profile context required before capability resolution."""

    model_config = ConfigDict(extra="forbid")

    source_platform: str = Field(min_length=1)
    jurisdiction: str = Field(min_length=1)
    regime: str = Field(min_length=1)
    profile_id: str = Field(min_length=1)
    profile_version: str = Field(min_length=1)
    source_snapshot_id: str = Field(min_length=1)
    effective_at: str = Field(min_length=1)
    mapping_version: str | None = None
    capability_maturity: str = "implemented_candidate"


class CapabilityResolution(BaseModel):
    """Resolved candidate capability with explicit non-certification boundaries."""

    model_config = ConfigDict(extra="forbid")

    capability_id: str
    version: str
    context: CapabilityContext
    status: str = "resolved_candidate"
    machine_certification_allowed: bool = False
    human_review_required: bool = True
    prohibited_follow_ons: list[str] = Field(default_factory=list)
    source_registry: str


def validate_registry(path: Path = DEFAULT_REGISTRY) -> dict[str, Any]:
    """Return a compact validation report for CI and local descriptor generation."""
    registry = load_capability_registry(path)
    required_fields = {
        "capability_id",
        "version",
        "input_schema",
        "output_schema",
        "minimum_maturity",
        "required_context",
        "effects",
        "human_review_required",
        "evaluation_suites",
    }
    missing = {
        str(item.get("capability_id", index)): sorted(required_fields - set(item))
        for index, item in enumerate(registry["capabilities"])
        if required_fields - set(item)
    }
    ids = [item.get("capability_id") for item in registry["capabilities"]]
    duplicates = sorted({item for item in ids if ids.count(item) > 1})
    return {
        "ok": not missing and not duplicates,
        "registry_id": registry.get("registry_id"),
        "version": registry.get("version"),
        "capability_count": len(ids),
        "missing_fields": missing,
        "duplicate_capability_ids": duplicates,
    }


def load_capability_registry(path: Path = DEFAULT_REGISTRY) -> dict[str, Any]:
    """Load and minimally validate the canonical registry without mutating it."""
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(document, dict) or not isinstance(document.get("capabilities"), list):
        raise ValueError("capability registry must contain a capabilities list")
    if document.get("defaults", {}).get("profile_required") is not True:
        raise ValueError("capability registry must require exact profile context")
    if document.get("defaults", {}).get("machine_certification_allowed") is not False:
        raise ValueError("capability registry must fail closed for machine certification")
    return document


def resolve_capability(
    capability_id: str,
    context: CapabilityContext,
    *,
    path: Path = DEFAULT_REGISTRY,
) -> CapabilityResolution:
    """Resolve a capability only after exact jurisdiction/profile context is present."""
    registry = load_capability_registry(path)
    descriptor = next(
        (item for item in registry["capabilities"] if item.get("capability_id") == capability_id),
        None,
    )
    if descriptor is None:
        raise ValueError(f"unknown capability: {capability_id}")
    required = descriptor.get("required_context", [])
    values = context.model_dump()
    missing = [key for key in required if not values.get(key)]
    if missing:
        raise ValueError(f"capability context is incomplete: {', '.join(missing)}")
    if descriptor.get("profile_capability") and not context.capability_maturity:
        raise ValueError("profile capability maturity is required")
    return CapabilityResolution(
        capability_id=capability_id,
        version=str(descriptor.get("version", "0.0.0")),
        context=context,
        machine_certification_allowed=False,
        human_review_required=bool(descriptor.get("human_review_required", True)),
        prohibited_follow_ons=list(descriptor.get("prohibited_follow_ons", [])),
        source_registry=str(path),
    )


def build_registry_manifest(*, path: Path = DEFAULT_REGISTRY) -> dict[str, Any]:
    """Generate a conservative descriptor inventory from the registry."""
    registry = load_capability_registry(path)
    return {
        "schema_version": "foio.capability-manifest.v1.0.0",
        "registry_id": registry.get("registry_id"),
        "registry_version": registry.get("version"),
        "machine_certification_allowed": False,
        "capabilities": [
            {
                "capability_id": item.get("capability_id"),
                "version": item.get("version"),
                "required_context": item.get("required_context", []),
                "input_schema": item.get("input_schema"),
                "output_schema": item.get("output_schema"),
                "human_review_required": item.get("human_review_required", True),
                "prohibited_follow_ons": item.get("prohibited_follow_ons", []),
                "read_only": True,
                "machine_certification_allowed": False,
            }
            for item in sorted(registry["capabilities"], key=lambda value: value["capability_id"])
        ],
    }

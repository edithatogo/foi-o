"""Machine-readable FOI-O contract capability declarations."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Literal

from pydantic import BaseModel, ConfigDict, Field

from foi_o_nz.io import write_json

if TYPE_CHECKING:
    from foi_o_nz.empirical_contracts import ExtractionContract, ExtractionMigration

UnknownVersionBehavior = Literal["reject", "retain_with_warning"]


class ContractCapability(BaseModel):
    """A consumer's support declaration for one versioned contract."""

    model_config = ConfigDict(extra="forbid")
    contract_id: str = Field(min_length=1)
    supported_versions: list[str] = Field(min_length=1)
    unknown_version_behavior: UnknownVersionBehavior = "reject"


class CapabilityDeclaration(BaseModel):
    """Versioned capability document exchanged by FOI-O consumers."""

    model_config = ConfigDict(extra="forbid")
    schema_version: Literal["foi-o-nz.capability-declaration.v0.1.0"] = (
        "foi-o-nz.capability-declaration.v0.1.0"
    )
    consumer_id: str = Field(min_length=1)
    capabilities: list[ContractCapability] = Field(min_length=1)


class NegotiationResult(BaseModel):
    """Deterministic result of negotiating one requested contract version."""

    model_config = ConfigDict(extra="forbid")
    contract_id: str
    requested_version: str
    accepted: bool
    reason: Literal["supported", "unknown_version_rejected", "unknown_version_retained"]


class ExtractionNegotiationResult(BaseModel):
    """Fail-closed result for one extraction-contract negotiation."""

    model_config = ConfigDict(extra="forbid")
    requested_version: str
    accepted: bool
    reason: Literal[
        "exact_version",
        "declared_range",
        "invalid_version_rejected",
        "unknown_major_rejected",
        "unsupported_revision_rejected",
        "missing_capability",
    ]
    missing_capability_ids: list[str] = Field(default_factory=list)


def _parse_semver(value: str) -> tuple[int, int, int] | None:
    """Parse strict three-component semver without coercing unknown syntax."""
    parts = value.split(".")
    if len(parts) != 3 or any(not part.isdigit() for part in parts):
        return None
    return int(parts[0]), int(parts[1]), int(parts[2])


def discover_extraction_capabilities(contract: ExtractionContract) -> list[str]:
    """Return the contract's declared capabilities without adding inferred support."""
    return list(contract.capability_ids)


def find_extraction_migration(
    contract: ExtractionContract, *, from_version: str
) -> ExtractionMigration | None:
    """Return only an explicitly declared migration for the requested source version."""
    return next(
        (
            migration
            for migration in contract.migration_catalogue
            if migration.from_version == from_version
        ),
        None,
    )


def negotiate_extraction_contract(
    contract: ExtractionContract,
    *,
    requested_version: str,
    required_capability_ids: list[str] | None = None,
) -> ExtractionNegotiationResult:
    """Negotiate a strict version and capability set with explicit rejection reasons."""
    required = required_capability_ids or []
    missing = sorted(set(required) - set(contract.capability_ids))
    if missing:
        return ExtractionNegotiationResult(
            requested_version=requested_version,
            accepted=False,
            reason="missing_capability",
            missing_capability_ids=missing,
        )
    requested = _parse_semver(requested_version)
    if requested is None:
        return ExtractionNegotiationResult(
            requested_version=requested_version,
            accepted=False,
            reason="invalid_version_rejected",
        )
    if requested_version in contract.compatibility.exact_versions:
        return ExtractionNegotiationResult(
            requested_version=requested_version,
            accepted=True,
            reason="exact_version",
        )
    for version_range in contract.compatibility.version_ranges:
        minimum = _parse_semver(version_range.minimum_inclusive)
        maximum = _parse_semver(version_range.maximum_exclusive)
        if minimum is not None and maximum is not None and minimum <= requested < maximum:
            return ExtractionNegotiationResult(
                requested_version=requested_version,
                accepted=True,
                reason="declared_range",
            )
    known_majors = {
        parsed[0]
        for version in contract.compatibility.exact_versions
        if (parsed := _parse_semver(version)) is not None
    }
    known_majors.update(
        parsed[0]
        for version_range in contract.compatibility.version_ranges
        if (parsed := _parse_semver(version_range.minimum_inclusive)) is not None
    )
    reason = (
        "unknown_major_rejected"
        if requested[0] not in known_majors
        else "unsupported_revision_rejected"
    )
    return ExtractionNegotiationResult(
        requested_version=requested_version,
        accepted=False,
        reason=reason,
    )


def negotiate_contract(
    declaration: CapabilityDeclaration, *, contract_id: str, requested_version: str
) -> NegotiationResult:
    """Negotiate a version without silently widening compatibility."""
    capability = next(
        (item for item in declaration.capabilities if item.contract_id == contract_id), None
    )
    if capability is not None and requested_version in capability.supported_versions:
        return NegotiationResult(
            contract_id=contract_id,
            requested_version=requested_version,
            accepted=True,
            reason="supported",
        )
    behavior = capability.unknown_version_behavior if capability is not None else "reject"
    return NegotiationResult(
        contract_id=contract_id,
        requested_version=requested_version,
        accepted=behavior == "retain_with_warning",
        reason=(
            "unknown_version_retained"
            if behavior == "retain_with_warning"
            else "unknown_version_rejected"
        ),
    )


def build_capability_declaration(consumer_id: str = "foi-o-nz") -> CapabilityDeclaration:
    """Build the default FOI-O producer declaration for downstream consumers."""
    return CapabilityDeclaration(
        consumer_id=consumer_id,
        capabilities=[
            ContractCapability(
                contract_id="foi-o-nz.core-event",
                supported_versions=["foi-o-nz.core-event.v0.1.0"],
            ),
            ContractCapability(
                contract_id="foi-o-nz.request-profile",
                supported_versions=["foi-o-nz.request-profile.v0.1.0"],
            ),
        ],
    )


def write_capability_declaration(output: Path, *, consumer_id: str = "foi-o-nz") -> dict[str, str]:
    """Write the default declaration as portable JSON."""
    declaration = build_capability_declaration(consumer_id)
    write_json(output, declaration.model_dump(mode="json"))
    return {"output": str(output), "consumer_id": consumer_id}

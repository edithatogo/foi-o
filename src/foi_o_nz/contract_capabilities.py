"""Machine-readable FOI-O contract capability declarations."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

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

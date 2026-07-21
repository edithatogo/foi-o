"""Profile-aware runtime boundary for candidate state mappings."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from foi_o_nz.capability_registry import CapabilityContext, CapabilityResolution, resolve_capability


class ProfileResolution(BaseModel):
    """Resolved profile and capability context for one bounded runtime call."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = "foio.profile-resolution.v1.0.0"
    context: CapabilityContext
    capability: CapabilityResolution
    status: str = "candidate_only"
    legal_certification: bool = False


class CandidateStateMapping(BaseModel):
    """Unknown-or-candidate platform mapping that cannot certify a legal outcome."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = "foio.candidate-state-mapping.v1.0.0"
    source_state: str = Field(min_length=1)
    mapped_state: str | None = None
    status: str = "candidate"
    profile_id: str
    profile_version: str
    mapping_version: str
    human_review_required: bool = True
    legal_certification: bool = False


def resolve_profile_context(
    context: CapabilityContext,
    *,
    capability_id: str = "foio.capability.map_platform_state",
) -> ProfileResolution:
    """Resolve exact profile and capability context before any mapping work."""
    capability = resolve_capability(capability_id, context)
    if capability_id.endswith("map_platform_state") and not context.mapping_version:
        raise ValueError("mapping_version is required for platform-state mapping")
    return ProfileResolution(context=context, capability=capability)


def map_platform_state_candidate(
    source_state: str,
    *,
    context: CapabilityContext,
    mapping: dict[str, str],
) -> CandidateStateMapping:
    """Return an unknown/candidate mapping; never emit a certified outcome."""
    resolution = resolve_profile_context(context)
    mapped = mapping.get(source_state)
    return CandidateStateMapping(
        source_state=source_state,
        mapped_state=mapped,
        status="candidate" if mapped is not None else "unknown",
        profile_id=resolution.context.profile_id,
        profile_version=resolution.context.profile_version,
        mapping_version=resolution.context.mapping_version or "unknown",
    )

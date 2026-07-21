"""Fail-closed readiness checks for Australian empirical validation inputs."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    """Reject undeclared contract fields."""

    model_config = ConfigDict(extra="forbid")


class ArtifactInput(StrictModel):
    """Reference one owner-repository artifact without copying its content."""

    owner_repo: str = Field(pattern=r"^edithatogo/[A-Za-z0-9._-]+$")
    repository_revision: str = Field(pattern=r"^[0-9a-f]{40}$")
    artifact_path: str | None
    artifact_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    status: Literal["missing", "candidate", "blocked", "placeholder", "approved"]
    rights_reviewed: bool
    independently_reviewed: bool
    known_limitation: str = Field(min_length=1)


class ProfileInputs(StrictModel):
    """Bind legal, archive and extraction artifacts to one exact profile."""

    profile_id: str
    jurisdiction: str
    legislation: ArtifactInput
    archive: ArtifactInput
    extraction: ArtifactInput


class SamplingInputs(StrictModel):
    """Record design inputs that must be approved before sample freeze."""

    protocol_path: str = Field(min_length=1)
    protocol_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    unit_of_analysis: Literal["request_linked_candidate_assertion"]
    strata: list[str] = Field(min_length=1)
    exclusions: list[str] = Field(min_length=1)
    codebook_revision: str | None = Field(default=None, pattern=r"^[0-9a-f]{40}$")
    sampling_configuration_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    configuration_approved: bool
    reliability_thresholds_approved: bool


class HumanRoles(StrictModel):
    """Keep independent human empirical roles explicit and non-inferable."""

    annotator_ids: list[str]
    adjudicator_id: str | None
    assignment_approved: bool


class AustralianEmpiricalReadiness(StrictModel):
    """Australian Commonwealth/NSW empirical-input readiness contract."""

    schema_version: Literal["foi-o.australian-empirical-readiness.v0.1.0"]
    recorded_at: str
    status: Literal["candidate_readiness"]
    profiles: list[ProfileInputs]
    sampling: SamplingInputs
    human_roles: HumanRoles
    sample_freeze_allowed: Literal[False]
    empirical_claims_allowed: Literal[False]
    profile_promotion_allowed: Literal[False]

    @model_validator(mode="after")
    def require_exact_pilot_profiles(self) -> AustralianEmpiricalReadiness:
        """Prevent accidental expansion or cross-profile substitution."""
        observed = {(item.profile_id, item.jurisdiction) for item in self.profiles}
        expected = {("foio-au-cth", "AU-CTH"), ("foio-au-nsw", "AU-NSW")}
        if observed != expected or len(self.profiles) != 2:
            raise ValueError("readiness contract must contain exactly AU-CTH and AU-NSW")
        if "jurisdiction" not in self.sampling.strata:
            raise ValueError("sampling strata must isolate jurisdiction")
        return self


class AustralianEmpiricalReadinessResult(StrictModel):
    """Deterministic readiness result; never a promotion decision."""

    ready: bool
    profile_ids: list[str]
    blockers: list[str]
    promotion_allowed: Literal[False] = False


def _placeholder_or_missing(value: str | None) -> bool:
    return value is None or len(value) != 64 or len(set(value)) == 1


def _artifact_ready(artifact: ArtifactInput) -> bool:
    return (
        artifact.status == "approved"
        and bool(artifact.artifact_path)
        and not _placeholder_or_missing(artifact.artifact_sha256)
        and artifact.rights_reviewed
        and artifact.independently_reviewed
    )


def audit_australian_empirical_readiness(
    manifest: AustralianEmpiricalReadiness,
) -> AustralianEmpiricalReadinessResult:
    """Enumerate every unmet pre-freeze requirement deterministically."""
    blockers: list[str] = []
    suffixes = {
        "legislation": "approved_source_pack_missing",
        "archive": "immutable_sample_missing",
        "extraction": "placeholder_or_missing",
    }
    for profile in sorted(manifest.profiles, key=lambda item: item.profile_id):
        for field, suffix in suffixes.items():
            artifact = getattr(profile, field)
            if not _artifact_ready(artifact):
                blockers.append(f"{profile.profile_id}.{field}.{suffix}")

    sampling = manifest.sampling
    if sampling.codebook_revision is None:
        blockers.append("sampling.codebook_revision_missing")
    if sampling.sampling_configuration_sha256 is None or not sampling.configuration_approved:
        blockers.append("sampling.configuration_not_approved")
    if not sampling.reliability_thresholds_approved:
        blockers.append("sampling.reliability_thresholds_not_approved")

    roles = manifest.human_roles
    annotators = roles.annotator_ids
    if (
        len(annotators) != 2
        or len(set(annotators)) != 2
        or not all(item.startswith("human:") for item in annotators)
    ):
        blockers.append("human_roles.two_independent_annotators_missing")
    if roles.adjudicator_id is None or not roles.adjudicator_id.startswith("human:"):
        blockers.append("human_roles.adjudicator_missing")
    elif roles.adjudicator_id in annotators:
        blockers.append("human_roles.adjudicator_not_independent")
    if not roles.assignment_approved:
        blockers.append("human_roles.assignment_not_approved")

    return AustralianEmpiricalReadinessResult(
        ready=not blockers,
        profile_ids=sorted(item.profile_id for item in manifest.profiles),
        blockers=sorted(blockers),
    )

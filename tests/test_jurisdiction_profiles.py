"""Red-phase contract tests for jurisdiction-specific FOI-O profiles."""

from __future__ import annotations

from datetime import UTC, date, datetime

import pytest
from pydantic import ValidationError

from foi_o_nz.empirical_contracts import JurisdictionProfile


def _source(jurisdiction: str = "AU-COM") -> dict[str, object]:
    return {
        "source_id": f"{jurisdiction.lower()}.foi.act.2025",
        "jurisdiction": jurisdiction,
        "source_type": "act",
        "title": "Freedom of Information Act",
        "provider": "Official legislation register",
        "source_uri": "https://example.gov.au/foi-act",
        "authority_level": "binding_law",
        "effective_time": {"from": "2025-01-01", "to": None},
        "observation_time": {
            "observed_at": "2025-01-02T00:00:00Z",
            "retrieved_at": "2025-01-03T00:00:00Z",
        },
        "version": {"source_version_id": "2025-current"},
        "integrity": {"sha256": "a" * 64},
        "rights": {
            "access_basis": "official public register",
            "redistribution_status": "metadata_only",
        },
        "review_status": "human_reviewed",
    }


def _profile(**overrides: object) -> dict[str, object]:
    profile: dict[str, object] = {
        "profile_id": "foi-o-au-com-v0.1.0",
        "jurisdiction": "AU-COM",
        "name": "Australian Commonwealth FOI profile",
        "status": "candidate",
        "core_compatibility": "foi-o-core.v0.1.0",
        "supported_surfaces": ["requests", "decisions"],
        "unsupported_surfaces": ["proactive_release"],
        "uncertain_surfaces": ["disclosure_logs"],
        "human_certified_surfaces": [],
        "sources": [_source()],
        "provenance": {
            "source_manifest_id": "legislation-au-2025-01",
            "source_manifest_sha256": "b" * 64,
            "generated_at": "2025-02-01T00:00:00Z",
            "generated_by": "foi-o-profile-builder/0.1.0",
        },
    }
    profile.update(overrides)
    return profile


def test_profile_preserves_identity_temporal_sources_and_provenance() -> None:
    profile = JurisdictionProfile.model_validate(_profile())

    assert profile.jurisdiction == "AU-COM"
    assert profile.sources[0].effective_time.from_ == date(2025, 1, 1)
    assert profile.provenance.source_manifest_id == "legislation-au-2025-01"
    assert profile.provenance.generated_at == datetime(2025, 2, 1, tzinfo=UTC)


def test_profile_requires_explicit_supported_unsupported_and_uncertain_surfaces() -> None:
    payload = _profile()
    del payload["uncertain_surfaces"]

    with pytest.raises(ValidationError):
        JurisdictionProfile.model_validate(payload)


def test_profile_rejects_sources_from_another_jurisdiction() -> None:
    with pytest.raises(ValidationError, match="jurisdiction"):
        JurisdictionProfile.model_validate(_profile(sources=[_source("NZ")]))


def test_profile_cannot_claim_certification_without_human_certification() -> None:
    with pytest.raises(ValidationError, match="certif"):
        JurisdictionProfile.model_validate(
            _profile(
                status="validated",
                human_certified_surfaces=["requests"],
                provenance={
                    "source_manifest_id": "legislation-au-2025-01",
                    "source_manifest_sha256": "b" * 64,
                    "generated_at": "2025-02-01T00:00:00Z",
                    "generated_by": "foi-o-profile-builder/0.1.0",
                    "certified_by": "human-review-board",
                    "certified_at": "2025-02-02T00:00:00Z",
                },
            )
        )

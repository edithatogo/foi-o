from datetime import UTC, datetime

import pytest

from foi_o_nz.capability_registry import (
    CapabilityContext,
    build_registry_manifest,
    resolve_capability,
)
from foi_o_nz.context_pack import (
    ContextPlan,
    build_claim_evidence_record,
    build_context_diff,
    compile_context_pack,
)
from foi_o_nz.profile_runtime import map_platform_state_candidate, resolve_profile_context


def _plan(**overrides):
    values = {
        "task_id": "task-1",
        "request_id": "request-1",
        "jurisdiction": "NZ",
        "regime": "OIA",
        "profile_id": "foio-nz-oia",
        "profile_version": "1.0.0",
        "source_snapshot_id": "snapshot-1",
        "legal_source_pack_id": "laws-1",
        "effective_at": datetime(2026, 7, 20, tzinfo=UTC),
        "capability_id": "foio.capability.context.compile",
        "privacy_class": "restricted",
        "token_budget": 1000,
        "prompt_version": "prompt-1",
        "tool_version": "tool-1",
        "model_version": "model-1",
    }
    values.update(overrides)
    return ContextPlan.model_validate(values)


def test_context_diff_recommends_abstention_when_evidence_is_removed():
    plan = _plan()
    before = compile_context_pack(
        plan,
        request={"request_id": "request-1"},
        evidence=[
            {
                "evidence_id": "e-1",
                "request_id": "request-1",
                "profile_id": "foio-nz-oia",
                "profile_version": "1.0.0",
            }
        ],
    )
    after = compile_context_pack(plan, request={"request_id": "request-1"}, evidence=[])
    diff = build_context_diff(before, after)
    assert diff.removed_decisive_evidence == ["e-1"]
    assert diff.abstention_recommended is True


def test_claim_record_abstains_without_evidence_and_flags_conflict():
    assert (
        build_claim_evidence_record(claim_id="c-1", claim_text="x", evidence_ids=[]).status
        == "abstained"
    )
    record = build_claim_evidence_record(
        claim_id="c-2", claim_text="x", evidence_ids=["e-1"], conflicts=[{"conflict_id": "conf-1"}]
    )
    assert record.status == "conflicted"
    assert record.machine_certification_allowed is False


def test_registry_requires_exact_profile_context_and_emits_safe_manifest():
    context = CapabilityContext(
        source_platform="fyi",
        jurisdiction="NZ",
        regime="OIA",
        profile_id="foio-nz-oia",
        profile_version="1.0.0",
        source_snapshot_id="snapshot-1",
        effective_at="2026-07-20T00:00:00Z",
        mapping_version="map-1",
    )
    resolution = resolve_capability("foio.capability.map_platform_state", context)
    assert resolution.machine_certification_allowed is False
    manifest = build_registry_manifest()
    assert manifest["machine_certification_allowed"] is False
    assert manifest["capabilities"]


def test_profile_runtime_returns_unknown_for_unmapped_state():
    context = CapabilityContext(
        source_platform="fyi",
        jurisdiction="NZ",
        regime="OIA",
        profile_id="foio-nz-oia",
        profile_version="1.0.0",
        source_snapshot_id="snapshot-1",
        effective_at="2026-07-20T00:00:00Z",
        mapping_version="map-1",
    )
    result = map_platform_state_candidate("future-state", context=context, mapping={})
    assert result.status == "unknown"
    assert result.legal_certification is False


def test_profile_runtime_fails_without_mapping_version():
    context = CapabilityContext(
        source_platform="fyi",
        jurisdiction="NZ",
        regime="OIA",
        profile_id="foio-nz-oia",
        profile_version="1.0.0",
        source_snapshot_id="snapshot-1",
        effective_at="2026-07-20T00:00:00Z",
    )
    with pytest.raises(ValueError, match="mapping_version"):
        resolve_profile_context(context)

from datetime import UTC, datetime

import pytest

from foi_o_nz.context_pack import ContextPlan, compile_context_pack


def _plan(**overrides: object) -> ContextPlan:
    values: dict[str, object] = {
        "task_id": "task-1",
        "request_id": "req-a",
        "jurisdiction": "NZ",
        "regime": "OIA",
        "profile_id": "foi-o-nz-oia",
        "profile_version": "0.9.0",
        "source_snapshot_id": "snapshot-1",
        "legal_source_pack_id": "nz-oia-pack-1",
        "effective_at": datetime(2026, 7, 20, tzinfo=UTC),
        "capability_id": "foio.capability.context.compile",
        "privacy_class": "public",
        "token_budget": 1000,
        "prompt_version": "prompt-1",
        "tool_version": "tool-1",
        "model_version": "model-1",
    }
    values.update(overrides)
    return ContextPlan.model_validate(values)


def _record(
    evidence_id: str, request_id: str = "req-a", profile_version: str = "0.9.0"
) -> dict[str, object]:
    return {
        "evidence_id": evidence_id,
        "request_id": request_id,
        "profile_id": "foi-o-nz-oia",
        "profile_version": profile_version,
        "text": "evidence only",
    }


def test_missing_request_fails_closed() -> None:
    with pytest.raises(ValueError, match="missing"):
        compile_context_pack(_plan(), request=None, evidence=[])


def test_request_and_profile_mismatches_are_excluded() -> None:
    pack = compile_context_pack(
        _plan(),
        request={"request_id": "req-a"},
        evidence=[
            _record("a"),
            _record("b", request_id="req-b"),
            _record("c", profile_version="0.8.0"),
        ],
    )
    assert [item["evidence_id"] for item in pack.included] == ["a"]
    assert {item["evidence_id"] for item in pack.excluded} == {"b", "c"}


def test_canonical_reordering_is_stable() -> None:
    plan = _plan()
    left = compile_context_pack(
        plan, request={"request_id": "req-a", "z": 1}, evidence=[_record("b"), _record("a")]
    )
    right = compile_context_pack(
        plan, request={"z": 1, "request_id": "req-a"}, evidence=[_record("a"), _record("b")]
    )
    assert left.pack_id == right.pack_id


def test_cross_profile_requires_comparative_capability() -> None:
    pack = compile_context_pack(
        _plan(allow_cross_profile=True),
        request={"request_id": "req-a"},
        evidence=[_record("a", profile_version="0.8.0")],
    )
    assert pack.included == []
    assert "cross_profile_capability_not_authorised" in pack.excluded[0]["reason"]

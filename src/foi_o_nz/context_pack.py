"""Fail-closed, request/profile-aware context compilation.

This module is the versioned successor to the legacy agent pack builder.  It
keeps source text as evidence, filters before ranking, and hashes the complete
canonical selection rather than a subset of file-level counters.
"""

from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from foi_o_nz.ledger import canonical_record_json

CONTEXT_PLAN_VERSION = "foio.context-plan.v1.0.0"
CONTEXT_PACK_VERSION = "foio.context-pack.v1.0.0"
CONTEXT_DIFF_VERSION = "foio.context-diff.v1.0.0"
CLAIM_EVIDENCE_VERSION = "foio.claim-evidence-conflict.v1.0.0"


class ContextPlan(BaseModel):
    """Immutable input describing the exact context permitted for a task."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["foio.context-plan.v1.0.0"] = CONTEXT_PLAN_VERSION
    task_id: str = Field(min_length=1)
    request_id: str = Field(min_length=1)
    jurisdiction: str = Field(min_length=1)
    regime: str = Field(min_length=1)
    profile_id: str = Field(min_length=1)
    profile_version: str = Field(min_length=1)
    source_snapshot_id: str = Field(min_length=1)
    legal_source_pack_id: str = Field(min_length=1)
    effective_at: datetime
    capability_id: str = Field(min_length=1)
    privacy_class: str = Field(min_length=1)
    token_budget: int = Field(gt=0)
    retrieval_query: str = ""
    retrieval_configuration: dict[str, Any] = Field(default_factory=dict)
    prompt_version: str = Field(min_length=1)
    tool_version: str = Field(min_length=1)
    model_version: str = Field(min_length=1)
    allow_cross_request: bool = False
    allow_cross_profile: bool = False
    allow_partial: bool = False
    comparative_capability: bool = False


class ContextPack(BaseModel):
    """Compiled context and its complete selection/provenance record."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["foio.context-pack.v1.0.0"] = CONTEXT_PACK_VERSION
    pack_id: str = Field(min_length=1)
    generated_at: datetime
    plan: ContextPlan
    request: dict[str, Any]
    included: list[dict[str, Any]] = Field(default_factory=list)
    excluded: list[dict[str, Any]] = Field(default_factory=list)
    truncated: list[dict[str, Any]] = Field(default_factory=list)
    known_missing: list[str] = Field(default_factory=list)
    unavailable_attachments: list[str] = Field(default_factory=list)
    conflicts: list[dict[str, Any]] = Field(default_factory=list)
    unresolved_authority_identity: list[str] = Field(default_factory=list)
    constraints: dict[str, Any]


class ContextDiff(BaseModel):
    """Structured, conservative comparison of two compiled context packs."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["foio.context-diff.v1.0.0"] = CONTEXT_DIFF_VERSION
    before_pack_id: str
    after_pack_id: str
    changed_plan_fields: list[str] = Field(default_factory=list)
    added_evidence_ids: list[str] = Field(default_factory=list)
    removed_evidence_ids: list[str] = Field(default_factory=list)
    modified_evidence_ids: list[str] = Field(default_factory=list)
    changed_constraints: list[str] = Field(default_factory=list)
    new_conflicts: list[dict[str, Any]] = Field(default_factory=list)
    removed_decisive_evidence: list[str] = Field(default_factory=list)
    abstention_recommended: bool = False
    reasons: list[str] = Field(default_factory=list)


class ClaimEvidenceRecord(BaseModel):
    """A typed claim/evidence/conflict record; never a legal certification."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["foio.claim-evidence-conflict.v1.0.0"] = CLAIM_EVIDENCE_VERSION
    claim_id: str = Field(min_length=1)
    claim_text: str = Field(min_length=1)
    status: Literal["candidate", "supported", "conflicted", "abstained"]
    evidence_ids: list[str] = Field(default_factory=list)
    conflict_ids: list[str] = Field(default_factory=list)
    derivation: dict[str, Any] = Field(default_factory=dict)
    human_review_required: bool = True
    machine_certification_allowed: Literal[False] = False


def _material_evidence(pack: ContextPack) -> dict[str, dict[str, Any]]:
    return {item["evidence_id"]: item for item in pack.included}


def build_context_diff(before: ContextPack, after: ContextPack) -> ContextDiff:
    """Compare context packs and recommend abstention for decisive removals/conflicts."""
    before_plan = before.plan.model_dump(mode="json")
    after_plan = after.plan.model_dump(mode="json")
    changed_plan_fields = sorted(
        key
        for key in set(before_plan) | set(after_plan)
        if before_plan.get(key) != after_plan.get(key)
    )
    before_items = _material_evidence(before)
    after_items = _material_evidence(after)
    before_ids = set(before_items)
    after_ids = set(after_items)
    modified = sorted(
        key for key in before_ids & after_ids if before_items[key] != after_items[key]
    )
    changed_constraints = sorted(
        key
        for key in set(before.constraints) | set(after.constraints)
        if before.constraints.get(key) != after.constraints.get(key)
    )
    new_conflicts = [conflict for conflict in after.conflicts if conflict not in before.conflicts]
    removed = sorted(before_ids - after_ids)
    reasons: list[str] = []
    if removed:
        reasons.append("included_evidence_removed")
    if new_conflicts:
        reasons.append("new_conflict_detected")
    if changed_plan_fields:
        reasons.append("context_plan_changed")
    if changed_constraints:
        reasons.append("context_constraints_changed")
    return ContextDiff(
        before_pack_id=before.pack_id,
        after_pack_id=after.pack_id,
        changed_plan_fields=changed_plan_fields,
        added_evidence_ids=sorted(after_ids - before_ids),
        removed_evidence_ids=removed,
        modified_evidence_ids=modified,
        changed_constraints=changed_constraints,
        new_conflicts=new_conflicts,
        removed_decisive_evidence=removed,
        abstention_recommended=bool(removed or new_conflicts),
        reasons=reasons,
    )


def build_claim_evidence_record(
    *,
    claim_id: str,
    claim_text: str,
    evidence_ids: list[str],
    conflicts: list[dict[str, Any]] | None = None,
    derivation: dict[str, Any] | None = None,
) -> ClaimEvidenceRecord:
    """Build a reviewable claim record, abstaining when evidence conflicts or is absent."""
    conflict_records = conflicts or []
    if not evidence_ids:
        status: Literal["candidate", "supported", "conflicted", "abstained"] = "abstained"
    elif conflict_records:
        status = "conflicted"
    else:
        status = "candidate"
    return ClaimEvidenceRecord(
        claim_id=claim_id,
        claim_text=claim_text,
        status=status,
        evidence_ids=sorted(set(evidence_ids)),
        conflict_ids=[
            str(item.get("conflict_id", f"conflict-{index}"))
            for index, item in enumerate(conflict_records)
        ],
        derivation=derivation or {},
    )


def _request_id(record: dict[str, Any]) -> str | None:
    value = record.get("request_id")
    if value is not None:
        return str(value)
    reference = record.get("request_ref")
    if isinstance(reference, dict) and reference.get("source_request_id") is not None:
        return str(reference["source_request_id"])
    return None


def _profile(record: dict[str, Any]) -> tuple[str | None, str | None]:
    profile = record.get("profile")
    if isinstance(profile, dict):
        return (
            str(profile.get("profile_id")) if profile.get("profile_id") is not None else None,
            str(profile.get("profile_version"))
            if profile.get("profile_version") is not None
            else None,
        )
    return (
        str(record["profile_id"]) if record.get("profile_id") is not None else None,
        str(record["profile_version"]) if record.get("profile_version") is not None else None,
    )


def _evidence_id(record: dict[str, Any], index: int) -> str:
    for key in ("evidence_id", "chunk_id", "event_id", "source_id", "record_id"):
        if record.get(key) is not None:
            return str(record[key])
    return f"evidence-{index}"


def _digest(value: Any) -> str:
    return sha256(canonical_record_json(value).encode("utf-8")).hexdigest()


def compile_context_pack(
    plan: ContextPlan,
    *,
    request: dict[str, Any] | None,
    evidence: list[dict[str, Any]] | None = None,
    known_missing: list[str] | None = None,
    unavailable_attachments: list[str] | None = None,
    conflicts: list[dict[str, Any]] | None = None,
) -> ContextPack:
    """Compile only evidence compatible with the immutable plan.

    Mismatched records are retained in the exclusion ledger.  They are never
    silently ranked into the pack, and a missing request fails by default.
    """
    if request is None or _request_id(request) != plan.request_id:
        if not plan.allow_partial:
            raise ValueError("requested case is missing or does not match the context plan")
        request = {"request_id": plan.request_id, "status": "missing"}

    included: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    for index, record in enumerate(evidence or []):
        evidence_id = _evidence_id(record, index)
        record_request = _request_id(record)
        record_profile, record_profile_version = _profile(record)
        reasons: list[str] = []
        if not plan.allow_cross_request and record_request != plan.request_id:
            reasons.append("request_mismatch")
        profile_match = (record_profile, record_profile_version) == (
            plan.profile_id,
            plan.profile_version,
        )
        if not plan.allow_cross_profile and not profile_match:
            reasons.append("profile_mismatch")
        if plan.allow_cross_profile and not plan.comparative_capability:
            reasons.append("cross_profile_capability_not_authorised")
        entry = {"evidence_id": evidence_id, "record": record, "reason": reasons}
        if reasons:
            excluded.append(entry)
        else:
            included.append(entry)

    included.sort(key=lambda item: item["evidence_id"])
    excluded.sort(key=lambda item: (item["evidence_id"], item["reason"]))
    constraints = {
        "allow_cross_request": plan.allow_cross_request,
        "allow_cross_profile": plan.allow_cross_profile,
        "allow_partial": plan.allow_partial,
        "comparative_capability": plan.comparative_capability,
        "source_text_is_untrusted_evidence": True,
        "machine_certification_allowed": False,
        "prohibited_follow_on_actions": [
            "certify_release",
            "certify_refusal",
            "approve_redaction",
            "certify_extension",
            "promote_profile",
            "publish_manuscript",
        ],
    }
    material = {
        "plan": plan.model_dump(mode="json"),
        "request": request,
        "included": included,
        "excluded": excluded,
        "known_missing": sorted(known_missing or []),
        "unavailable_attachments": sorted(unavailable_attachments or []),
        "conflicts": conflicts or [],
        "constraints": constraints,
    }
    pack_id = f"foio:context-pack:{_digest(material)}"
    return ContextPack(
        pack_id=pack_id,
        generated_at=datetime.now(UTC),
        plan=plan,
        request=request,
        included=included,
        excluded=excluded,
        known_missing=sorted(known_missing or []),
        unavailable_attachments=sorted(unavailable_attachments or []),
        conflicts=conflicts or [],
        constraints=constraints,
    )

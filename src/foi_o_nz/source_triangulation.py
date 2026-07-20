"""Deterministic, candidate-only source triangulation and exception routing."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

ExceptionReason = Literal[
    "blocked",
    "conflicting",
    "stale",
    "rights_uncertain",
    "insufficient_evidence",
]


class StrictModel(BaseModel):
    """Forbid undeclared fields in triangulation contracts."""

    model_config = ConfigDict(extra="forbid")


class SourceAssertion(StrictModel):
    """Record one source's candidate stance on a claim."""

    assertion_id: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    claim_id: str = Field(min_length=1)
    stance: Literal["supports", "contradicts"]
    availability: Literal["available", "blocked"]
    freshness: Literal["event_time_match", "stale", "unknown"]
    rights_status: Literal["permitted", "metadata_only", "restricted", "unknown"]
    integrity: Literal["hash_verified", "archived_unverified", "live_unverified", "derived"]


class TriangulationRequest(StrictModel):
    """Group assertions for one deterministic claim-level evaluation."""

    run_id: str = Field(min_length=1)
    minimum_supporting_sources: int = Field(default=2, ge=2)
    assertions: list[SourceAssertion] = Field(min_length=1)

    @model_validator(mode="after")
    def require_one_claim_and_unique_assertions(self) -> TriangulationRequest:
        """Reject ambiguous claim groups and duplicate assertion identifiers."""
        assertion_ids = [item.assertion_id for item in self.assertions]
        if len(assertion_ids) != len(set(assertion_ids)):
            raise ValueError("assertion_id values must be unique")
        claim_ids = {item.claim_id for item in self.assertions}
        if len(claim_ids) != 1:
            raise ValueError("a triangulation request must contain exactly one claim_id")
        return self


class HumanException(StrictModel):
    """Describe a deterministic reason requiring human resolution."""

    reason: ExceptionReason
    assertion_ids: list[str]
    source_ids: list[str]
    message: str


class TriangulationResult(StrictModel):
    """Return candidate support or an explicit human exception queue."""

    run_id: str
    claim_id: str
    status: Literal["candidate_supported", "human_exception_required"]
    supporting_source_ids: list[str]
    contradicting_source_ids: list[str]
    exception_queue: list[HumanException]
    human_review_required: Literal[True] = True
    promotion_allowed: Literal[False] = False


_MESSAGES: dict[ExceptionReason, str] = {
    "blocked": "one or more declared sources could not be inspected",
    "conflicting": "available event-time sources both support and contradict the claim",
    "stale": "one or more sources do not match the claim event time",
    "rights_uncertain": "one or more sources have restricted or unknown reuse rights",
    "insufficient_evidence": "too few independent eligible sources support the claim",
}


def _exception(reason: ExceptionReason, assertions: list[SourceAssertion]) -> HumanException:
    return HumanException(
        reason=reason,
        assertion_ids=sorted(item.assertion_id for item in assertions),
        source_ids=sorted({item.source_id for item in assertions}),
        message=_MESSAGES[reason],
    )


def evaluate_triangulation(request: TriangulationRequest) -> TriangulationResult:
    """Evaluate source agreement without certifying or promoting the claim."""
    assertions = sorted(request.assertions, key=lambda item: item.assertion_id)
    eligible = [
        item
        for item in assertions
        if item.availability == "available"
        and item.freshness == "event_time_match"
        and item.rights_status in {"permitted", "metadata_only"}
        and item.integrity == "hash_verified"
    ]
    supports = [item for item in eligible if item.stance == "supports"]
    contradicts = [item for item in eligible if item.stance == "contradicts"]
    exceptions: list[HumanException] = []

    blocked = [item for item in assertions if item.availability == "blocked"]
    if blocked:
        exceptions.append(_exception("blocked", blocked))
    if supports and contradicts:
        exceptions.append(_exception("conflicting", supports + contradicts))
    stale = [item for item in assertions if item.freshness in {"stale", "unknown"}]
    if stale:
        exceptions.append(_exception("stale", stale))
    uncertain_rights = [
        item for item in assertions if item.rights_status in {"restricted", "unknown"}
    ]
    if uncertain_rights:
        exceptions.append(_exception("rights_uncertain", uncertain_rights))

    supporting_source_ids = sorted({item.source_id for item in supports})
    if len(supporting_source_ids) < request.minimum_supporting_sources:
        exceptions.append(_exception("insufficient_evidence", supports))

    return TriangulationResult(
        run_id=request.run_id,
        claim_id=assertions[0].claim_id,
        status="human_exception_required" if exceptions else "candidate_supported",
        supporting_source_ids=supporting_source_ids,
        contradicting_source_ids=sorted({item.source_id for item in contradicts}),
        exception_queue=exceptions,
    )

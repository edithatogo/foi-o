"""Pure-Python fallback semantics for FOI-O NZ native kernels.

The project is intended to prefer small, deterministic Mojo kernels where the
Modular toolchain is available. This module is the compatibility contract: every
native Mojo helper should have a Python equivalent here, with tests asserting the
expected behaviour. The Python fallback is deliberately dependency-light and is
safe to run in CI, notebooks, and environments without Mojo/MAX.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from foi_o_nz.constants import HUMAN_CERTIFICATION_EVENT_TYPES
from foi_o_nz.state_machine import (
    TERMINAL_STATES,
    RequestState,
    can_transition,
    map_alaveteli_state,
)

KernelValue = str | int | float | bool

FNV1A64_OFFSET = 14695981039346656037
FNV1A64_PRIME = 1099511628211
FNV1A64_MASK = (1 << 64) - 1


@dataclass(frozen=True, slots=True)
class KernelEvaluation:
    """Result of evaluating a deterministic kernel operation."""

    operation: str
    args: tuple[KernelValue, ...]
    value: KernelValue
    runtime: Literal["python-fallback"] = "python-fallback"


def normalise_alaveteli_state(source_state: str | None) -> str:
    """Return the canonical lifecycle state for an FYI/Alaveteli source state."""
    return map_alaveteli_state(source_state).normalised_state.value


def confidence_for_alaveteli_state(source_state: str | None) -> float:
    """Return the cautious state-mapping confidence used by the process profile."""
    return map_alaveteli_state(source_state).confidence


def requires_human_certification(event_type: str) -> bool:
    """Return whether an event type crosses the human-certification boundary."""
    return event_type in HUMAN_CERTIFICATION_EVENT_TYPES


def can_agent_certify_event(event_type: str) -> bool:
    """Return whether an agent may certify the event type.

    Current policy: agents may draft/flag these events but never certify legal or
    dispositive outcomes.
    """
    return not requires_human_certification(event_type)


def is_terminal_state(state: str) -> bool:
    """Return whether a lifecycle state is terminal in the current profile."""
    try:
        return RequestState(state) in TERMINAL_STATES
    except ValueError:
        return False


def can_transition_value(from_state: str, to_state: str) -> bool:
    """Check lifecycle transition validity using string inputs."""
    try:
        return can_transition(RequestState(from_state), RequestState(to_state))
    except ValueError:
        return False


def is_oia_summer_excluded(month: int, day: int) -> bool:
    """Return whether a month/day falls in the OIA summer-excluded interval."""
    return (month == 12 and day >= 25) or (month == 1 and day <= 15)


def is_weekend(weekday: int) -> bool:
    """Return whether a weekday number is Saturday/Sunday.

    Convention: Monday=0 ... Sunday=6.
    """
    return weekday in {5, 6}


def is_machine_working_day(weekday: int, month: int, day: int) -> bool:
    """Return a deterministic machine-working-day predicate."""
    return not is_weekend(weekday) and not is_oia_summer_excluded(month, day)


def token_estimate_from_chars(char_count: int) -> int:
    """Estimate token count using the same conservative helper as the Mojo text kernel."""
    if char_count <= 0:
        return 1
    return (char_count + 3) // 4


def risk_level_from_score(
    score: int, has_health_identifier: bool
) -> Literal["low", "medium", "high"]:
    """Map deterministic risk score to review level."""
    if has_health_identifier or score >= 5:
        return "high"
    if score >= 1:
        return "medium"
    return "low"


def review_required_for_score(score: int, has_health_identifier: bool) -> bool:
    """Return whether the deterministic score should route to human review."""
    return bool(has_health_identifier or score >= 1)


def can_machine_certify_safety_class(_safety_class: str) -> bool:
    """Current policy: no machine safety class can certify an FOI/OIA decision."""
    return False


def blend_scores(lexical_score: float, vector_score: float, lexical_weight: float) -> float:
    """Blend lexical and vector scores with bounded lexical weight."""
    weight = max(0.0, min(1.0, lexical_weight))
    return weight * lexical_score + (1.0 - weight) * vector_score


def normalise_cosine(cosine_score: float) -> float:
    """Normalise cosine score from [-1, 1] into [0, 1]."""
    if cosine_score <= -1.0:
        return 0.0
    if cosine_score >= 1.0:
        return 1.0
    return (cosine_score + 1.0) / 2.0


def should_include_hit(score: float, min_score: float) -> bool:
    """Return whether a search hit clears the inclusion threshold."""
    return score >= min_score


def clamp_top_k(top_k: int, max_top_k: int) -> int:
    """Clamp top-k retrieval parameters to a safe bounded interval."""
    if top_k <= 0:
        return 1
    if top_k > max_top_k:
        return max_top_k
    return top_k


def is_dispositive_event(event_type: str) -> bool:
    """Return whether an event is dispositive or certification-sensitive."""
    return event_type in HUMAN_CERTIFICATION_EVENT_TYPES or event_type == "HumanDecisionCertified"


def severity_rank(severity: str) -> int:
    """Rank guardrail severities for deterministic sorting."""
    return {"error": 3, "warning": 2, "info": 1}.get(severity, 0)


def action_requires_review(safety_class: str, requires_human_certification: bool) -> bool:
    """Return whether an agent action requires human review."""
    return bool(requires_human_certification or safety_class in {"high", "prohibited"})


def can_replay_pass(error_count: int) -> bool:
    """Return whether a guardrail replay can pass."""
    return error_count == 0


def transition_rank(state: str) -> int:
    """Return a coarse lifecycle-order rank for native transition diagnostics."""
    order = {
        "Drafted": 0,
        "Submitted": 1,
        "Received": 2,
        "Acknowledged": 3,
        "ValidityChecking": 4,
        "AwaitingClarification": 4,
        "Valid": 5,
        "SearchPlanning": 6,
        "Searching": 7,
        "DocumentsIdentified": 8,
        "ConsultationRequired": 8,
        "ThirdPartyConsultation": 9,
        "ChargeAssessment": 9,
        "ExtensionApplied": 9,
        "DecisionDrafting": 10,
        "HumanDecisionRequired": 11,
        "DecisionApproved": 12,
        "ReleasedInFull": 13,
        "ReleasedInPart": 13,
        "Refused": 13,
        "NoDocumentsFound": 13,
        "Withdrawn": 13,
        "Closed": 13,
    }
    return order.get(state, -1)


def is_forward_transition(from_state: str, to_state: str) -> bool:
    """Return whether a transition is non-regressive by rank.

    This is a diagnostic helper, not the authoritative state machine.
    """
    source_rank = transition_rank(from_state)
    target_rank = transition_rank(to_state)
    return source_rank >= 0 and target_rank >= 0 and target_rank >= source_rank


def is_ascii_alpha(codepoint: int) -> bool:
    """Return whether an ASCII codepoint is alphabetic."""
    return 65 <= codepoint <= 90 or 97 <= codepoint <= 122


def is_ascii_digit(codepoint: int) -> bool:
    """Return whether an ASCII codepoint is numeric."""
    return 48 <= codepoint <= 57


def is_email_local_char(codepoint: int) -> bool:
    """Return whether a codepoint is accepted in the simple local-part scanner."""
    return (
        is_ascii_alpha(codepoint) or is_ascii_digit(codepoint) or codepoint in {45, 46, 95, 37, 43}
    )


def is_email_domain_char(codepoint: int) -> bool:
    """Return whether a codepoint is accepted in the simple domain scanner."""
    return is_ascii_alpha(codepoint) or is_ascii_digit(codepoint) or codepoint in {45, 46}


def looks_like_email(value: str) -> bool:
    """Small deterministic email-like predicate mirrored by the Mojo redaction kernel."""
    if value.count("@") != 1:
        return False
    local, domain = value.split("@", 1)
    if not local or not domain or "." not in domain:
        return False
    return all(is_email_local_char(ord(ch)) for ch in local) and all(
        is_email_domain_char(ord(ch)) for ch in domain
    )


def redaction_preview_width(value_length: int) -> int:
    """Return a bounded preview width for privacy-preserving candidate displays."""
    if value_length <= 0:
        return 0
    if value_length <= 2:
        return value_length
    if value_length <= 8:
        return 1
    return 2


def assertion_status_rank(status: str) -> int:
    """Return an epistemic-status rank used for deterministic sorting."""
    return {
        "unknown": 0,
        "inferred": 1,
        "asserted": 2,
        "observed": 3,
        "certified": 4,
    }.get(status, -1)


def confidence_band(score: float) -> Literal["none", "low", "medium", "high"]:
    """Map a numeric confidence score to a coarse deterministic band."""
    if score <= 0.0:
        return "none"
    if score < 0.5:
        return "low"
    if score < 0.8:
        return "medium"
    return "high"


def can_agent_assert_status(status: str) -> bool:
    """Return whether an agent may emit, but not certify, this assertion status."""
    return status in {"observed", "inferred", "asserted"}


def stable_text_bucket(value: str, bucket_count: int) -> int:
    """Return a deterministic non-cryptographic text bucket."""
    if bucket_count <= 0:
        return 0
    return fnv1a64_text(value) % bucket_count


def fnv1a64_bytes(data: bytes) -> int:
    """Compute the FNV-1a 64-bit hash used by experimental Mojo kernels."""
    digest = FNV1A64_OFFSET
    for byte in data:
        digest ^= byte
        digest = (digest * FNV1A64_PRIME) & FNV1A64_MASK
    return digest


def fnv1a64_text(value: str) -> int:
    """Compute a deterministic, non-cryptographic text hash."""
    return fnv1a64_bytes(value.encode("utf-8"))


def evaluate_operation(operation: str, args: tuple[KernelValue, ...]) -> KernelEvaluation:
    """Evaluate a named deterministic operation using the Python fallback contract."""
    operations: dict[str, Any] = {
        "normalise_alaveteli_state": normalise_alaveteli_state,
        "confidence_for_alaveteli_state": confidence_for_alaveteli_state,
        "requires_human_certification": requires_human_certification,
        "can_agent_certify_event": can_agent_certify_event,
        "is_terminal_state": is_terminal_state,
        "can_transition_value": can_transition_value,
        "is_oia_summer_excluded": is_oia_summer_excluded,
        "is_weekend": is_weekend,
        "is_machine_working_day": is_machine_working_day,
        "token_estimate_from_chars": token_estimate_from_chars,
        "risk_level_from_score": risk_level_from_score,
        "review_required_for_score": review_required_for_score,
        "can_machine_certify_safety_class": can_machine_certify_safety_class,
        "blend_scores": blend_scores,
        "normalise_cosine": normalise_cosine,
        "should_include_hit": should_include_hit,
        "clamp_top_k": clamp_top_k,
        "is_dispositive_event": is_dispositive_event,
        "severity_rank": severity_rank,
        "action_requires_review": action_requires_review,
        "can_replay_pass": can_replay_pass,
        "transition_rank": transition_rank,
        "is_forward_transition": is_forward_transition,
        "looks_like_email": looks_like_email,
        "redaction_preview_width": redaction_preview_width,
        "assertion_status_rank": assertion_status_rank,
        "confidence_band": confidence_band,
        "can_agent_assert_status": can_agent_assert_status,
        "stable_text_bucket": stable_text_bucket,
        "fnv1a64_text": fnv1a64_text,
    }
    try:
        func = operations[operation]
    except KeyError as exc:
        raise ValueError(f"unsupported kernel operation: {operation}") from exc
    return KernelEvaluation(operation=operation, args=args, value=func(*args))


def conformance_cases() -> list[tuple[str, tuple[KernelValue, ...], KernelValue]]:
    """Return the built-in kernel parity/conformance fixture set."""
    return [
        ("normalise_alaveteli_state", ("successful",), "ReleasedInFull"),
        ("normalise_alaveteli_state", ("future_state",), "Unknown"),
        ("confidence_for_alaveteli_state", ("successful",), 0.55),
        ("requires_human_certification", ("ReleaseMade",), True),
        ("can_agent_certify_event", ("ReleaseMade",), False),
        ("is_terminal_state", ("ReleasedInFull",), True),
        ("is_oia_summer_excluded", (12, 25), True),
        ("is_machine_working_day", (0, 6, 1), True),
        ("is_machine_working_day", (5, 6, 1), False),
        ("token_estimate_from_chars", (5,), 2),
        ("risk_level_from_score", (5, False), "high"),
        ("review_required_for_score", (0, True), True),
        ("can_machine_certify_safety_class", ("low",), False),
        ("blend_scores", (2.0, 1.0, 0.5), 1.5),
        ("normalise_cosine", (0.0,), 0.5),
        ("clamp_top_k", (500, 100), 100),
        ("is_dispositive_event", ("DecisionCommunicated",), True),
        ("severity_rank", ("warning",), 2),
        ("action_requires_review", ("high", False), True),
        ("can_replay_pass", (0,), True),
        ("transition_rank", ("Received",), 2),
        ("is_forward_transition", ("Received", "Searching"), True),
        ("looks_like_email", ("a@example.org",), True),
        ("redaction_preview_width", (12,), 2),
        ("assertion_status_rank", ("certified",), 4),
        ("confidence_band", (0.74,), "medium"),
        ("can_agent_assert_status", ("certified",), False),
        ("stable_text_bucket", ("foi-o-nz", 16), stable_text_bucket("foi-o-nz", 16)),
        ("fnv1a64_text", ("foi-o-nz",), fnv1a64_text("foi-o-nz")),
    ]

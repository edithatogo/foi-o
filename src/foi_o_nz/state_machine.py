"""State normalisation and workflow transition helpers."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class RequestState(StrEnum):
    """Canonical FOI-O NZ lifecycle states.

    These are process states, not legal conclusions. Public FYI/Alaveteli states
    are mapped to these cautiously with a confidence value and notes.
    """

    DRAFTED = "Drafted"
    SUBMITTED = "Submitted"
    RECEIVED = "Received"
    ACKNOWLEDGED = "Acknowledged"
    VALIDITY_CHECKING = "ValidityChecking"
    AWAITING_CLARIFICATION = "AwaitingClarification"
    VALID = "Valid"
    TRANSFERRED_IN_PART = "TransferredInPart"
    TRANSFERRED_IN_FULL = "TransferredInFull"
    SEARCH_PLANNING = "SearchPlanning"
    SEARCHING = "Searching"
    DOCUMENTS_IDENTIFIED = "DocumentsIdentified"
    CONSULTATION_REQUIRED = "ConsultationRequired"
    THIRD_PARTY_CONSULTATION = "ThirdPartyConsultation"
    CHARGE_ASSESSMENT = "ChargeAssessment"
    EXTENSION_APPLIED = "ExtensionApplied"
    DECISION_DRAFTING = "DecisionDrafting"
    HUMAN_DECISION_REQUIRED = "HumanDecisionRequired"
    DECISION_APPROVED = "DecisionApproved"
    RELEASED_IN_FULL = "ReleasedInFull"
    RELEASED_IN_PART = "ReleasedInPart"
    REFUSED = "Refused"
    NO_DOCUMENTS_FOUND = "NoDocumentsFound"
    WITHDRAWN = "Withdrawn"
    DEEMED_REFUSED = "DeemedRefused"
    INTERNAL_REVIEW_REQUESTED = "InternalReviewRequested"
    EXTERNAL_REVIEW_REQUESTED = "ExternalReviewRequested"
    COMPLAINT_MADE = "ComplaintMade"
    CLOSED = "Closed"
    PUBLISHED_TO_DISCLOSURE_LOG = "PublishedToDisclosureLog"
    UNKNOWN = "Unknown"


@dataclass(frozen=True, slots=True)
class AlaveteliStateMapping:
    """Mapping result for a source Alaveteli/FYI state."""

    source_state: str
    normalised_state: RequestState
    confidence: float
    assertion_status: str
    notes: str


_STATE_MAP: dict[str, AlaveteliStateMapping] = {
    "waiting_response": AlaveteliStateMapping(
        "waiting_response",
        RequestState.RECEIVED,
        0.74,
        "inferred",
        "FYI indicates a submitted request awaiting authority response; legal validity is not proven.",
    ),
    "waiting_clarification": AlaveteliStateMapping(
        "waiting_clarification",
        RequestState.AWAITING_CLARIFICATION,
        0.78,
        "observed",
        "FYI indicates the authority or requester is awaiting clarification.",
    ),
    "gone_postal": AlaveteliStateMapping(
        "gone_postal",
        RequestState.SEARCHING,
        0.48,
        "inferred",
        "Alaveteli state means offline/postal handling; exact agency process state is unknown.",
    ),
    "internal_review": AlaveteliStateMapping(
        "internal_review",
        RequestState.INTERNAL_REVIEW_REQUESTED,
        0.82,
        "observed",
        "FYI state indicates internal review stage.",
    ),
    "error_message": AlaveteliStateMapping(
        "error_message",
        RequestState.UNKNOWN,
        0.2,
        "observed",
        "Source platform reports an error, not a legal/process outcome.",
    ),
    "requires_admin": AlaveteliStateMapping(
        "requires_admin",
        RequestState.UNKNOWN,
        0.2,
        "observed",
        "Platform moderation/admin state, not an OIA process state.",
    ),
    "successful": AlaveteliStateMapping(
        "successful",
        RequestState.RELEASED_IN_FULL,
        0.55,
        "inferred",
        "Public source marks success, but full/partial/legal outcome requires message/document review.",
    ),
    "partially_successful": AlaveteliStateMapping(
        "partially_successful",
        RequestState.RELEASED_IN_PART,
        0.58,
        "inferred",
        "Public source marks partial success; withholding grounds require separate evidence.",
    ),
    "rejected": AlaveteliStateMapping(
        "rejected",
        RequestState.REFUSED,
        0.58,
        "inferred",
        "Public source marks rejection; exact statutory reason requires decision-letter evidence.",
    ),
    "not_held": AlaveteliStateMapping(
        "not_held",
        RequestState.NO_DOCUMENTS_FOUND,
        0.62,
        "inferred",
        "Public source indicates information not held; formal statutory treatment requires review.",
    ),
    "information_not_held": AlaveteliStateMapping(
        "information_not_held",
        RequestState.NO_DOCUMENTS_FOUND,
        0.62,
        "inferred",
        "Public source indicates information not held; formal statutory treatment requires review.",
    ),
    "user_withdrawn": AlaveteliStateMapping(
        "user_withdrawn",
        RequestState.WITHDRAWN,
        0.75,
        "observed",
        "Public source indicates requester withdrawal.",
    ),
    "not_foi": AlaveteliStateMapping(
        "not_foi",
        RequestState.CLOSED,
        0.45,
        "inferred",
        "Platform state indicates not an FOI/OIA request; regime classification needs review.",
    ),
}

TERMINAL_STATES: frozenset[RequestState] = frozenset(
    {
        RequestState.RELEASED_IN_FULL,
        RequestState.RELEASED_IN_PART,
        RequestState.REFUSED,
        RequestState.NO_DOCUMENTS_FOUND,
        RequestState.WITHDRAWN,
        RequestState.CLOSED,
    }
)

ALLOWED_TRANSITIONS: dict[RequestState, frozenset[RequestState]] = {
    RequestState.DRAFTED: frozenset({RequestState.SUBMITTED, RequestState.WITHDRAWN}),
    RequestState.SUBMITTED: frozenset({RequestState.RECEIVED, RequestState.AWAITING_CLARIFICATION}),
    RequestState.RECEIVED: frozenset(
        {
            RequestState.ACKNOWLEDGED,
            RequestState.VALIDITY_CHECKING,
            RequestState.TRANSFERRED_IN_FULL,
            RequestState.SEARCH_PLANNING,
            RequestState.AWAITING_CLARIFICATION,
            RequestState.WITHDRAWN,
        }
    ),
    RequestState.SEARCH_PLANNING: frozenset({RequestState.SEARCHING, RequestState.CONSULTATION_REQUIRED}),
    RequestState.SEARCHING: frozenset(
        {
            RequestState.DOCUMENTS_IDENTIFIED,
            RequestState.NO_DOCUMENTS_FOUND,
            RequestState.EXTENSION_APPLIED,
            RequestState.CONSULTATION_REQUIRED,
        }
    ),
    RequestState.DOCUMENTS_IDENTIFIED: frozenset(
        {
            RequestState.DECISION_DRAFTING,
            RequestState.CONSULTATION_REQUIRED,
            RequestState.HUMAN_DECISION_REQUIRED,
        }
    ),
    RequestState.DECISION_DRAFTING: frozenset({RequestState.HUMAN_DECISION_REQUIRED}),
    RequestState.HUMAN_DECISION_REQUIRED: frozenset({RequestState.DECISION_APPROVED}),
    RequestState.DECISION_APPROVED: frozenset(
        {RequestState.RELEASED_IN_FULL, RequestState.RELEASED_IN_PART, RequestState.REFUSED}
    ),
}


def map_alaveteli_state(source_state: str | None) -> AlaveteliStateMapping:
    """Map an FYI/Alaveteli state into the cautious FOI-O NZ lifecycle vocabulary."""
    raw = (source_state or "").strip().lower().replace("-", "_").replace(" ", "_")
    if raw in _STATE_MAP:
        return _STATE_MAP[raw]
    return AlaveteliStateMapping(
        source_state=source_state or "",
        normalised_state=RequestState.UNKNOWN,
        confidence=0.0,
        assertion_status="unknown",
        notes="No mapping rule exists for this source state.",
    )


def can_transition(from_state: RequestState, to_state: RequestState) -> bool:
    """Return whether a workflow transition is known to be allowed."""
    if from_state == to_state:
        return True
    if from_state in TERMINAL_STATES:
        return False
    return to_state in ALLOWED_TRANSITIONS.get(from_state, frozenset())


def requires_human_certification(event_type: str) -> bool:
    """Return whether an event type must carry human certification metadata."""
    return event_type in {
        "HumanDecisionCertified",
        "DecisionCommunicated",
        "ReleaseMade",
        "RefusalCommunicated",
        "ChargeNoticeSent",
    }

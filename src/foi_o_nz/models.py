"""Pydantic models for the FOI-O NZ process/profile contracts."""

from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import AnyUrl, BaseModel, ConfigDict, Field, field_validator, model_validator

from foi_o_nz.constants import (
    AGENT_ACTION_SCHEMA_VERSION,
    CORE_EVENT_SCHEMA_VERSION,
    DEFAULT_JURISDICTION,
    DEFAULT_REGIME,
    HUMAN_CERTIFICATION_EVENT_TYPES,
    REQUEST_PROFILE_SCHEMA_VERSION,
)


class AssertionStatus(StrEnum):
    """Epistemic status of a record/event assertion."""

    OBSERVED = "observed"
    INFERRED = "inferred"
    ASSERTED = "asserted"
    CERTIFIED = "certified"
    UNKNOWN = "unknown"


class ActorRole(StrEnum):
    """Process actor role."""

    REQUESTER = "requester"
    AUTHORITY = "authority"
    MINISTER = "minister"
    AGENCY_OFFICIAL = "agency_official"
    OMBUDSMAN = "ombudsman"
    SYSTEM = "system"
    AGENT = "agent"
    UNKNOWN = "unknown"


class Regime(StrEnum):
    """New Zealand access-to-information regime label."""

    OIA = "OIA"
    LGOIMA = "LGOIMA"
    PRIVACY_ACT = "PrivacyAct"
    ADMINISTRATIVE_ACCESS = "AdministrativeAccess"
    UNKNOWN = "Unknown"


class EventType(StrEnum):
    """Supported core process event types."""

    REQUEST_OBSERVED = "RequestObserved"
    MESSAGE_OBSERVED = "MessageObserved"
    ATTACHMENT_OBSERVED = "AttachmentObserved"
    STATE_OBSERVED = "StateObserved"
    REQUEST_REGISTERED = "RequestRegistered"
    VALIDITY_ASSESSED = "ValidityAssessed"
    CLARIFICATION_REQUESTED = "ClarificationRequested"
    SCOPE_AMENDED = "ScopeAmended"
    TRANSFER_ASSESSED = "TransferAssessed"
    TRANSFER_NOTIFIED = "TransferNotified"
    TRANSFER_RECEIVED = "TransferReceived"
    DEADLINE_CALCULATED = "DeadlineCalculated"
    EXTENSION_ASSESSED = "ExtensionAssessed"
    EXTENSION_NOTIFIED = "ExtensionNotified"
    OVERDUE_FLAGGED = "OverdueFlagged"
    SEARCH_PLAN_DRAFTED = "SearchPlanDrafted"
    SEARCH_PERFORMED = "SearchPerformed"
    RECORDS_IDENTIFIED = "RecordsIdentified"
    NO_RECORDS_FOUND = "NoRecordsFound"
    CONSULTATION_REQUIRED = "ConsultationRequired"
    CONSULTATION_STARTED = "ConsultationStarted"
    CONSULTATION_RESPONSE_OBSERVED = "ConsultationResponseObserved"
    LEGAL_ISSUE_FLAGGED = "LegalIssueFlagged"
    WITHHOLDING_GROUND_FLAGGED = "WithholdingGroundFlagged"
    PUBLIC_INTEREST_ISSUE_FLAGGED = "PublicInterestIssueFlagged"
    DECISION_PACK_DRAFTED = "DecisionPackDrafted"
    HUMAN_DECISION_CERTIFIED = "HumanDecisionCertified"
    DECISION_COMMUNICATED = "DecisionCommunicated"
    RELEASE_MADE = "ReleaseMade"
    REFUSAL_COMMUNICATED = "RefusalCommunicated"
    CHARGE_NOTICE_SENT = "ChargeNoticeSent"
    DISCLOSURE_LOG_CANDIDATE_CREATED = "DisclosureLogCandidateCreated"
    PUBLICATION_OBSERVED = "PublicationObserved"
    COMPLAINT_OBSERVED = "ComplaintObserved"
    REVIEW_OUTCOME_OBSERVED = "ReviewOutcomeObserved"
    CLOSED = "Closed"


class RequestRef(BaseModel):
    """Reference to a request in a source system."""

    model_config = ConfigDict(extra="forbid")

    source_system: str
    source_request_id: str | int
    source_url: AnyUrl | None = None
    url_title: str | None = None
    content_sha256: str | None = None

    @field_validator("content_sha256")
    @classmethod
    def validate_sha256(cls, value: str | None) -> str | None:
        """Validate SHA-256 hex digests when provided."""
        if value is None:
            return None
        lowered = value.lower()
        if len(lowered) != 64 or any(ch not in "0123456789abcdef" for ch in lowered):
            raise ValueError("content_sha256 must be a 64-character hex digest")
        return lowered


class Actor(BaseModel):
    """Actor associated with an event."""

    model_config = ConfigDict(extra="forbid")

    role: ActorRole
    name: str | None = None
    authority_id: str | None = None


class Generator(BaseModel):
    """Machine generator metadata."""

    model_config = ConfigDict(extra="forbid")

    system: str
    model: str | None = None
    prompt_id: str | None = None
    software_version: str | None = None


class HumanCertification(BaseModel):
    """Human certification metadata for legally/materially dispositive events."""

    model_config = ConfigDict(extra="forbid")

    certified: bool
    certified_by_role: str | None = None
    certified_at: datetime | None = None
    certification_reference: str | None = None


class LegalReference(BaseModel):
    """Version-aware legal source reference."""

    model_config = ConfigDict(extra="forbid")

    source_id: str
    title: str
    reference: str
    uri: AnyUrl | None = None
    work_id: str | None = None
    version_id: str | None = None
    retrieved_at: datetime | None = None
    applicability_basis: Literal[
        "current_at_event_time", "current_at_extraction_time", "unknown"
    ] = "unknown"


class EvidenceType(StrEnum):
    """Types of evidence that can support an event assertion."""

    SOURCE_RECORD = "source_record"
    MESSAGE = "message"
    ATTACHMENT = "attachment"
    ARCHIVE_MANIFEST = "archive_manifest"
    STATUTE = "statute"
    GUIDANCE = "guidance"
    MANUAL_ANNOTATION = "manual_annotation"
    SYSTEM_LOG = "system_log"
    NONE = "none"


class EvidenceRef(BaseModel):
    """Evidence reference carried by an event."""

    model_config = ConfigDict(extra="forbid")

    evidence_id: str
    evidence_type: EvidenceType
    source_url: AnyUrl | None = None
    archive_ref: str | None = None
    content_sha256: str | None = None
    excerpt: str | None = Field(default=None, max_length=500)
    observed_at: datetime | None = None

    @field_validator("content_sha256")
    @classmethod
    def validate_sha256(cls, value: str | None) -> str | None:
        """Validate SHA-256 hex digests when provided."""
        if value is None:
            return None
        lowered = value.lower()
        if len(lowered) != 64 or any(ch not in "0123456789abcdef" for ch in lowered):
            raise ValueError("content_sha256 must be a 64-character hex digest")
        return lowered


class CoreEvent(BaseModel):
    """Core FOI-O NZ process event."""

    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    schema_version: Literal["foi-o-nz.core-event.v0.1.0"] = CORE_EVENT_SCHEMA_VERSION
    event_id: str
    event_type: EventType
    event_time: datetime
    request_ref: RequestRef
    jurisdiction: Literal["NZ"] = DEFAULT_JURISDICTION
    regime: Regime = Regime(DEFAULT_REGIME)
    source_system: str
    lifecycle_state_after: str | None = None
    actor: Actor
    assertion_status: AssertionStatus
    confidence: float | None = Field(default=None, ge=0, le=1)
    machine_generated: bool
    generator: Generator | None = None
    requires_human_certification: bool
    human_certification: HumanCertification | None = None
    legal_references: list[LegalReference] = Field(default_factory=list)
    evidence: list[EvidenceRef] = Field(min_length=1)
    payload: dict[str, Any] = Field(default_factory=dict)
    quality_flags: list[str] = Field(default_factory=list)

    @field_validator("event_id")
    @classmethod
    def validate_event_id(cls, value: str) -> str:
        """Check event ID namespace."""
        if not (value.startswith("urn:uuid:") or value.startswith("foio-nz:event:")):
            raise ValueError("event_id must start with urn:uuid: or foio-nz:event:")
        return value

    @model_validator(mode="after")
    def validate_certification_boundary(self) -> CoreEvent:
        """Enforce human-certification requirements for dispositive event types."""
        if str(self.event_type) in HUMAN_CERTIFICATION_EVENT_TYPES:
            if not self.requires_human_certification:
                raise ValueError(f"{self.event_type} requires human certification")
            if self.human_certification is None:
                raise ValueError(f"{self.event_type} must carry human_certification metadata")
        if self.assertion_status == AssertionStatus.CERTIFIED:
            if self.human_certification is None or not self.human_certification.certified:
                raise ValueError("certified assertions must carry positive human certification")
        if self.machine_generated and self.generator is None:
            self.quality_flags.append("missing_generator_metadata")
        return self


class StateMapping(BaseModel):
    """State mapping evidence metadata."""

    model_config = ConfigDict(extra="forbid")

    method: Literal["manual", "rule", "model", "hybrid", "unknown"]
    confidence: float | None = Field(default=None, ge=0, le=1)
    evidence_ids: list[str] = Field(default_factory=list)
    notes: str | None = None


class LegalClock(BaseModel):
    """Indicative legal clock metadata.

    This is deliberately an annotation, not a legal decision. Calendar/working-day
    calculations should carry warnings until verified against official holiday and
    closure calendars.
    """

    model_config = ConfigDict(extra="forbid")

    received_at: datetime | None = None
    decision_due_date: date | None = None
    transfer_due_date: date | None = None
    calculation_method: str | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    warnings: list[str] = Field(default_factory=list)


class RequestProfile(BaseModel):
    """Normalised request profile derived from public FYI archive-style records."""

    model_config = ConfigDict(extra="allow")

    schema_version: Literal["foi-o-nz.request-profile.v0.1.0"] = REQUEST_PROFILE_SCHEMA_VERSION
    source: str
    request_id: str | int
    url_title: str | None = None
    source_url: AnyUrl | None = None
    title: str
    authority: str
    source_state: str
    normalised_state: str | None = None
    state_mapping: StateMapping | None = None
    first_sent: datetime | None = None
    last_updated: datetime | None = None
    content_sha256: str | None = None
    html_captured: bool | None = None
    attachments: list[dict[str, Any]] = Field(default_factory=list)
    warc_record_ids: list[str] = Field(default_factory=list)
    legal_clock: LegalClock | None = None

    @field_validator("content_sha256")
    @classmethod
    def validate_sha256(cls, value: str | None) -> str | None:
        """Validate SHA-256 hex digests when provided."""
        if value is None:
            return None
        lowered = value.lower()
        if len(lowered) != 64 or any(ch not in "0123456789abcdef" for ch in lowered):
            raise ValueError("content_sha256 must be a 64-character hex digest")
        return lowered


class AgentAction(BaseModel):
    """Bounded agent action record aligned with the JSON Schema contract."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["foi-o-nz.agent-action.v0.1.0"] = AGENT_ACTION_SCHEMA_VERSION
    action_id: str
    action_type: Literal[
        "extract_events",
        "map_state",
        "calculate_deadline",
        "draft_search_plan",
        "draft_correspondence",
        "quality_check",
        "generate_reporting_metric",
        "flag_legal_issue",
        "search_chunks",
        "propose_redaction_candidates",
        "build_agent_pack",
        "diff_streams",
        "build_review_queue",
        "build_process_advice",
        "export_graph",
        "attest_artifacts",
        "sample_goldset",
        "export_annotation_tasks",
        "cas_manifest",
        "materialise_cas",
        "lineage_graph",
        "trace_artifacts",
        "build_goldset_tasks",
        "replay_guardrails",
        "export_table_contracts",
        "materialise_oci",
        "export_mcp_bundle",
    ]
    requested_at: datetime
    agent: dict[str, Any]
    inputs: list[str] = Field(default_factory=list)
    outputs: list[str] = Field(default_factory=list)
    legal_effect: Literal["none", "preparatory", "requires_certification", "prohibited"]
    requires_human_certification: bool
    safety_class: Literal["low", "medium", "high", "prohibited"]
    prohibited_follow_on_actions: list[str] = Field(default_factory=list)
    audit_trace: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_agent_boundary(self) -> AgentAction:
        """Require safety/certification consistency for risky actions."""
        if self.legal_effect in {"requires_certification", "prohibited"} and not self.requires_human_certification:
            raise ValueError("risky/prohibited legal-effect actions must require human certification")
        if self.safety_class == "prohibited" and self.legal_effect != "prohibited":
            raise ValueError("prohibited safety class must have prohibited legal_effect")
        return self


class ReportingMetric(BaseModel):
    """Reporting metric derivability descriptor."""

    model_config = ConfigDict(extra="forbid")

    metric_id: str
    name: str
    jurisdiction: Literal["NZ"] = "NZ"
    source_profile: str
    derivability: Literal[
        "public_fyi_derivable", "partially_derivable", "agency_internal_required", "not_derivable"
    ]
    notes: str | None = None

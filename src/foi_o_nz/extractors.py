"""Rule-based process-event extraction from public FYI-style correspondence.

These extractors produce observed or inferred process events, never certified
legal decisions. They are intentionally simple and auditable so they can become
fixtures for later LLM/MAX-assisted extraction.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from foi_o_nz.constants import DEFAULT_REGIME, HUMAN_CERTIFICATION_EVENT_TYPES
from foi_o_nz.dates import parse_datetime
from foi_o_nz.models import Actor, CoreEvent, EvidenceRef, RequestProfile, RequestRef

_MESSAGE_FIELDS = (
    "correspondence",
    "messages",
    "communications",
    "updates",
    "mail",
)

_EXTENSION_RE = re.compile(r"\b(extension|extend(?:ed|ing)?|time\s*limit|further\s+working\s+days)\b", re.I)
_TRANSFER_RE = re.compile(r"\b(transfer(?:red|ring)?|transferring|section\s+14|s\s*14)\b", re.I)
_CLARIFICATION_RE = re.compile(r"\b(clarif(?:y|ication)|scope|refine|narrow|due\s+particularity)\b", re.I)
_CHARGE_RE = re.compile(r"\b(charge|charges|charging|deposit|invoice|fee)\b", re.I)
_REFUSAL_RE = re.compile(r"\b(refuse|refused|decline|declined|withhold|withheld|section\s+18|s\s*18)\b", re.I)
_RELEASE_RE = re.compile(r"\b(release|released|attached|provided|enclosed|supply|supplied)\b", re.I)
_COMPLAINT_RE = re.compile(r"\b(ombudsman|complaint|complain|review)\b", re.I)
_DECISION_RE = re.compile(r"\b(decision|decided|we have considered|our response)\b", re.I)

_LEGAL_REFS: dict[str, list[dict[str, str]]] = {
    "ExtensionNotified": [
        {"source_id": "nz.oia.act", "title": "Official Information Act 1982", "reference": "s 15A"},
    ],
    "TransferNotified": [
        {"source_id": "nz.oia.act", "title": "Official Information Act 1982", "reference": "s 14"},
    ],
    "DecisionCommunicated": [
        {"source_id": "nz.oia.act", "title": "Official Information Act 1982", "reference": "s 15"},
    ],
    "RefusalCommunicated": [
        {"source_id": "nz.oia.act", "title": "Official Information Act 1982", "reference": "s 18"},
    ],
    "ChargeNoticeSent": [
        {"source_id": "nz.oia.act", "title": "Official Information Act 1982", "reference": "s 15"},
    ],
}


def _legal_refs_for(event_type: str) -> list[dict[str, str]]:
    return _LEGAL_REFS.get(event_type, [])


@dataclass(frozen=True, slots=True)
class ExtractedMessage:
    """Normalised public correspondence item."""

    message_id: str
    body: str
    sent_at: datetime | None
    sender: str | None = None
    recipient: str | None = None
    subject: str | None = None
    source_url: str | None = None


def iter_message_records(record: dict[str, Any]) -> list[ExtractedMessage]:
    """Extract message-like objects from a raw archive record."""
    messages: list[ExtractedMessage] = []
    for field in _MESSAGE_FIELDS:
        value = record.get(field)
        if isinstance(value, list):
            for index, item in enumerate(value):
                message = _coerce_message(item, fallback_index=index, field=field)
                if message is not None:
                    messages.append(message)
        elif isinstance(value, dict):
            message = _coerce_message(value, fallback_index=0, field=field)
            if message is not None:
                messages.append(message)
    # Some archive records carry a single text block under response/body/text.
    for field in ("body", "text", "response", "description"):
        value = record.get(field)
        if isinstance(value, str) and value.strip():
            messages.append(
                ExtractedMessage(
                    message_id=f"{field}:0",
                    body=value.strip(),
                    sent_at=parse_datetime(record.get("last_updated") or record.get("first_sent")),
                    sender=None,
                    recipient=None,
                    subject=str(record.get("title") or "") or None,
                    source_url=_safe_str(record.get("source_url") or record.get("url")),
                )
            )
    return messages


def _coerce_message(item: Any, *, fallback_index: int, field: str) -> ExtractedMessage | None:
    if isinstance(item, str):
        body = item.strip()
        if not body:
            return None
        return ExtractedMessage(message_id=f"{field}:{fallback_index}", body=body, sent_at=None)
    if not isinstance(item, dict):
        return None
    body_value = (
        item.get("body")
        or item.get("text")
        or item.get("content")
        or item.get("response")
        or item.get("html_to_text")
    )
    if not isinstance(body_value, str) or not body_value.strip():
        return None
    message_id = str(item.get("id") or item.get("message_id") or f"{field}:{fallback_index}")
    return ExtractedMessage(
        message_id=message_id,
        body=body_value.strip(),
        sent_at=parse_datetime(item.get("sent_at") or item.get("date") or item.get("created_at")),
        sender=_safe_str(item.get("sender") or item.get("from")),
        recipient=_safe_str(item.get("recipient") or item.get("to")),
        subject=_safe_str(item.get("subject")),
        source_url=_safe_str(item.get("source_url") or item.get("url")),
    )


def _safe_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _message_event_id(kind: str, profile: RequestProfile, message: ExtractedMessage) -> str:
    base = f"https://w3id.org/foio-nz/event/{kind}/{profile.source}/{profile.request_id}/{message.message_id}"
    return f"urn:uuid:{uuid5(NAMESPACE_URL, base)}"


def _evidence(profile: RequestProfile, message: ExtractedMessage, event_time: datetime) -> EvidenceRef:
    excerpt = message.body[:500]
    return EvidenceRef(
        evidence_id=f"evidence:{profile.source}:{profile.request_id}:message:{message.message_id}",
        evidence_type="message",
        source_url=message.source_url or profile.source_url,
        archive_ref=f"{profile.url_title or profile.request_id}#{message.message_id}",
        content_sha256=profile.content_sha256,
        excerpt=excerpt,
        observed_at=event_time,
    )


def _request_ref(profile: RequestProfile) -> RequestRef:
    return RequestRef(
        source_system=profile.source,
        source_request_id=profile.request_id,
        source_url=profile.source_url,
        url_title=profile.url_title,
        content_sha256=profile.content_sha256,
    )


def _base_event_kwargs(profile: RequestProfile, message: ExtractedMessage) -> dict[str, Any]:
    event_time = message.sent_at or profile.last_updated or profile.first_sent or datetime.now(UTC)
    return {
        "event_time": event_time,
        "request_ref": _request_ref(profile),
        "regime": DEFAULT_REGIME,
        "source_system": profile.source,
        "actor": Actor(role="system", name="fyi-archive-nz"),
        "machine_generated": True,
        "generator": {
            "system": "foi-o-nz",
            "model": None,
            "prompt_id": "rule-extractors-v0.2.0",
            "software_version": "0.2.0",
        },
        "evidence": [_evidence(profile, message, event_time)],
    }


def build_message_events(profile: RequestProfile, messages: list[ExtractedMessage]) -> list[CoreEvent]:
    """Build MessageObserved plus candidate process events from messages."""
    events: list[CoreEvent] = []
    for message in messages:
        kwargs = _base_event_kwargs(profile, message)
        events.append(
            CoreEvent(
                **kwargs,
                event_id=_message_event_id("message-observed", profile, message),
                event_type="MessageObserved",
                lifecycle_state_after=profile.normalised_state,
                assertion_status="observed",
                confidence=1.0,
                requires_human_certification=False,
                payload={
                    "message_id": message.message_id,
                    "sender": message.sender,
                    "recipient": message.recipient,
                    "subject": message.subject,
                    "body_chars": len(message.body),
                },
            )
        )
        events.extend(_candidate_events_from_message(profile, message))
    return events


def _candidate_events_from_message(profile: RequestProfile, message: ExtractedMessage) -> list[CoreEvent]:
    text = message.body
    candidates: list[tuple[str, str | None, float, str]] = []
    if _EXTENSION_RE.search(text):
        candidates.append(("ExtensionNotified", "ExtensionApplied", 0.58, "extension_language_detected"))
    if _TRANSFER_RE.search(text):
        candidates.append(("TransferNotified", "TransferredInFull", 0.54, "transfer_language_detected"))
    if _CLARIFICATION_RE.search(text):
        candidates.append(("ClarificationRequested", "AwaitingClarification", 0.52, "clarification_language_detected"))
    if _CHARGE_RE.search(text):
        candidates.append(("ChargeNoticeSent", "ChargeAssessment", 0.42, "charge_language_detected"))
    if _REFUSAL_RE.search(text):
        candidates.append(("RefusalCommunicated", "Refused", 0.46, "refusal_language_detected"))
    if _RELEASE_RE.search(text):
        candidates.append(("ReleaseMade", "ReleasedInPart", 0.38, "release_language_detected"))
    if _COMPLAINT_RE.search(text):
        candidates.append(("ComplaintObserved", "ComplaintMade", 0.44, "complaint_or_review_language_detected"))
    if _DECISION_RE.search(text):
        candidates.append(("DecisionCommunicated", profile.normalised_state, 0.40, "decision_language_detected"))

    out: list[CoreEvent] = []
    for event_type, lifecycle_state, confidence, flag in candidates:
        kwargs = _base_event_kwargs(profile, message)
        requires_certification = event_type in HUMAN_CERTIFICATION_EVENT_TYPES
        # These are observed communications/candidates, not certified legal acts.
        # Dispositive-looking event types carry the human-certification requirement
        # and a negative certification record to prevent accidental approval.
        human_certification = None
        if requires_certification:
            human_certification = {
                "certified": False,
                "certified_by_role": None,
                "certified_at": None,
                "certification_reference": None,
            }
        out.append(
            CoreEvent(
                **kwargs,
                event_id=_message_event_id(event_type.lower(), profile, message),
                event_type=event_type,
                lifecycle_state_after=lifecycle_state,
                assertion_status="inferred",
                confidence=confidence,
                requires_human_certification=requires_certification,
                human_certification=human_certification,
                legal_references=_legal_refs_for(event_type),
                payload={
                    "message_id": message.message_id,
                    "candidate_rule": flag,
                    "extractor": "regex_v0.2.0",
                },
                quality_flags=[flag, "requires_human_review"],
            )
        )
    return out

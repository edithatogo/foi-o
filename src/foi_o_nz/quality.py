"""Quality gates for FOI-O NZ event streams."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from foi_o_nz.constants import HUMAN_CERTIFICATION_EVENT_TYPES
from foi_o_nz.io import iter_jsonl

QUALITY_LIMITATIONS = [
    "Quality gates validate metadata, provenance, and guardrail consistency; they do not certify legal correctness."
]
LEGAL_REFERENCE_VERSION_FIELDS = {
    "uri",
    "work_id",
    "version_id",
    "retrieved_at",
    "source_status",
    "applicability_basis",
}
STALE_OR_UNVERIFIED_SOURCE_STATUS = {"external_gate", "deprecated", "unknown"}


@dataclass(frozen=True, slots=True)
class QualityFinding:
    """A machine-readable quality finding."""

    severity: str
    code: str
    message: str
    event_id: str | None = None

    def as_dict(self) -> dict[str, str | None]:
        """Serialise the finding."""
        return {
            "severity": self.severity,
            "code": self.code,
            "message": self.message,
            "event_id": self.event_id,
        }


def assess_event(event: dict[str, Any]) -> list[QualityFinding]:
    """Assess one event dictionary for certification/provenance issues."""
    findings: list[QualityFinding] = []
    event_id = str(event.get("event_id") or "") or None
    event_type = str(event.get("event_type") or "")
    assertion_status = str(event.get("assertion_status") or "")
    evidence = event.get("evidence")
    if not isinstance(evidence, list) or len(evidence) == 0:
        findings.append(
            QualityFinding(
                "error",
                "missing_evidence",
                "event must carry at least one evidence reference",
                event_id,
            )
        )
    if event.get("machine_generated") and not event.get("generator"):
        findings.append(
            QualityFinding(
                "warning",
                "missing_generator",
                "machine-generated event lacks generator metadata",
                event_id,
            )
        )
    if event_type in HUMAN_CERTIFICATION_EVENT_TYPES:
        if not event.get("requires_human_certification"):
            findings.append(
                QualityFinding(
                    "error",
                    "certification_boundary_bypassed",
                    f"{event_type} must require human certification",
                    event_id,
                )
            )
        human = event.get("human_certification")
        if not isinstance(human, dict):
            findings.append(
                QualityFinding(
                    "error",
                    "missing_human_certification_metadata",
                    f"{event_type} must carry human certification metadata",
                    event_id,
                )
            )
        elif assertion_status == "certified" and human.get("certified") is not True:
            findings.append(
                QualityFinding(
                    "error",
                    "false_certified_assertion",
                    "certified assertion must have human_certification.certified=true",
                    event_id,
                )
            )
        elif assertion_status != "certified" and human.get("certified") is True:
            findings.append(
                QualityFinding(
                    "warning",
                    "certification_status_mismatch",
                    "human certification is positive but assertion_status is not certified",
                    event_id,
                )
            )
    legal_references = event.get("legal_references")
    if isinstance(legal_references, list):
        for reference in legal_references:
            if not isinstance(reference, dict):
                continue
            missing = sorted(
                field
                for field in LEGAL_REFERENCE_VERSION_FIELDS
                if reference.get(field) in {None, ""}
            )
            if missing:
                findings.append(
                    QualityFinding(
                        "warning",
                        "unversioned_legal_reference",
                        f"legal reference lacks version/source fields: {', '.join(missing)}",
                        event_id,
                    )
                )
            if reference.get("source_status") in STALE_OR_UNVERIFIED_SOURCE_STATUS:
                findings.append(
                    QualityFinding(
                        "warning",
                        "stale_or_unverified_legal_reference",
                        "legal reference source status is not an official current snapshot",
                        event_id,
                    )
                )
    if assertion_status == "certified" and event.get("machine_generated") is True:
        findings.append(
            QualityFinding(
                "warning",
                "machine_generated_certified_event",
                "certified event is marked machine_generated; verify authorised human action is captured",
                event_id,
            )
        )
    return findings


def assess_events(events: list[dict[str, Any]]) -> dict[str, Any]:
    """Assess an in-memory event list."""
    findings: list[QualityFinding] = []
    for event in events:
        findings.extend(assess_event(event))
    error_count = sum(1 for finding in findings if finding.severity == "error")
    warning_count = sum(1 for finding in findings if finding.severity == "warning")
    return {
        "ok": error_count == 0,
        "event_count": len(events),
        "error_count": error_count,
        "warning_count": warning_count,
        "findings": [finding.as_dict() for finding in findings],
        "limitations": QUALITY_LIMITATIONS,
    }


def assess_events_jsonl(path: Path) -> dict[str, Any]:
    """Assess an event JSONL file."""
    return assess_events(list(iter_jsonl(path)))

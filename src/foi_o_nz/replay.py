"""Replay guardrails over events and agent actions."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic_core import ValidationError

from foi_o_nz.agent_policy import evaluate_agent_action
from foi_o_nz.constants import GUARDRAIL_REPLAY_SCHEMA_VERSION, HUMAN_CERTIFICATION_EVENT_TYPES
from foi_o_nz.io import iter_jsonl, write_json


class ReplayFinding(BaseModel):
    """One replay finding."""

    model_config = ConfigDict(extra="forbid")

    severity: Literal["info", "warning", "error"]
    code: str
    source_id: str | None = None
    message: str


class GuardrailReplayReport(BaseModel):
    """Guardrail replay report for a request/event/action stream."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["foi-o-nz.guardrail-replay.v0.1.0"] = GUARDRAIL_REPLAY_SCHEMA_VERSION
    generated_at: datetime
    ok: bool
    event_count: int = Field(ge=0)
    action_count: int = Field(ge=0)
    findings: list[ReplayFinding] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


def replay_guardrails(
    *,
    events_jsonl: Path | None = None,
    actions_jsonl: Path | None = None,
) -> GuardrailReplayReport:
    """Replay certification-boundary and action-policy guardrails."""
    findings: list[ReplayFinding] = []
    event_count = 0
    action_count = 0
    if events_jsonl is not None:
        for event in iter_jsonl(events_jsonl):
            event_count += 1
            event_id = str(event.get("event_id") or f"event-{event_count}")
            event_type = str(event.get("event_type") or "")
            if event_type in HUMAN_CERTIFICATION_EVENT_TYPES:
                if event.get("requires_human_certification") is not True:
                    findings.append(
                        ReplayFinding(
                            severity="error",
                            code="dispositive_event_missing_certification_requirement",
                            source_id=event_id,
                            message=f"{event_type} must require human certification.",
                        )
                    )
                certification = (
                    event.get("human_certification")
                    if isinstance(event.get("human_certification"), dict)
                    else None
                )
                if certification is None:
                    findings.append(
                        ReplayFinding(
                            severity="error",
                            code="dispositive_event_missing_human_certification_metadata",
                            source_id=event_id,
                            message=f"{event_type} must carry human_certification metadata.",
                        )
                    )
            if event.get("assertion_status") == "certified":
                certification = (
                    event.get("human_certification")
                    if isinstance(event.get("human_certification"), dict)
                    else None
                )
                if certification is None or certification.get("certified") is not True:
                    findings.append(
                        ReplayFinding(
                            severity="error",
                            code="certified_assertion_without_positive_human_certification",
                            source_id=event_id,
                            message="Certified assertions require positive human certification metadata.",
                        )
                    )
            if (
                event.get("machine_generated") is True
                and event.get("assertion_status") == "certified"
            ):
                findings.append(
                    ReplayFinding(
                        severity="error",
                        code="machine_generated_certified_event",
                        source_id=event_id,
                        message="Machine-generated events must not be directly certified without human metadata and review.",
                    )
                )
    if actions_jsonl is not None:
        for action in iter_jsonl(actions_jsonl):
            action_count += 1
            try:
                result = evaluate_agent_action(action)
            except (ValueError, ValidationError) as exc:
                findings.append(
                    ReplayFinding(
                        severity="error",
                        code="invalid_agent_action",
                        source_id=str(action.get("action_id") or f"action-{action_count}"),
                        message=str(exc),
                    )
                )
                continue
            for finding in result.get("findings", []):
                if not isinstance(finding, dict):
                    continue
                findings.append(
                    ReplayFinding(
                        severity=finding.get("severity", "warning"),  # type: ignore[arg-type]
                        code=str(finding.get("code", "agent_action_policy_finding")),
                        source_id=str(result.get("action_id")),
                        message=str(finding.get("message", "Agent action policy finding.")),
                    )
                )
            if result.get("requires_human_certification") and not action.get(
                "human_review_required", True
            ):
                findings.append(
                    ReplayFinding(
                        severity="warning",
                        code="high_risk_action_without_explicit_human_review_flag",
                        source_id=str(result.get("action_id")),
                        message="Action policy requires human certification/review; retain explicit review workflow metadata.",
                    )
                )
            if result.get("legal_effect") == "preparatory" and result.get("ok"):
                audit_trace = [
                    str(item) for item in action.get("audit_trace", []) if isinstance(item, str)
                ]
                if audit_trace:
                    findings.append(
                        ReplayFinding(
                            severity="info",
                            code="preparatory_action_context_retained",
                            source_id=str(result.get("action_id")),
                            message=(
                                "Safe preparatory action retained provenance for human review: "
                                + ", ".join(audit_trace)
                            ),
                        )
                    )
                else:
                    findings.append(
                        ReplayFinding(
                            severity="warning",
                            code="preparatory_action_missing_audit_trace",
                            source_id=str(result.get("action_id")),
                            message="Preparatory action should retain audit_trace provenance.",
                        )
                    )
    ok = not any(finding.severity == "error" for finding in findings)
    return GuardrailReplayReport(
        generated_at=datetime.now(UTC),
        ok=ok,
        event_count=event_count,
        action_count=action_count,
        findings=findings,
        limitations=[
            "Replay checks guardrail metadata only; they do not validate factual correctness or legal adequacy.",
            "Warnings should be triaged by a human operator before relying on derived artifacts.",
        ],
    )


def write_guardrail_replay(
    output: Path,
    *,
    events_jsonl: Path | None = None,
    actions_jsonl: Path | None = None,
) -> dict[str, Any]:
    """Write a guardrail replay report."""
    report = replay_guardrails(events_jsonl=events_jsonl, actions_jsonl=actions_jsonl)
    write_json(output, report.model_dump(mode="json", exclude_none=True))
    return report.model_dump(mode="json", exclude_none=True)

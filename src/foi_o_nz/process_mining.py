"""Process-mining fixture exports for FOI-O NZ event logs."""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime
from html import escape
from pathlib import Path
from typing import Any, Literal

from foi_o_nz.io import read_json_records, write_json

ProcessMiningFormat = Literal["xes", "ocel"]
PROCESS_MINING_SCHEMA_VERSION = "foi-o-nz.process-mining-ocel.v0.1.0"
PROCESS_MINING_CONFORMANCE_SCHEMA_VERSION = "foi-o-nz.process-mining-conformance.v0.1.0"
EXPECTED_RELEASE_PATH = [
    "RequestObserved",
    "RequestRegistered",
    "DeadlineCalculated",
    "SearchPlanDrafted",
    "DecisionPackDrafted",
    "HumanDecisionCertified",
    "DecisionCommunicated",
    "ReleaseMade",
    "Closed",
]


def load_process_mining_events(path: Path) -> list[dict[str, Any]]:
    """Load and order event records for deterministic process-mining export."""
    records = read_json_records(path)
    return sorted(
        records, key=lambda item: (str(item.get("event_time", "")), str(item.get("event_id", "")))
    )


def build_xes_event_log(events: list[dict[str, Any]]) -> str:
    """Build a minimal XES log with one trace per source request id."""
    cases: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for event in events:
        case_id = _case_id(event)
        cases[case_id].append(event)

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<log xes.version="1.0" xes.features="nested-attributes" xmlns="http://www.xes-standard.org/">',
        '  <extension name="Concept" prefix="concept" uri="http://www.xes-standard.org/concept.xesext"/>',
        '  <extension name="Time" prefix="time" uri="http://www.xes-standard.org/time.xesext"/>',
        '  <extension name="Lifecycle" prefix="lifecycle" uri="http://www.xes-standard.org/lifecycle.xesext"/>',
        '  <string key="concept:name" value="FOI-O NZ fixture event log"/>',
        '  <string key="foio:scope" value="fixture_only"/>',
        '  <string key="foio:claim_boundary" value="not_live_corpus_validation"/>',
    ]
    for case_id in sorted(cases):
        lines.append("  <trace>")
        lines.append(f'    <string key="concept:name" value="{escape(case_id)}"/>')
        for event in cases[case_id]:
            lines.extend(_xes_event_lines(event))
        lines.append("  </trace>")
    lines.append("</log>")
    return "\n".join(lines) + "\n"


def build_ocel_event_log(events: list[dict[str, Any]]) -> dict[str, Any]:
    """Build an OCEL-style JSON fixture for process-mining tool import."""
    ordered = sorted(
        events, key=lambda item: (str(item.get("event_time", "")), str(item.get("event_id", "")))
    )
    request_ids = sorted({_case_id(event) for event in ordered})
    objects = [
        {
            "id": request_id,
            "type": "foi_request",
            "attributes": {
                "jurisdiction": _first_case_value(ordered, request_id, "jurisdiction"),
                "regime": _first_case_value(ordered, request_id, "regime"),
                "source_system": _first_case_value(ordered, request_id, "source_system"),
            },
        }
        for request_id in request_ids
    ]
    events_out = [
        {
            "id": str(event["event_id"]),
            "activity": str(event["event_type"]),
            "timestamp": str(event["event_time"]),
            "objects": [_case_id(event)],
            "attributes": {
                "assertion_status": event.get("assertion_status"),
                "lifecycle_state_after": event.get("lifecycle_state_after"),
                "machine_generated": event.get("machine_generated"),
                "requires_human_certification": event.get("requires_human_certification"),
            },
        }
        for event in ordered
    ]
    return {
        "schema_version": PROCESS_MINING_SCHEMA_VERSION,
        "scope": "fixture_only",
        "claim_boundary": "not_live_corpus_validation",
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "object_types": [{"name": "foi_request"}],
        "event_types": sorted({str(event["event_type"]) for event in ordered}),
        "objects": objects,
        "events": events_out,
        "notes": [
            "This fixture demonstrates process-mining interchange only.",
            "It is not a human-reviewed gold standard and does not prove process performance.",
        ],
    }


def write_process_mining_export(
    *,
    events_path: Path,
    output: Path,
    fmt: ProcessMiningFormat,
) -> dict[str, Any]:
    """Write a process-mining export in XES or OCEL JSON format."""
    events = load_process_mining_events(events_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    if fmt == "xes":
        output.write_text(build_xes_event_log(events), encoding="utf-8")
    elif fmt == "ocel":
        data = build_ocel_event_log(events)
        data["generated_at"] = "2026-07-03T00:00:00Z"
        write_json(output, data)
    else:
        raise ValueError(f"Unsupported process-mining format: {fmt}")
    return {
        "ok": True,
        "output": str(output),
        "format": fmt,
        "scope": "fixture_only",
        "event_count": len(events),
        "case_count": len({_case_id(event) for event in events}),
    }


def build_process_mining_conformance(events: list[dict[str, Any]]) -> dict[str, Any]:
    """Build a fixture-only conformance report for the expected release path."""
    ordered = sorted(
        events, key=lambda item: (str(item.get("event_time", "")), str(item.get("event_id", "")))
    )
    activities = [str(event["event_type"]) for event in ordered]
    case_ids = sorted({_case_id(event) for event in ordered})
    findings: list[dict[str, str]] = [
        {
            "severity": "info",
            "code": "fixture_only",
            "message": "Conformance is checked only for the committed fixture event log; it is not live corpus validation.",
        }
    ]
    if activities != EXPECTED_RELEASE_PATH:
        findings.append(
            {
                "severity": "error",
                "code": "release_path_sequence_mismatch",
                "message": "Fixture activities do not match the expected release-path sequence.",
            }
        )
    if not _activity_before(activities, "HumanDecisionCertified", "DecisionCommunicated"):
        findings.append(
            {
                "severity": "error",
                "code": "decision_communicated_before_certification",
                "message": "Decision communication must follow human certification in the fixture path.",
            }
        )
    if not _activity_before(activities, "HumanDecisionCertified", "ReleaseMade"):
        findings.append(
            {
                "severity": "error",
                "code": "release_before_certification",
                "message": "Release must follow human certification in the fixture path.",
            }
        )
    if len(case_ids) != 1:
        findings.append(
            {
                "severity": "warning",
                "code": "unexpected_fixture_case_count",
                "message": "The current fixture conformance report is designed for one request case.",
            }
        )
    if any(event.get("assertion_status") == "candidate" for event in ordered):
        findings.append(
            {
                "severity": "info",
                "code": "candidate_events_preserved",
                "message": "Candidate events are preserved in the fixture and not treated as certified outcomes.",
            }
        )
    error_count = sum(1 for finding in findings if finding["severity"] == "error")
    return {
        "schema_version": PROCESS_MINING_CONFORMANCE_SCHEMA_VERSION,
        "scope": "fixture_only",
        "claim_boundary": "not_live_corpus_validation",
        "case_count": len(case_ids),
        "event_count": len(ordered),
        "expected_release_path": EXPECTED_RELEASE_PATH,
        "observed_activity_sequence": activities,
        "human_certification_before_decision": _activity_before(
            activities, "HumanDecisionCertified", "DecisionCommunicated"
        ),
        "human_certification_before_release": _activity_before(
            activities, "HumanDecisionCertified", "ReleaseMade"
        ),
        "candidate_event_types": sorted(
            {
                str(event["event_type"])
                for event in ordered
                if event.get("assertion_status") == "candidate"
            }
        ),
        "findings": findings,
        "ok": error_count == 0,
    }


def write_process_mining_conformance(events_path: Path, output: Path) -> dict[str, Any]:
    """Write a fixture-only process-mining conformance report."""
    report = build_process_mining_conformance(load_process_mining_events(events_path))
    write_json(output, report)
    return report


def _xes_event_lines(event: dict[str, Any]) -> list[str]:
    attrs = {
        "concept:name": str(event["event_type"]),
        "lifecycle:transition": "complete",
        "foio:event_id": str(event["event_id"]),
        "foio:assertion_status": str(event.get("assertion_status", "")),
        "foio:lifecycle_state_after": str(event.get("lifecycle_state_after", "")),
        "foio:requires_human_certification": str(
            event.get("requires_human_certification", "")
        ).lower(),
    }
    lines = ["    <event>"]
    for key, value in attrs.items():
        lines.append(f'      <string key="{escape(key)}" value="{escape(value)}"/>')
    lines.append(f'      <date key="time:timestamp" value="{escape(str(event["event_time"]))}"/>')
    lines.append("    </event>")
    return lines


def _case_id(event: dict[str, Any]) -> str:
    request_ref = event.get("request_ref", {})
    source_system = request_ref.get("source_system", event.get("source_system", "unknown"))
    source_request_id = request_ref.get("source_request_id", "unknown")
    return f"{source_system}:{source_request_id}"


def _first_case_value(events: list[dict[str, Any]], case_id: str, key: str) -> Any:
    for event in events:
        if _case_id(event) == case_id:
            return event.get(key)
    return None


def _activity_before(activities: list[str], earlier: str, later: str) -> bool:
    if earlier not in activities or later not in activities:
        return False
    return activities.index(earlier) < activities.index(later)

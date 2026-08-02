from __future__ import annotations

from pathlib import Path

import defusedxml.ElementTree as ET  # noqa: N817

PLAN = Path(
    "conductor/tracks/australian_jurisdiction_profiles_20260714/nsw-source-recovery-20260724.md"
)
BPMN = Path(
    "conductor/tracks/australian_jurisdiction_profiles_20260714/nsw-source-recovery-20260724.bpmn"
)
TRACK_PLAN = Path("conductor/tracks/australian_jurisdiction_profiles_20260714/plan.md")
BPMN_NS = {"bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL"}


def test_source_recovery_plan_preserves_all_capture_and_human_gate_boundaries() -> None:
    plan = PLAN.read_text(encoding="utf-8")

    assert "`url_index`" in plan
    assert "`all_captures`" in plan
    assert "`EXPORT_ALL_CAPTURE_METADATA`" in plan
    assert "hash-bound human approval" in plan
    assert "partial export" in plan
    assert "30176570901" in plan
    assert "954af9aa0b844484cc9d88cf3a6b5bb9812644176b237c238f0419ec82fe1449" in plan
    assert "operator-supplied non-empty CDX export" in plan
    assert "not a standing authorization" in plan
    assert "AU-NSW historical source recovery refinement" in TRACK_PLAN.read_text(encoding="utf-8")


def test_source_recovery_bpmn_is_a_non_executable_human_gated_review_model() -> None:
    root = ET.parse(BPMN).getroot()
    assert root is not None
    process = root.find("bpmn:process", BPMN_NS)
    assert process is not None
    assert process.attrib["isExecutable"] == "false"
    approvals = {task.attrib["id"] for task in process.findall("bpmn:userTask", BPMN_NS)}
    flows = {
        (flow.attrib["sourceRef"], flow.attrib["targetRef"])
        for flow in process.findall("bpmn:sequenceFlow", BPMN_NS)
    }
    assert approvals == {"Task_HashBoundApproval"}
    assert ("Task_ValidateJSONL", "Task_HashBoundApproval") in flows
    assert ("Task_HashBoundApproval", "Task_CreateManifest") in flows

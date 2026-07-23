from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path


PLAN = Path("conductor/tracks/australian_jurisdiction_profiles_20260714/nsw-source-recovery-20260724.md")
BPMN = Path("conductor/tracks/australian_jurisdiction_profiles_20260714/nsw-source-recovery-20260724.bpmn")
BPMN_NS = {"bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL"}


def test_source_recovery_plan_preserves_all_capture_and_human_gate_boundaries() -> None:
    plan = PLAN.read_text(encoding="utf-8")

    assert "`url_index`" in plan
    assert "`all_captures`" in plan
    assert "`EXPORT_ALL_CAPTURE_METADATA`" in plan
    assert "hash-bound human approval" in plan
    assert "partial export" in plan


def test_source_recovery_bpmn_is_a_non_executable_human_gated_review_model() -> None:
    process = ET.parse(BPMN).getroot().find("bpmn:process", BPMN_NS)

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

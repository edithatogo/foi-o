"""Generate process-model interchange artefacts from canonical transitions."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from html import escape
from pathlib import Path
from typing import Any, Literal

from foi_o_nz.io import write_json
from foi_o_nz.state_machine import ALLOWED_TRANSITIONS, TERMINAL_STATES, RequestState

ProcessModelFormat = Literal["bpmn", "pnml", "mermaid"]
BPMN_NS = {"bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL"}


def canonical_states() -> list[RequestState]:
    """Return all states that participate in the canonical transition model."""
    states = set(ALLOWED_TRANSITIONS) | {
        target for targets in ALLOWED_TRANSITIONS.values() for target in targets
    }
    states.update(TERMINAL_STATES)
    return sorted(states, key=lambda state: state.value)


def canonical_transitions() -> list[tuple[RequestState, RequestState]]:
    """Return sorted canonical transitions from the state-machine contract."""
    transitions = [
        (source, target) for source, targets in ALLOWED_TRANSITIONS.items() for target in targets
    ]
    return sorted(transitions, key=lambda item: (item[0].value, item[1].value))


def build_process_model(fmt: ProcessModelFormat) -> str:
    """Build a process-model source string in the requested format."""
    if fmt == "bpmn":
        return build_bpmn_model()
    if fmt == "pnml":
        return build_pnml_model()
    if fmt == "mermaid":
        return build_mermaid_model()
    raise ValueError(f"Unsupported process model format: {fmt}")


def build_bpmn_model() -> str:
    """Build non-executable BPMN 2.0 XML from canonical transitions."""
    states = canonical_states()
    transitions = canonical_transitions()
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<definitions xmlns="http://www.omg.org/spec/BPMN/20100524/MODEL"',
        '  id="Definitions_FOIO_NZ_StateMachine"',
        '  targetNamespace="https://w3id.org/foio-nz/process/bpmn/state-machine">',
        '  <process id="Process_FOIO_NZ_StateMachine" name="FOI-O NZ canonical state transitions" isExecutable="false">',
        '    <startEvent id="Start_StateMachine" name="Start"/>',
        '    <endEvent id="End_StateMachine" name="End"/>',
    ]
    for state in states:
        lines.append(f'    <task id="{_bpmn_state_id(state)}" name="{escape(state.value)}"/>')
    lines.append(
        f'    <sequenceFlow id="Flow_Start_Drafted" sourceRef="Start_StateMachine" targetRef="{_bpmn_state_id(RequestState.DRAFTED)}"/>'
    )
    for index, (source, target) in enumerate(transitions, start=1):
        lines.append(
            f'    <sequenceFlow id="Flow_{index:03d}" sourceRef="{_bpmn_state_id(source)}" targetRef="{_bpmn_state_id(target)}"/>'
        )
    for state in sorted(TERMINAL_STATES, key=lambda item: item.value):
        lines.append(
            f'    <sequenceFlow id="Flow_End_{_xml_id(state.value)}" sourceRef="{_bpmn_state_id(state)}" targetRef="End_StateMachine"/>'
        )
    lines.extend(["  </process>", "</definitions>"])
    return "\n".join(lines) + "\n"


def build_pnml_model() -> str:
    """Build PNML from canonical transitions."""
    states = canonical_states()
    transitions = canonical_transitions()
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        "<pnml>",
        '  <net id="foio_nz_state_machine" type="http://www.pnml.org/version-2009/grammar/ptnet">',
        "    <name><text>FOI-O NZ canonical state-transition Petri net</text></name>",
        '    <page id="page_state_machine">',
    ]
    for state in states:
        lines.append(
            f'      <place id="{_pnml_place_id(state)}"><name><text>{escape(state.value)}</text></name></place>'
        )
    for index, (source, target) in enumerate(transitions, start=1):
        transition_id = _pnml_transition_id(index)
        lines.append(
            f'      <transition id="{transition_id}"><name><text>{escape(source.value)} to {escape(target.value)}</text></name></transition>'
        )
        lines.append(
            f'      <arc id="arc_{index:03d}_in" source="{_pnml_place_id(source)}" target="{transition_id}"/>'
        )
        lines.append(
            f'      <arc id="arc_{index:03d}_out" source="{transition_id}" target="{_pnml_place_id(target)}"/>'
        )
    lines.extend(["    </page>", "  </net>", "</pnml>"])
    return "\n".join(lines) + "\n"


def build_mermaid_model() -> str:
    """Build Mermaid stateDiagram source from canonical transitions."""
    lines = ["stateDiagram-v2", "  [*] --> Drafted"]
    for source, target in canonical_transitions():
        lines.append(f"  {source.value} --> {target.value}")
    for state in sorted(TERMINAL_STATES, key=lambda item: item.value):
        lines.append(f"  {state.value} --> [*]")
    return "\n".join(lines) + "\n"


def write_process_model(output: Path, fmt: ProcessModelFormat) -> dict[str, Any]:
    """Write a process-model source file and return a summary."""
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(build_process_model(fmt), encoding="utf-8")
    return {
        "ok": True,
        "output": str(output),
        "format": fmt,
        "state_count": len(canonical_states()),
        "transition_count": len(canonical_transitions()),
    }


def build_process_model_conformance(
    *,
    core_bpmn: Path = Path("process_models/foi-o-nz-core.bpmn"),
    core_pnml: Path = Path("process_models/foi-o-nz-core.pnml"),
    generated_bpmn: Path = Path("process_models/foi-o-nz-state-machine.bpmn"),
    generated_pnml: Path = Path("process_models/foi-o-nz-state-machine.pnml"),
) -> dict[str, Any]:
    """Compare hand-authored process models with generated canonical exports."""
    core_bpmn_summary = _summarise_bpmn(core_bpmn)
    generated_bpmn_summary = _summarise_bpmn(generated_bpmn)
    core_pnml_summary = _summarise_pnml(core_pnml)
    generated_pnml_summary = _summarise_pnml(generated_pnml)
    findings = [
        {
            "severity": "info",
            "code": "abstraction_expected",
            "message": "Hand-authored core BPMN/PNML models are process-review abstractions; generated state-machine models are canonical transition exports.",
        },
        {
            "severity": "info",
            "code": "state_transition_count_difference",
            "message": "Generated models expose each canonical state transition; core models collapse related administrative work into higher-level workflow activities.",
        },
    ]
    if not core_bpmn_summary["human_certification_before_outcome"]:
        findings.append(
            {
                "severity": "error",
                "code": "bpmn_human_certification_missing",
                "message": "Core BPMN does not route decision-like outcomes through human certification.",
            }
        )
    if not core_pnml_summary["human_certification_before_outcome"]:
        findings.append(
            {
                "severity": "error",
                "code": "pnml_human_certification_missing",
                "message": "Core PNML does not route decision-like outcomes through human certification.",
            }
        )
    error_count = sum(1 for finding in findings if finding["severity"] == "error")
    return {
        "schema_version": "foi-o-nz.process-model-conformance.v0.1.0",
        "scope": "Core workflow process models compared with generated canonical state-machine exports",
        "core_bpmn": core_bpmn_summary,
        "generated_bpmn": generated_bpmn_summary,
        "core_pnml": core_pnml_summary,
        "generated_pnml": generated_pnml_summary,
        "canonical_state_count": len(canonical_states()),
        "canonical_transition_count": len(canonical_transitions()),
        "intentional_abstractions": [
            "Core BPMN groups search, consultation, extension, and charge assessment as workflow activities.",
            "Generated BPMN exposes state-to-state transitions from ALLOWED_TRANSITIONS.",
            "Core PNML is a process-review net; generated PNML is a state-transition net.",
            "Neither model is executable legal workflow or decision certification.",
        ],
        "human_certification_preserved": (
            core_bpmn_summary["human_certification_before_outcome"]
            and core_pnml_summary["human_certification_before_outcome"]
        ),
        "findings": findings,
        "ok": error_count == 0,
    }


def write_process_model_conformance(output: Path) -> dict[str, Any]:
    """Write the process-model conformance report."""
    report = build_process_model_conformance()
    write_json(output, report)
    return report


def _xml_id(value: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in value)


def _bpmn_state_id(state: RequestState) -> str:
    return f"State_{_xml_id(state.value)}"


def _pnml_place_id(state: RequestState) -> str:
    return f"p_{_xml_id(state.value)}"


def _pnml_transition_id(index: int) -> str:
    return f"t_{index:03d}"


def _summarise_bpmn(path: Path) -> dict[str, Any]:
    # These are committed repo-local process-model artefacts, not user-supplied XML.
    root = ET.parse(path).getroot()  # noqa: S314
    process = root.find("bpmn:process", BPMN_NS)
    if process is None:
        raise ValueError(f"{path}: missing BPMN process")
    task_ids = {
        task.attrib["id"]
        for tag in ["task", "userTask"]
        for task in process.findall(f"bpmn:{tag}", BPMN_NS)
    }
    flows = [
        (flow.attrib["sourceRef"], flow.attrib["targetRef"])
        for flow in process.findall("bpmn:sequenceFlow", BPMN_NS)
    ]
    human_before_outcome = (
        ("Task_HumanCertification", "Gateway_Outcome") in flows
        and ("Gateway_Outcome", "Task_ReleaseFull") in flows
        and ("Gateway_Outcome", "Task_ReleasePart") in flows
        and ("Gateway_Outcome", "Task_Refuse") in flows
    )
    return {
        "path": str(path),
        "task_count": len(task_ids),
        "sequence_flow_count": len(flows),
        "human_certification_before_outcome": human_before_outcome,
        "is_generated": "state-machine" in path.name,
    }


def _summarise_pnml(path: Path) -> dict[str, Any]:
    # These are committed repo-local process-model artefacts, not user-supplied XML.
    root = ET.parse(path).getroot()  # noqa: S314
    places = {place.attrib["id"] for place in root.findall(".//place")}
    transitions = {transition.attrib["id"] for transition in root.findall(".//transition")}
    arcs = {(arc.attrib["source"], arc.attrib["target"]) for arc in root.findall(".//arc")}
    human_before_outcome = (
        ("p_decision_pack", "t_human_certification") in arcs
        and ("t_human_certification", "p_human_certified") in arcs
        and ("p_human_certified", "t_release_full") in arcs
        and ("p_human_certified", "t_release_part") in arcs
        and ("p_human_certified", "t_refuse") in arcs
    )
    return {
        "path": str(path),
        "place_count": len(places),
        "transition_count": len(transitions),
        "arc_count": len(arcs),
        "human_certification_before_outcome": human_before_outcome,
        "is_generated": "state-machine" in path.name,
    }

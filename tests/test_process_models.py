from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

from foi_o_nz.process_models import (
    build_bpmn_model,
    build_mermaid_model,
    build_pnml_model,
    build_process_model_conformance,
    write_process_model_conformance,
)
from foi_o_nz.validation import validate_json_schema

BPMN = Path("process_models/foi-o-nz-core.bpmn")
PNML = Path("process_models/foi-o-nz-core.pnml")
GENERATED_BPMN = Path("process_models/foi-o-nz-state-machine.bpmn")
GENERATED_PNML = Path("process_models/foi-o-nz-state-machine.pnml")
GENERATED_MERMAID = Path("process_models/foi-o-nz-state-machine.mmd")
CONFORMANCE = Path("examples/process-model-conformance.ontology-maturation.json")
CONFORMANCE_SCHEMA = Path("schemas/json/process-model-conformance.schema.json")
PROCESS_DOC = Path("docs/31-process-models.md")
ASSET_INDEX = Path("docs/25-generated-asset-index.md")

BPMN_NS = {"bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL"}


def test_process_model_document_distinguishes_ontology_from_process_model() -> None:
    text = PROCESS_DOC.read_text(encoding="utf-8")

    assert "FOI-O NZ has both an ontology and a process model" in text
    assert "`ontology/foi-o-nz.ttl`" in text
    assert "`process_models/foi-o-nz-core.bpmn`" in text
    assert "`process_models/foi-o-nz-core.pnml`" in text
    assert "`process_models/foi-o-nz-state-machine.bpmn`" in text
    assert "`process_models/foi-o-nz-state-machine.pnml`" in text
    assert "`examples/process-model-conformance.ontology-maturation.json`" in text
    assert "They do not replace the ontology" in text


def test_bpmn_core_process_model_parses_and_preserves_human_certification() -> None:
    tree = ET.parse(BPMN)
    root = tree.getroot()

    process = root.find("bpmn:process", BPMN_NS)
    assert process is not None
    assert process.attrib["isExecutable"] == "false"

    start_events = process.findall("bpmn:startEvent", BPMN_NS)
    end_events = process.findall("bpmn:endEvent", BPMN_NS)
    tasks = {
        task.attrib["id"]: task.attrib.get("name", "")
        for tag in ["task", "userTask"]
        for task in process.findall(f"bpmn:{tag}", BPMN_NS)
    }
    flows = [
        (flow.attrib["sourceRef"], flow.attrib["targetRef"])
        for flow in process.findall("bpmn:sequenceFlow", BPMN_NS)
    ]

    assert start_events
    assert end_events
    assert "Task_HumanCertification" in tasks
    assert tasks["Task_HumanCertification"] == "Human certifies decision-like outcome"
    assert ("Task_DraftDecisionPack", "Task_HumanCertification") in flows
    assert ("Task_HumanCertification", "Gateway_Outcome") in flows
    assert ("Gateway_Outcome", "Task_ReleaseFull") in flows
    assert ("Gateway_Outcome", "Task_ReleasePart") in flows
    assert ("Gateway_Outcome", "Task_Refuse") in flows


def test_pnml_core_process_model_parses_and_preserves_human_certification() -> None:
    tree = ET.parse(PNML)
    root = tree.getroot()

    places = {place.attrib["id"] for place in root.findall(".//place")}
    transitions = {transition.attrib["id"] for transition in root.findall(".//transition")}
    arcs = {(arc.attrib["source"], arc.attrib["target"]) for arc in root.findall(".//arc")}

    assert "p_observed" in places
    assert "p_human_certified" in places
    assert "p_closed" in places
    assert "t_human_certification" in transitions
    assert ("p_decision_pack", "t_human_certification") in arcs
    assert ("p_no_records", "t_human_certification") in arcs
    assert ("t_human_certification", "p_human_certified") in arcs
    assert ("p_human_certified", "t_release_full") in arcs
    assert ("p_human_certified", "t_release_part") in arcs
    assert ("p_human_certified", "t_refuse") in arcs


def test_process_models_are_registered_as_generated_assets() -> None:
    index = ASSET_INDEX.read_text(encoding="utf-8")

    for path in [BPMN, PNML, GENERATED_BPMN, GENERATED_PNML, GENERATED_MERMAID]:
        assert path.exists(), path
        assert f"`{path}`" in index


def test_generated_process_models_match_canonical_transition_generator() -> None:
    assert GENERATED_BPMN.read_text(encoding="utf-8") == build_bpmn_model()
    assert GENERATED_PNML.read_text(encoding="utf-8") == build_pnml_model()
    assert GENERATED_MERMAID.read_text(encoding="utf-8") == build_mermaid_model()


def test_generated_bpmn_and_pnml_parse() -> None:
    bpmn_tree = ET.parse(GENERATED_BPMN)
    bpmn_root = bpmn_tree.getroot()
    bpmn_process = bpmn_root.find("bpmn:process", BPMN_NS)
    assert bpmn_process is not None
    assert bpmn_process.attrib["isExecutable"] == "false"
    assert len(bpmn_process.findall("bpmn:task", BPMN_NS)) >= 20
    assert len(bpmn_process.findall("bpmn:sequenceFlow", BPMN_NS)) >= 37

    pnml_tree = ET.parse(GENERATED_PNML)
    pnml_root = pnml_tree.getroot()
    assert len(pnml_root.findall(".//place")) >= 20
    assert len(pnml_root.findall(".//transition")) >= 37


def test_process_model_conformance_report_validates_and_matches_generator(
    tmp_path: Path,
) -> None:
    result = validate_json_schema(CONFORMANCE, CONFORMANCE_SCHEMA)
    assert not result.errors, result.errors

    fixture = json.loads(CONFORMANCE.read_text(encoding="utf-8"))
    generated = build_process_model_conformance()
    assert fixture == generated
    assert fixture["ok"] is True
    assert fixture["human_certification_preserved"] is True
    assert fixture["core_bpmn"]["human_certification_before_outcome"] is True
    assert fixture["core_pnml"]["human_certification_before_outcome"] is True
    assert fixture["generated_bpmn"]["is_generated"] is True
    assert fixture["generated_pnml"]["is_generated"] is True
    assert {finding["code"] for finding in fixture["findings"]} >= {
        "abstraction_expected",
        "state_transition_count_difference",
    }

    output = tmp_path / "process-model-conformance.json"
    written = write_process_model_conformance(output)
    assert written == generated
    assert json.loads(output.read_text(encoding="utf-8")) == generated

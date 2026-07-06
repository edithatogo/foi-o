from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

from foi_o_nz.process_mining import (
    build_ocel_event_log,
    build_process_mining_conformance,
    build_xes_event_log,
    load_process_mining_events,
    write_process_mining_conformance,
    write_process_mining_export,
)
from foi_o_nz.validation import validate_json_schema

EVENTS = Path("examples/process-mining-events.fixture.jsonl")
XES = Path("examples/process-mining.fixture.xes")
OCEL = Path("examples/process-mining.fixture.ocel.json")
CONFORMANCE = Path("examples/process-mining-conformance.fixture.json")
OCEL_SCHEMA = Path("schemas/json/process-mining-ocel.schema.json")
CONFORMANCE_SCHEMA = Path("schemas/json/process-mining-conformance.schema.json")
PROCESS_MINING_DOC = Path("docs/32-process-mining-fixtures.md")
CLAIMS = Path("docs/24-ontology-claims-register.md")
ASSET_INDEX = Path("docs/25-generated-asset-index.md")
ASSET_MANIFEST = Path("examples/generated-asset-manifest.foi-o-publication.json")

XES_NS = {"xes": "http://www.xes-standard.org/"}


def test_process_mining_doc_states_fixture_boundary() -> None:
    text = PROCESS_MINING_DOC.read_text(encoding="utf-8")

    assert "`examples/process-mining-events.fixture.jsonl`" in text
    assert "`examples/process-mining.fixture.xes`" in text
    assert "`examples/process-mining.fixture.ocel.json`" in text
    assert "`examples/process-mining-conformance.fixture.json`" in text
    assert "not a human-reviewed gold standard" in text
    assert "not a live corpus sample" in text
    assert "does not prove process performance" in text

    claims = CLAIMS.read_text(encoding="utf-8")
    assert "Process-mining interchange artefacts exist" in claims
    assert "Do not claim live-corpus conformance" in claims


def test_process_mining_assets_are_registered() -> None:
    index = ASSET_INDEX.read_text(encoding="utf-8")
    manifest = json.loads(ASSET_MANIFEST.read_text(encoding="utf-8"))
    asset_paths = {asset["path"] for asset in manifest["assets"]}

    for path in [EVENTS, XES, OCEL, CONFORMANCE]:
        assert path.exists(), path
        assert f"`{path}`" in index
        assert str(path) in asset_paths


def test_process_mining_xes_fixture_matches_generator() -> None:
    events = load_process_mining_events(EVENTS)
    assert XES.read_text(encoding="utf-8") == build_xes_event_log(events)

    root = ET.parse(XES).getroot()
    assert root.attrib["xes.version"] == "1.0"
    trace = root.find("xes:trace", XES_NS)
    assert trace is not None

    activities = [
        attr.attrib["value"]
        for event in trace.findall("xes:event", XES_NS)
        for attr in event.findall("xes:string", XES_NS)
        if attr.attrib["key"] == "concept:name"
    ]
    assert activities == [
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
    assert activities.index("HumanDecisionCertified") < activities.index("ReleaseMade")


def test_process_mining_ocel_fixture_validates_and_matches_generator(tmp_path: Path) -> None:
    result = validate_json_schema(OCEL, OCEL_SCHEMA)
    assert not result.errors, result.errors

    events = load_process_mining_events(EVENTS)
    expected = build_ocel_event_log(events)
    expected["generated_at"] = "2026-07-03T00:00:00Z"
    fixture = json.loads(OCEL.read_text(encoding="utf-8"))
    assert fixture == expected
    assert fixture["scope"] == "fixture_only"
    assert fixture["claim_boundary"] == "not_live_corpus_validation"
    assert len(fixture["objects"]) == 1
    assert len(fixture["events"]) == 9

    certified = [
        event for event in fixture["events"] if event["activity"] == "HumanDecisionCertified"
    ]
    released = [event for event in fixture["events"] if event["activity"] == "ReleaseMade"]
    assert certified
    assert released
    assert certified[0]["attributes"]["requires_human_certification"] is True
    assert released[0]["attributes"]["requires_human_certification"] is True

    output = tmp_path / "process-mining.fixture.ocel.json"
    summary = write_process_mining_export(events_path=EVENTS, output=output, fmt="ocel")
    assert summary["ok"] is True
    assert json.loads(output.read_text(encoding="utf-8")) == fixture


def test_process_mining_conformance_validates_and_matches_generator(tmp_path: Path) -> None:
    result = validate_json_schema(CONFORMANCE, CONFORMANCE_SCHEMA)
    assert not result.errors, result.errors

    events = load_process_mining_events(EVENTS)
    expected = build_process_mining_conformance(events)
    fixture = json.loads(CONFORMANCE.read_text(encoding="utf-8"))
    assert fixture == expected
    assert fixture["scope"] == "fixture_only"
    assert fixture["claim_boundary"] == "not_live_corpus_validation"
    assert fixture["ok"] is True
    assert fixture["human_certification_before_decision"] is True
    assert fixture["human_certification_before_release"] is True
    assert fixture["candidate_event_types"] == ["DecisionPackDrafted", "SearchPlanDrafted"]
    assert {finding["code"] for finding in fixture["findings"]} >= {
        "fixture_only",
        "candidate_events_preserved",
    }

    output = tmp_path / "process-mining-conformance.fixture.json"
    written = write_process_mining_conformance(EVENTS, output)
    assert written == expected
    assert json.loads(output.read_text(encoding="utf-8")) == fixture

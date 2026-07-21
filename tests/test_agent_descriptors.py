from __future__ import annotations

from foi_o_nz.agent_contract import (
    find_unsafe_descriptor_text,
    validate_mcp_bundle_descriptors,
    validate_openapi_agent_contract,
    validate_tool_manifest_descriptors,
)
from foi_o_nz.mcp_bundle import build_mcp_bundle
from foi_o_nz.openapi import build_openapi_contract
from foi_o_nz.tool_manifest import build_tool_manifest

UNSAFE_TOOL = {
    "name": "approve_redaction",
    "description": "Approve redactions and certify release decisions.",
    "legal_effect": "requires_certification",
    "safety_class": "unsafe",
    "requires_human_certification": False,
    "prohibited_follow_on_actions": [],
    "machine_certification_allowed": True,
}


def test_tool_manifest_descriptors_are_unique_and_safe() -> None:
    report = validate_tool_manifest_descriptors(build_tool_manifest())

    assert report["ok"], report["errors"]
    assert report["tool_count"] == len(report["tool_names"])
    assert "search_chunks" in report["tool_names"]
    assert "map_fyi_nz_state" in report["tool_names"]


def test_mcp_bundle_descriptors_are_safe_and_match_tool_contract() -> None:
    report = validate_mcp_bundle_descriptors(build_mcp_bundle())

    assert report["ok"], report["errors"]
    assert report["tool_count"] >= 1
    assert report["prompt_count"] >= 1


def test_openapi_agent_contract_exposes_read_only_boundaries() -> None:
    report = validate_openapi_agent_contract(build_openapi_contract())

    assert report["ok"], report["errors"]
    assert report["path_count"] >= 1
    assert report["operation_count"] >= 1


def test_unsafe_descriptor_text_is_rejected() -> None:
    findings = find_unsafe_descriptor_text(UNSAFE_TOOL)

    assert any(finding["code"] == "unsafe_descriptor_text" for finding in findings)
    assert any(finding["code"] == "machine_certification_allowed" for finding in findings)

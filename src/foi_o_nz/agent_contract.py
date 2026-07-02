"""Descriptor conformance checks for bounded agent and MCP contracts."""

from __future__ import annotations

from typing import Any

UNSAFE_DESCRIPTOR_PHRASES = (
    "approve redaction",
    "approve redactions",
    "apply redaction",
    "apply redactions",
    "certify release",
    "certify refusal",
    "certify legal",
    "finalise decision",
    "finalize decision",
    "refuse request",
    "release document",
    "release information",
    "approve charge",
    "certify transfer",
    "certify extension",
    "certify complaint",
    "certify review",
)


def find_unsafe_descriptor_text(descriptor: dict[str, Any]) -> list[dict[str, str]]:
    """Return safety findings for one descriptor-like mapping."""
    findings: list[dict[str, str]] = []
    name = str(descriptor.get("name") or "")
    description = str(descriptor.get("description") or "")
    searchable = f"{name} {description}".lower().replace("_", " ")
    for phrase in UNSAFE_DESCRIPTOR_PHRASES:
        if phrase in searchable:
            findings.append(
                {
                    "code": "unsafe_descriptor_text",
                    "message": f"descriptor contains unsafe phrase: {phrase}",
                    "name": name,
                }
            )
    if descriptor.get("machine_certification_allowed") is True:
        findings.append(
            {
                "code": "machine_certification_allowed",
                "message": "machine certification must be disabled",
                "name": name,
            }
        )
    if descriptor.get("legal_effect") not in {None, "none", "preparatory"}:
        findings.append(
            {
                "code": "unsafe_legal_effect",
                "message": "agent descriptors must be none or preparatory only",
                "name": name,
            }
        )
    if descriptor.get("read_only") is False:
        findings.append(
            {
                "code": "not_read_only",
                "message": "agent descriptors must be read-only",
                "name": name,
            }
        )
    return findings


def validate_tool_manifest_descriptors(manifest: dict[str, Any]) -> dict[str, Any]:
    """Validate bounded tool manifest descriptors."""
    errors: list[str] = []
    tools = manifest.get("tools")
    if not isinstance(tools, list):
        return {"ok": False, "tool_count": 0, "tool_names": [], "errors": ["tools: expected list"]}
    names: list[str] = []
    seen: set[str] = set()
    for index, tool in enumerate(tools):
        if not isinstance(tool, dict):
            errors.append(f"tools.{index}: expected mapping")
            continue
        name = str(tool.get("name") or "")
        if not name:
            errors.append(f"tools.{index}.name: required")
        elif name in seen:
            errors.append(f"tools.{index}.name: duplicate {name}")
        seen.add(name)
        names.append(name)
        if tool.get("read_only") is not True:
            errors.append(f"tools.{index}.read_only: must be true")
        if tool.get("machine_certification_allowed") is not False:
            errors.append(f"tools.{index}.machine_certification_allowed: must be false")
        if not isinstance(tool.get("prohibited_follow_on_actions"), list):
            errors.append(f"tools.{index}.prohibited_follow_on_actions: expected list")
        for finding in find_unsafe_descriptor_text(tool):
            errors.append(f"tools.{index}.{finding['code']}: {finding['message']}")
    return {
        "ok": not errors,
        "tool_count": len(tools),
        "tool_names": sorted(names),
        "errors": errors,
    }


def validate_mcp_bundle_descriptors(bundle: dict[str, Any]) -> dict[str, Any]:
    """Validate MCP bundle tools and prompt safety descriptors."""
    tool_report = validate_tool_manifest_descriptors({"tools": bundle.get("tools")})
    errors = list(tool_report["errors"])
    prompts = bundle.get("prompts")
    if not isinstance(prompts, list):
        errors.append("prompts: expected list")
        prompts = []
    for index, prompt in enumerate(prompts):
        if not isinstance(prompt, dict):
            errors.append(f"prompts.{index}: expected mapping")
            continue
        if not prompt.get("safety"):
            errors.append(f"prompts.{index}.safety: required")
        for finding in find_unsafe_descriptor_text(prompt):
            errors.append(f"prompts.{index}.{finding['code']}: {finding['message']}")
    return {
        "ok": not errors,
        "tool_count": tool_report["tool_count"],
        "prompt_count": len(prompts),
        "errors": errors,
    }


def validate_openapi_agent_contract(contract: dict[str, Any]) -> dict[str, Any]:
    """Validate OpenAPI operation metadata for read-only agent boundaries."""
    errors: list[str] = []
    operation_count = 0
    paths = contract.get("paths")
    if not isinstance(paths, dict):
        return {
            "ok": False,
            "path_count": 0,
            "operation_count": 0,
            "errors": ["paths: expected mapping"],
        }
    for path, methods in paths.items():
        if not isinstance(methods, dict):
            errors.append(f"paths.{path}: expected mapping")
            continue
        for method, operation in methods.items():
            if not isinstance(operation, dict):
                errors.append(f"paths.{path}.{method}: expected mapping")
                continue
            operation_count += 1
            if operation.get("x-read-only") is not True:
                errors.append(f"paths.{path}.{method}.x-read-only: must be true")
            if operation.get("x-machine-certification-allowed") is not False:
                errors.append(
                    f"paths.{path}.{method}.x-machine-certification-allowed: must be false"
                )
            if operation.get("x-legal-effect") not in {"none", "preparatory"}:
                errors.append(f"paths.{path}.{method}.x-legal-effect: unsupported value")
            descriptor = {
                "name": f"{method} {path}",
                "description": operation.get("summary"),
                "legal_effect": operation.get("x-legal-effect"),
                "read_only": operation.get("x-read-only"),
                "machine_certification_allowed": operation.get("x-machine-certification-allowed"),
            }
            for finding in find_unsafe_descriptor_text(descriptor):
                errors.append(f"paths.{path}.{method}.{finding['code']}: {finding['message']}")
    return {
        "ok": not errors,
        "path_count": len(paths),
        "operation_count": operation_count,
        "errors": errors,
    }

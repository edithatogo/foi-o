"""Validate paired workflow Markdown/Mermaid and BPMN identifiers."""

from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import yaml


def validate(root: Path = Path("workflows")) -> list[str]:
    errors: list[str] = []
    for markdown in sorted(root.rglob("workflow.md")):
        bpmn = markdown.with_name("workflow.bpmn")
        workflow_yaml = markdown.with_name("workflow.yaml")
        if not bpmn.exists():
            errors.append(f"missing BPMN pair: {bpmn}")
            continue
        if not workflow_yaml.exists():
            errors.append(f"missing workflow contract: {workflow_yaml}")
            continue
        try:
            ET.parse(bpmn)  # noqa: S314 - workflow files are repository-controlled XML
        except ET.ParseError as exc:
            errors.append(f"invalid BPMN {bpmn}: {exc}")
        markdown_text = markdown.read_text(encoding="utf-8")
        mermaid_ids = set(re.findall(r"\b([A-Z][A-Za-z0-9_]*)\b", markdown_text))
        bpmn_ids = set(re.findall(r'id="([^"]+)"', bpmn.read_text(encoding="utf-8")))
        contract = yaml.safe_load(workflow_yaml.read_text(encoding="utf-8"))
        step_ids = {str(step["id"]) for step in contract.get("steps", [])}
        if not step_ids:
            errors.append(f"workflow has no stable steps: {workflow_yaml}")
        if not step_ids <= mermaid_ids:
            errors.append(f"workflow steps missing from Mermaid: {workflow_yaml}")
        if not step_ids <= bpmn_ids:
            errors.append(f"workflow steps missing from BPMN: {workflow_yaml}")
        if not mermaid_ids.intersection({"StartEvent", "Task", "Gateway", "EndEvent"}):
            # Mermaid node IDs are free-form; require a diagram rather than a brittle naming match.
            if "```mermaid" not in markdown_text:
                errors.append(f"missing Mermaid diagram: {markdown}")
        if not bpmn_ids:
            errors.append(f"missing BPMN identifiers: {bpmn}")
    return errors


if __name__ == "__main__":
    failures = validate()
    if failures:
        print("\n".join(failures))
        sys.exit(1)
    print("workflow validation: PASS")

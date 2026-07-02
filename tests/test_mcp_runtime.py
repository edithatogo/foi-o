from __future__ import annotations

import inspect
import json
from pathlib import Path
from typing import Any

import pytest

from foi_o_nz import mcp_server
from foi_o_nz.agent_contract import find_unsafe_descriptor_text


class FakeFastMCP:
    def __init__(self, name: str) -> None:
        self.name = name
        self.tools: dict[str, dict[str, Any]] = {}
        self.resources: dict[str, dict[str, Any]] = {}
        self.prompts: dict[str, dict[str, Any]] = {}

    def tool(self, **metadata: Any) -> Any:
        def decorator(func: Any) -> Any:
            self.tools[func.__name__] = {"func": func, "metadata": metadata}
            return func

        return decorator

    def resource(self, uri: str, **metadata: Any) -> Any:
        def decorator(func: Any) -> Any:
            self.resources[uri] = {"func": func, "metadata": metadata}
            return func

        return decorator

    def prompt(self, **metadata: Any) -> Any:
        def decorator(func: Any) -> Any:
            self.prompts[func.__name__] = {"func": func, "metadata": metadata}
            return func

        return decorator


def _events_jsonl(tmp_path: Path) -> Path:
    path = tmp_path / "events.jsonl"
    path.write_text(
        json.dumps(
            {
                "event_id": "foio-nz:event:mcp-ok",
                "event_type": "RequestObserved",
                "assertion_status": "observed",
                "machine_generated": True,
                "generator": {"system": "foi-o-nz-test"},
                "requires_human_certification": False,
                "evidence": [{"evidence_id": "e1"}],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def test_mcp_runtime_status_fails_closed_without_fastmcp(monkeypatch: pytest.MonkeyPatch) -> None:
    def missing_fastmcp() -> type[Any]:
        raise ModuleNotFoundError("fastmcp")

    monkeypatch.setattr(mcp_server, "_load_fastmcp", missing_fastmcp)

    status = mcp_server.mcp_runtime_status()

    assert status["ok"] is False
    assert status["mode"] == "degraded"
    assert status["read_only"] is True
    assert "install foi-o-nz[mcp]" in status["message"]
    assert "fail-closed" in status["message"]
    with pytest.raises(RuntimeError, match="fail-closed"):
        mcp_server.create_server()


def test_mcp_server_registers_read_only_safe_tools_and_prompt() -> None:
    server = mcp_server.create_server(fastmcp_cls=FakeFastMCP)

    assert {"map_state", "validate_json", "validate_jsonl", "quality_gate"} <= set(server.tools)
    assert "foio://schema/{schema_name}" in server.resources
    assert "state_mapping_context" in server.prompts

    for name, record in server.tools.items():
        descriptor = {"name": name, **record["metadata"]}
        assert descriptor["read_only"] is True
        assert descriptor["machine_certification_allowed"] is False
        assert descriptor["legal_effect"] == "none"
        assert not find_unsafe_descriptor_text(descriptor)

    prompt_text = server.prompts["state_mapping_context"]["func"]("waiting_response")
    assert "cannot certify" in prompt_text.lower()


def test_mcp_runtime_tools_are_fixture_backed_and_do_not_write(tmp_path: Path) -> None:
    server = mcp_server.create_server(fixture_root=tmp_path, fastmcp_cls=FakeFastMCP)
    events_path = _events_jsonl(tmp_path)
    instance_path = tmp_path / "instance.json"
    schema_path = tmp_path / "instance.schema.json"
    instance_path.write_text(json.dumps({"ok": True}), encoding="utf-8")
    schema_path.write_text(
        json.dumps(
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "additionalProperties": False,
                "required": ["ok"],
                "properties": {"ok": {"type": "boolean"}},
            }
        ),
        encoding="utf-8",
    )

    mapped = server.tools["map_state"]["func"]("waiting_response")
    assert mapped["normalised_state"] == "Received"
    assert mapped["read_only"] is True

    validated = server.tools["validate_json"]["func"](
        "instance.json",
        "instance.schema.json",
    )
    assert validated == {"ok": True, "errors": [], "legal_effect": "none", "read_only": True}

    quality_gate = server.tools["quality_gate"]["func"]
    assert "output_path" not in inspect.signature(quality_gate).parameters
    report = quality_gate(str(events_path))

    assert report["ok"] is True
    assert report["event_count"] == 1
    assert report["legal_effect"] == "none"
    assert report["read_only"] is True
    assert sorted(path.name for path in tmp_path.iterdir()) == [
        "events.jsonl",
        "instance.json",
        "instance.schema.json",
    ]


def test_mcp_schema_resource_is_committed_schema_only() -> None:
    server = mcp_server.create_server(fastmcp_cls=FakeFastMCP)
    schema_resource = server.resources["foio://schema/{schema_name}"]["func"]

    schema_text = schema_resource("core-event.schema.json")

    assert "FOI-O NZ Core Process Event" in schema_text
    with pytest.raises(ValueError, match="committed JSON Schema"):
        schema_resource("../pyproject.toml")

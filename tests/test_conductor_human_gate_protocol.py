"""Regression checks for the sole-maintainer human-gate protocol binding."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
PROTOCOL = "conductor/sole-maintainer-agent-panel-gate-protocol.md"
HUMAN_GATE_KINDS = {"human", "external_action"}


def _requires_protocol(metadata: dict[str, object]) -> bool:
    if metadata.get("human_gates"):
        return True
    return any(
        isinstance(gate, dict) and gate.get("kind") in HUMAN_GATE_KINDS
        for gate in metadata.get("gates", [])
    )


def test_all_human_or_external_gate_tracks_bind_the_sole_maintainer_protocol() -> None:
    metadata_paths = sorted((ROOT / "conductor" / "tracks").glob("*/metadata.json"))
    governed = []
    for path in metadata_paths:
        metadata = json.loads(path.read_text(encoding="utf-8"))
        if _requires_protocol(metadata):
            governed.append(path)
            assert metadata.get("human_gate_protocol") == PROTOCOL, path
    assert governed


def test_no_agent_review_can_satisfy_a_human_gate_by_itself() -> None:
    text = (ROOT / PROTOCOL).read_text(encoding="utf-8")
    assert "cannot approve" in text
    assert "sole maintainer explicitly approves" in text
    assert "If a panel cannot be formed, a candidate remains pending" in text


def test_protocol_reuses_unchanged_exact_authorizations() -> None:
    text = (ROOT / PROTOCOL).read_text(encoding="utf-8")
    normalized = " ".join(text.split())
    assert "Authorization reuse and decision hygiene" in text
    assert "Reuse an existing explicit authorization" in text
    assert "do not ask the maintainer to restate an unchanged authorization" in normalized

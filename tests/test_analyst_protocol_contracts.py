import json
from pathlib import Path

from foi_o_nz.validation import validate_json_schema

ROOT = Path(__file__).parents[1]
SCHEMAS = ROOT / "schemas/json"


def _write(tmp_path: Path, name: str, payload: dict[str, object]) -> Path:
    path = tmp_path / name
    path.write_text(json.dumps(payload))
    return path


def _agent(actor_id: str, role: str) -> dict[str, object]:
    return {
        "actor_id": actor_id,
        "actor_class": "automated_agent",
        "role": role,
        "runtime": {
            "provider": "codex",
            "model": "recorded-by-runner",
            "prompt_sha256": "a" * 64,
            "session_id": actor_id.removeprefix("agent:"),
        },
    }


def test_agent_analyst_execution_is_role_based_and_bounded(tmp_path: Path) -> None:
    payload = {
        "schema_version": "foi-o.analyst-execution-authorization.v0.1.0",
        "authorization_id": "local-agent-analyst-run",
        "status": "approved_local_agent_analysis",
        "execution_allowed": True,
        "local_only": True,
        "analysts": [_agent("agent:analyst-a", "analyst"), _agent("agent:analyst-b", "analyst")],
        "reconciler": _agent("agent:reconciler", "reconciler"),
        "approved_by": "human:edithatogo",
        "approved_at": "2026-07-17T00:00:00Z",
        "empirical_evidence": False,
        "human_reviewed": False,
        "gold_eligible": False,
        "release_qualifying": False,
        "publication_eligible": False,
        "prohibited_actions": [
            "redistribution",
            "publication",
            "training",
            "fine_tuning",
            "release",
            "dataset_publication",
            "gold_promotion",
        ],
    }
    path = _write(tmp_path, "authorization.json", payload)
    schema = SCHEMAS / "analyst-execution-authorization.schema.json"
    assert not validate_json_schema(path, schema).errors

    payload["reconciler"] = _agent("agent:analyst-a", "reconciler")
    path.write_text(json.dumps(payload))
    assert validate_json_schema(path, schema).errors


def test_locked_agent_analysis_requires_independence_and_nonpromotion(tmp_path: Path) -> None:
    payload = {
        "schema_version": "foi-o.locked-analyst-record.v0.1.0",
        "record_id": "analysis:unit-1:a",
        "status": "locked_agent_analysis",
        "analyst": _agent("agent:analyst-a", "analyst"),
        "unit_sha256": "b" * 64,
        "codebook_revision": "c" * 40,
        "label": "unknown",
        "span": None,
        "uncertainty": 0.25,
        "abstention": False,
        "abstention_reason": None,
        "notes": "Fixture-pipeline analysis only.",
        "independence": {
            "blinded_to_peer_outputs": True,
            "blinded_to_candidate": True,
            "context_sha256": "d" * 64,
        },
        "created_at": "2026-07-17T00:01:00Z",
        "locked_at": "2026-07-17T00:02:00Z",
        "empirical_evidence": False,
        "human_reviewed": False,
        "gold_eligible": False,
    }
    path = _write(tmp_path, "analysis.json", payload)
    schema = SCHEMAS / "locked-analyst-record.schema.json"
    assert not validate_json_schema(path, schema).errors

    payload["empirical_evidence"] = True
    path.write_text(json.dumps(payload))
    assert validate_json_schema(path, schema).errors


def test_agent_reconciliation_preserves_two_locked_inputs(tmp_path: Path) -> None:
    payload = {
        "schema_version": "foi-o.analyst-reconciliation-record.v0.1.0",
        "record_id": "reconciliation:unit-1",
        "status": "locked_agent_reconciliation",
        "unit_sha256": "b" * 64,
        "analysis_refs": [
            {
                "analyst_id": "agent:analyst-a",
                "sha256": "d" * 64,
                "locked_at": "2026-07-17T00:02:00Z",
            },
            {
                "analyst_id": "agent:analyst-b",
                "sha256": "e" * 64,
                "locked_at": "2026-07-17T00:03:00Z",
            },
        ],
        "reconciler": _agent("agent:reconciler", "reconciler"),
        "outcome": "resolved",
        "reconciled_candidate_label": "unknown",
        "reconciled_candidate_span": None,
        "rationale": "The two locked analyses support this candidate outcome.",
        "created_at": "2026-07-17T00:04:00Z",
        "locked_at": "2026-07-17T00:05:00Z",
        "empirical_evidence": False,
        "human_reviewed": False,
        "gold_eligible": False,
    }
    path = _write(tmp_path, "reconciliation.json", payload)
    schema = SCHEMAS / "analyst-reconciliation-record.schema.json"
    assert not validate_json_schema(path, schema).errors

    payload["analysis_refs"] = [payload["analysis_refs"][0]]  # type: ignore[index]
    path.write_text(json.dumps(payload))
    assert validate_json_schema(path, schema).errors


def test_active_protocol_uses_analyst_roles_and_agent_provenance() -> None:
    protocol = (ROOT / "docs/42-v2-analyst-execution-protocol.md").read_text()
    assert "two independent analysts" in protocol
    assert "automated agents may serve as analysts" in protocol
    assert "distinct reconciler" in protocol
    assert "not human-reviewed" in protocol
    assert "docs/41-v2-sampling-and-annotation-protocol.md" in protocol

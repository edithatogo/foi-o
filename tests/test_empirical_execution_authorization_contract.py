import json
from pathlib import Path
from typing import cast

from foi_o_nz.validation import validate_json_schema

ROOT = Path(__file__).parents[1]
SCHEMA = ROOT / "schemas/json/empirical-execution-authorization.schema.json"


def _authorization() -> dict[str, object]:
    artifact = {"path": "fixture-only", "sha256": "a" * 64, "approved": False}
    return {
        "schema_version": "foi-o.empirical-execution-authorization.v0.1.0",
        "authorization_id": "fixture-only",
        "status": "pending_human_authorization",
        "execution_allowed": False,
        "protocol": dict(artifact),
        "source_population": dict(artifact),
        "codebook": dict(artifact),
        "codebook_revision": "fixture-codebook",
        "sampling_configuration": dict(artifact),
        "annotator_ids": [],
        "adjudicator_id": None,
        "approved_by": None,
        "approved_at": None,
        "agents_may_fill_human_roles": False,
        "limitations": ["Schema fixture only; no execution is authorized."],
    }


def test_pending_authorization_is_fail_closed(tmp_path: Path) -> None:
    path = tmp_path / "authorization.json"
    path.write_text(json.dumps(_authorization()))
    assert not validate_json_schema(path, SCHEMA).errors


def test_approved_authorization_requires_human_roles_and_all_approvals(tmp_path: Path) -> None:
    payload = _authorization()
    payload.update(
        status="approved_human_authorization",
        execution_allowed=True,
        annotator_ids=["human:synthetic-a", "human:synthetic-b"],
        adjudicator_id="agent:synthetic-adjudicator",
        approved_by="human:synthetic-approver",
        approved_at="2026-07-17T00:00:00Z",
    )
    for key in ("protocol", "source_population", "codebook", "sampling_configuration"):
        cast(dict[str, object], payload[key])["approved"] = True
    path = tmp_path / "authorization.json"
    path.write_text(json.dumps(payload))
    assert validate_json_schema(path, SCHEMA).errors


def test_schema_valid_approval_remains_contract_only(tmp_path: Path) -> None:
    payload = _authorization()
    payload.update(
        status="approved_human_authorization",
        execution_allowed=True,
        annotator_ids=["human:synthetic-a", "human:synthetic-b"],
        adjudicator_id="human:synthetic-adjudicator",
        approved_by="human:synthetic-approver",
        approved_at="2026-07-17T00:00:00Z",
    )
    for key in ("protocol", "source_population", "codebook", "sampling_configuration"):
        cast(dict[str, object], payload[key])["approved"] = True
    path = tmp_path / "authorization.json"
    path.write_text(json.dumps(payload))
    assert not validate_json_schema(path, SCHEMA).errors


def test_agent_analysts_require_exact_runtime_provenance(tmp_path: Path) -> None:
    payload = _authorization()
    payload.update(
        schema_version="foi-o.empirical-execution-authorization.v0.2.0",
        status="approved_analyst_authorization",
        execution_allowed=True,
        annotator_ids=["agent:analyst-a", "agent:analyst-b"],
        adjudicator_id="agent:reconciler",
        approved_by="human:edithatogo",
        approved_at="2026-07-19T00:00:00Z",
        agents_may_fill_human_roles=True,
        actor_provenance=[
            {
                "actor_id": "agent:analyst-a",
                "actor_class": "automated_agent",
                "role": "analyst",
                "runtime": "runtime-a",
            },
            {
                "actor_id": "agent:analyst-b",
                "actor_class": "automated_agent",
                "role": "analyst",
                "runtime": "runtime-b",
            },
            {
                "actor_id": "agent:reconciler",
                "actor_class": "automated_agent",
                "role": "reconciler",
                "runtime": "runtime-c",
            },
        ],
    )
    for key in ("protocol", "source_population", "codebook", "sampling_configuration"):
        cast(dict[str, object], payload[key])["approved"] = True
    path = tmp_path / "authorization.json"
    path.write_text(json.dumps(payload))
    assert not validate_json_schema(path, SCHEMA).errors

    cast(list[dict[str, object]], payload["actor_provenance"]).pop()
    path.write_text(json.dumps(payload))
    assert validate_json_schema(path, SCHEMA).errors

import copy
import json
from hashlib import sha256
from pathlib import Path

import pytest

from foi_o_nz.bounded_pilot_attachment_derivation import PROHIBITED_ACTIONS
from foi_o_nz.validation import validate_json_schema

ROOT = Path(__file__).parents[1]
HUMAN_SCHEMA = ROOT / "schemas/json/bounded-pilot-attachment-diagnostic-human-approval.schema.json"
AUTHORIZATION_SCHEMA = (
    ROOT / "schemas/json/bounded-pilot-attachment-diagnostic-execution-authorization.schema.json"
)
REQUEST_PATH = "examples/v2/bounded-pilot-attachment-stderr-diagnostic-request.pending.json"
REQUEST_SHA256 = "b8c16f51f86b4d1a462edf495dc309f4f6e1dd09c47fb55010a5d08955c40d7f"


def _human_approval() -> dict[str, object]:
    statement = "Exact synthetic diagnostic approval used only for schema validation."
    return {
        "schema_version": "foi-o.bounded-pilot-attachment-diagnostic-human-approval.v0.1.0",
        "approved_by": "human:edithatogo",
        "approved_on": "2026-07-19",
        "approval_statement": statement,
        "approval_statement_sha256": sha256(statement.encode()).hexdigest(),
        "approved_request": {"path": REQUEST_PATH, "sha256": REQUEST_SHA256},
        "bound_scope": {
            "source_root": "/private/tmp/fyi-attachment-snapshot-11872-approved",
            "output_directory": "/private/tmp/foio-bounded-pilot-11872-derived",
            "quarantine_parent": "/private/tmp",
            "diagnostic_only": True,
            "derived_content_retention_allowed": False,
        },
        "prohibited_actions": PROHIBITED_ACTIONS,
    }


def _authorization() -> dict[str, object]:
    pin = {"path": REQUEST_PATH, "sha256": REQUEST_SHA256}
    return {
        "schema_version": "foi-o.bounded-pilot-attachment-diagnostic-execution-authorization.v0.1.0",
        "authorization_id": "bounded-pilot-11872-attachment-diagnostic-approved",
        "status": "approved_exact_local_diagnostic",
        "diagnostic_request": pin,
        "human_approval": {
            "path": "examples/v2/bounded-pilot-attachment-diagnostic-human-approval.approved.json",
            "sha256": "1" * 64,
        },
        "wrapper": {
            "path": "src/foi_o_nz/bounded_pilot_attachment_derivation.py",
            "sha256": "6d18c3c7a9c16c327fc934a516666d4dfc7d86a2e057824bfbd3eea79a6f7659",
            "repository_commit": "d11a4b2ca3b3bfb518187e36ae18696dcd77c95f",
        },
        "method": {
            "path": "examples/v2/bounded-pilot-attachment-text-method.pending.json",
            "sha256": "99918773c74eed9a923972eb5a498e8a4166c8958ac53b04c4358f70ef1d770a",
        },
        "method_approval": {
            "path": "examples/v2/bounded-pilot-attachment-text-method-approval.approved.json",
            "sha256": "b036b475541a2334019b771fce789b7a7d97a4c30282bbada68a88a68ad12d51",
        },
        "source_root": "/private/tmp/fyi-attachment-snapshot-11872-approved",
        "output_directory": "/private/tmp/foio-bounded-pilot-11872-derived",
        "quarantine_parent": "/private/tmp",
        "diagnostic_execution_allowed": True,
        "pdf_processing_allowed": True,
        "transient_derived_content_allowed": True,
        "derived_content_retention_allowed": False,
        "local_only": True,
        "context_presentation_allowed": False,
        "analyst_execution_allowed": False,
        "reconciliation_allowed": False,
        "empirical_evidence": False,
        "human_reviewed": False,
        "gold_eligible": False,
    }


def _validate(instance: dict[str, object], schema: Path, tmp_path: Path) -> tuple[str, ...]:
    path = tmp_path / "instance.json"
    path.write_text(json.dumps(instance), encoding="utf-8")
    return validate_json_schema(path, schema).errors


def test_diagnostic_human_approval_schema_accepts_exact_contract(tmp_path: Path) -> None:
    assert not _validate(_human_approval(), HUMAN_SCHEMA, tmp_path)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("approved_request", {"path": REQUEST_PATH, "sha256": "0" * 64}),
        ("bound_scope", {}),
        ("prohibited_actions", PROHIBITED_ACTIONS[:-1]),
    ],
)
def test_diagnostic_human_approval_schema_rejects_scope_drift(
    field: str, value: object, tmp_path: Path
) -> None:
    candidate = _human_approval()
    candidate[field] = value
    assert _validate(candidate, HUMAN_SCHEMA, tmp_path)


def test_diagnostic_authorization_schema_accepts_exact_contract(tmp_path: Path) -> None:
    assert not _validate(_authorization(), AUTHORIZATION_SCHEMA, tmp_path)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("diagnostic_execution_allowed", False),
        ("derived_content_retention_allowed", True),
        ("context_presentation_allowed", True),
        ("quarantine_parent", "/tmp/not-the-bound-parent"),
    ],
)
def test_diagnostic_authorization_schema_rejects_scope_drift(
    field: str, value: object, tmp_path: Path
) -> None:
    candidate = copy.deepcopy(_authorization())
    candidate[field] = value
    assert _validate(candidate, AUTHORIZATION_SCHEMA, tmp_path)

"""Pending-only authorization records and mechanically rendered packets."""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from typing import Any

from .build import seal_record
from .canonical import content_sha256


def build_pending_authorization(
    *,
    authorization_id: str,
    object_scope: str,
    population_scope: str,
    population_id: str,
    population_sha256: str,
    transformation_id: str,
    transformation_version: str,
    transformation_contract_sha256: str,
    run_id: str,
    run_occurrence_sha256: str,
    allowed_capabilities: Sequence[str],
    denied_capabilities: Sequence[str],
    approved_input_sha256: Sequence[str],
    one_use: bool = True,
    predecessor_authorization_sha256: str | None = None,
) -> dict[str, Any]:
    """Create a proposal that cannot represent its own human authorization."""
    denied = sorted(set(denied_capabilities))
    allowed = sorted(set(allowed_capabilities))
    if not denied:
        raise ValueError("a pending authorization must state at least one denied capability")
    if set(allowed) & set(denied):
        raise ValueError("allowed and denied capabilities must not overlap")
    approved_inputs = sorted(set(approved_input_sha256))
    if not approved_inputs:
        raise ValueError("a pending authorization must pin at least one input digest")

    allowed_text = ", ".join(allowed) if allowed else "none"
    denied_text = ", ".join(denied)
    input_text = ", ".join(approved_inputs)
    statement = (
        f"I authorize {object_scope}, limited to {population_scope}, under transformation "
        f"{transformation_id} version {transformation_version}, contract SHA-256 "
        f"{transformation_contract_sha256}, population {population_id} SHA-256 "
        f"{population_sha256}, run {run_id} occurrence SHA-256 {run_occurrence_sha256}, "
        f"and exact input SHA-256 digests: {input_text}. Allowed capabilities: {allowed_text}. "
        f"Denied capabilities: {denied_text}."
    )
    record: dict[str, Any] = {
        "schema_version": "foio.authorization-record.v1.0.0",
        "authorization_id": authorization_id,
        "status": "pending_human_decision",
        "object_scope": object_scope,
        "population_scope": population_scope,
        "population_id": population_id,
        "population_sha256": population_sha256,
        "transformation_id": transformation_id,
        "transformation_version": transformation_version,
        "transformation_contract_sha256": transformation_contract_sha256,
        "run_id": run_id,
        "run_occurrence_sha256": run_occurrence_sha256,
        "approved_input_sha256": approved_inputs,
        "allowed_capabilities": allowed,
        "denied_capabilities": denied,
        "approval_statement": statement,
        "approval_statement_sha256": hashlib.sha256(statement.encode("utf-8")).hexdigest(),
        "one_use": one_use,
        "predecessor_authorization_sha256": predecessor_authorization_sha256,
    }
    return seal_record(record, "authorization_sha256")


def render_pending_approval_packet(authorization: dict[str, Any]) -> str:
    """Render a proposal; approved or rejected records are deliberately refused."""
    if authorization.get("status") != "pending_human_decision":
        raise ValueError("approval packet renderer accepts pending_human_decision records only")
    if authorization.get("authorization_sha256") != content_sha256(
        authorization,
        "authorization_sha256",
    ):
        raise ValueError("approval packet authorization self-pin is invalid")
    denied = authorization.get("denied_capabilities")
    if not isinstance(denied, list) or not denied:
        raise ValueError("approval packet requires an explicit non-empty denial set")
    statement = authorization.get("approval_statement")
    if not isinstance(statement, str) or authorization.get("approval_statement_sha256") != (
        hashlib.sha256(statement.encode("utf-8")).hexdigest()
    ):
        raise ValueError("approval packet statement hash is invalid")

    allowed_lines = "\n".join(
        f"- `{capability}`" for capability in authorization["allowed_capabilities"]
    )
    denied_lines = "\n".join(f"- `{capability}`" for capability in denied)
    allowed_lines = allowed_lines or "- None"
    return (
        "# Pending provenance authorization\n\n"
        "Status: `pending_human_decision`\n\n"
        "This generated packet is a proposal only and cannot authorize itself.\n\n"
        f"Object: {authorization['object_scope']}\n\n"
        f"Population: {authorization['population_scope']}\n\n"
        f"Transformation contract SHA-256: "
        f"`{authorization['transformation_contract_sha256']}`\n\n"
        "## Allowed capabilities\n\n"
        f"{allowed_lines}\n\n"
        "## Denied capabilities\n\n"
        f"{denied_lines}\n\n"
        "## Exact proposed statement\n\n"
        f"> {authorization['approval_statement']}\n\n"
        f"Statement SHA-256: `{authorization['approval_statement_sha256']}`\n\n"
        f"Authorization-record SHA-256: `{authorization['authorization_sha256']}`\n"
    )

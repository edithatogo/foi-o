"""Fail-closed construction of the bounded-pilot attachment execution request.

This module intentionally contains no extraction executor. The approved scope
permits request construction, but PDF processing requires another exact gate.
"""

from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path
from typing import Any


def file_sha256(path: Path) -> str:
    """Return the SHA-256 digest of exact file bytes."""
    return sha256(path.read_bytes()).hexdigest()


def load_object(path: Path) -> dict[str, Any]:
    """Load a JSON object or fail closed."""
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def build_attachment_derivation_execution_request(
    *, repository_root: Path, wrapper_path: str, wrapper_sha256: str
) -> dict[str, Any]:
    """Build an inert request from the exact approved method chain."""
    method_path = repository_root / "examples/v2/bounded-pilot-attachment-text-method.pending.json"
    approval_path = (
        repository_root / "examples/v2/bounded-pilot-attachment-text-method-approval.approved.json"
    )
    method = load_object(method_path)
    approval = load_object(approval_path)
    if file_sha256(method_path) != approval["approved_candidate"]["sha256"]:
        raise ValueError("approved method candidate digest mismatch")
    if not approval["method_approved"] or approval["pdf_processing_allowed"]:
        raise ValueError("method approval scope is not fail-closed")
    if not wrapper_path.startswith("src/foi_o_nz/") or not wrapper_path.endswith(".py"):
        raise ValueError("wrapper path is outside the package")
    if len(wrapper_sha256) != 64:
        raise ValueError("wrapper digest is invalid")
    return {
        "schema_version": "foi-o.bounded-pilot-attachment-derivation-execution-request.v0.1.0",
        "request_id": "bounded-pilot-11872-attachment-derivation-execution",
        "status": "pending_exact_execution_authorization",
        "method": {
            "path": str(method_path.relative_to(repository_root)),
            "sha256": file_sha256(method_path),
        },
        "method_approval": {
            "path": str(approval_path.relative_to(repository_root)),
            "sha256": file_sha256(approval_path),
        },
        "wrapper": {"path": wrapper_path, "sha256": wrapper_sha256},
        "sources": method["sources"],
        "method_tool": method["method_tool"],
        "runtime_observation": method["runtime_observation"],
        "environment": method["environment"],
        "argv_template": method["argv_template"],
        "output_contract": method["output_contract"],
        "failure_contract": method["failure_contract"],
        "requested_scope": "two_pass_local_pdf_text_derivation_for_exact_three_request_11872_attachments_only",
        "authorization_present": False,
        "pdf_processing_allowed": False,
        "derived_content_creation_allowed": False,
        "context_presentation_allowed": False,
        "analyst_execution_allowed": False,
        "reconciliation_allowed": False,
        "empirical_evidence": False,
        "human_reviewed": False,
        "gold_eligible": False,
    }

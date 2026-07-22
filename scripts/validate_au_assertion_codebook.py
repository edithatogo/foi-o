"""Validate the exact AU-CTH assertion-codebook contract."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

REVISION = re.compile(r"^[0-9a-f]{40}$")
LABELS = {"observed", "inferred", "candidate", "unknown"}
ABSTENTION_REASONS = {"missing_evidence", "insufficient_evidence", "out_of_scope", "other"}


def validate_codebook(codebook: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if codebook.get("schema_version") != "foi-o.au-cth-assertion-codebook.v0.2.0":
        errors.append("unsupported schema_version")
    if codebook.get("status") not in {"pending_human_approval", "approved"}:
        errors.append("invalid status")
    if codebook.get("codebook_id") != "foio-au-pilot-assertion-v0.2.0":
        errors.append("invalid codebook_id")
    revision = codebook.get("revision")
    if not isinstance(revision, str) or not REVISION.fullmatch(revision):
        errors.append("revision must be a real 40-character Git revision")
    assertion = codebook.get("assertion")
    if (
        not isinstance(assertion, dict)
        or not assertion.get("statement")
        or not assertion.get("evidence_window")
    ):
        errors.append("assertion statement and evidence_window are required")
    labels = codebook.get("labels")
    if (
        not isinstance(labels, list)
        or {label.get("id") for label in labels if isinstance(label, dict)} != LABELS
    ):
        errors.append("labels must contain exactly observed, inferred, candidate, unknown")
    elif any(not label.get("positive_rule") or not label.get("negative_rule") for label in labels):
        errors.append("every label requires positive_rule and negative_rule")
    span = codebook.get("span_policy")
    if not isinstance(span, dict) or span.get("coordinate_system") != "utf8_character_half_open":
        errors.append("span coordinate system must be utf8_character_half_open")
    if (
        not isinstance(span, dict)
        or not isinstance(span.get("maximum_span_characters"), int)
        or span["maximum_span_characters"] <= 0
    ):
        errors.append("maximum_span_characters must be positive")
    abstention = codebook.get("abstention")
    if not isinstance(abstention, dict) or set(abstention.get("reasons", [])) != ABSTENTION_REASONS:
        errors.append("abstention reasons are incomplete")
    serialization = codebook.get("serialization")
    if not isinstance(serialization, dict) or serialization.get("one_primary_label") is not True:
        errors.append("serialization must require one primary label")
    thresholds = codebook.get("registered_thresholds")
    if (
        not isinstance(thresholds, dict)
        or thresholds.get("raw_agreement_minimum") != 0.8
        or thresholds.get("cohen_kappa_minimum") != 0.6
    ):
        errors.append("registered reliability thresholds must remain 0.8 and 0.6")
    if codebook.get("status") == "approved" and codebook.get("approval_present") is not True:
        errors.append("approved codebook requires approval_present=true")
    if codebook.get("execution_allowed") is not False:
        errors.append("codebook cannot authorize execution")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("codebook", type=Path)
    args = parser.parse_args()
    try:
        value = json.loads(args.codebook.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        print(f"ERROR: codebook is not readable JSON: {error}")
        return 1
    errors = validate_codebook(value)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("AU assertion codebook: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

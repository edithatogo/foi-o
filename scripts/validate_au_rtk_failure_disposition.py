"""Validate the explicit nine-record AU RightToKnow 404 disposition ledger."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

EXPECTED_SELECTION_SHA256 = (
    "a1c2308ecc81de3754f37b3c26f7ba7fc232ff5bac930b86b36fb10463178c51"
)
EXPECTED_FAILURES = {
    "acting_treasurer_scott_morrisons",
    "inquiry_about_contact_tracing_ap",
    "inquiry_about_contact_tracing_ap_2",
    "inquiry_about_contact_tracing_ap_5",
    "inquiry_about_contact_tracing_ap_7",
    "masschallenge_contracts",
    "nuclear_fuel_cycle_activities_in",
    "number_of_approved_citizens_wait",
    "which_agencies_are_rbas_transact",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(selection_path: Path, ledger_path: Path) -> dict[str, object]:
    if sha256(selection_path) != EXPECTED_SELECTION_SHA256:
        raise ValueError("selection SHA-256 does not match the approved population")
    selection = json.loads(selection_path.read_text(encoding="utf-8"))
    selected = {str(item["canonical_slug"]): item for item in selection["records"]}
    if len(selected) != 2082 or selection.get("record_count") != 2082:
        raise ValueError("selection does not contain exactly 2,082 canonical records")

    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    if ledger.get("schema") != "foio.au-rtk-replay-failure-ledger.v1":
        raise ValueError("failure ledger schema is invalid")
    if ledger.get("selection_sha256") != EXPECTED_SELECTION_SHA256:
        raise ValueError("failure ledger selection pin is invalid")
    failures = ledger.get("failures")
    if not isinstance(failures, list) or ledger.get("failure_count") != 9:
        raise ValueError("failure ledger must contain exactly nine failures")
    actual = {str(item.get("canonical_slug")) for item in failures}
    if actual != EXPECTED_FAILURES:
        raise ValueError("failure ledger membership does not match the approved nine")
    for item in failures:
        slug = str(item["canonical_slug"])
        if slug not in selected:
            raise ValueError(f"failure is outside approved selection: {slug}")
        expected = selected[slug]
        for field in ("source_url", "archive_timestamp", "archive_digest", "media_kind"):
            if item.get(field) != expected.get(field):
                raise ValueError(f"failure provenance mismatch for {slug}: {field}")
        if not str(item.get("diagnostic", "")).startswith("Client error '404"):
            raise ValueError(f"failure is not an explicit HTTP 404: {slug}")
    return {
        "ok": True,
        "selection_count": len(selected),
        "failure_count": len(failures),
        "successful_positions": len(selected) - len(failures),
        "ledger_sha256": sha256(ledger_path),
        "finalization": "not authorized by this validator",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selection", type=Path, required=True)
    parser.add_argument("--ledger", type=Path, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(validate(args.selection, args.ledger), sort_keys=True))
    except (OSError, ValueError, json.JSONDecodeError, KeyError, TypeError) as error:
        print(f"ERROR: {error}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

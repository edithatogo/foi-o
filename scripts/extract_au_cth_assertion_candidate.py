"""Candidate-only AU-CTH assertion extractor with explicit evidence spans."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

CODEBOOK_ID = "foio-au-pilot-assertion-v0.2.0"
AGENCY_CROSSWALK_ID = "foio-au-cth-commonwealth-agencies-v0.1.0"
INCLUDE_AGENCY = re.compile(
    r"(?:Commonwealth|Australian Government|Australian Federal Police|Australian Taxation Office|"
    r"Australian Public Service Commission|Australian Radiation Protection|Australian Communications|"
    r"Australian Securities and Investments Commission|Australian Prudential Regulation Authority|"
    r"Australian Trade Commission|Australian Border Force|Attorney-General's Department|"
    r"Department of Finance|Department of Health|Department of Home Affairs|Department of Defence|"
    r"Department of Immigration|Department of Infrastructure|Department of the Treasury|"
    r"Department of Education|Department of Human Services|Department of Employment|"
    r"National Disability Insurance Agency|Services Australia|Office of the|Prime Minister|"
    r"Treasurer|Minister for Defence|Federal Court)",
    re.IGNORECASE,
)
EXCLUDE_AGENCY = re.compile(
    r"(?:Queensland|New South Wales|\bNSW\b|Victoria|Tasmania|South Australia|Western Australia|"
    r"Northern Territory|Local Government|City Council|Shire Council|University|Police Service|"
    r"Police Force|Fire and Emergency|VicRoads)",
    re.IGNORECASE,
)
REQUEST_TARGET = re.compile(
    r"Freedom of Information request to\s+(?P<target>.{1,220}?)(?:\s+-\s+Right\s+To\s+Know|\s+-\s+Right\s+to\s+Know)",
    re.IGNORECASE | re.DOTALL,
)
PATTERNS = (
    re.compile(
        r"\b(?:a\s+)?Freedom of Information request to\b.{0,300}", re.IGNORECASE | re.DOTALL
    ),
    re.compile(r"\b(?:request under|under)\s+the\s+Freedom of Information Act\b", re.IGNORECASE),
    re.compile(
        r"\bCommonwealth\b.{0,120}\b(?:Freedom of Information|FOI)\b", re.IGNORECASE | re.DOTALL
    ),
    re.compile(
        r"\b(?:Freedom of Information|FOI)\b.{0,120}\bCommonwealth\b", re.IGNORECASE | re.DOTALL
    ),
    re.compile(
        r"\b(?:Australian Government|federal government)\b.{0,120}\b(?:Freedom of Information|FOI)\b",
        re.IGNORECASE | re.DOTALL,
    ),
    re.compile(
        r"\b(?:Freedom of Information|FOI)\b.{0,120}\b(?:Australian Government|federal government)\b",
        re.IGNORECASE | re.DOTALL,
    ),
)


def extract_unit(unit: dict[str, Any], *, extractor_revision: str) -> dict[str, Any]:
    text = str(unit.get("text") or "")
    target_match = REQUEST_TARGET.search(text)
    target = target_match.group("target") if target_match else text
    blocked = EXCLUDE_AGENCY.search(target) and not re.search(
        r"Australian Federal Police", target, re.IGNORECASE
    )
    agency_match = INCLUDE_AGENCY.search(target)
    match = (
        None
        if blocked
        else agency_match
        or next((pattern.search(text) for pattern in PATTERNS if pattern.search(text)), None)
    )
    if match is None:
        return {
            "unit_id": unit["unit_id"],
            "unit_sha256": unit["unit_sha256"],
            "label": "unknown",
            "abstention": True,
            "abstention_reason": "insufficient_evidence",
            "span": None,
            "extractor_revision": extractor_revision,
            "codebook_id": CODEBOOK_ID,
            "agency_crosswalk_id": AGENCY_CROSSWALK_ID,
        }
    return {
        "unit_id": unit["unit_id"],
        "unit_sha256": unit["unit_sha256"],
        "label": "observed",
        "abstention": False,
        "abstention_reason": None,
        "span": {
            "start": match.start(),
            "end": match.end(),
            "coordinate_system": "utf8_character_half_open",
        },
        "extractor_revision": extractor_revision,
        "codebook_id": CODEBOOK_ID,
        "agency_crosswalk_id": AGENCY_CROSSWALK_ID,
    }


def extract(frame_path: Path, *, extractor_revision: str) -> dict[str, Any]:
    frame = json.loads(frame_path.read_text(encoding="utf-8"))
    units = [extract_unit(unit, extractor_revision=extractor_revision) for unit in frame["units"]]
    return {
        "schema_version": "foi-o.au-cth-assertion-extractor-output.v0.1.0",
        "status": "candidate_not_promoted",
        "jurisdiction": "AU-CTH",
        "extractor_revision": extractor_revision,
        "codebook_id": CODEBOOK_ID,
        "source_population_sha256": frame["source_population_sha256"],
        "units": units,
        "promotion_allowed": False,
        "publication": False,
        "redistribution": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--frame", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--revision", default="local-candidate-v0.1.0")
    args = parser.parse_args()
    result = extract(args.frame, extractor_revision=args.revision)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"units": len(result["units"]), "output": str(args.output)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

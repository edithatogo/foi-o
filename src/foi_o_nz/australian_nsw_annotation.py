"""Bounded automated AU-NSW annotation roles and disagreement adjudication."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

MEMBERSHIP_SHA256 = "4f9ec5e094ff9e9fa4e2dbb6f1c83c3fe33d28eb68c89397997c4e9bb9988840"
CODEBOOK_SHA256 = "3b8d76366e7dccb52e52a5e2275469ea4b52bc54eacff00b89c0bf26a8d6a49f"
FRAME_FILE_SHA256 = "d09deb2ce966fb1b13ef33244f542a4c897df534baaeab94e7bc064c10643176"
PROTOCOL_SHA256 = "9e8415e60c90d8feba2290c5a97aa1a03f7200978fb6b212f5df54ed99b44caf"
ANNOTATOR_A = "agent:au-nsw-annotator-a"
ANNOTATOR_B = "agent:au-nsw-annotator-b"
ADJUDICATOR = "agent:au-nsw-adjudicator"
_A_OBSERVED = re.compile(r"\bGIPA\b|Government Information \(Public Access\)", re.IGNORECASE)
_B_OBSERVED = re.compile(
    r"\bGIPA Act\b|Government Information \(Public Access\) Act", re.IGNORECASE
)
_CANDIDATE = re.compile(r"\binformation access\b|\bFOI\b", re.IGNORECASE)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _annotate(unit: dict[str, Any], *, role: str) -> dict[str, Any]:
    text = str(unit["text"])
    observed_pattern = _A_OBSERVED if role == ANNOTATOR_A else _B_OBSERVED
    match = observed_pattern.search(text)
    label = (
        "observed" if match else "candidate" if (match := _CANDIDATE.search(text)) else "unknown"
    )
    return {
        "unit_id": unit["unit_id"],
        "unit_sha256": unit["text_sha256"],
        "role": role,
        "label": label,
        "abstention": label == "unknown",
        "abstention_reason": "insufficient_evidence" if label == "unknown" else None,
        "span": None
        if match is None
        else {
            "start": match.start(),
            "end": match.end(),
            "coordinate_system": "utf8_character_half_open",
        },
    }


def run_annotation(
    *, membership_path: Path, frame_path: Path, codebook_path: Path, output_root: Path
) -> dict[str, Any]:
    """Generate packets, independent annotations, and disagreement-only adjudication."""
    if _sha256(membership_path) != MEMBERSHIP_SHA256 or _sha256(codebook_path) != CODEBOOK_SHA256:
        raise ValueError("membership or NSW codebook SHA-256 mismatch")
    if _sha256(frame_path) != FRAME_FILE_SHA256:
        raise ValueError("immutable NSW frame SHA-256 mismatch")
    membership = json.loads(membership_path.read_text(encoding="utf-8"))
    frame = json.loads(frame_path.read_text(encoding="utf-8"))
    units = {unit["unit_id"]: unit for unit in frame["units"]}
    selected = membership.get("membership")
    if not isinstance(selected, list) or len(selected) != 100:
        raise ValueError("membership is not the approved 100-unit set")
    chosen = []
    for row in selected:
        unit = units.get(row["unit_id"])
        if unit is None or unit["text_sha256"] != row["text_sha256"]:
            raise ValueError("membership escaped immutable frame")
        chosen.append(unit)
    output_root.mkdir(parents=True, exist_ok=True)
    annotations: dict[str, list[dict[str, Any]]] = {}
    packet_hashes: dict[str, str] = {}
    for role in (ANNOTATOR_A, ANNOTATOR_B):
        packet = {
            "schema": "foi-o.au-nsw-blinded-annotation-packet.v1",
            "role": role,
            "jurisdiction": "AU-NSW",
            "membership_sha256": MEMBERSHIP_SHA256,
            "codebook_sha256": CODEBOOK_SHA256,
            "blinded_to_peer": True,
            "blinded_to_extractor": True,
            "units": [
                {key: unit[key] for key in ("unit_id", "text_sha256", "text", "source_ref")}
                for unit in chosen
            ],
        }
        packet_path = output_root / f"{role.rsplit(':', 1)[1]}.packet.json"
        packet_path.write_text(
            json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        packet_hashes[role] = _sha256(packet_path)
        records = [_annotate(unit, role=role) for unit in chosen]
        annotations[role] = records
        (output_root / f"{role.rsplit(':', 1)[1]}.annotations.json").write_text(
            json.dumps(records, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    a, b = annotations[ANNOTATOR_A], annotations[ANNOTATOR_B]
    disagreements = [
        {
            "unit_id": left["unit_id"],
            "a_label": left["label"],
            "b_label": right["label"],
            "dimension": "label_or_span_or_abstention",
        }
        for left, right in zip(a, b, strict=True)
        if (left["label"], left["span"], left["abstention"])
        != (right["label"], right["span"], right["abstention"])
    ]
    adjudications = [
        {
            "unit_id": row["unit_id"],
            "role": ADJUDICATOR,
            "outcome": "resolved",
            "label": "observed"
            if "observed" in {row["a_label"], row["b_label"]}
            else row["a_label"],
            "rationale": "Distinct disagreement-only automated adjudication under the approved NSW GIPA codebook.",
        }
        for row in disagreements
    ]
    (output_root / "adjudications.json").write_text(
        json.dumps(adjudications, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    annotation_hashes = {
        role: _sha256(output_root / f"{role.rsplit(':', 1)[1]}.annotations.json")
        for role in annotations
    }
    report = {
        "schema": "foi-o.au-nsw-automated-annotation-report.v1",
        "status": "bounded_automated_annotation_not_gold",
        "membership_sha256": MEMBERSHIP_SHA256,
        "frame_file_sha256": FRAME_FILE_SHA256,
        "codebook_sha256": CODEBOOK_SHA256,
        "protocol_sha256": PROTOCOL_SHA256,
        "roles": [ANNOTATOR_A, ANNOTATOR_B, ADJUDICATOR],
        "packet_sha256": packet_hashes,
        "annotation_sha256": annotation_hashes,
        "adjudications_sha256": _sha256(output_root / "adjudications.json"),
        "unit_count": len(a),
        "raw_label_agreement": {
            "numerator": sum(x["label"] == y["label"] for x, y in zip(a, b, strict=True)),
            "denominator": len(a),
        },
        "disagreement_count": len(disagreements),
        "adjudication_count": len(adjudications),
        "extractor_metrics_authorized": False,
        "gold_promotion_authorized": False,
        "publication_authorized": False,
        "redistribution_authorized": False,
        "training_authorized": False,
        "profile_promotion_authorized": False,
    }
    report_path = output_root / "report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "ok": True,
        "unit_count": len(a),
        "disagreement_count": len(disagreements),
        "report_sha256": _sha256(report_path),
    }


def validate_annotation_report(report_path: Path) -> dict[str, Any]:
    """Validate locked role outputs and disagreement accounting."""
    report = json.loads(report_path.read_text(encoding="utf-8"))
    root = report_path.parent
    if report.get("membership_sha256") != MEMBERSHIP_SHA256 or report.get("unit_count") != 100:
        raise ValueError("report membership or unit count mismatch")
    sets = []
    for role in (ANNOTATOR_A, ANNOTATOR_B):
        path = root / f"{role.rsplit(':', 1)[1]}.annotations.json"
        if _sha256(path) != report["annotation_sha256"][role]:
            raise ValueError("annotation SHA-256 mismatch")
        sets.append(json.loads(path.read_text(encoding="utf-8")))
    disagreements = sum(
        (left["label"], left["span"], left["abstention"])
        != (right["label"], right["span"], right["abstention"])
        for left, right in zip(sets[0], sets[1], strict=True)
    )
    adjudications_path = root / "adjudications.json"
    if _sha256(adjudications_path) != report["adjudications_sha256"]:
        raise ValueError("adjudication SHA-256 mismatch")
    if report.get("disagreement_count") != disagreements or report.get("adjudication_count") != len(
        json.loads(adjudications_path.read_text(encoding="utf-8"))
    ):
        raise ValueError("disagreement accounting mismatch")
    if any(item is not False for key, item in report.items() if key.endswith("_authorized")):
        raise ValueError("annotation report crossed an unapproved boundary")
    return {
        "ok": True,
        "report_sha256": _sha256(report_path),
        "unit_count": 100,
        "disagreement_count": disagreements,
    }

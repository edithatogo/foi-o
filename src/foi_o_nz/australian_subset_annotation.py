"""Bounded automated AU-CTH annotation roles and disagreement-only adjudication."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, cast

MEMBERSHIP_SHA256 = "f86ed488429009bf3d6a78a7853cca8bb67b8783c728d5ffd255575a9665bda7"
CODEBOOK_SHA256 = "ed1f4f1ee9b0442ed8570e0591f0c2a8dc498dbb8bf0f09df49b4eee779ca8b9"
PROTOCOL_SHA256 = "9e8415e60c90d8feba2290c5a97aa1a03f7200978fb6b212f5df54ed99b44caf"
_A_OBSERVED = re.compile(r"\bfreedom\s+of\s+information\b|\bfoi\b", re.IGNORECASE)
_B_OBSERVED = re.compile(r"\bfreedom\s+of\s+information\b|\bfoi\s+(?:request|act)\b", re.IGNORECASE)
_CANDIDATE = re.compile(r"\binformation\s+request\b|\brequest\s+for\s+information\b", re.IGNORECASE)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _annotate(unit: dict[str, Any], text: str, *, role: str) -> dict[str, Any]:
    observed = _A_OBSERVED if role == "agent:au-cth-annotator-a" else _B_OBSERVED
    match = observed.search(text)
    label = (
        "observed" if match else "candidate" if (match := _CANDIDATE.search(text)) else "unknown"
    )
    return {
        "unit_id": unit["unit_id"],
        "unit_sha256": unit["unit_sha256"],
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


def validate_annotation_record(record: dict[str, Any], *, expected_role: str) -> None:
    """Validate one locked automated role record without consulting peer output."""
    if record.get("role") != expected_role:
        raise ValueError("annotation role identity mismatch")
    if not isinstance(record.get("unit_id"), str) or not record["unit_id"]:
        raise ValueError("annotation unit identity is missing")
    unit_sha256 = record.get("unit_sha256")
    if not isinstance(unit_sha256, str) or not re.fullmatch(r"[a-f0-9]{64}", unit_sha256):
        raise ValueError("annotation unit SHA-256 is invalid")
    if record.get("label") not in {"observed", "inferred", "candidate", "unknown"}:
        raise ValueError("annotation label is not in the approved codebook")
    abstention = record.get("abstention")
    if not isinstance(abstention, bool):
        raise ValueError("annotation abstention must be boolean")
    span = record.get("span")
    if abstention:
        if record.get("label") != "unknown" or not record.get("abstention_reason"):
            raise ValueError("abstention requires unknown label and reason")
        if span is not None:
            raise ValueError("abstention span must be null")
    elif record.get("label") == "unknown" or record.get("abstention_reason") is not None:
        raise ValueError("non-abstaining annotation has invalid null encoding")
    elif not isinstance(span, dict):
        raise ValueError("non-abstaining annotation requires a span")
    if span is not None:
        if span.get("coordinate_system") != "utf8_character_half_open":
            raise ValueError("annotation span coordinate system is invalid")
        if (
            not isinstance(span.get("start"), int)
            or not isinstance(span.get("end"), int)
            or span["start"] < 0
            or span["end"] <= span["start"]
            or span["end"] - span["start"] > 1000
        ):
            raise ValueError("annotation span bounds are invalid")


def run_annotation(
    *,
    membership_path: Path,
    frame_path: Path,
    text_root: Path,
    codebook_path: Path,
    output_root: Path,
) -> dict[str, Any]:
    """Execute two blinded automated roles, then adjudicate exact disagreements only."""
    if _sha256(membership_path) != MEMBERSHIP_SHA256 or _sha256(codebook_path) != CODEBOOK_SHA256:
        raise ValueError("membership or approved codebook SHA-256 mismatch")
    membership = json.loads(membership_path.read_text(encoding="utf-8"))
    frame = json.loads(frame_path.read_text(encoding="utf-8"))
    units = {unit["unit_id"]: unit for unit in frame["units"]}
    selected_value = membership.get("membership")
    if not isinstance(selected_value, list) or len(selected_value) != 385:
        raise ValueError("candidate membership is not the approved 385-unit set")
    selected = cast("list[dict[str, Any]]", selected_value)
    chosen = [units[row["unit_id"]] for row in selected]
    if any(
        unit["unit_sha256"] != row["unit_sha256"]
        for unit, row in zip(chosen, selected, strict=True)
    ):
        raise ValueError("candidate membership escaped the frozen frame")
    output_root.mkdir(parents=True, exist_ok=True)
    packets = {}
    annotations: dict[str, list[dict[str, Any]]] = {}
    for role in ("agent:au-cth-annotator-a", "agent:au-cth-annotator-b"):
        packet = [
            {key: unit[key] for key in ("unit_id", "unit_sha256", "text_filename", "source_spans")}
            for unit in chosen
        ]
        packet_path = output_root / f"{role.rsplit(':', 1)[1]}.packet.json"
        packet_path.write_text(
            json.dumps(
                {
                    "role": role,
                    "blinded_to_peer": True,
                    "blinded_to_extractor": True,
                    "units": packet,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        packets[role] = _sha256(packet_path)
        annotations[role] = [
            _annotate(
                unit,
                (text_root / unit["text_filename"]).read_text(encoding="utf-8").rstrip("\n"),
                role=role,
            )
            for unit in chosen
        ]
        (output_root / f"{role.rsplit(':', 1)[1]}.annotations.json").write_text(
            json.dumps(annotations[role], indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    a, b = annotations.values()
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
            "role": "agent:au-cth-adjudicator",
            "outcome": "resolved",
            "label": "observed" if "observed" in {row["a_label"], row["b_label"]} else "candidate",
            "rationale": "Distinct disagreement-only automated adjudication under the approved codebook.",
        }
        for row in disagreements
    ]
    (output_root / "adjudications.json").write_text(
        json.dumps(adjudications, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    matches = sum(left["label"] == right["label"] for left, right in zip(a, b, strict=True))
    report = {
        "schema": "foi-o.au-cth-subset-automated-annotation-report.v1",
        "status": "bounded_automated_annotation_not_gold",
        "membership_sha256": MEMBERSHIP_SHA256,
        "codebook_sha256": CODEBOOK_SHA256,
        "protocol_sha256": PROTOCOL_SHA256,
        "roles": [
            "agent:au-cth-annotator-a",
            "agent:au-cth-annotator-b",
            "agent:au-cth-adjudicator",
        ],
        "packet_sha256": packets,
        "annotation_sha256": {
            role: _sha256(output_root / f"{role.rsplit(':', 1)[1]}.annotations.json")
            for role in annotations
        },
        "adjudications_sha256": _sha256(output_root / "adjudications.json"),
        "unit_count": len(a),
        "raw_label_agreement": {
            "numerator": matches,
            "denominator": len(a),
            "estimate": matches / len(a),
        },
        "disagreement_count": len(disagreements),
        "adjudication_count": len(adjudications),
        "extractor_metrics_authorized": False,
        "gold_promotion_authorized": False,
        "publication_authorized": False,
        "redistribution_authorized": False,
        "training_authorized": False,
    }
    report_path = output_root / "report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "ok": True,
        "report_sha256": _sha256(report_path),
        "disagreement_count": len(disagreements),
    }


def validate_annotation_report(report_path: Path) -> dict[str, Any]:
    """Bind the automated report to its two locked role outputs and queue."""
    report = json.loads(report_path.read_text(encoding="utf-8"))
    root = report_path.parent
    roles = ["agent:au-cth-annotator-a", "agent:au-cth-annotator-b"]
    if report.get("membership_sha256") != MEMBERSHIP_SHA256 or report.get("unit_count") != 385:
        raise ValueError("annotation report membership or unit count mismatch")
    sets = []
    for role in roles:
        path = root / f"{role.rsplit(':', 1)[1]}.annotations.json"
        if _sha256(path) != report.get("annotation_sha256", {}).get(role):
            raise ValueError("locked annotation SHA-256 mismatch")
        records = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(records, list) or len(records) != report.get("unit_count"):
            raise ValueError("locked annotation record count mismatch")
        for record in records:
            if not isinstance(record, dict):
                raise ValueError("locked annotation record is not an object")
            validate_annotation_record(record, expected_role=role)
        if len({record["unit_id"] for record in records}) != len(records):
            raise ValueError("locked annotation unit IDs are not unique")
        sets.append(records)
    disagreements = sum(
        (left["label"], left["span"], left["abstention"])
        != (right["label"], right["span"], right["abstention"])
        for left, right in zip(sets[0], sets[1], strict=True)
    )
    adjudications_path = root / "adjudications.json"
    if _sha256(adjudications_path) != report.get("adjudications_sha256"):
        raise ValueError("adjudication SHA-256 mismatch")
    adjudications = json.loads(adjudications_path.read_text(encoding="utf-8"))
    if not isinstance(adjudications, list):
        raise ValueError("adjudication output is not a list")
    if any(item.get("role") != "agent:au-cth-adjudicator" for item in adjudications):
        raise ValueError("adjudication role identity mismatch")
    if (
        report.get("disagreement_count") != disagreements
        or report.get("adjudication_count") != len(adjudications)
        or len(adjudications) != disagreements
    ):
        raise ValueError("disagreement queue accounting mismatch")
    if any(item is not False for key, item in report.items() if key.endswith("_authorized")):
        raise ValueError("annotation report crossed an unapproved boundary")
    return {"ok": True, "report_sha256": _sha256(report_path), "disagreement_count": disagreements}

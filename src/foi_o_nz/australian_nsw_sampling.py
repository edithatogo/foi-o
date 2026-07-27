"""Deterministic AU-NSW paired-annotation membership selection."""

from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path
from typing import Any

FRAME_FILE_SHA256 = "d09deb2ce966fb1b13ef33244f542a4c897df534baaeab94e7bc064c10643176"
FRAME_SELF_SHA256 = "37af88495c8896e83028b4692a10f18f2dd5a5e4dcad6b6140f40312f64d4000"
SEED = 20260721
POPULATION = 115
SAMPLE_SIZE = 100
PRIOR_MEMBERSHIP_SHA256 = "4f9ec5e094ff9e9fa4e2dbb6f1c83c3fe33d28eb68c89397997c4e9bb9988840"
REMEDIATION_CODEBOOK_SHA256 = "56c33dd1d681841b5512aa75dc859fa6febb1da687d2b74d9193b40230ebe1c6"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _selection(units: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ordered = sorted(units, key=lambda unit: str(unit["text_sha256"]))
    selected = set(random.Random(SEED).sample(range(len(ordered)), SAMPLE_SIZE))  # noqa: S311
    probability = SAMPLE_SIZE / POPULATION
    return [
        {
            "unit_id": unit["unit_id"],
            "canonical_slug": unit["canonical_slug"],
            "text_sha256": unit["text_sha256"],
            "duplicate_cluster_id": unit["duplicate_cluster_id"],
            "stratum": "AU-NSW:GIPA:accessible-request-text",
            "inclusion_probability": probability,
            "sampling_weight": 1 / probability,
        }
        for index, unit in enumerate(ordered)
        if index in selected
    ]


def build_membership(*, frame_path: Path, output: Path) -> dict[str, Any]:
    """Draw the approved 100-unit membership from the immutable frame."""
    if _sha256(frame_path) != FRAME_FILE_SHA256:
        raise ValueError("immutable AU-NSW frame stored SHA-256 mismatch")
    frame = json.loads(frame_path.read_text(encoding="utf-8"))
    if (
        frame.get("frame_sha256") != FRAME_SELF_SHA256
        or frame.get("record_count") != POPULATION
        or frame.get("rights_eligible") is not True
        or any(unit.get("text") is None for unit in frame.get("units", []))
    ):
        raise ValueError("immutable AU-NSW frame is not the approved 115-unit frame")
    value = {
        "schema": "foi-o.au-nsw-paired-annotation-membership-candidate.v1",
        "status": "candidate_membership_not_annotation",
        "frame_file_sha256": FRAME_FILE_SHA256,
        "frame_self_sha256": FRAME_SELF_SHA256,
        "seed": SEED,
        "population_count": POPULATION,
        "selected_count": SAMPLE_SIZE,
        "excluded_count": POPULATION - SAMPLE_SIZE,
        "sampling_design": "100 of 115 without replacement; sorted text SHA-256; Python MT19937",
        "membership": _selection(frame["units"]),
        "annotation_authorized": False,
        "adjudication_authorized": False,
        "extractor_metrics_authorized": False,
        "publication_authorized": False,
        "redistribution_authorized": False,
        "training_authorized": False,
        "profile_promotion_authorized": False,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"ok": True, "selected_count": SAMPLE_SIZE, "membership_sha256": _sha256(output)}


def validate_membership(path: Path, *, frame_path: Path) -> dict[str, Any]:
    """Recompute the draw and reject changed membership or authorization flags."""
    value = json.loads(path.read_text(encoding="utf-8"))
    if _sha256(frame_path) != FRAME_FILE_SHA256:
        raise ValueError("immutable AU-NSW frame stored SHA-256 mismatch")
    frame = json.loads(frame_path.read_text(encoding="utf-8"))
    if (
        value.get("schema") != "foi-o.au-nsw-paired-annotation-membership-candidate.v1"
        or value.get("status") != "candidate_membership_not_annotation"
        or value.get("frame_file_sha256") != FRAME_FILE_SHA256
        or value.get("frame_self_sha256") != FRAME_SELF_SHA256
        or value.get("seed") != SEED
        or value.get("population_count") != POPULATION
        or value.get("selected_count") != SAMPLE_SIZE
        or value.get("excluded_count") != POPULATION - SAMPLE_SIZE
        or value.get("membership") != _selection(frame["units"])
    ):
        raise ValueError("candidate membership does not match the approved deterministic draw")
    if any(item is not False for key, item in value.items() if key.endswith("_authorized")):
        raise ValueError("candidate membership crossed an unapproved boundary")
    return {"ok": True, "selected_count": SAMPLE_SIZE, "membership_sha256": _sha256(path)}


def build_fresh_holdout(
    *, frame_path: Path, prior_membership_path: Path, output: Path
) -> dict[str, Any]:
    """Create the approved 15-unit complement holdout without replacement."""
    if (
        _sha256(frame_path) != FRAME_FILE_SHA256
        or _sha256(prior_membership_path) != PRIOR_MEMBERSHIP_SHA256
    ):
        raise ValueError("frame or prior membership SHA-256 mismatch")
    frame = json.loads(frame_path.read_text(encoding="utf-8"))
    prior = json.loads(prior_membership_path.read_text(encoding="utf-8"))
    units = frame["units"]
    prior_ids = {row["unit_id"] for row in prior["membership"]}
    holdout = [unit for unit in units if unit["unit_id"] not in prior_ids]
    holdout.sort(key=lambda unit: str(unit["text_sha256"]))
    if len(holdout) != POPULATION - SAMPLE_SIZE:
        raise ValueError("prior membership does not leave the approved 15-unit complement")
    value = {
        "schema": "foi-o.au-nsw-remediation-holdout-membership-candidate.v1",
        "status": "candidate_membership_not_annotation",
        "frame_file_sha256": FRAME_FILE_SHA256,
        "frame_self_sha256": FRAME_SELF_SHA256,
        "prior_membership_sha256": PRIOR_MEMBERSHIP_SHA256,
        "codebook_sha256": REMEDIATION_CODEBOOK_SHA256,
        "seed": SEED,
        "population_count": POPULATION,
        "prior_membership_count": SAMPLE_SIZE,
        "selected_count": len(holdout),
        "sampling_design": "deterministic complement of prior 100-unit membership; sorted text SHA-256; singleton clusters",
        "membership": [
            {
                "unit_id": unit["unit_id"],
                "canonical_slug": unit["canonical_slug"],
                "text_sha256": unit["text_sha256"],
                "duplicate_cluster_id": unit["duplicate_cluster_id"],
                "stratum": "AU-NSW:GIPA:accessible-request-text",
            }
            for unit in holdout
        ],
        "packet_generation_authorized": False,
        "annotation_authorized": False,
        "adjudication_authorized": False,
        "extractor_metrics_authorized": False,
        "publication_authorized": False,
        "redistribution_authorized": False,
        "training_authorized": False,
        "profile_promotion_authorized": False,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"ok": True, "selected_count": len(holdout), "membership_sha256": _sha256(output)}


def validate_fresh_holdout(
    path: Path, *, frame_path: Path, prior_membership_path: Path
) -> dict[str, Any]:
    """Validate the exact complement and its downstream authorization boundary."""
    value = json.loads(path.read_text(encoding="utf-8"))
    if (
        _sha256(frame_path) != FRAME_FILE_SHA256
        or _sha256(prior_membership_path) != PRIOR_MEMBERSHIP_SHA256
    ):
        raise ValueError("frame or prior membership SHA-256 mismatch")
    frame = json.loads(frame_path.read_text(encoding="utf-8"))
    prior = json.loads(prior_membership_path.read_text(encoding="utf-8"))
    prior_ids = {row["unit_id"] for row in prior["membership"]}
    expected = sorted(
        (unit for unit in frame["units"] if unit["unit_id"] not in prior_ids),
        key=lambda unit: str(unit["text_sha256"]),
    )
    actual_ids = [row["unit_id"] for row in value.get("membership", [])]
    if (
        value.get("schema") != "foi-o.au-nsw-remediation-holdout-membership-candidate.v1"
        or value.get("status") != "candidate_membership_not_annotation"
        or value.get("codebook_sha256") != REMEDIATION_CODEBOOK_SHA256
        or value.get("seed") != SEED
        or value.get("selected_count") != 15
        or actual_ids != [unit["unit_id"] for unit in expected]
    ):
        raise ValueError("fresh holdout does not match the approved complement")
    if any(item is not False for key, item in value.items() if key.endswith("_authorized")):
        raise ValueError("fresh holdout crossed an unapproved boundary")
    return {"ok": True, "selected_count": 15, "membership_sha256": _sha256(path)}

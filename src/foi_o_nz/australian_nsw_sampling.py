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

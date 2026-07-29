"""Deterministic, non-annotation membership selection for the AU-CTH subset."""

from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path
from typing import Any

FRAME_SHA256 = "47115d3d422f0b1d0a2aae856cebd1b8ffca8591e01d42c82d494818c7af2a80"
REGISTRY_SHA256 = "e4f818d3afbbd4f7bdc1b2f57d94b1da5af73b5887a67e37d528f8813f83f38d"
SEED = 20260721
POPULATION = 517
SAMPLE_SIZE = 385


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _selection(units: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ordered = sorted(units, key=lambda unit: str(unit["unit_sha256"]))
    selected_indexes = set(random.Random(SEED).sample(range(len(ordered)), SAMPLE_SIZE))  # noqa: S311
    probability = SAMPLE_SIZE / POPULATION
    return [
        {
            "unit_id": unit["unit_id"],
            "unit_sha256": unit["unit_sha256"],
            "duplicate_cluster_id": unit["duplicate_cluster_id"],
            "stratum": "AU-CTH:retained-html",
            "inclusion_probability": probability,
            "sampling_weight": 1 / probability,
        }
        for index, unit in enumerate(ordered)
        if index in selected_indexes
    ]


def build_membership(*, frame_path: Path, registry_path: Path, output: Path) -> dict[str, Any]:
    """Draw the exact approved candidate membership once from the frozen frame."""
    if _sha256(frame_path) != FRAME_SHA256 or _sha256(registry_path) != REGISTRY_SHA256:
        raise ValueError("frozen frame or duplicate registry SHA-256 mismatch")
    frame = json.loads(frame_path.read_text(encoding="utf-8"))
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    units = frame.get("units")
    if (
        not isinstance(units, list)
        or len(units) != POPULATION
        or len(registry.get("clusters", [])) != POPULATION
    ):
        raise ValueError("frozen frame is not the approved singleton-cluster population")
    selected = _selection(units)
    value = {
        "schema": "foi-o.au-cth-subset-sampling-membership-candidate.v1",
        "status": "candidate_membership_not_annotation",
        "frame_sha256": FRAME_SHA256,
        "duplicate_clusters_sha256": REGISTRY_SHA256,
        "seed": SEED,
        "population_count": POPULATION,
        "selected_count": SAMPLE_SIZE,
        "excluded_count": POPULATION - SAMPLE_SIZE,
        "sampling_design": "one proportional available stratum; sorted unit SHA-256; Python MT19937; no replacement",
        "membership": selected,
        "annotation_authorized": False,
        "adjudication_authorized": False,
        "extractor_metrics_authorized": False,
        "population_inference_authorized": False,
        "publication_authorized": False,
        "redistribution_authorized": False,
        "training_authorized": False,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"ok": True, "selected_count": SAMPLE_SIZE, "membership_sha256": _sha256(output)}


def validate_membership(path: Path, *, frame_path: Path, registry_path: Path) -> dict[str, Any]:
    """Recompute the approved draw and reject any changed membership or boundary."""
    value = json.loads(path.read_text(encoding="utf-8"))
    if _sha256(frame_path) != FRAME_SHA256 or _sha256(registry_path) != REGISTRY_SHA256:
        raise ValueError("frozen frame or duplicate registry SHA-256 mismatch")
    frame = json.loads(frame_path.read_text(encoding="utf-8"))
    if (
        value.get("schema") != "foi-o.au-cth-subset-sampling-membership-candidate.v1"
        or value.get("status") != "candidate_membership_not_annotation"
        or value.get("frame_sha256") != FRAME_SHA256
        or value.get("duplicate_clusters_sha256") != REGISTRY_SHA256
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

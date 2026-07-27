"""Create and validate the approved restricted-local AU-CTH HTML subset frame."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from pathlib import Path
from typing import Any

from foi_o_nz.australian_retained_html_text import EXPECTED_HTML_COUNT

CANDIDATE_SUMMARY_SHA256 = "efd5e6be4e588eb3d1f0eaa15104595da41faaa0c89d5b1d3958afbb9f97b8e6"
CANDIDATE_JSONL_SHA256 = "a09c4b8fc2cf01ca957c3c0c8d3963ab0e0a37253a6fbcf6731cc889a9ed8c34"
SEED = 20260721
_SPACE = re.compile(r"\s+")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _canonical(value: str) -> str:
    return _SPACE.sub(" ", unicodedata.normalize("NFC", value).lower()).strip()


def _cluster_id(*, title: str, authority: str, text: str) -> str:
    key = "\x1f".join((_canonical(title), _canonical(authority), _canonical(text), "AU-CTH"))
    return f"exact:{hashlib.sha256(key.encode()).hexdigest()}"


def build_subset_frame(
    *,
    candidate_summary: Path,
    candidate_jsonl: Path,
    text_root: Path,
    classification_summary: Path,
    output_root: Path,
) -> dict[str, Any]:
    """Create the exact authorized source subset; never sample or annotate it."""
    if _sha256(candidate_summary) != CANDIDATE_SUMMARY_SHA256:
        raise ValueError("retained HTML candidate summary SHA-256 mismatch")
    if _sha256(candidate_jsonl) != CANDIDATE_JSONL_SHA256:
        raise ValueError("retained HTML candidate JSONL SHA-256 mismatch")
    summary = json.loads(candidate_summary.read_text(encoding="utf-8"))
    if summary.get("accessible_text_record_count") != EXPECTED_HTML_COUNT:
        raise ValueError("candidate does not contain all approved accessible HTML records")
    classification = json.loads(classification_summary.read_text(encoding="utf-8"))
    cth_path = (
        classification_summary.parent / classification["jurisdiction_outputs"]["AU-CTH"]["path"]
    )
    source = {row["canonical_slug"]: row for row in _jsonl(cth_path) if row["media_kind"] == "html"}
    candidates = _jsonl(candidate_jsonl)
    if len(candidates) != EXPECTED_HTML_COUNT or {
        row["canonical_slug"] for row in candidates
    } != set(source):
        raise ValueError("candidate membership is not the exact approved HTML subset")
    units = []
    for candidate in sorted(candidates, key=lambda row: row["canonical_slug"]):
        slug = candidate["canonical_slug"]
        record = source[slug]
        text_path = text_root / candidate["text_filename"]
        text = text_path.read_text(encoding="utf-8").rstrip("\n")
        if hashlib.sha256(text_path.read_bytes()).hexdigest() != candidate["text_sha256"]:
            raise ValueError("text artifact SHA-256 mismatch")
        unit_sha256 = hashlib.sha256(
            f"{slug}\x1f{candidate['text_sha256']}\x1f{candidate['raw_sha256']}".encode()
        ).hexdigest()
        units.append(
            {
                "unit_id": f"AU-CTH:retained-html:{slug}",
                "canonical_slug": slug,
                "unit_sha256": unit_sha256,
                "raw_sha256": candidate["raw_sha256"],
                "text_sha256": candidate["text_sha256"],
                "text_filename": candidate["text_filename"],
                "source_spans": candidate["source_spans"],
                "authority": record["authority"],
                "duplicate_cluster_id": _cluster_id(
                    title=record["title"], authority=record["authority"], text=text
                ),
                "rights_eligible": True,
                "accessibility": "accessible",
            }
        )
    clusters: dict[str, list[str]] = {}
    for unit in units:
        cluster_id = str(unit["duplicate_cluster_id"])
        unit_sha256 = str(unit["unit_sha256"])
        clusters.setdefault(cluster_id, []).append(unit_sha256)
    registry = {
        "schema": "foi-o.au-cth-restricted-local-duplicate-clusters.v1",
        "status": "frozen_restricted_local",
        "seed": SEED,
        "algorithm": {
            "exact": "NFC/lowercase/whitespace title+text+authority+jursidiction SHA-256",
            "near_duplicate": "not compared: request-family key is unique per retained request",
        },
        "clusters": [
            {"cluster_id": key, "member_unit_sha256": sorted(value)}
            for key, value in sorted(clusters.items())
        ],
    }
    output_root.mkdir(parents=True, exist_ok=True)
    registry_path = output_root / "duplicate-clusters.json"
    registry_path.write_text(
        json.dumps(registry, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    frame = {
        "schema": "foi-o.au-cth-restricted-local-source-frame.v1",
        "status": "frozen_restricted_local_source_frame",
        "jurisdiction": "AU-CTH",
        "record_count": len(units),
        "seed": SEED,
        "candidate_summary_sha256": CANDIDATE_SUMMARY_SHA256,
        "candidate_jsonl_sha256": CANDIDATE_JSONL_SHA256,
        "duplicate_clusters_sha256": _sha256(registry_path),
        "units": units,
        "boundaries": {
            "sampling_authorized": False,
            "annotation_authorized": False,
            "publication_authorized": False,
            "redistribution_authorized": False,
            "training_authorized": False,
            "population_inference_authorized": False,
        },
    }
    frame_path = output_root / "frame.json"
    frame_path.write_text(json.dumps(frame, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"ok": True, "record_count": len(units), "frame_sha256": _sha256(frame_path)}


def validate_subset_frame(frame_path: Path, *, registry_path: Path) -> dict[str, Any]:
    """Check frame cardinality, clusters, pins, and all downstream prohibitions."""
    frame = json.loads(frame_path.read_text(encoding="utf-8"))
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    if (
        frame.get("schema") != "foi-o.au-cth-restricted-local-source-frame.v1"
        or frame.get("record_count") != EXPECTED_HTML_COUNT
        or frame.get("seed") != SEED
        or frame.get("candidate_summary_sha256") != CANDIDATE_SUMMARY_SHA256
        or frame.get("candidate_jsonl_sha256") != CANDIDATE_JSONL_SHA256
        or frame.get("duplicate_clusters_sha256") != _sha256(registry_path)
    ):
        raise ValueError("frame pins or record count mismatch")
    units = frame.get("units")
    if not isinstance(units, list) or len(units) != EXPECTED_HTML_COUNT:
        raise ValueError("frame unit count mismatch")
    if len({unit["unit_id"] for unit in units}) != len(units) or not all(
        unit["rights_eligible"] is True for unit in units
    ):
        raise ValueError("frame unit identity or rights mismatch")
    memberships = {
        member for cluster in registry["clusters"] for member in cluster["member_unit_sha256"]
    }
    if memberships != {unit["unit_sha256"] for unit in units}:
        raise ValueError("cluster registry does not exactly cover frame units")
    if any(value is not False for value in frame["boundaries"].values()):
        raise ValueError("frame crossed an unapproved boundary")
    return {"ok": True, "record_count": len(units), "frame_sha256": _sha256(frame_path)}

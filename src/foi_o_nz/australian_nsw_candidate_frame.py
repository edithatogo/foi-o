"""Build a restricted-local, non-empirical AU-NSW candidate frame."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from foi_o_nz.australian_retained_html_text import _extract

MANIFEST_FILE_SHA256 = "c77ce6aafad557f5555fe347d2e9025d07e460574c15a4343728bb1ba3015393"
CLASSIFICATION_SHA256 = "98eae70428e630cbd36849e5ad19c4133dbd9f01c413cf33221d2b0eef0091ab"
NSW_CANDIDATE_SHA256 = "c8486d035279e400b4100cbd7f9443a23dc648d6b1494527657cd294102238b6"
EXPECTED_RECORD_COUNT = 179


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _rows(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _bounded(root: Path, name: str) -> Path:
    path = root / name
    if (
        Path(name).name != name
        or path.is_symlink()
        or path.resolve(strict=False).parent != root.resolve()
    ):
        raise ValueError("artifact path escaped its approved root")
    return path


def build_candidate_frame(
    *, manifest_path: Path, classification_summary: Path, replay_root: Path, output: Path
) -> dict[str, Any]:
    """Validate retained bytes and create a restricted-local candidate frame only."""
    if _sha256(manifest_path.read_bytes()) != MANIFEST_FILE_SHA256:
        raise ValueError("immutable manifest stored-file SHA-256 mismatch")
    if _sha256(classification_summary.read_bytes()) != CLASSIFICATION_SHA256:
        raise ValueError("classification-summary SHA-256 mismatch")
    summary = json.loads(classification_summary.read_text(encoding="utf-8"))
    root = classification_summary.parent
    candidate = summary["jurisdiction_outputs"]["AU-NSW"]
    candidate_path = _bounded(root, candidate["path"])
    if _sha256(candidate_path.read_bytes()) != NSW_CANDIDATE_SHA256:
        raise ValueError("AU-NSW candidate SHA-256 mismatch")
    records = _rows(candidate_path)
    if len(records) != EXPECTED_RECORD_COUNT or any(
        row.get("jurisdiction") != "AU-NSW" for row in records
    ):
        raise ValueError("AU-NSW candidate membership mismatch")
    index_info = summary["replay_index"]
    index_path = _bounded(root, index_info["path"])
    if _sha256(index_path.read_bytes()) != index_info["sha256"]:
        raise ValueError("replay-index SHA-256 mismatch")
    index = {row["canonical_slug"]: row for row in _rows(index_path)}

    units: list[dict[str, Any]] = []
    for record in sorted(records, key=lambda row: str(row["canonical_slug"])):
        slug = str(record["canonical_slug"])
        replay = index.get(slug)
        if replay is None or replay.get("raw_sha256") != record.get("raw_sha256"):
            raise ValueError("candidate escaped approved replay provenance")
        raw_path = _bounded(replay_root / "raw", str(replay["raw_filename"]))
        raw = raw_path.read_bytes()
        if _sha256(raw) != record["raw_sha256"]:
            raise ValueError("retained raw SHA-256 mismatch")
        is_html = record.get("media_kind") == "html"
        text = _extract(raw.decode("utf-8")) if is_html else None
        accessibility = "accessible_request_text" if text else "metadata_only_no_request_text"
        units.append({
            "unit_id": f"AU-NSW:{slug}",
            "canonical_slug": slug,
            "jurisdiction": "AU-NSW",
            "regime": "GIPA",
            "text": text,
            "text_sha256": _sha256(text.encode("utf-8")) if text else None,
            "accessibility": accessibility,
            "rights_disposition": "restricted_local_non_redistributable",
            "rights_eligible": False,
            "annotation_eligible": False,
            "source_ref": {
                "source_url": record["source_url"],
                "archive_url": record["archive_url"],
                "archive_timestamp": record["archive_timestamp"],
                "raw_sha256": record["raw_sha256"],
                "content_type": record["content_type"],
                "jurisdiction_basis": record["jurisdiction_basis"],
            },
        })
    frame: dict[str, Any] = {
        "schema": "foi-o.au-nsw-restricted-candidate-frame.v1",
        "status": "candidate_frame_restricted_local_not_empirical",
        "immutable_manifest_file_sha256": MANIFEST_FILE_SHA256,
        "classification_summary_sha256": CLASSIFICATION_SHA256,
        "candidate_jsonl_sha256": NSW_CANDIDATE_SHA256,
        "jurisdiction": "AU-NSW",
        "regime": "GIPA",
        "record_count": len(units),
        "accessible_request_text_count": sum(unit["text"] is not None for unit in units),
        "metadata_only_count": sum(unit["text"] is None for unit in units),
        "rights_eligible": False,
        "sampling_authorized": False,
        "annotation_authorized": False,
        "publication_authorized": False,
        "redistribution_authorized": False,
        "units": units,
    }
    frame["frame_sha256"] = _sha256(
        json.dumps(frame, sort_keys=True, separators=(",", ":")).encode()
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(frame, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return frame


def validate_candidate_frame(path: Path) -> dict[str, Any]:
    """Ensure a frame remains bounded and cannot authorize empirical use."""
    frame = json.loads(path.read_text(encoding="utf-8"))
    if (
        frame.get("schema") != "foi-o.au-nsw-restricted-candidate-frame.v1"
        or frame.get("status") != "candidate_frame_restricted_local_not_empirical"
        or frame.get("record_count") != EXPECTED_RECORD_COUNT
        or frame.get("candidate_jsonl_sha256") != NSW_CANDIDATE_SHA256
    ):
        raise ValueError("candidate frame identity is invalid")
    for key in (
        "rights_eligible",
        "sampling_authorized",
        "annotation_authorized",
        "publication_authorized",
        "redistribution_authorized",
    ):
        if frame.get(key) is not False:
            raise ValueError("candidate frame crossed an unapproved boundary")
    units = frame.get("units")
    if not isinstance(units, list) or len(units) != EXPECTED_RECORD_COUNT:
        raise ValueError("candidate frame membership is invalid")
    if sum(unit.get("text") is not None for unit in units) != frame.get(
        "accessible_request_text_count"
    ):
        raise ValueError("accessible text count is invalid")
    if sum(unit.get("text") is None for unit in units) != frame.get("metadata_only_count"):
        raise ValueError("metadata-only count is invalid")
    observed = dict(frame)
    actual = observed.pop("frame_sha256", None)
    expected = _sha256(json.dumps(observed, sort_keys=True, separators=(",", ":")).encode())
    if actual != expected:
        raise ValueError("candidate frame self-hash mismatch")
    return {"ok": True, "frame_sha256": actual, "record_count": len(units)}


def build_immutable_frame(candidate_path: Path, output: Path) -> dict[str, Any]:
    """Finalize the specifically approved 115-unit restricted-local frame."""
    candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
    validate_candidate_frame(candidate_path)
    units = [unit for unit in candidate["units"] if unit.get("text") is not None]
    if len(units) != 115:
        raise ValueError("approved AU-NSW text-bearing membership is not 115 units")
    clusters: dict[str, list[str]] = {}
    for unit in units:
        cluster_id = f"text-sha256:{unit['text_sha256']}"
        unit["duplicate_cluster_id"] = cluster_id
        clusters.setdefault(cluster_id, []).append(unit["unit_id"])
    registry = {
        "schema": "foi-o.au-nsw-duplicate-cluster-registry.v1",
        "rule": "exact normalized retained request-text SHA-256; singleton clusters retained",
        "clusters": {key: sorted(value) for key, value in sorted(clusters.items())},
    }
    frame: dict[str, Any] = {
        "schema": "foi-o.au-nsw-immutable-empirical-frame.v1",
        "status": "immutable_restricted_local",
        "jurisdiction": "AU-NSW",
        "regime": "GIPA",
        "source_candidate_frame_sha256": candidate["frame_sha256"],
        "source_candidate_frame_file_sha256": _sha256(candidate_path.read_bytes()),
        "record_count": len(units),
        "duplicate_cluster_count": len(clusters),
        "duplicate_clustering_rule": registry["rule"],
        "duplicate_registry": registry,
        "rights_eligible": True,
        "restricted_local": True,
        "sampling_authorized": False,
        "annotation_authorized": False,
        "publication_authorized": False,
        "redistribution_authorized": False,
        "training_authorized": False,
        "legal_certification_authorized": False,
        "profile_promotion_authorized": False,
        "units": units,
    }
    frame["frame_sha256"] = _sha256(
        json.dumps(frame, sort_keys=True, separators=(",", ":")).encode()
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(frame, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return frame


def validate_immutable_frame(path: Path) -> dict[str, Any]:
    """Validate the immutable frame without authorizing any downstream stage."""
    frame = json.loads(path.read_text(encoding="utf-8"))
    if frame.get("schema") != "foi-o.au-nsw-immutable-empirical-frame.v1":
        raise ValueError("immutable frame schema is invalid")
    if frame.get("status") != "immutable_restricted_local" or frame.get("record_count") != 115:
        raise ValueError("immutable frame identity is invalid")
    for key in (
        "restricted_local",
        "rights_eligible",
        "sampling_authorized",
        "annotation_authorized",
        "publication_authorized",
        "redistribution_authorized",
        "training_authorized",
        "legal_certification_authorized",
        "profile_promotion_authorized",
    ):
        expected = key in {"restricted_local", "rights_eligible"}
        if frame.get(key) is not expected:
            raise ValueError(f"immutable frame boundary is invalid: {key}")
    units = frame.get("units")
    if (
        not isinstance(units, list)
        or len(units) != 115
        or any(unit.get("text") is None for unit in units)
    ):
        raise ValueError("immutable frame membership is invalid")
    observed = dict(frame)
    actual = observed.pop("frame_sha256", None)
    expected = _sha256(json.dumps(observed, sort_keys=True, separators=(",", ":")).encode())
    if actual != expected:
        raise ValueError("immutable frame self-hash mismatch")
    return {
        "ok": True,
        "frame_sha256": actual,
        "record_count": len(units),
        "duplicate_cluster_count": frame["duplicate_cluster_count"],
    }

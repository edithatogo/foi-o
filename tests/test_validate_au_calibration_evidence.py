import hashlib
import json
from pathlib import Path

from scripts.validate_au_calibration_evidence import validate_manifest


def _write(root: Path, relative: str, value: object) -> str:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _manifest(root: Path) -> dict:
    files = {}
    for name, value in {
        "codebook.json": {"revision": "a" * 40, "status": "approved"},
        "packet-a.json": {"role": "annotator_a", "units": [{"unit_id": "u1"}]},
        "packet-b.json": {"role": "annotator_b", "units": [{"unit_id": "u1"}]},
        "labels-a.json": {"role": "annotator_a", "labels": [{"unit_id": "u1"}]},
        "labels-b.json": {"role": "annotator_b", "records": [{"unit_id": "u1"}]},
        "adjudicated.json": {"adjudicator_id": "role-adjudicator", "units": [{"unit_id": "u1"}]},
    }.items():
        files[name] = _write(root, name, value)
    return {
        "schema_version": "foi-o.au-cth-calibration-evidence.v0.1.0",
        "status": "calibration_only",
        "source_population_sha256": "b" * 64,
        "codebook": {
            "path": "codebook.json",
            "sha256": files["codebook.json"],
            "revision": "a" * 40,
        },
        "packets": [
            {"role": "annotator_a", "path": "packet-a.json", "sha256": files["packet-a.json"]},
            {"role": "annotator_b", "path": "packet-b.json", "sha256": files["packet-b.json"]},
        ],
        "annotations": [
            {"role": "annotator_a", "path": "labels-a.json", "sha256": files["labels-a.json"]},
            {"role": "annotator_b", "path": "labels-b.json", "sha256": files["labels-b.json"]},
        ],
        "adjudication": {
            "path": "adjudicated.json",
            "sha256": files["adjudicated.json"],
            "role": "adjudicator",
        },
        "unit_ids": ["u1"],
    }


def test_valid_calibration_manifest(tmp_path: Path) -> None:
    manifest = _manifest(tmp_path)
    assert validate_manifest(manifest, tmp_path) == []


def test_rejects_ephemeral_path_and_synthetic_revision(tmp_path: Path) -> None:
    manifest = _manifest(tmp_path)
    manifest["codebook"]["path"] = "/tmp/codebook.json"
    manifest["codebook"]["revision"] = "3642e28" + "0" * 33
    errors = validate_manifest(manifest, tmp_path)
    assert any("relative" in error or "ephemeral" in error for error in errors)
    assert any("synthetic" in error for error in errors)


def test_rejects_role_collision_and_unit_mismatch(tmp_path: Path) -> None:
    manifest = _manifest(tmp_path)
    manifest["annotations"][1]["role"] = "annotator_a"
    manifest["unit_ids"] = ["u1", "u2"]
    errors = validate_manifest(manifest, tmp_path)
    assert any("distinct" in error for error in errors)
    assert any("unit" in error for error in errors)

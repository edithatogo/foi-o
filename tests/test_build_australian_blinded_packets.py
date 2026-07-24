"""Tests for the fail-closed authentic AU packet builder."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from scripts.build_australian_blinded_packets import build_packets


def _write_inputs(tmp_path: Path, *, leak_candidate: bool = False) -> tuple[Path, Path]:
    codebook = tmp_path / "codebook.json"
    codebook.write_text(json.dumps({"status": "approved", "revision": "a" * 40}), encoding="utf-8")
    frame = tmp_path / "frame.json"
    unit = {
        "unit_id": "AU-CTH:1",
        "jurisdiction": "AU-CTH",
        "text": "Public source text",
        "unit_sha256": "b" * 64,
        "rights_eligible": True,
    }
    if leak_candidate:
        unit["candidate_label"] = "observed"
    frame.write_text(
        json.dumps(
            {
                "status": "frozen_authentic",
                "rights_eligible": True,
                "jurisdiction": "AU-CTH",
                "source_population_sha256": "c" * 64,
                "codebook_sha256": hashlib.sha256(codebook.read_bytes()).hexdigest(),
                "units": [unit],
            }
        ),
        encoding="utf-8",
    )
    return frame, codebook


def test_builder_emits_two_identical_blinded_unit_sets(tmp_path: Path) -> None:
    frame, codebook = _write_inputs(tmp_path)
    result = build_packets(frame, codebook, tmp_path / "a.json", tmp_path / "b.json")
    assert result == {"ok": True, "jurisdiction": "AU-CTH", "unit_count": 1, "seed": 20260721}
    first = json.loads((tmp_path / "a.json").read_text())
    second = json.loads((tmp_path / "b.json").read_text())
    assert first["units"] == second["units"]
    assert first["blinded_to_extractor_candidate"] is True
    assert "candidate_label" not in first["units"][0]


def test_builder_rejects_candidate_leak(tmp_path: Path) -> None:
    frame, codebook = _write_inputs(tmp_path, leak_candidate=True)
    with pytest.raises(ValueError, match="leaks extractor candidate"):
        build_packets(frame, codebook, tmp_path / "a.json", tmp_path / "b.json")


def test_builder_accepts_pending_codebook_only_with_matching_approval_wrapper(
    tmp_path: Path,
) -> None:
    frame, codebook = _write_inputs(tmp_path)
    codebook.write_text(
        json.dumps(
            {"status": "pending_human_approval", "codebook_id": "v0.2", "revision": "a" * 40}
        ),
        encoding="utf-8",
    )
    frame.write_text(
        json.dumps(
            {
                **json.loads(frame.read_text()),
                "codebook_sha256": hashlib.sha256(codebook.read_bytes()).hexdigest(),
            }
        ),
        encoding="utf-8",
    )
    approval = tmp_path / "approval.json"
    approval.write_text(
        json.dumps(
            {
                "status": "approved_for_fresh_holdout_use",
                "approved_artifact": {
                    "sha256": hashlib.sha256(codebook.read_bytes()).hexdigest(),
                    "codebook_id": "v0.2",
                },
            }
        ),
        encoding="utf-8",
    )
    result = build_packets(
        frame, codebook, tmp_path / "a.json", tmp_path / "b.json", approval_path=approval
    )
    assert result["ok"] is True

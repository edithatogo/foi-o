from __future__ import annotations

import hashlib
import json

import pytest

from foi_o_nz.australian_nsw_candidate_frame import (
    NSW_CANDIDATE_SHA256,
    validate_candidate_frame,
    validate_immutable_frame,
)


def _frame() -> dict[str, object]:
    units = [{"unit_id": f"AU-NSW:{index}", "text": None} for index in range(179)]
    frame: dict[str, object] = {
        "schema": "foi-o.au-nsw-restricted-candidate-frame.v1",
        "status": "candidate_frame_restricted_local_not_empirical",
        "candidate_jsonl_sha256": NSW_CANDIDATE_SHA256,
        "record_count": 179,
        "accessible_request_text_count": 0,
        "metadata_only_count": 179,
        "rights_eligible": False,
        "sampling_authorized": False,
        "annotation_authorized": False,
        "publication_authorized": False,
        "redistribution_authorized": False,
        "units": units,
    }
    frame["frame_sha256"] = hashlib.sha256(
        json.dumps(frame, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return frame


def test_restricted_candidate_frame_validates(tmp_path) -> None:
    path = tmp_path / "frame.json"
    path.write_text(json.dumps(_frame()), encoding="utf-8")
    assert validate_candidate_frame(path)["record_count"] == 179


def test_restricted_candidate_frame_rejects_sampling_authorization(tmp_path) -> None:
    frame = _frame()
    frame["sampling_authorized"] = True
    path = tmp_path / "frame.json"
    path.write_text(json.dumps(frame), encoding="utf-8")
    with pytest.raises(ValueError, match="unapproved boundary"):
        validate_candidate_frame(path)


def test_immutable_frame_requires_exactly_115_text_units(tmp_path) -> None:
    frame = _frame()
    frame["schema"] = "foi-o.au-nsw-immutable-empirical-frame.v1"
    frame["status"] = "immutable_restricted_local"
    frame["record_count"] = 115
    frame["rights_eligible"] = True
    frame["restricted_local"] = True
    frame["duplicate_cluster_count"] = 1
    frame["duplicate_clustering_rule"] = (
        "exact normalized retained request-text SHA-256; singleton clusters retained"
    )
    frame["duplicate_registry"] = {"clusters": {"text-sha256:test": ["AU-NSW:0"]}}
    frame.update({
        "training_authorized": False,
        "legal_certification_authorized": False,
        "profile_promotion_authorized": False,
    })
    frame["frame_sha256"] = hashlib.sha256(
        json.dumps(frame, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    path = tmp_path / "frame.json"
    path.write_text(json.dumps(frame), encoding="utf-8")
    with pytest.raises(ValueError, match="membership"):
        validate_immutable_frame(path)

from __future__ import annotations

from hashlib import sha256

import pytest

from foi_o_nz import australian_immutable_manifest as manifest


def _value() -> dict[str, object]:
    payload: dict[str, object] = {
        "schema": manifest.MANIFEST_SCHEMA,
        "status": "immutable_restricted_local",
        "population": {
            "record_count": 2082,
            "completion_additions": 0,
            "completion_no_capture_slugs": 858,
        },
        "approved_inputs": manifest.PINNED_INPUTS,
        "boundaries": {"restricted_local": True, "publication_authorized": False},
    }
    payload["manifest_sha256"] = sha256(manifest._canonical_bytes(payload)).hexdigest()
    return payload


def test_validates_a_restricted_local_manifest(tmp_path) -> None:
    path = tmp_path / "manifest.json"
    path.write_bytes(manifest._canonical_bytes(_value()))
    assert manifest.validate_manifest(path)["record_count"] == 2082


def test_rejects_manifest_with_changed_pin(tmp_path) -> None:
    value = _value()
    value["approved_inputs"] = {**manifest.PINNED_INPUTS, "source_cdx": "0" * 64}
    value["manifest_sha256"] = sha256(
        manifest._canonical_bytes(
            {key: item for key, item in value.items() if key != "manifest_sha256"}
        )
    ).hexdigest()
    path = tmp_path / "manifest.json"
    path.write_bytes(manifest._canonical_bytes(value))
    with pytest.raises(ValueError, match="input pins"):
        manifest.validate_manifest(path)


def test_rejects_manifest_with_downstream_authority(tmp_path) -> None:
    value = _value()
    value["boundaries"] = {"restricted_local": True, "annotation_authorized": True}
    value["manifest_sha256"] = sha256(
        manifest._canonical_bytes(
            {key: item for key, item in value.items() if key != "manifest_sha256"}
        )
    ).hexdigest()
    path = tmp_path / "manifest.json"
    path.write_bytes(manifest._canonical_bytes(value))
    with pytest.raises(ValueError, match="boundaries"):
        manifest.validate_manifest(path)

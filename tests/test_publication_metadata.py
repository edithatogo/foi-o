from __future__ import annotations

import json
from pathlib import Path

from foi_o_nz.dataset_metadata import (
    write_croissant_metadata,
    write_dataset_metadata,
    write_huggingface_dataset_card,
    write_repository_release_metadata,
)
from foi_o_nz.io import write_jsonl
from foi_o_nz.validation import validate_json_schema


REPOSITORY_URL = "https://github.com/edithatogo/foi-o"
RELEASE_EXAMPLE = Path("examples/repository-release-metadata.v0.9.0.json")
RELEASE_SCHEMA = Path("schemas/json/repository-release-metadata.schema.json")


def _artifact(tmp_path: Path) -> Path:
    path = tmp_path / "requests.jsonl"
    write_jsonl(
        path,
        [
            {
                "schema_version": "foi-o-nz.request-profile.v0.1.0",
                "request_id": "123",
                "title": "Example",
                "authority": "Example Ministry",
            }
        ],
    )
    return path


def test_publication_metadata_uses_current_repository_and_rights(tmp_path: Path) -> None:
    artifact = _artifact(tmp_path)
    metadata_path = tmp_path / "dataset-metadata.json"
    croissant_path = tmp_path / "croissant.json"
    card_path = tmp_path / "README.md"

    write_dataset_metadata([artifact], metadata_path, base_dir=tmp_path)
    write_croissant_metadata([artifact], croissant_path, base_dir=tmp_path)
    write_huggingface_dataset_card([artifact], card_path, base_dir=tmp_path)

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    croissant = json.loads(croissant_path.read_text(encoding="utf-8"))
    card = card_path.read_text(encoding="utf-8")

    assert metadata["homepage"] == REPOSITORY_URL
    assert REPOSITORY_URL in croissant["url"]
    assert "original rights" in metadata["license"]
    assert "original rights" in card
    assert "not an official agency record" in card
    assert croissant["foio:agentBoundary"] == (
        "process-support-only; no autonomous OIA decision certification"
    )
    assert croissant["foio:rightsNotice"].startswith("MIT applies")


def test_repository_release_metadata_example_validates_and_labels_external_targets() -> None:
    assert RELEASE_SCHEMA.exists()
    assert RELEASE_EXAMPLE.exists()

    schema_errors = validate_json_schema(RELEASE_EXAMPLE, RELEASE_SCHEMA).errors
    assert not schema_errors

    metadata = json.loads(RELEASE_EXAMPLE.read_text(encoding="utf-8"))
    assert metadata["repository"] == REPOSITORY_URL
    assert metadata["release_version"] == "0.9.0"
    assert "original rights" in metadata["rights_notice"]
    assert {item["status"] for item in metadata["publication_targets"]} <= {
        "manual_approval_required",
        "external_gate",
    }
    assert all(Path(item["path"]).exists() for item in metadata["artifacts"])


def test_repository_release_metadata_writer_references_existing_artifacts(tmp_path: Path) -> None:
    artifact = _artifact(tmp_path)
    output = tmp_path / "repository-release.json"

    result = write_repository_release_metadata(
        [artifact],
        output,
        base_dir=tmp_path,
        release_version="0.9.0",
    )

    assert result["artifact_count"] == 1
    metadata = json.loads(output.read_text(encoding="utf-8"))
    assert metadata["artifacts"][0]["path"] == "requests.jsonl"
    assert len(metadata["artifacts"][0]["sha256"]) == 64
    assert metadata["publication_targets"][0]["status"] == "manual_approval_required"

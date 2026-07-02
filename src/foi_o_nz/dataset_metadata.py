"""Dataset metadata generators for FOI-O NZ artifacts."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from foi_o_nz.constants import DATASET_METADATA_SCHEMA_VERSION
from foi_o_nz.io import write_json


class DatasetResource(BaseModel):
    """One resource in the generated dataset metadata."""

    model_config = ConfigDict(extra="forbid")

    name: str
    path: str
    media_type: str
    encoding: str | None = None
    sha256: str | None = None
    bytes: int | None = None
    description: str | None = None


class DatasetMetadata(BaseModel):
    """Minimal machine-readable metadata for repo/dataset publication."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["foi-o-nz.dataset-metadata.v0.1.0"] = DATASET_METADATA_SCHEMA_VERSION
    name: str
    title: str
    description: str
    license: str
    homepage: str | None = None
    resources: list[DatasetResource] = Field(default_factory=list)
    caveats: list[str] = Field(default_factory=list)


def _resource_for_path(path: Path, *, base_dir: Path) -> DatasetResource:
    media_type = "application/octet-stream"
    suffix = path.suffix.lower()
    if suffix == ".jsonl":
        media_type = "application/x-ndjson"
    elif suffix in {".json", ".jsonld"}:
        media_type = "application/json"
    elif suffix == ".parquet":
        media_type = "application/vnd.apache.parquet"
    elif suffix == ".ttl":
        media_type = "text/turtle"
    elif suffix == ".csv":
        media_type = "text/csv"
    data = path.read_bytes()
    return DatasetResource(
        name=path.stem,
        path=str(path.relative_to(base_dir) if path.is_relative_to(base_dir) else path),
        media_type=media_type,
        encoding="utf-8"
        if media_type.startswith("text/") or "json" in media_type or "ndjson" in media_type
        else None,
        sha256=sha256(data).hexdigest(),
        bytes=len(data),
    )


def build_dataset_metadata(
    paths: list[Path],
    *,
    base_dir: Path,
    name: str = "foi-o-nz-artifacts",
    title: str = "FOI-O NZ derived process artifacts",
) -> DatasetMetadata:
    """Build deterministic dataset metadata for selected local artifacts."""
    resources = [
        _resource_for_path(path, base_dir=base_dir)
        for path in paths
        if path.exists() and path.is_file()
    ]
    return DatasetMetadata(
        name=name,
        title=title,
        description="Machine-readable FOI-O NZ process artifacts generated from public FYI/OIA source records.",
        license="MIT for code/metadata; source records retain their original rights and platform terms.",
        homepage="https://github.com/edithatogo/foi-o-nz",
        resources=resources,
        caveats=[
            "Derived process metadata is not an official agency record.",
            "Agent-generated or inferred fields are not legal decisions.",
            "Coverage depends on the supplied source artifacts and must not be overclaimed.",
        ],
    )


def write_dataset_metadata(
    paths: list[Path], output: Path, *, base_dir: Path | None = None
) -> dict[str, Any]:
    """Write dataset metadata JSON and return a compact report."""
    base = base_dir or Path.cwd()
    metadata = build_dataset_metadata(paths, base_dir=base)
    write_json(output, metadata.model_dump(mode="json", exclude_none=True))
    return {"ok": True, "output": str(output), "resource_count": len(metadata.resources)}


def write_frictionless_datapackage(
    paths: list[Path], output: Path, *, base_dir: Path | None = None
) -> dict[str, Any]:
    """Write a small Frictionless-style datapackage descriptor."""
    base = base_dir or Path.cwd()
    metadata = build_dataset_metadata(paths, base_dir=base)
    package = {
        "profile": "data-package",
        "name": metadata.name,
        "title": metadata.title,
        "description": metadata.description,
        "licenses": [{"name": "MIT", "title": "MIT License"}],
        "resources": [
            {
                "name": resource.name,
                "path": resource.path,
                "mediatype": resource.media_type,
                "bytes": resource.bytes,
                "hash": resource.sha256,
            }
            for resource in metadata.resources
        ],
        "foi_o_nz_caveats": metadata.caveats,
    }
    write_json(output, package)
    return {"ok": True, "output": str(output), "resource_count": len(metadata.resources)}


def write_croissant_metadata(
    paths: list[Path], output: Path, *, base_dir: Path | None = None
) -> dict[str, Any]:
    """Write a lightweight Croissant-style JSON-LD dataset descriptor.

    This is dependency-free and intentionally conservative; full MLCommons
    validation can be added later through optional tooling.
    """
    base = base_dir or Path.cwd()
    metadata = build_dataset_metadata(paths, base_dir=base)
    croissant = {
        "@context": {
            "@vocab": "https://schema.org/",
            "cr": "http://mlcommons.org/croissant/",
            "dcat": "http://www.w3.org/ns/dcat#",
            "foio": "https://w3id.org/foio-nz/ontology#",
            "odrl": "http://www.w3.org/ns/odrl/2/",
        },
        "@type": ["Dataset", "foio:DatasetPublication"],
        "name": metadata.name,
        "description": metadata.description,
        "license": metadata.license,
        "url": metadata.homepage,
        "distribution": [
            {
                "@type": "cr:FileObject",
                "name": resource.name,
                "contentUrl": resource.path,
                "encodingFormat": resource.media_type,
                "sha256": resource.sha256,
                "contentSize": resource.bytes,
            }
            for resource in metadata.resources
        ],
        "foio:hasDistribution": [
            {
                "@type": "dcat:Distribution",
                "dcat:downloadURL": resource.path,
                "dcat:mediaType": resource.media_type,
                "foio:contentSha256": resource.sha256,
            }
            for resource in metadata.resources
        ],
        "foio:caveats": metadata.caveats,
        "foio:publicationCaveat": metadata.caveats,
        "foio:agentBoundary": "process-support-only; no autonomous OIA decision certification",
    }
    write_json(output, croissant)
    return {"ok": True, "output": str(output), "resource_count": len(metadata.resources)}


def write_huggingface_dataset_card(
    paths: list[Path], output: Path, *, base_dir: Path | None = None
) -> dict[str, Any]:
    """Write a concise Hugging Face dataset-card scaffold for derived artifacts."""
    base = base_dir or Path.cwd()
    metadata = build_dataset_metadata(paths, base_dir=base)
    rows = "\n".join(
        f"| `{resource.path}` | {resource.media_type} | `{resource.sha256}` |"
        for resource in metadata.resources
    )
    card = f"""---
license: mit
task_categories:
- text-classification
- feature-extraction
pretty_name: FOI-O NZ Derived Process Artifacts
tags:
- new-zealand
- official-information-act
- oia
- agents
- ontology
- process-mining
---

# {metadata.title}

{metadata.description}

This card describes derived FOI-O NZ process artifacts. It does not publish or
certify official agency decisions. Agent-generated, inferred, or asserted fields
must remain distinguishable from human-certified events.

## Resources

| Path | Media type | SHA-256 |
| --- | --- | --- |
{rows}

## Caveats

"""
    card += "\n".join(f"- {item}" for item in metadata.caveats)
    card += "\n"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(card, encoding="utf-8")
    return {"ok": True, "output": str(output), "resource_count": len(metadata.resources)}

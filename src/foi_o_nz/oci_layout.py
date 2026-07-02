"""OCI image-layout materialisation for FOI-O NZ artefact bundles.

This is a lightweight, dependency-free OCI layout writer intended for future
publishing experiments. It writes an OCI-like layout with artifact descriptors;
it does not push to a registry or sign artefacts.
"""

from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from shutil import copyfileobj
from typing import Any

from foi_o_nz.cas import digest_file, infer_media_type
from foi_o_nz.encoding import dumps_json
from foi_o_nz.io import write_json

OCI_LAYOUT_VERSION = "1.0.0"
FOIO_ARTIFACT_TYPE = "application/vnd.foi-o-nz.artifact.bundle.v0.1+json"


def _copy_blob(path: Path, blobs_dir: Path) -> tuple[str, int]:
    digest, size = digest_file(path)
    target = blobs_dir / "sha256" / digest
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        with path.open("rb") as src, target.open("wb") as dst:
            copyfileobj(src, dst)
    return digest, size


def _descriptor(
    path: Path, digest: str, size: int, *, base_dir: Path | None = None
) -> dict[str, Any]:
    label = (
        str(path.relative_to(base_dir))
        if base_dir is not None and path.is_relative_to(base_dir)
        else str(path)
    )
    return {
        "mediaType": infer_media_type(path),
        "digest": f"sha256:{digest}",
        "size": size,
        "annotations": {
            "org.opencontainers.image.title": label,
            "nz.foio.agent_boundary": "artifact_only_no_legal_decision",
        },
    }


def materialise_oci_layout(
    paths: list[Path], output_dir: Path, *, base_dir: Path | None = None
) -> dict[str, Any]:
    """Write selected artefacts into a local OCI image-layout directory."""
    output_dir.mkdir(parents=True, exist_ok=True)
    blobs_dir = output_dir / "blobs"
    manifests: list[dict[str, Any]] = []
    for path in sorted(paths, key=str):
        digest, size = _copy_blob(path, blobs_dir)
        manifests.append(_descriptor(path, digest, size, base_dir=base_dir))
    manifest_payload = {
        "schemaVersion": 2,
        "mediaType": FOIO_ARTIFACT_TYPE,
        "artifactType": FOIO_ARTIFACT_TYPE,
        "blobs": manifests,
        "annotations": {
            "org.opencontainers.image.created": datetime.now(UTC).isoformat(),
            "org.opencontainers.image.title": "foi-o-nz artefact bundle",
            "nz.foio.agent_boundary": "process-support-only",
        },
    }
    manifest_bytes = dumps_json(manifest_payload, pretty=False, sort_keys=True).encode("utf-8")
    manifest_digest = sha256(manifest_bytes).hexdigest()
    manifest_path = blobs_dir / "sha256" / manifest_digest
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_bytes(manifest_bytes)
    write_json(output_dir / "oci-layout", {"imageLayoutVersion": OCI_LAYOUT_VERSION})
    write_json(
        output_dir / "index.json",
        {
            "schemaVersion": 2,
            "manifests": [
                {
                    "mediaType": FOIO_ARTIFACT_TYPE,
                    "digest": f"sha256:{manifest_digest}",
                    "size": len(manifest_bytes),
                    "annotations": {"org.opencontainers.image.ref.name": "foi-o-nz-artifacts"},
                }
            ],
        },
    )
    return {
        "ok": True,
        "output_dir": str(output_dir),
        "artifact_count": len(manifests),
        "manifest_digest": manifest_digest,
        "limitations": [
            "Local OCI layout only; no registry push, signature, or remote retention guarantee."
        ],
    }

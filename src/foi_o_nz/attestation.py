"""Unsigned in-toto/SLSA-style attestations for generated artefacts."""

from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import Any

from foi_o_nz.io import write_json


def file_sha256(path: Path) -> str:
    """Return SHA-256 digest for a file."""
    digest = sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def build_attestation(
    paths: list[Path],
    *,
    builder_id: str = "foi-o-nz.local",
    build_type: str = "https://github.com/edithatogo/foi-o-nz/attestations/local-run/v0.1",
    invocation_id: str | None = None,
) -> dict[str, Any]:
    """Build an unsigned in-toto Statement v1 compatible provenance payload."""
    subjects = [
        {
            "name": str(path),
            "digest": {"sha256": file_sha256(path)},
            "size": path.stat().st_size,
        }
        for path in sorted(paths, key=str)
    ]
    generated_at = datetime.now(UTC).isoformat()
    return {
        "_type": "https://in-toto.io/Statement/v1",
        "subject": subjects,
        "predicateType": "https://slsa.dev/provenance/v1",
        "predicate": {
            "buildDefinition": {
                "buildType": build_type,
                "externalParameters": {
                    "invocation_id": invocation_id,
                    "artefact_count": len(subjects),
                },
                "internalParameters": {},
                "resolvedDependencies": [],
            },
            "runDetails": {
                "builder": {"id": builder_id},
                "metadata": {
                    "invocationId": invocation_id,
                    "startedOn": generated_at,
                    "finishedOn": generated_at,
                },
                "byproducts": [
                    {
                        "name": "foi-o-nz-boundary",
                        "digest": {
                            "sha256": sha256(b"no autonomous FOI/OIA decisions").hexdigest()
                        },
                    }
                ],
            },
        },
        "x_foio_nz": {
            "signed": False,
            "signing_note": "Unsigned local provenance statement. Sign with Sigstore/cosign or another DSSE workflow before relying on it across trust boundaries.",
            "agent_boundary": "process-support-only; no autonomous OIA decision certification",
        },
    }


def write_attestation(
    paths: list[Path],
    output: Path,
    *,
    builder_id: str = "foi-o-nz.local",
    invocation_id: str | None = None,
) -> dict[str, Any]:
    """Write an unsigned provenance attestation."""
    statement = build_attestation(paths, builder_id=builder_id, invocation_id=invocation_id)
    write_json(output, statement)
    return {"ok": True, "output": str(output), "subject_count": len(statement["subject"])}

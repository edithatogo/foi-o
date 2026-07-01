"""Run manifest and checksum helpers."""

from __future__ import annotations

import hashlib
import platform
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from foi_o_nz.version import __version__


def sha256_file(path: Path) -> str:
    """Return SHA-256 hex digest for a file."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_run_manifest(
    *,
    input_path: Path,
    outputs: list[Path],
    counts: dict[str, int],
    command: str,
) -> dict[str, Any]:
    """Build a deterministic-enough run manifest for provenance/audit."""
    output_records = []
    for path in outputs:
        if path.exists() and path.is_file():
            output_records.append(
                {
                    "path": str(path),
                    "bytes": path.stat().st_size,
                    "sha256": sha256_file(path),
                }
            )
    return {
        "schema_version": "foi-o-nz.run-manifest.v0.2.0",
        "created_at": datetime.now(UTC).isoformat(),
        "software": {"name": "foi-o-nz", "version": __version__},
        "command": command,
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
        },
        "input": {
            "path": str(input_path),
            "bytes": input_path.stat().st_size if input_path.exists() else None,
            "sha256": sha256_file(input_path) if input_path.exists() else None,
        },
        "outputs": output_records,
        "counts": counts,
    }

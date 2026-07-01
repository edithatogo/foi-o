"""Reproducibility manifests for local and CI runs."""

from __future__ import annotations

import platform
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from foi_o_nz.io import write_json
from foi_o_nz.ledger import sha256_text

REPRO_MANIFEST_SCHEMA_VERSION = "foi-o-nz.reproducibility.v0.1.0"


class FileDigest(BaseModel):
    """Digest metadata for one artefact."""

    model_config = ConfigDict(extra="forbid")

    path: str
    size_bytes: int = Field(ge=0)
    sha256: str


class ToolVersion(BaseModel):
    """Observed command-line tool availability and version output."""

    model_config = ConfigDict(extra="forbid")

    name: str
    available: bool
    executable: str | None = None
    version_output: str | None = None


class ReproducibilityManifest(BaseModel):
    """Machine-readable local build/run reproducibility manifest."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["foi-o-nz.reproducibility.v0.1.0"] = REPRO_MANIFEST_SCHEMA_VERSION
    generated_at: datetime
    python: dict[str, str]
    platform: dict[str, str]
    tools: list[ToolVersion]
    files: list[FileDigest]


def file_digest(path: Path, *, base_dir: Path | None = None) -> FileDigest:
    """Digest one file."""
    data = path.read_bytes()
    label = str(path.relative_to(base_dir)) if base_dir is not None and path.is_relative_to(base_dir) else str(path)
    return FileDigest(path=label, size_bytes=len(data), sha256=sha256_text(data.decode("utf-8", errors="surrogateescape")))


def binary_file_digest(path: Path, *, base_dir: Path | None = None) -> FileDigest:
    """Digest one file without assuming UTF-8 semantics."""
    import hashlib

    data = path.read_bytes()
    label = str(path.relative_to(base_dir)) if base_dir is not None and path.is_relative_to(base_dir) else str(path)
    return FileDigest(path=label, size_bytes=len(data), sha256=hashlib.sha256(data).hexdigest())


def tool_version(name: str, *args: str) -> ToolVersion:
    """Capture best-effort tool version information."""
    executable = shutil.which(name)
    if executable is None:
        return ToolVersion(name=name, available=False)
    try:
        completed = subprocess.run(  # noqa: S603 - executable resolved with shutil.which
            [executable, *args],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
        output = (completed.stdout or completed.stderr).strip().splitlines()[0:3]
        version_output = "\n".join(output) if output else None
    except Exception as exc:  # noqa: BLE001 - best-effort environment capture
        version_output = f"version check failed: {exc}"
    return ToolVersion(name=name, available=True, executable=executable, version_output=version_output)


def build_reproducibility_manifest(paths: list[Path], *, base_dir: Path | None = None) -> ReproducibilityManifest:
    """Build a reproducibility manifest for selected artefacts."""
    files = [binary_file_digest(path, base_dir=base_dir) for path in sorted(paths) if path.is_file()]
    return ReproducibilityManifest(
        generated_at=datetime.now(UTC),
        python={"version": sys.version, "executable": sys.executable},
        platform={
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "python_implementation": platform.python_implementation(),
        },
        tools=[
            tool_version("uv", "--version"),
            tool_version("pixi", "--version"),
            tool_version("mojo", "--version"),
            tool_version("max", "--version"),
            tool_version("git", "--version"),
        ],
        files=files,
    )


def write_reproducibility_manifest(
    paths: list[Path],
    output_json: Path,
    *,
    base_dir: Path | None = None,
) -> dict[str, Any]:
    """Write a reproducibility manifest."""
    data = build_reproducibility_manifest(paths, base_dir=base_dir).model_dump(mode="json")
    write_json(output_json, data)
    return data

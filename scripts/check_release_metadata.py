"""Verify that release-facing version metadata is internally consistent."""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _version_from_toml(path: Path) -> str:
    match = re.search(r'^version\s*=\s*"([^"]+)"', path.read_text(encoding="utf-8"), re.MULTILINE)
    if match is None:
        raise ValueError(f"missing version in {path}")
    return match.group(1)


def _version_from_cff(path: Path) -> str:
    match = re.search(r'^version:\s*"([^"]+)"', path.read_text(encoding="utf-8"), re.MULTILINE)
    if match is None:
        raise ValueError(f"missing version in {path}")
    return match.group(1)


def _version_from_python(path: Path) -> str:
    match = re.search(
        r'^__version__\s*=\s*"([^"]+)"', path.read_text(encoding="utf-8"), re.MULTILINE
    )
    if match is None:
        raise ValueError(f"missing version in {path}")
    return match.group(1)


def main() -> int:
    """Validate all package and release metadata, optionally against a tag."""
    versions = {
        "pyproject": _version_from_toml(ROOT / "pyproject.toml"),
        "pixi": _version_from_toml(ROOT / "pixi.toml"),
        "citation": _version_from_cff(ROOT / "CITATION.cff"),
        "runtime": _version_from_python(ROOT / "src/foi_o_nz/version.py"),
    }
    if len(set(versions.values())) != 1:
        raise ValueError(f"release metadata diverges: {versions}")

    expected_tag = os.environ.get("EXPECTED_RELEASE_TAG")
    if expected_tag and expected_tag.removeprefix("v") != versions["pyproject"]:
        raise ValueError(f"release tag {expected_tag!r} does not match {versions['pyproject']!r}")

    openapi = (
        json.loads((ROOT / "data" / "smoke" / "openapi.json").read_text(encoding="utf-8"))
        if (ROOT / "data" / "smoke" / "openapi.json").exists()
        else None
    )
    if openapi is not None and openapi.get("info", {}).get("version") != versions["pyproject"]:
        raise ValueError("generated OpenAPI metadata does not match package version")

    print(f"release metadata consistent: {versions['pyproject']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

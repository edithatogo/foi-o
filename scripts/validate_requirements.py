"""Validate the canonical MoSCoW requirement registry."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

REQUIRED = {
    "id",
    "version",
    "title",
    "priority",
    "status",
    "source",
    "rationale",
    "owner_repo",
    "acceptance_evidence",
    "dependencies",
    "blockers",
    "risk",
    "release_target",
    "supersedes",
    "superseded_by",
    "change_log",
}
ALLOWED_PRIORITIES = {"must", "should", "could", "wont"}


def _repository_path(path: Path) -> Path:
    """Resolve a CLI path while keeping reads inside this repository."""

    repository_root = Path.cwd().resolve()
    resolved = path.resolve()
    if not resolved.is_relative_to(repository_root):
        raise ValueError(f"path must remain inside repository: {path}")
    if not resolved.is_file():
        raise ValueError(f"requirements file does not exist: {path}")
    return resolved


def validate(path: Path = Path("requirements.yaml")) -> dict[str, Any]:
    document = yaml.safe_load(_repository_path(path).read_text(encoding="utf-8"))
    requirements = document.get("requirements") if isinstance(document, dict) else None
    errors: list[str] = []
    ids: list[str] = []
    if not isinstance(requirements, list):
        errors.append("requirements must be a list")
        requirements = []
    for index, requirement in enumerate(requirements):
        if not isinstance(requirement, dict):
            errors.append(f"requirements[{index}] must be a mapping")
            continue
        identifier = str(requirement.get("id", index))
        ids.append(identifier)
        missing = sorted(REQUIRED - set(requirement))
        if missing:
            errors.append(f"{identifier}: missing {', '.join(missing)}")
        if requirement.get("priority") not in ALLOWED_PRIORITIES:
            errors.append(f"{identifier}: invalid priority")
    duplicates = sorted({identifier for identifier in ids if ids.count(identifier) > 1})
    errors.extend(f"duplicate requirement: {identifier}" for identifier in duplicates)
    return {"ok": not errors, "requirement_count": len(requirements), "errors": errors}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path, nargs="?", default=Path("requirements.yaml"))
    args = parser.parse_args()
    result = validate(args.path)
    print(json.dumps(result, indent=2))
    if not result["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

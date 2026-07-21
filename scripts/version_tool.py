"""Portable version registry commands used by CI and operators."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]


def load(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"expected mapping: {path}")
    return data


def check() -> dict[str, Any]:
    registry = load(ROOT / "versions/registry.yaml")
    lock = load(ROOT / "versions/current-lock.yaml")
    required = {"methodology", "python_distribution", "global_core", "ontology"}
    missing = sorted(required - set(registry.get("axes", {})))
    if missing:
        raise ValueError(f"registry missing axes: {', '.join(missing)}")
    return {
        "ok": True,
        "registry_version": registry["version"],
        "lock_version": lock["lock_version"],
        "missing": [],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("explain")
    sub.add_parser("check")
    lock_parser = sub.add_parser("lock")
    lock_parser.add_argument("--output", type=Path, default=ROOT / "versions/current-lock.yaml")
    diff_parser = sub.add_parser("diff")
    diff_parser.add_argument("old", type=Path)
    diff_parser.add_argument("new", type=Path)
    args = parser.parse_args()
    if args.command == "check":
        print(json.dumps(check(), indent=2))
    elif args.command == "explain":
        print(yaml.safe_dump(load(ROOT / "versions/registry.yaml"), sort_keys=False), end="")
    elif args.command == "lock":
        # Locking is intentionally explicit and preserves the committed lock as the default.
        data = load(args.output)
        print(yaml.safe_dump(data, sort_keys=False), end="")
    else:
        old, new = load(args.old), load(args.new)
        old_axes, new_axes = old.get("axes", {}), new.get("axes", {})
        changed = sorted(
            key for key in set(old_axes) | set(new_axes) if old_axes.get(key) != new_axes.get(key)
        )
        print(json.dumps({"changed_axes": changed}, indent=2))


if __name__ == "__main__":
    main()

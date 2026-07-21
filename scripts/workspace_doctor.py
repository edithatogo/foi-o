"""Read-only local workspace identity and dirty-state audit.

The doctor never fetches, pulls, clones, edits, or deletes repositories. It is
safe to run from a dirty workspace and emits JSON suitable for a lock review.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

REPOSITORIES = {
    "foi-o": "https://github.com/edithatogo/foi-o",
    "rac-conformance": "https://github.com/edithatogo/rac-conformance",
    "fyi-cli": "https://github.com/edithatogo/fyi-cli",
    "fyi-archive": "https://github.com/edithatogo/fyi-archive",
    "foi-process": "https://github.com/edithatogo/foi-process",
    "legislation": "https://github.com/edithatogo/legislation",
    "nlp-policy-nz": "https://github.com/edithatogo/nlp-policy-nz",
    "rulespec-nz": "https://github.com/edithatogo/rulespec-nz",
    "sourceright": "https://github.com/edithatogo/sourceright",
    "authentext": "https://github.com/edithatogo/authentext",
}


def _git(path: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(path), *args],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return result.stdout.strip()


def _normalise_remote(remote: str | None) -> str | None:
    if remote is None:
        return None
    value = remote.removesuffix(".git")
    return value.removesuffix("/")


def audit(root: Path) -> dict[str, Any]:
    """Audit only bounded child directories and the selected root."""
    candidates = list(
        dict.fromkeys([root, *sorted(p for p in root.parent.iterdir() if p.is_dir())])
    )
    found: dict[str, list[dict[str, Any]]] = {name: [] for name in REPOSITORIES}
    for candidate in candidates:
        remote = _normalise_remote(_git(candidate, "remote", "get-url", "origin"))
        if remote is None:
            continue
        for name, expected in REPOSITORIES.items():
            if remote == expected:
                found[name].append(
                    {
                        "path": str(candidate),
                        "remote": remote,
                        "commit": _git(candidate, "rev-parse", "HEAD"),
                        "branch": _git(candidate, "branch", "--show-current"),
                        "dirty": bool(_git(candidate, "status", "--porcelain")),
                        "upstream": _git(candidate, "rev-parse", "--abbrev-ref", "@{upstream}"),
                    }
                )
    duplicates = {name: entries for name, entries in found.items() if len(entries) > 1}
    return {"root": str(root), "repositories": found, "duplicate_remote_identities": duplicates}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    print(json.dumps(audit(args.root.resolve()), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

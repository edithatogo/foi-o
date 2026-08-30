#!/usr/bin/env python3
"""Check pixi.toml and pyproject.toml environments do not drift apart.

Fails when:
- the pixi-managed Python spec is incompatible with pyproject ``requires-python``;
- a dependency declared in a pyproject extra is missing from pixi's dependencies.
Historical evidence and governed files are read-only here: this check never
mutates either manifest.
"""

from __future__ import annotations

import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE_PYPI_DEPS = {
    "pydantic",
    "pydantic-settings",
    "jsonschema",
    "pyyaml",
    "rdflib",
    "typer",
    "rich",
    "loguru",
    "orjson",
    "msgspec",
    "defusedxml",
    "polars",
    "pyarrow",
    "duckdb",
    "lancedb",
    "narwhals",
    "pyshacl",
}
ADVISORY_ONLY_EXTRAS = {"experiments"}  # not installed in the pixi environment


def main() -> int:
    failures: list[str] = []
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text())
    pixi = tomllib.loads((ROOT / "pixi.toml").read_text())

    requires_python = pyproject["project"]["requires-python"]
    pixi_deps = pixi.get("dependencies", {})
    pixi_python = pixi_deps.get("python")
    if not pixi_python:
        failures.append("pixi.toml does not pin a python dependency")
    else:
        # Both specs must accept a common interpreter; approximate by requiring
        # the pixi lower bound to match the pyproject lower bound.
        py_floor = requires_python.lstrip(">=").strip()
        pixi_floor = pixi_python.lstrip(">=").split(",")[0].strip()
        if py_floor != pixi_floor:
            failures.append(
                f"python floor drift: pyproject requires-python floor {py_floor} "
                f"vs pixi floor {pixi_floor}"
            )

    # pixi installs foi-o-nz editable with extras; every non-advisory extra in
    # pyproject must be covered there.
    pypi = pixi.get("pypi-dependencies", {}).get("foi-o-nz", {})
    pixi_extras = set(pypi.get("extras", []))
    project_extras = set(pyproject["project"].get("optional-dependencies", {}))
    missing_extras = {e for e in project_extras - ADVISORY_ONLY_EXTRAS if e not in pixi_extras}
    if missing_extras:
        failures.append(
            f"pyproject extras missing from pixi foi-o-nz install: {sorted(missing_extras)}"
        )

    if failures:
        for f in failures:
            print(f"ENV-PARITY-FAIL: {f}")
        return 1
    print("ENV-PARITY-OK: pixi.toml and pyproject.toml environments agree")
    return 0


if __name__ == "__main__":
    sys.exit(main())

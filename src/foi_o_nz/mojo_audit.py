"""Static Mojo-kernel audit utilities.

The sandbox and many CI environments may not have the Modular compiler
installed. This module gives the repo a dependency-light way to check whether
Mojo source files at least declare the deterministic kernel functions required
by the Python fallback contract. It does not replace native compilation, but it
makes the Mojo-first boundary inspectable before a Mojo toolchain is present.
"""

from __future__ import annotations

import re
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from foi_o_nz.constants import MOJO_AUDIT_SCHEMA_VERSION
from foi_o_nz.io import write_json
from foi_o_nz.kernel_fallback import conformance_cases

_FUNCTION_RE = re.compile(r"^\s*fn\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", re.MULTILINE)


@dataclass(frozen=True, slots=True)
class MojoFunctionDeclaration:
    """One statically discovered Mojo function declaration."""

    name: str
    path: str

    def model_dump(self) -> dict[str, str]:
        """Return JSON-serialisable data."""
        return asdict(self)


def expected_kernel_operations() -> list[str]:
    """Return sorted kernel operation names expected from conformance fixtures."""
    return sorted({operation for operation, _args, _expected in conformance_cases()})


def discover_mojo_functions(mojo_root: Path = Path("mojo")) -> list[MojoFunctionDeclaration]:
    """Statically discover public-looking Mojo functions under ``mojo_root``."""
    declarations: list[MojoFunctionDeclaration] = []
    if not mojo_root.exists():
        return declarations
    for path in sorted(mojo_root.rglob("*.mojo")):
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        for match in _FUNCTION_RE.finditer(text):
            name = match.group(1)
            if name == "main" or name.startswith("test_"):
                continue
            declarations.append(MojoFunctionDeclaration(name=name, path=str(path)))
    return declarations


def build_mojo_audit(mojo_root: Path = Path("mojo")) -> dict[str, Any]:
    """Build a static Mojo-kernel audit report."""
    expected = expected_kernel_operations()
    declarations = discover_mojo_functions(mojo_root)
    by_name: dict[str, list[str]] = {}
    for declaration in declarations:
        by_name.setdefault(declaration.name, []).append(declaration.path)
    declared_names = sorted(by_name)
    missing = sorted(set(expected) - set(declared_names))
    extra = sorted(set(declared_names) - set(expected))
    mojo_cli = shutil.which("mojo")
    return {
        "schema_version": MOJO_AUDIT_SCHEMA_VERSION,
        "ok": not missing,
        "mojo_root": str(mojo_root),
        "mojo_cli_available": mojo_cli is not None,
        "mojo_cli_path": mojo_cli,
        "expected_operation_count": len(expected),
        "declared_function_count": len(declared_names),
        "declared_expected_count": len(set(expected) & set(declared_names)),
        "missing_expected_operations": missing,
        "extra_declared_functions": extra,
        "expected_operations": expected,
        "declared_functions": [declaration.model_dump() for declaration in declarations],
        "notes": [
            "This is a static source audit, not native Mojo compilation.",
            "A passing static audit means every Python fallback conformance operation has a matching Mojo function declaration.",
            "Native parity still requires pixi run mojo-format-check, pixi run mojo-test, and pixi run mojo-build.",
        ],
    }


def write_mojo_audit(output: Path, *, mojo_root: Path = Path("mojo")) -> dict[str, Any]:
    """Write a static Mojo-kernel audit report."""
    report = build_mojo_audit(mojo_root)
    write_json(output, report)
    return report

"""Mojo-first kernel facade with Python fallback.

This module makes the architecture explicit: deterministic kernels should be
implemented natively in Mojo where the Modular toolchain or a compiled kernel
binary is available; otherwise the dependency-light Python fallback in
``kernel_fallback`` is used. The fallback is not a separate policy: it is the
reference compatibility contract for environments where Mojo/MAX are absent.
"""

from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal

from foi_o_nz.constants import KERNEL_CONFORMANCE_SCHEMA_VERSION, NATIVE_KERNEL_STATUS_SCHEMA_VERSION
from foi_o_nz.io import write_json
from foi_o_nz.kernel_fallback import KernelValue, conformance_cases, evaluate_operation

RuntimeKind = Literal["mojo-binary", "mojo-cli", "python-fallback"]


@dataclass(frozen=True, slots=True)
class KernelDiscovery:
    """Discovered kernel runtime state."""

    schema_version: str
    preferred_runtime: RuntimeKind
    mojo_binary: str | None
    mojo_cli: str | None
    max_cli: str | None
    pixi_cli: str | None
    python_executable: str
    platform: str
    notes: list[str]

    def model_dump(self) -> dict[str, Any]:
        """Return a JSON-serialisable representation."""
        return asdict(self)


def _candidate_binary_paths(project_root: Path | None = None) -> list[Path]:
    """Return candidate compiled kernel binary locations."""
    candidates: list[Path] = []
    env_path = os.environ.get("FOI_O_NZ_MOJO_KERNEL")
    if env_path:
        candidates.append(Path(env_path))
    root = project_root or Path.cwd()
    candidates.extend(
        [
            root / "build" / "foi-o-nz-mojo",
            root / "build" / "foi-o-nz-kernel",
            root / "dist" / "foi-o-nz-mojo",
        ]
    )
    which = shutil.which("foi-o-nz-mojo") or shutil.which("foi-o-nz-kernel")
    if which:
        candidates.append(Path(which))
    return candidates


def _existing_executable(path: Path) -> str | None:
    """Return path if it exists and appears executable enough for subprocess."""
    try:
        if path.exists() and path.is_file():
            return str(path)
    except OSError:
        return None
    return None


def discover_kernel(project_root: Path | None = None) -> KernelDiscovery:
    """Discover Mojo/MAX tooling and choose the preferred available runtime."""
    binary = next((candidate for candidate in (_existing_executable(p) for p in _candidate_binary_paths(project_root)) if candidate), None)
    mojo_cli = shutil.which("mojo")
    max_cli = shutil.which("max")
    pixi_cli = shutil.which("pixi")
    notes: list[str] = []
    if binary:
        preferred: RuntimeKind = "mojo-binary"
        notes.append("Compiled Mojo kernel binary found; Python will call it using the JSON operation protocol.")
    elif mojo_cli:
        preferred = "mojo-cli"
        notes.append("Mojo CLI found, but no compiled FOI-O kernel binary was found; Python fallback remains authoritative for CLI commands.")
    else:
        preferred = "python-fallback"
        notes.append("No Mojo runtime discovered; using dependency-light Python fallback semantics.")
    if max_cli:
        notes.append("MAX CLI detected; inference/serving integrations can be exercised separately from deterministic kernels.")
    else:
        notes.append("MAX CLI not detected; MAX integrations remain optional/deferred.")
    return KernelDiscovery(
        schema_version=NATIVE_KERNEL_STATUS_SCHEMA_VERSION,
        preferred_runtime=preferred,
        mojo_binary=binary,
        mojo_cli=mojo_cli,
        max_cli=max_cli,
        pixi_cli=pixi_cli,
        python_executable=sys.executable,
        platform=platform.platform(),
        notes=notes,
    )


def _call_mojo_binary(binary: str, operation: str, args: tuple[KernelValue, ...], *, timeout_seconds: float = 5.0) -> KernelValue:
    """Call a compiled Mojo kernel binary that implements the JSON operation protocol.

    The current repo includes the protocol contract and tests for the Python
    fallback. If a local Mojo binary has not yet implemented the protocol, this
    function raises and the caller may fall back to Python semantics.
    """
    payload = json.dumps({"operation": operation, "args": list(args)})
    completed = subprocess.run(  # noqa: S603 - binary path is explicit operator/tool discovery
        [binary, "--json"],
        input=payload,
        text=True,
        capture_output=True,
        timeout=timeout_seconds,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip() or f"kernel exited {completed.returncode}")
    try:
        data = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"kernel returned non-JSON output: {completed.stdout[:200]!r}") from exc
    if not data.get("ok", False):
        raise RuntimeError(str(data.get("error", "kernel operation failed")))
    return data.get("value")


def evaluate_kernel(
    operation: str,
    *args: KernelValue,
    prefer_native: bool = True,
    project_root: Path | None = None,
) -> dict[str, Any]:
    """Evaluate one deterministic kernel operation with Mojo preferred and Python fallback."""
    discovery = discover_kernel(project_root)
    fallback = evaluate_operation(operation, tuple(args))
    runtime_used: RuntimeKind = "python-fallback"
    value: KernelValue = fallback.value
    native_error: str | None = None
    if prefer_native and discovery.mojo_binary:
        try:
            value = _call_mojo_binary(discovery.mojo_binary, operation, tuple(args))
            runtime_used = "mojo-binary"
        except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
            native_error = str(exc)
            value = fallback.value
            runtime_used = "python-fallback"
    return {
        "ok": True,
        "operation": operation,
        "args": list(args),
        "value": value,
        "runtime_used": runtime_used,
        "preferred_runtime": discovery.preferred_runtime,
        "fallback_value": fallback.value,
        "native_error": native_error,
    }


def kernel_status(project_root: Path | None = None) -> dict[str, Any]:
    """Return the current native/fallback kernel status report."""
    discovery = discover_kernel(project_root)
    report = discovery.model_dump()
    report["fallback_available"] = True
    report["conformance_case_count"] = len(conformance_cases())
    report["operations"] = sorted({case[0] for case in conformance_cases()})
    return report


def write_kernel_status(output: Path, *, project_root: Path | None = None) -> dict[str, Any]:
    """Write the current kernel status report."""
    report = kernel_status(project_root)
    write_json(output, report)
    return report


def run_kernel_conformance(output: Path | None = None, *, project_root: Path | None = None) -> dict[str, Any]:
    """Run built-in parity/conformance cases through the kernel facade."""
    discovery = discover_kernel(project_root)
    cases: list[dict[str, Any]] = []
    failed = 0
    native_attempted = 0
    native_succeeded = 0
    for operation, args, expected in conformance_cases():
        result = evaluate_kernel(operation, *args, project_root=project_root)
        ok = result["value"] == expected and result["fallback_value"] == expected
        if result["runtime_used"] == "mojo-binary":
            native_attempted += 1
            native_succeeded += 1
        elif discovery.mojo_binary:
            native_attempted += 1
        if not ok:
            failed += 1
        cases.append(
            {
                "operation": operation,
                "args": list(args),
                "expected": expected,
                "value": result["value"],
                "fallback_value": result["fallback_value"],
                "runtime_used": result["runtime_used"],
                "native_error": result["native_error"],
                "ok": ok,
            }
        )
    report = {
        "schema_version": KERNEL_CONFORMANCE_SCHEMA_VERSION,
        "ok": failed == 0,
        "case_count": len(cases),
        "failed_count": failed,
        "native_attempted_count": native_attempted,
        "native_succeeded_count": native_succeeded,
        "preferred_runtime": discovery.preferred_runtime,
        "cases": cases,
        "notes": [
            "Conformance cases assert that the Python fallback matches the expected kernel contract.",
            "If a compiled Mojo binary is present, the facade also attempts native execution through the JSON operation protocol.",
        ],
    }
    if output is not None:
        write_json(output, report)
    return report

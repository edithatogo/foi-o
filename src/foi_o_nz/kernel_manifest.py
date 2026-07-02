"""Kernel manifest, fixture, and readiness exports.

These artefacts make the Mojo-first/Python-fallback boundary concrete. The
manifest documents every deterministic operation, the static Mojo declaration
that should implement it, and the conformance fixtures that keep native and
fallback semantics aligned.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from foi_o_nz.constants import KERNEL_MANIFEST_SCHEMA_VERSION, KERNEL_READINESS_SCHEMA_VERSION
from foi_o_nz.io import write_json, write_jsonl
from foi_o_nz.kernel_fallback import KernelValue, conformance_cases
from foi_o_nz.mojo_audit import build_mojo_audit
from foi_o_nz.native_kernel import kernel_status

CERTIFICATION_OPERATION_HINTS = (
    "certify",
    "certification",
    "dispositive",
    "human",
    "review",
    "safety",
    "replay",
)

REPO_LOCAL_KERNEL_VALIDATION_COMMANDS = [
    "uv run pytest -q tests/test_kernel_fallback_native.py",
    "uv run pytest -q tests/test_mojo_audit_kernel_manifest.py",
    "uv run python scripts/validate_examples.py",
]


def _case_id(index: int, operation: str) -> str:
    """Return a stable human-readable conformance case id."""
    return f"kernel-case-{index:04d}-{operation.replace('_', '-')}"


def _json_type(value: KernelValue) -> str:
    """Return a compact JSON-compatible type label."""
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    return "string"


def build_conformance_fixture_records() -> list[dict[str, Any]]:
    """Return JSONL-friendly conformance fixture records."""
    records: list[dict[str, Any]] = []
    for index, (operation, args, expected) in enumerate(conformance_cases(), start=1):
        records.append(
            {
                "case_id": _case_id(index, operation),
                "operation": operation,
                "args": list(args),
                "arg_types": [_json_type(value) for value in args],
                "expected": expected,
                "expected_type": _json_type(expected),
            }
        )
    return records


def build_kernel_manifest(*, mojo_root: Path = Path("mojo")) -> dict[str, Any]:
    """Build the deterministic kernel operation manifest."""
    audit = build_mojo_audit(mojo_root)
    status = kernel_status()
    declarations_by_name: dict[str, list[str]] = {}
    for declaration in audit["declared_functions"]:
        declarations_by_name.setdefault(declaration["name"], []).append(declaration["path"])
    records = build_conformance_fixture_records()
    by_operation: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        by_operation.setdefault(record["operation"], []).append(record)
    operations: list[dict[str, Any]] = []
    for operation in sorted(by_operation):
        first = by_operation[operation][0]
        operations.append(
            {
                "operation": operation,
                "arg_types": first["arg_types"],
                "return_type": first["expected_type"],
                "conformance_case_count": len(by_operation[operation]),
                "python_fallback": True,
                "mojo_declared": operation in declarations_by_name,
                "mojo_paths": sorted(declarations_by_name.get(operation, [])),
                "native_runtime_verified": False,
                "risk_class": "certification-boundary"
                if any(hint in operation for hint in CERTIFICATION_OPERATION_HINTS)
                else "deterministic-helper",
            }
        )
    return {
        "schema_version": KERNEL_MANIFEST_SCHEMA_VERSION,
        "generated_at": datetime.now(UTC).isoformat(),
        "preferred_runtime": status["preferred_runtime"],
        "fallback_available": True,
        "mojo_cli_available": status.get("mojo_cli") is not None,
        "max_cli_available": status.get("max_cli") is not None,
        "operation_count": len(operations),
        "conformance_case_count": len(records),
        "mojo_declared_operation_count": sum(
            1 for operation in operations if operation["mojo_declared"]
        ),
        "operations": operations,
        "notes": [
            "Python fallback is the executable reference contract in no-Mojo environments.",
            "Mojo declarations are statically audited; native compilation is verified separately by Pixi/CI.",
            "Decision-making and human-certification operations remain guardrail helpers only; they do not make legal decisions.",
        ],
    }


def write_kernel_manifest(output: Path, *, mojo_root: Path = Path("mojo")) -> dict[str, Any]:
    """Write the deterministic kernel manifest."""
    manifest = build_kernel_manifest(mojo_root=mojo_root)
    write_json(output, manifest)
    return manifest


def write_kernel_fixtures(output: Path) -> list[dict[str, Any]]:
    """Write kernel conformance fixtures as JSONL for native test harnesses."""
    records = build_conformance_fixture_records()
    write_jsonl(output, records)
    return records


def build_kernel_readiness(*, mojo_root: Path = Path("mojo")) -> dict[str, Any]:
    """Build a single readiness report for the Mojo-first kernel layer."""
    manifest = build_kernel_manifest(mojo_root=mojo_root)
    audit = build_mojo_audit(mojo_root)
    missing_count = len(audit["missing_expected_operations"])
    blocked: list[str] = []
    if not audit["mojo_cli_available"]:
        blocked.append("Modular Mojo CLI is not installed in this environment.")
    if missing_count:
        blocked.append("Some Python fallback operations do not yet have static Mojo declarations.")
    blocked.append(
        "Native runtime parity cannot be certified until Mojo tests and binary build run in a Modular environment."
    )
    return {
        "schema_version": KERNEL_READINESS_SCHEMA_VERSION,
        "ok_for_python_fallback": True,
        "ok_for_static_mojo_source": missing_count == 0,
        "ok_for_native_release": False,
        "preferred_runtime": manifest["preferred_runtime"],
        "operation_count": manifest["operation_count"],
        "conformance_case_count": manifest["conformance_case_count"],
        "mojo_declared_operation_count": manifest["mojo_declared_operation_count"],
        "missing_expected_operations": audit["missing_expected_operations"],
        "blocked_by": blocked,
        "repo_local_validation_commands": REPO_LOCAL_KERNEL_VALIDATION_COMMANDS,
        "next_external_checks": [
            "pixi run mojo-format-check",
            "pixi run mojo-test",
            "pixi run mojo-build",
            "PYTHONPATH=src python -m pytest -q",
        ],
        "notes": [
            "This readiness report is the strongest Mojo assessment possible without a Mojo compiler installed.",
            "A native release should require passing both the Python conformance suite and the native Mojo test/build tasks.",
        ],
    }


def write_kernel_readiness(output: Path, *, mojo_root: Path = Path("mojo")) -> dict[str, Any]:
    """Write the Mojo-kernel readiness report."""
    report = build_kernel_readiness(mojo_root=mojo_root)
    write_json(output, report)
    return report

#!/usr/bin/env python3
"""Seal one authorized, precomputed Australian empirical stage result."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from foi_o_nz.empirical_pipeline.contracts import (  # noqa: E402
    EmpiricalContractError,
    RunSpecification,
    canonical_bytes,
    content_sha256,
    seal_record,
    validate_stage_result,
)
from foi_o_nz.empirical_pipeline.execution import (  # noqa: E402
    ExecutionContextError,
    VerifiedExecutionContext,
    load_verified_execution_context,
)
from foi_o_nz.empirical_pipeline.maturity import (  # noqa: E402
    MaturityContractError,
    validate_maturity_candidate,
)

AUTH_FIELDS = {
    "schema_version",
    "status",
    "authorization_id",
    "authorizer_kind",
    "authorizer_identity",
    "approval_artifact_sha256",
    "run_id",
    "run_spec_sha256",
    "stage_id",
    "stage_spec_sha256",
    "capability",
    "input_sha256",
    "output_sha256",
    "calibration_sha256",
    "authorization_sha256",
}
CALIBRATION_FIELDS = {
    "schema_version",
    "status",
    "run_id",
    "run_spec_sha256",
    "stage_id",
    "stage_spec_sha256",
    "capability",
    "approval_artifact_sha256",
    "calibrator_identity",
    "calibration_sha256",
}
RESULT_FILENAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


class StageExecutionError(ValueError):
    """Raised when a stage cannot be sealed safely."""


def _json_object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise StageExecutionError(f"cannot read {label}: {path}") from exc
    if not isinstance(value, dict):
        raise StageExecutionError(f"{label} must be a JSON object")
    return value


def _require_committed_run_spec(path: Path) -> None:
    try:
        root = Path(
            subprocess.run(
                ["git", "-C", str(path.parent), "rev-parse", "--show-toplevel"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
        ).resolve()
        resolved = path.resolve()
        relative = resolved.relative_to(root)
        committed = subprocess.run(
            ["git", "-C", str(root), "show", f"HEAD:{relative.as_posix()}"],
            check=True,
            capture_output=True,
        ).stdout
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        raise StageExecutionError("run specification is not a committed HEAD artifact") from exc
    if resolved.read_bytes() != committed:
        raise StageExecutionError("run specification differs from its committed HEAD artifact")


def _file_hashes(paths: list[Path], label: str) -> list[str]:
    if not paths:
        raise StageExecutionError(f"at least one explicit {label} path is required")
    digests = []
    for path in paths:
        try:
            digests.append(hashlib.sha256(path.read_bytes()).hexdigest())
        except OSError as exc:
            raise StageExecutionError(f"cannot read {label}: {path}") from exc
    if len(set(digests)) != len(digests):
        raise StageExecutionError(f"duplicate {label} content is not permitted")
    return digests


def _stage(spec: RunSpecification, stage_id: str) -> dict[str, Any]:
    stages = spec.raw["stages"]
    sequences = sorted(stage["sequence"] for stage in stages)
    if sequences != list(range(1, len(stages) + 1)):
        raise StageExecutionError("stage order must be contiguous from sequence one")
    matches = [stage for stage in stages if stage["stage_id"] == stage_id]
    if len(matches) != 1:
        raise StageExecutionError("stage identity is absent or ambiguous")
    return matches[0]


def _stage_pin(stage: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_bytes(stage)).hexdigest()


def _require_registered_approval(spec: RunSpecification, prefix: str, digest: object) -> None:
    matches = [
        artifact
        for artifact in spec.raw.get("referenced_artifacts", [])
        if artifact.get("artifact_id", "").startswith(prefix) and artifact.get("sha256") == digest
    ]
    if len(matches) != 1:
        raise StageExecutionError(
            f"{prefix.rstrip(':')} approval artifact is not uniquely registered"
        )


def _validate_prior_results(
    paths: list[Path], spec: RunSpecification, current: dict[str, Any]
) -> None:
    expected = sorted(
        (stage for stage in spec.raw["stages"] if stage["sequence"] < current["sequence"]),
        key=lambda stage: stage["sequence"],
    )
    if len(paths) != len(expected):
        raise StageExecutionError("exactly one completed prior result is required in stage order")
    for path, stage in zip(paths, expected, strict=True):
        result = _json_object(path, "prior stage result")
        validate_stage_result(result, spec.raw)
        if result["stage_id"] != stage["stage_id"] or result["result_status"] != "completed":
            raise StageExecutionError("prior stage result is incomplete or out of order")


def _validate_authorization(
    path: Path,
    spec: RunSpecification,
    stage: dict[str, Any],
    capability: str,
    calibration: dict[str, Any] | None,
) -> dict[str, Any]:
    authorization = _json_object(path, "authorization")
    if set(authorization) != AUTH_FIELDS:
        raise StageExecutionError("authorization violates the strict field contract")
    if authorization["authorization_sha256"] != content_sha256(
        authorization, "authorization_sha256"
    ):
        raise StageExecutionError("authorization self-pin is invalid")
    if (
        authorization["schema_version"] != "foio.empirical-stage-authorization.v1.0.0"
        or authorization["status"] != "approved"
        or authorization["authorizer_kind"] != "external_human"
    ):
        raise StageExecutionError("authorization must be approved by an external human")
    identity = authorization["authorizer_identity"]
    if (
        not isinstance(identity, dict)
        or set(identity) != {"identity_id", "identity_kind"}
        or identity.get("identity_kind") != "external_human"
        or not isinstance(identity.get("identity_id"), str)
        or not identity["identity_id"]
    ):
        raise StageExecutionError("authorization requires an external-human identity")
    _require_registered_approval(spec, "authorization:", authorization["approval_artifact_sha256"])
    expected = {
        "run_id": spec.run_id,
        "run_spec_sha256": spec.run_spec_sha256,
        "stage_id": stage["stage_id"],
        "stage_spec_sha256": _stage_pin(stage),
        "capability": capability,
        "input_sha256": stage["input_sha256"],
        "output_sha256": stage["output_sha256"],
        "calibration_sha256": (
            calibration["calibration_sha256"] if calibration is not None else None
        ),
    }
    if any(authorization[key] != value for key, value in expected.items()):
        raise StageExecutionError("authorization is not bound to the exact stage execution")
    authorization_id = authorization["authorization_id"]
    if (
        not isinstance(authorization_id, str)
        or not authorization_id.startswith("authorization:external-human:")
        or authorization_id in {spec.run_id, stage["stage_id"]}
        or authorization["authorization_sha256"]
        in {*stage["input_sha256"], *stage["output_sha256"]}
    ):
        raise StageExecutionError("self-authorization is forbidden")
    return authorization


def _validate_calibration(
    path: Path | None,
    spec: RunSpecification,
    stage: dict[str, Any],
    capability: str,
) -> dict[str, Any] | None:
    governed = stage["stage_kind"] in {"packet", "annotation", "maturity"}
    if governed and path is None:
        raise StageExecutionError("passed calibration is required before packet or annotation")
    if path is None:
        return None
    calibration = _json_object(path, "calibration")
    if set(calibration) != CALIBRATION_FIELDS:
        raise StageExecutionError("calibration violates the strict field contract")
    if calibration["calibration_sha256"] != content_sha256(calibration, "calibration_sha256"):
        raise StageExecutionError("calibration self-pin is invalid")
    _require_registered_approval(spec, "calibration:", calibration["approval_artifact_sha256"])
    identity = calibration["calibrator_identity"]
    if (
        not isinstance(identity, dict)
        or set(identity) != {"identity_id", "identity_kind"}
        or identity.get("identity_kind") not in {"external_human", "automated_calibration_harness"}
        or not isinstance(identity.get("identity_id"), str)
        or not identity["identity_id"]
    ):
        raise StageExecutionError("calibration requires a distinct calibrator identity")
    expected = {
        "schema_version": "foio.empirical-stage-calibration.v1.0.0",
        "status": "passed",
        "run_id": spec.run_id,
        "run_spec_sha256": spec.run_spec_sha256,
        "stage_id": stage["stage_id"],
        "stage_spec_sha256": _stage_pin(stage),
        "capability": capability,
    }
    if any(calibration[key] != value for key, value in expected.items()):
        raise StageExecutionError("calibration is not passed and bound to the exact stage")
    return calibration


def _validate_maturity_outputs(
    paths: list[Path], stage: dict[str, Any], context: VerifiedExecutionContext
) -> None:
    if stage["stage_kind"] != "maturity":
        return
    if len(paths) != 1:
        raise StageExecutionError("exactly one maturity candidate output is required")
    for path in paths:
        output = _json_object(path, "maturity output")
        validate_maturity_candidate(output, context=context)


def _safe_result_path(path: Path, outputs: list[Path]) -> Path:
    """Confine a new result to an existing output directory and safe filename."""
    if not RESULT_FILENAME.fullmatch(path.name):
        raise StageExecutionError("result filename violates the safe filename contract")
    resolved = path.resolve(strict=False)
    allowed_parents = {output.resolve().parent for output in outputs}
    if resolved.parent not in allowed_parents:
        raise StageExecutionError("result path must share an exact output directory")
    if path.is_symlink() or resolved.exists():
        raise StageExecutionError("result path must be a new non-symlink artifact")
    return resolved


def _atomic_write(path: Path, value: dict[str, Any]) -> None:
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(canonical_bytes(value) + b"\n")
            handle.flush()
            os.fsync(handle.fileno())
        Path(temporary).replace(path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-spec", type=Path, required=True)
    parser.add_argument("--membership", type=Path, required=True)
    parser.add_argument("--units", type=Path, required=True)
    parser.add_argument("--codebook", type=Path, required=True)
    parser.add_argument("--stage-id", required=True)
    parser.add_argument("--capability", required=True)
    parser.add_argument("--input", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path, action="append", required=True)
    parser.add_argument("--authorization", type=Path, required=True)
    parser.add_argument("--calibration", type=Path, required=True)
    parser.add_argument("--prior-result", type=Path, action="append", default=[])
    parser.add_argument("--result", type=Path, required=True)
    return parser


def main() -> int:
    """Validate and seal one precomputed stage result."""
    args = _parser().parse_args()
    try:
        governed_paths = {
            args.run_spec.resolve(),
            args.authorization.resolve(),
            args.calibration.resolve(),
            args.membership.resolve(),
            args.units.resolve(),
            args.codebook.resolve(),
        }
        data_paths = {
            *(path.resolve() for path in args.input),
            *(path.resolve() for path in args.output),
            *(path.resolve() for path in args.prior_result),
        }
        expected_governed_count = 6
        if len(governed_paths) != expected_governed_count or governed_paths & data_paths:
            raise StageExecutionError("governance and empirical evidence paths must be distinct")
        context = load_verified_execution_context(
            run_spec_path=args.run_spec,
            membership_path=args.membership,
            units_path=args.units,
            codebook_path=args.codebook,
            calibration_path=args.calibration,
            authorization_path=args.authorization,
        )
        spec = context.run_spec
        stage = _stage(spec, args.stage_id)
        context.require_capability(stage["stage_kind"], args.capability)
        if args.capability not in context.authorization.get("capabilities", []):
            raise StageExecutionError("capability is not present in external authorization")
        _validate_prior_results(args.prior_result, spec, stage)
        _validate_maturity_outputs(args.output, stage, context)
        if _file_hashes(args.input, "input") != stage["input_sha256"]:
            raise StageExecutionError("input paths do not match exact stage pins")
        if stage["stage_kind"] != "maturity" and (
            _file_hashes(args.output, "output") != stage["output_sha256"]
        ):
            raise StageExecutionError("output paths do not match exact stage pins")
        protected = {
            args.run_spec.resolve(),
            args.authorization.resolve(),
            args.calibration.resolve(),
            args.membership.resolve(),
            args.units.resolve(),
            args.codebook.resolve(),
            *(path.resolve() for path in args.input),
            *(path.resolve() for path in args.output),
            *(path.resolve() for path in args.prior_result),
        }
        result_path = _safe_result_path(args.result, args.output)
        if result_path in protected:
            raise StageExecutionError("result path must not overwrite governed evidence")
        result = seal_record(
            {
                "schema_version": "foio.australian-empirical-stage-result.v1.0.0",
                "run_id": spec.run_id,
                "run_spec_sha256": spec.run_spec_sha256,
                "stage_id": stage["stage_id"],
                "stage_sequence": stage["sequence"],
                "stage_spec_sha256": _stage_pin(stage),
                "result_status": "completed",
                "input_sha256": stage["input_sha256"],
                "output_sha256": stage["output_sha256"],
                "population": stage["population"],
                "allowed_capabilities": stage["allowed_capabilities"],
                "denied_capabilities": stage["denied_capabilities"],
            },
            "stage_result_sha256",
        )
        validate_stage_result(result, spec.raw)
        _atomic_write(result_path, result)
    except (
        EmpiricalContractError,
        ExecutionContextError,
        MaturityContractError,
        StageExecutionError,
    ) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"valid": True, "stage_result_sha256": result["stage_result_sha256"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

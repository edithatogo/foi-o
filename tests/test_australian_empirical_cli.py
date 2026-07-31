from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

from empirical_context_fixture import ContextFixture, build_context_fixture
from test_empirical_pipeline_maturity import _lifecycle, _metrics

from foi_o_nz.empirical_pipeline.contracts import canonical_bytes, seal_record
from foi_o_nz.empirical_pipeline.maturity import build_maturity_candidate

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_australian_empirical_stage.py"


def _run(
    fixture: ContextFixture,
    tmp_path: Path,
    *,
    stage_id: str = "stage:packet",
    capability: str = "packet.generate",
    input_path: Path | None = None,
    output_path: Path | None = None,
    prior: list[Path] | None = None,
) -> subprocess.CompletedProcess[str]:
    kind = stage_id.split(":", 1)[1]
    input_path = input_path or (tmp_path / f"input-{kind}")
    output_path = output_path or (tmp_path / f"output-{kind}")
    if not input_path.exists():
        input_path.write_bytes(f"input:{kind}".encode())
    if not output_path.exists():
        output_path.write_bytes(f"output:{kind}".encode())
    result = tmp_path / f"result-{kind}.json"
    command = [
        sys.executable,
        str(SCRIPT),
        "--run-spec",
        str(fixture.paths["run_spec"]),
        "--membership",
        str(fixture.paths["membership"]),
        "--units",
        str(fixture.paths["units"]),
        "--codebook",
        str(fixture.paths["codebook"]),
        "--stage-id",
        stage_id,
        "--capability",
        capability,
        "--input",
        str(input_path),
        "--output",
        str(output_path),
        "--authorization",
        str(fixture.paths["authorization"]),
        "--calibration",
        str(fixture.paths["calibration"]),
        "--result",
        str(result),
    ]
    for path in prior or []:
        command.extend(["--prior-result", str(path)])
    return subprocess.run(command, capture_output=True, text=True, check=False)


def _prior_results(fixture: ContextFixture, tmp_path: Path, before_sequence: int) -> list[Path]:
    paths = []
    for stage in fixture.spec["stages"]:
        if stage["sequence"] >= before_sequence:
            continue
        result = seal_record(
            {
                "schema_version": "foio.australian-empirical-stage-result.v1.0.0",
                "run_id": fixture.spec["run_id"],
                "run_spec_sha256": fixture.spec["run_spec_sha256"],
                "stage_id": stage["stage_id"],
                "stage_sequence": stage["sequence"],
                "stage_spec_sha256": hashlib.sha256(canonical_bytes(stage)).hexdigest(),
                "result_status": "completed",
                "input_sha256": stage["input_sha256"],
                "output_sha256": stage["output_sha256"],
                "population": stage["population"],
                "allowed_capabilities": stage["allowed_capabilities"],
                "denied_capabilities": stage["denied_capabilities"],
            },
            "stage_result_sha256",
        )
        path = tmp_path / f"prior-{stage['sequence']}.json"
        path.write_bytes(canonical_bytes(result))
        paths.append(path)
    return paths


def test_cli_requires_and_uses_verified_execution_context(tmp_path: Path) -> None:
    fixture = build_context_fixture(tmp_path / "fixture")
    completed = _run(fixture, tmp_path)
    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["valid"] is True


def test_cli_rejects_uncommitted_run_spec(tmp_path: Path) -> None:
    fixture = build_context_fixture(tmp_path / "fixture")
    fixture.paths["run_spec"].write_text(fixture.paths["run_spec"].read_text() + "\n")
    completed = _run(fixture, tmp_path)
    assert completed.returncode == 2
    assert "committed HEAD" in completed.stderr


def test_cli_rejects_resealed_authority_substitution(tmp_path: Path) -> None:
    fixture = build_context_fixture(tmp_path / "fixture")
    authorization = json.loads(fixture.paths["authorization"].read_text())
    authorization["approved_roles"][0] = "role:invented"
    authorization = seal_record(authorization, "authorization_sha256")
    fixture.paths["authorization"].write_bytes(canonical_bytes(authorization))
    completed = _run(fixture, tmp_path)
    assert completed.returncode == 2
    assert "authority" in completed.stderr or "roles" in completed.stderr


def test_cli_accepts_complete_maturity_candidate_and_rejects_placeholder(
    tmp_path: Path,
) -> None:
    fixture, reliability, extractor = _metrics(tmp_path / "metrics")
    candidate = build_maturity_candidate(
        context=fixture.context,
        reliability=reliability,
        extractor_metrics=extractor,
        thresholds=[],
        evidence_lifecycle=_lifecycle(reliability, extractor),
    )
    candidate_path = tmp_path / "candidate.json"
    candidate_path.write_bytes(canonical_bytes(candidate))
    prior = _prior_results(fixture, tmp_path, before_sequence=5)
    completed = _run(
        fixture,
        tmp_path,
        stage_id="stage:maturity",
        capability="maturity.compare_thresholds",
        output_path=candidate_path,
        prior=prior,
    )
    assert completed.returncode == 0, completed.stderr

    placeholder = seal_record(
        {
            "schema_version": "foio.australian-maturity-decision-candidate.v1.0.0",
            "status": "pending_human_decision",
        },
        "candidate_sha256",
    )
    candidate_path.write_bytes(canonical_bytes(placeholder))
    rejected = _run(
        fixture,
        tmp_path,
        stage_id="stage:maturity",
        capability="maturity.compare_thresholds",
        output_path=candidate_path,
        prior=prior,
    )
    assert rejected.returncode == 2
    assert "schema validation" in rejected.stderr

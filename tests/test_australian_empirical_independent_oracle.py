from __future__ import annotations

import json
import runpy
import subprocess
import sys
from pathlib import Path

import pytest
from empirical_context_fixture import ContextFixture, build_context_fixture
from test_australian_empirical_cli import _prior_results, _run
from test_empirical_pipeline_maturity import _lifecycle, _metrics

from foi_o_nz.empirical_pipeline.contracts import canonical_bytes, seal_record
from foi_o_nz.empirical_pipeline.maturity import build_maturity_candidate

ROOT = Path(__file__).resolve().parents[1]
ORACLE = ROOT / "scripts" / "verify_australian_empirical_run.py"


def _oracle(fixture: ContextFixture, tmp_path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(ORACLE),
            "--run-spec",
            str(fixture.paths["run_spec"]),
            "--membership",
            str(fixture.paths["membership"]),
            "--units",
            str(fixture.paths["units"]),
            "--codebook",
            str(fixture.paths["codebook"]),
            "--stage-result",
            str(tmp_path / "result-packet.json"),
            "--capability",
            "packet.generate",
            "--input",
            str(tmp_path / "input-packet"),
            "--output",
            str(tmp_path / "output-packet"),
            "--authorization",
            str(fixture.paths["authorization"]),
            "--calibration",
            str(fixture.paths["calibration"]),
        ],
        capture_output=True,
        text=True,
        check=False,
    )


def _produced(tmp_path: Path):
    fixture = build_context_fixture(tmp_path / "fixture")
    produced = _run(fixture, tmp_path)
    assert produced.returncode == 0, produced.stderr
    return fixture


def test_oracle_is_independent_and_accepts_verified_producer_result(tmp_path: Path) -> None:
    fixture = _produced(tmp_path)
    completed = _oracle(fixture, tmp_path)
    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout)["valid"] is True
    assert "foi_o_nz.empirical_pipeline" not in ORACLE.read_text()


def test_oracle_rejects_authority_substitution(tmp_path: Path) -> None:
    fixture = _produced(tmp_path)
    authorization = json.loads(fixture.paths["authorization"].read_text())
    authorization["approved_roles"][0] = "role:invented"
    fixture.paths["authorization"].write_bytes(
        canonical_bytes(seal_record(authorization, "authorization_sha256"))
    )
    completed = _oracle(fixture, tmp_path)
    assert completed.returncode == 2
    assert "authority" in completed.stderr or "roles" in completed.stderr


def test_oracle_rejects_source_content_substitution(tmp_path: Path) -> None:
    fixture = _produced(tmp_path)
    bundle = json.loads(fixture.paths["units"].read_text())
    bundle["units"][0]["text"] = "substituted"
    fixture.paths["units"].write_bytes(canonical_bytes(bundle))
    completed = _oracle(fixture, tmp_path)
    assert completed.returncode == 2
    assert "content hash" in completed.stderr


def test_oracle_independently_rejects_self_and_overlapping_relationships(
    tmp_path: Path,
) -> None:
    fixture = _produced(tmp_path)
    repository = fixture.paths["run_spec"].parents[2]
    for relationships in (
        {"supersedes": ["run:au-test"], "invalidates": []},
        {"supersedes": ["run:au-prior"], "invalidates": ["run:au-prior"]},
    ):
        spec = json.loads(fixture.paths["run_spec"].read_text())
        spec["relationships"] = relationships
        spec = seal_record(spec, "run_spec_sha256")
        fixture.paths["run_spec"].write_bytes(canonical_bytes(spec))
        subprocess.run(["git", "-C", str(repository), "add", "."], check=True)
        subprocess.run(
            [
                "git",
                "-C",
                str(repository),
                "-c",
                "user.name=Test",
                "-c",
                "user.email=test@example.invalid",
                "commit",
                "-qm",
                "relationship mutation",
            ],
            check=True,
        )
        result_path = tmp_path / "result-packet.json"
        result = json.loads(result_path.read_text())
        result["run_spec_sha256"] = spec["run_spec_sha256"]
        result = seal_record(result, "stage_result_sha256")
        result_path.write_bytes(canonical_bytes(result))
        completed = _oracle(fixture, tmp_path)
        assert completed.returncode == 2
        assert "relationship" in completed.stderr


def test_oracle_rejects_resealed_stage_result_lineage(tmp_path: Path) -> None:
    fixture = _produced(tmp_path)
    result_path = tmp_path / "result-packet.json"
    result = json.loads(result_path.read_text())
    result["population"]["included"] = 2
    result = seal_record(result, "stage_result_sha256")
    result_path.write_bytes(canonical_bytes(result))
    completed = _oracle(fixture, tmp_path)
    assert completed.returncode == 2
    assert "population" in completed.stderr


def test_oracle_independently_rejects_resealed_metric_artifact(tmp_path: Path) -> None:
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
    produced = _run(
        fixture,
        tmp_path,
        stage_id="stage:maturity",
        capability="maturity.compare_thresholds",
        output_path=candidate_path,
        prior=prior,
    )
    assert produced.returncode == 0, produced.stderr

    original_reliability_sha = candidate["reliability_sha256"]
    forged = dict(candidate["source_metrics"]["reliability"])
    forged["raw_label_agreement"]["estimate"] = 1.0
    forged = seal_record(forged, "reliability_sha256")
    candidate["source_metrics"]["reliability"] = forged
    candidate["reliability_sha256"] = forged["reliability_sha256"]
    for row in candidate["evidence_lifecycle"]:
        if row["artifact_sha256"] == original_reliability_sha:
            row["artifact_sha256"] = forged["reliability_sha256"]
    candidate = seal_record(candidate, "candidate_sha256")
    candidate_path.write_bytes(canonical_bytes(candidate))

    completed = subprocess.run(
        [
            sys.executable,
            str(ORACLE),
            "--run-spec",
            str(fixture.paths["run_spec"]),
            "--membership",
            str(fixture.paths["membership"]),
            "--units",
            str(fixture.paths["units"]),
            "--codebook",
            str(fixture.paths["codebook"]),
            "--stage-result",
            str(tmp_path / "result-maturity.json"),
            "--capability",
            "maturity.compare_thresholds",
            "--input",
            str(tmp_path / "input-maturity"),
            "--output",
            str(candidate_path),
            "--authorization",
            str(fixture.paths["authorization"]),
            "--calibration",
            str(fixture.paths["calibration"]),
            *(argument for path in prior for argument in ("--prior-result", str(path))),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 2
    assert "metric estimate" in completed.stderr


def test_oracle_rejects_duplicate_metric_annotation_roles(tmp_path: Path) -> None:
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
    produced = _run(
        fixture,
        tmp_path,
        stage_id="stage:maturity",
        capability="maturity.compare_thresholds",
        output_path=candidate_path,
        prior=prior,
    )
    assert produced.returncode == 0, produced.stderr

    original = candidate["reliability_sha256"]
    forged = dict(candidate["source_metrics"]["reliability"])
    forged["annotation_lineage"] = [dict(row) for row in forged["annotation_lineage"]]
    forged["annotation_lineage"][1]["role_id"] = forged["annotation_lineage"][0]["role_id"]
    forged = seal_record(forged, "reliability_sha256")
    candidate["source_metrics"]["reliability"] = forged
    candidate["reliability_sha256"] = forged["reliability_sha256"]
    for row in candidate["evidence_lifecycle"]:
        if row["artifact_sha256"] == original:
            row["artifact_sha256"] = forged["reliability_sha256"]
    candidate = seal_record(candidate, "candidate_sha256")
    candidate_path.write_bytes(canonical_bytes(candidate))

    completed = subprocess.run(
        [
            sys.executable,
            str(ORACLE),
            "--run-spec",
            str(fixture.paths["run_spec"]),
            "--membership",
            str(fixture.paths["membership"]),
            "--units",
            str(fixture.paths["units"]),
            "--codebook",
            str(fixture.paths["codebook"]),
            "--stage-result",
            str(tmp_path / "result-maturity.json"),
            "--capability",
            "maturity.compare_thresholds",
            "--input",
            str(tmp_path / "input-maturity"),
            "--output",
            str(candidate_path),
            "--authorization",
            str(fixture.paths["authorization"]),
            "--calibration",
            str(fixture.paths["calibration"]),
            *(argument for path in prior for argument in ("--prior-result", str(path))),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 2
    assert "lineage" in completed.stderr or "role" in completed.stderr


@pytest.mark.parametrize("mutation", ["duplicate_role", "bootstrap_counts"])
def test_oracle_directly_mirrors_producer_metric_invariants(tmp_path: Path, mutation: str) -> None:
    _, reliability, _ = _metrics(tmp_path / "metrics")
    if mutation == "duplicate_role":
        reliability["annotation_lineage"][1]["role_id"] = reliability["annotation_lineage"][0][
            "role_id"
        ]
    else:
        reliability["cohen_kappa"]["bootstrap_replicates_valid"] -= 1
        reliability["cohen_kappa"]["bootstrap_replicates_undefined"] += 1
    reliability = seal_record(reliability, "reliability_sha256")
    oracle = runpy.run_path(str(ORACLE), run_name="foio_oracle_test")
    with pytest.raises(oracle["OracleError"], match=r"lineage|bootstrap"):
        oracle["_maturity_artifact"](reliability, "reliability_sha256", "reliability")

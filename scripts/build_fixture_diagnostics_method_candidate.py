"""Build and verify the inert fixture-diagnostics method candidate."""

from __future__ import annotations

import json
import platform
import random
from hashlib import sha256
from pathlib import Path
from subprocess import run
from typing import Any, cast

from jsonschema import Draft202012Validator

RECONCILIATION_PATH = "examples/v2/analyst-fixture-packet/results/reconciliation-set.locked.json"
RECONCILIATION_SHA256 = "09e2f7ad14298dac824acc21fac9bad6cfa5a6dfa62b9c2b7cd7ff870e183102"
RECONCILIATION_COMMIT = "6dcf482cdee5865bfc35813d648a13de5ac32866"
OUTPUT_PATH = "examples/v2/analyst-fixture-packet/diagnostics-method-candidate.pending.json"
SCHEMA_PATH = "schemas/json/fixture-diagnostics-method-candidate.schema.json"
PROHIBITED = [
    "bootstrap_execution",
    "diagnostics_finalization",
    "redistribution",
    "publication",
    "training",
    "fine_tuning",
    "release",
    "dataset_publication",
    "gold_promotion",
    "legal_certification",
    "paper_update",
    "human_reviewed_claims",
    "empirical_evidence_claims",
]
INPUTS: dict[str, tuple[str, str] | list[tuple[str, str]]] = {
    "analysis_lock": (
        "examples/v2/analyst-fixture-packet/results/analysis-lock.locked.json",
        "79faff0d554df7baff3e9f052dbc7f3a55d3e0e09baec95ab020fb3c4c002d1c",
    ),
    "ordered_analysis_sets": [
        (
            "examples/v2/analyst-fixture-packet/results/analysis-set.analyst-a.locked.json",
            "d22f72d91ade4a4a5992ba50ba54afa1586203a23d394f256066ef23b4b6c400",
        ),
        (
            "examples/v2/analyst-fixture-packet/results/analysis-set.analyst-b.locked.json",
            "ff72a35f840c97f26b07108c963574d664359b260719ad0dfc7c2986c0d665dd",
        ),
    ],
    "context_presentation": (
        "examples/v2/analyst-fixture-packet/context-presentation.pending.json",
        "72b75eb688541a712a62bea2569fb84353930c089ebaf8fc1082128aa3ef0e63",
    ),
    "codebook": (
        "examples/v2/analyst-fixture-packet/codebook.approved.json",
        "d918f1b705debcd6d8a14c078d7d0044e23c10615c9a7c27e4122d03088bbfdc",
    ),
    "sampling_configuration": (
        "examples/v2/analyst-fixture-packet/sampling-configuration.approved.json",
        "1a88278bff5d2d682ae56d119d7ed25b899a60214e71067e37f178052f4bfbc8",
    ),
    "cluster_registry": (
        "examples/v2/analyst-fixture-packet/cluster-registry.json",
        "4aef78cbad8a243a450de5c7f2fad1b21912bc4a26f1576375d1b163ad8cd14e",
    ),
    "unit_manifest": (
        "examples/v2/analyst-fixture-packet/unit-manifest.json",
        "a847c4f131ddcaaf8151d13c767859e8269bd1cca14ada20cf220d7c755ccddf",
    ),
}


def _strict_load(path: Path) -> dict[str, Any]:
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in items:
            if key in result:
                raise ValueError(f"{path.name}: duplicate JSON key {key}")
            result[key] = value
        return result

    value = json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=pairs,
        parse_constant=lambda token: (_ for _ in ()).throw(ValueError(f"non-finite {token}")),
    )
    if not isinstance(value, dict):
        raise ValueError(f"{path.name}: object required")
    return value


def _canonical_path(root: Path, relative: str) -> Path:
    path = root / relative
    if path.is_symlink() or path.resolve(strict=True) != path.absolute():
        raise ValueError(f"{relative}: non-canonical path")
    return path


def _committed_bytes(root: Path, commit: str, relative: str) -> bytes:
    result = run(
        ["git", "show", f"{commit}:{relative}"],
        cwd=root,
        check=False,
        capture_output=True,
    )
    if result.returncode != 0:
        raise ValueError(f"{relative}: not present at pinned commit")
    return result.stdout


def draw_sequence_commitment() -> dict[str, Any]:
    """Recompute the exact CPython 3.14.5 MT19937 draw stream commitment."""
    if platform.python_implementation() != "CPython" or platform.python_version() != "3.14.5":
        raise ValueError("diagnostics PRNG commitment requires CPython 3.14.5")
    generator = random.Random()  # noqa: S311 - deterministic statistical bootstrap, not crypto
    generator.seed(20260717, version=2)
    draws = [[generator.randrange(11) for _ in range(11)] for _ in range(2000)]
    encoded = json.dumps(draws, separators=(",", ":")).encode("ascii")
    return {
        "shape": [2000, 11],
        "total_draws": sum(len(replicate) for replicate in draws),
        "encoding": "canonical_compact_json_nested_integer_arrays",
        "sha256": sha256(encoded).hexdigest(),
        "first_replicate": draws[0],
        "last_replicate": draws[-1],
    }


def document() -> dict[str, Any]:
    """Return the fully deterministic, approval-absent candidate."""

    def pin(item: tuple[str, str]) -> dict[str, str]:
        return {"path": item[0], "sha256": item[1], "repository_commit": RECONCILIATION_COMMIT}

    sets = INPUTS["ordered_analysis_sets"]
    if not isinstance(sets, list):
        raise TypeError("ordered analysis-set pins must be a list")
    return {
        "schema_version": "foi-o.fixture-diagnostics-method-candidate.v0.1.0",
        "candidate_id": "local-fixture-diagnostics-method-v1",
        "status": "pending_exact_human_approval",
        "reconciliation": {
            "path": RECONCILIATION_PATH,
            "sha256": RECONCILIATION_SHA256,
            "repository_commit": RECONCILIATION_COMMIT,
        },
        "diagnostics_inputs": {
            "analysis_lock": pin(cast("tuple[str, str]", INPUTS["analysis_lock"])),
            "ordered_analysis_sets": [pin(item) for item in sets],
            "context_presentation": pin(cast("tuple[str, str]", INPUTS["context_presentation"])),
            "codebook": pin(cast("tuple[str, str]", INPUTS["codebook"])),
            "sampling_configuration": pin(
                cast("tuple[str, str]", INPUTS["sampling_configuration"])
            ),
            "cluster_registry": pin(cast("tuple[str, str]", INPUTS["cluster_registry"])),
            "unit_manifest": pin(cast("tuple[str, str]", INPUTS["unit_manifest"])),
        },
        "population": {
            "source": "ordered_11_cluster_fixture_census_from_cluster_registry_and_analysis_lock",
            "cluster_count": 11,
            "unit_count": 11,
            "ordered_unit_ids": [f"pm-{index:02d}" for index in range(1, 10)] + ["tl-01", "tl-02"],
            "ordered_unit_commitment_sha256": "d6e5c6b425903f09c6e3e08e0d6c4ccdee11eea91835d6ba96f64ba3306cf8ca",
        },
        "bootstrap": {
            "runtime": "CPython 3.14.5",
            "implementation": "python_stdlib_random.Random",
            "generator": "MT19937",
            "python_compatible_state_and_seeding": True,
            "seed": 20260717,
            "seed_call": "Random().seed(20260717, version=2)",
            "stream_lifecycle": "initialize_once_before_replicate_1_and_never_restart",
            "cluster_sampling_operation": "randrange",
            "draw_call": "randrange(11)",
            "resampling_unit": "singleton_duplicate_cluster",
            "cluster_draws_per_replicate": 11,
            "sample_size_rule": "sample_size_equals_observed_cluster_count",
            "sampled_unit_order": "concatenate_sampled_clusters_in_draw_order_and_units_within_each_cluster_in_canonical_unit_order",
            "metric_resample_rule": "one_shared_resample_per_replicate_reused_for_all_metrics",
            "replicates": 2000,
            "replicate_accounting": "per_metric_valid_and_invalid",
            "draw_sequence": draw_sequence_commitment(),
        },
        "metric_evaluation": {
            "order": [
                "raw_label_agreement",
                "cohen_kappa",
                "abstention_agreement",
                "reconciliation_trigger_rate",
            ],
            "non_kappa_requirement": "defined_on_every_replicate_or_build_fails",
            "span_metrics": "not_bootstrapped_zero_eligible_span_units",
        },
        "intervals": {
            "confidence_level": 0.95,
            "sides": "two_sided",
            "tail_probabilities": [0.025, 0.975],
            "method": "percentile",
            "quantile_definition": "Hyndman-Fan_type_7",
            "interpolation": "linear",
            "formula": "sort x ascending; for p in {0.025,0.975}, h=(n-1)*p, j=floor(h), g=h-j, q=(1-g)*x[j]+g*x[j+1], using zero-based indices; when j=n-1 return x[n-1]",
        },
        "undefined_metrics": {
            "kappa_predicate": "undefined exactly when expected_agreement == 1, including an empty eligible-label denominator",
            "kappa_handling": "exclude_undefined_replicates_from_kappa_interval_only_and_count_and_report_them",
            "other_metrics": "must_be_defined_on_every_replicate_or_build_fails",
        },
        "span_metrics": {
            "eligible_unit_count": 0,
            "null_input_metrics_remain_null": True,
            "bootstrapped": False,
        },
        "approval": None,
        "exact_approval_required": "named human approval of this exact candidate SHA-256 and committed repository commit",
        "bootstrap_execution_allowed": False,
        "diagnostics_results_present": False,
        "diagnostics_finalization_allowed": False,
        "local_only": True,
        "empirical_evidence": False,
        "human_reviewed": False,
        "gold_eligible": False,
        "release_qualifying": False,
        "publication_eligible": False,
        "prohibited_actions": PROHIBITED,
    }


def build(*, repository_root: Path) -> Path:
    """Write the candidate only after verifying the committed reconciliation pin."""
    root = repository_root.resolve(strict=True)
    reconciliation = _canonical_path(root, RECONCILIATION_PATH)
    if sha256(reconciliation.read_bytes()).hexdigest() != RECONCILIATION_SHA256:
        raise ValueError("reconciliation SHA-256 mismatch")
    committed = _committed_bytes(root, RECONCILIATION_COMMIT, RECONCILIATION_PATH)
    if (
        committed != reconciliation.read_bytes()
        or sha256(committed).hexdigest() != RECONCILIATION_SHA256
    ):
        raise ValueError("committed and canonical reconciliation bytes differ")
    inputs = document()["diagnostics_inputs"]
    pins = [inputs["analysis_lock"], *inputs["ordered_analysis_sets"]]
    pins.extend(
        inputs[key]
        for key in (
            "context_presentation",
            "codebook",
            "sampling_configuration",
            "cluster_registry",
            "unit_manifest",
        )
    )
    for pin in pins:
        current = _canonical_path(root, pin["path"]).read_bytes()
        historical = _committed_bytes(root, pin["repository_commit"], pin["path"])
        if current != historical or sha256(current).hexdigest() != pin["sha256"]:
            raise ValueError(f"{pin['path']}: committed/current input pin mismatch")
    schema = _strict_load(_canonical_path(root, SCHEMA_PATH))
    candidate = document()
    if candidate["bootstrap"]["draw_sequence"] != draw_sequence_commitment():
        raise ValueError("PRNG draw-sequence commitment mismatch")
    Draft202012Validator(schema).validate(candidate)
    output = root / OUTPUT_PATH
    if output.exists() and output.is_symlink():
        raise ValueError("candidate output is a symlink")
    output.write_text(json.dumps(candidate, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output


def verify(*, repository_root: Path, expected_sha256: str, expected_commit: str) -> str:
    """Verify an exact committed inert candidate and return its digest."""
    root = repository_root.resolve(strict=True)
    output = _canonical_path(root, OUTPUT_PATH)
    digest = sha256(output.read_bytes()).hexdigest()
    if digest != expected_sha256:
        raise ValueError("diagnostics method candidate SHA-256 mismatch")
    if _strict_load(output) != document():
        raise ValueError("diagnostics method candidate differs from deterministic contract")
    if _strict_load(output)["bootstrap"]["draw_sequence"] != draw_sequence_commitment():
        raise ValueError("PRNG draw-sequence commitment mismatch")
    committed = _committed_bytes(root, expected_commit, OUTPUT_PATH)
    if committed != output.read_bytes() or sha256(committed).hexdigest() != expected_sha256:
        raise ValueError("committed and canonical candidate bytes differ")
    status = run(
        ["git", "status", "--porcelain"], cwd=root, check=True, capture_output=True, text=True
    ).stdout
    if status:
        raise ValueError("repository worktree is not clean")
    return digest


if __name__ == "__main__":
    build(repository_root=Path(__file__).parents[1])

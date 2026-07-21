import json
from hashlib import sha256
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from scripts import build_fixture_diagnostics_method_candidate as builder

ROOT = Path(__file__).parents[1]
OUTPUT = ROOT / builder.OUTPUT_PATH


def test_builder_is_deterministic_and_candidate_is_inert() -> None:
    first = builder.build(repository_root=ROOT).read_bytes()
    second = builder.build(repository_root=ROOT).read_bytes()
    assert first == second
    value = json.loads(first)
    Draft202012Validator(json.loads((ROOT / builder.SCHEMA_PATH).read_text())).validate(value)
    assert value["approval"] is None
    assert value["bootstrap_execution_allowed"] is False
    assert value["diagnostics_results_present"] is False
    assert value["diagnostics_finalization_allowed"] is False
    assert value["bootstrap"]["seed"] == 20260717
    assert value["bootstrap"]["replicates"] == 2000
    assert value["intervals"]["quantile_definition"] == "Hyndman-Fan_type_7"


def test_schema_rejects_every_gate_expansion() -> None:
    schema = json.loads((ROOT / builder.SCHEMA_PATH).read_text())
    for field in (
        "bootstrap_execution_allowed",
        "diagnostics_results_present",
        "diagnostics_finalization_allowed",
        "empirical_evidence",
        "human_reviewed",
        "gold_eligible",
        "release_qualifying",
        "publication_eligible",
    ):
        value = builder.document()
        value[field] = True
        assert list(Draft202012Validator(schema).iter_errors(value)), field


@pytest.mark.parametrize(
    ("section", "field", "value"),
    [
        ("bootstrap", "cluster_draws_per_replicate", 2),
        ("bootstrap", "stream_lifecycle", "restart_each_replicate"),
        ("bootstrap", "metric_resample_rule", "one_resample_per_metric"),
        ("bootstrap", "runtime", "CPython 3.15.0"),
        ("bootstrap", "draw_sequence", {"sha256": "0" * 64}),
        ("metric_evaluation", "order", ["cohen_kappa"]),
        ("undefined_metrics", "kappa_predicate", "undefined_when_convenient"),
        ("intervals", "formula", "nearest_rank"),
        ("population", "cluster_count", 2),
    ],
)
def test_schema_rejects_method_or_population_drift(section: str, field: str, value: object) -> None:
    candidate = builder.document()
    candidate[section][field] = value
    schema = json.loads((ROOT / builder.SCHEMA_PATH).read_text())
    assert list(Draft202012Validator(schema).iter_errors(candidate))


def test_builder_rejects_changed_reconciliation(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(builder, "RECONCILIATION_SHA256", "0" * 64)
    with pytest.raises(ValueError, match="reconciliation SHA-256 mismatch"):
        builder.build(repository_root=ROOT)


def test_builder_rejects_input_that_differs_from_committed_bytes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = builder._committed_bytes

    def changed(root: Path, commit: str, relative: str) -> bytes:
        if relative.endswith("cluster-registry.json"):
            return b"{}\n"
        return original(root, commit, relative)

    monkeypatch.setattr(builder, "_committed_bytes", changed)
    with pytest.raises(ValueError, match="committed/current input pin mismatch"):
        builder.build(repository_root=ROOT)


def test_verifier_rejects_wrong_external_digest() -> None:
    with pytest.raises(ValueError, match="candidate SHA-256 mismatch"):
        builder.verify(repository_root=ROOT, expected_sha256="0" * 64, expected_commit="0" * 40)


def test_candidate_digest_is_stable() -> None:
    builder.build(repository_root=ROOT)
    assert (
        sha256(OUTPUT.read_bytes()).hexdigest()
        == "6e44b634e1bfde2cc21dd99f79fd0ad4bcd5a7fb96d361be7aae09567ed4c699"
    )


def test_prng_draw_sequence_commitment_and_diagnostics() -> None:
    commitment = builder.draw_sequence_commitment()
    assert commitment["total_draws"] == 22000
    assert (
        commitment["sha256"] == "9bb377fa38ed7758545eedb7676d2996ca6ac23cd06b72b7ecddb9b768728238"
    )
    assert commitment["first_replicate"] == [5, 4, 2, 8, 3, 3, 1, 9, 6, 6, 9]
    assert commitment["last_replicate"] == [4, 7, 7, 0, 6, 2, 3, 10, 8, 7, 4]

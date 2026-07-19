"""Build and verify bounded local inter-agent fixture diagnostics."""

from __future__ import annotations

import json
import math
import platform
import random
from hashlib import sha256
from pathlib import Path
from subprocess import run
from typing import Any, cast

from jsonschema import Draft202012Validator

OUTPUT_PATH = "examples/v2/analyst-fixture-packet/results/inter-agent-diagnostics.locked.json"
SCHEMA_PATH = "schemas/json/fixture-inter-agent-diagnostics.schema.json"
AUTHORIZATION_PATH = "examples/v2/analyst-fixture-packet/diagnostics-execution-authorization.pending-verification.json"
AUTHORIZATION_SHA256 = "3f0bd017674e0e72e5e383f8a16d7e6ff1e14f988bc82c89a720d648b51df7d8"
AUTHORIZATION_COMMIT = "da00026e98bbbac319a36d94e57fff2e8d8f9fc0"
METHOD_PATH = "examples/v2/analyst-fixture-packet/diagnostics-method-candidate.pending.json"
METHOD_SHA256 = "6e44b634e1bfde2cc21dd99f79fd0ad4bcd5a7fb96d361be7aae09567ed4c699"
METHOD_COMMIT = "c104a4cf193ef5f26de66b584e6a8cf37864a97e"
RECONCILIATION_COMMIT = "6dcf482cdee5865bfc35813d648a13de5ac32866"
PINS = {
    "analysis_lock": (
        "examples/v2/analyst-fixture-packet/results/analysis-lock.locked.json",
        "79faff0d554df7baff3e9f052dbc7f3a55d3e0e09baec95ab020fb3c4c002d1c",
        RECONCILIATION_COMMIT,
    ),
    "analysis_a": (
        "examples/v2/analyst-fixture-packet/results/analysis-set.analyst-a.locked.json",
        "d22f72d91ade4a4a5992ba50ba54afa1586203a23d394f256066ef23b4b6c400",
        RECONCILIATION_COMMIT,
    ),
    "analysis_b": (
        "examples/v2/analyst-fixture-packet/results/analysis-set.analyst-b.locked.json",
        "ff72a35f840c97f26b07108c963574d664359b260719ad0dfc7c2986c0d665dd",
        RECONCILIATION_COMMIT,
    ),
    "context_presentation": (
        "examples/v2/analyst-fixture-packet/context-presentation.pending.json",
        "72b75eb688541a712a62bea2569fb84353930c089ebaf8fc1082128aa3ef0e63",
        RECONCILIATION_COMMIT,
    ),
    "codebook": (
        "examples/v2/analyst-fixture-packet/codebook.approved.json",
        "d918f1b705debcd6d8a14c078d7d0044e23c10615c9a7c27e4122d03088bbfdc",
        RECONCILIATION_COMMIT,
    ),
    "sampling_configuration": (
        "examples/v2/analyst-fixture-packet/sampling-configuration.approved.json",
        "1a88278bff5d2d682ae56d119d7ed25b899a60214e71067e37f178052f4bfbc8",
        RECONCILIATION_COMMIT,
    ),
    "cluster_registry": (
        "examples/v2/analyst-fixture-packet/cluster-registry.json",
        "4aef78cbad8a243a450de5c7f2fad1b21912bc4a26f1576375d1b163ad8cd14e",
        RECONCILIATION_COMMIT,
    ),
    "unit_manifest": (
        "examples/v2/analyst-fixture-packet/unit-manifest.json",
        "a847c4f131ddcaaf8151d13c767859e8269bd1cca14ada20cf220d7c755ccddf",
        RECONCILIATION_COMMIT,
    ),
    "reconciliation": (
        "examples/v2/analyst-fixture-packet/results/reconciliation-set.locked.json",
        "09e2f7ad14298dac824acc21fac9bad6cfa5a6dfa62b9c2b7cd7ff870e183102",
        RECONCILIATION_COMMIT,
    ),
}
PROHIBITED = [
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
EXPECTED_OUTPUT_SHA256 = "fe2f9e29136fca68894bc3960b7a5cfcc4f97edc3e0a970d94b7fbc2a783bbc5"


def _strict_load(path: Path) -> dict[str, Any]:
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in items:
            if key in result:
                raise ValueError(f"{path.name}: duplicate JSON key {key}")
            result[key] = value
        return result

    value = json.loads(
        path.read_text(),
        object_pairs_hook=pairs,
        parse_constant=lambda token: (_ for _ in ()).throw(ValueError(f"non-finite {token}")),
    )
    if not isinstance(value, dict):
        raise ValueError(f"{path.name}: object required")
    return value


def _canonical(root: Path, relative: str) -> Path:
    path = root / relative
    if path.is_symlink() or path.resolve(strict=True) != path.absolute():
        raise ValueError(f"{relative}: non-canonical path")
    return path


def _committed(root: Path, commit: str, relative: str) -> bytes:
    result = run(
        ["git", "show", f"{commit}:{relative}"], cwd=root, check=False, capture_output=True
    )
    if result.returncode:
        raise ValueError(f"{relative}: missing committed bytes")
    return result.stdout


def _verify_pin(root: Path, relative: str, digest: str, commit: str) -> dict[str, Any]:
    path = _canonical(root, relative)
    current = path.read_bytes()
    if sha256(current).hexdigest() != digest:
        name = "authorization" if relative == AUTHORIZATION_PATH else relative
        raise ValueError(f"{name} SHA-256 mismatch")
    if _committed(root, commit, relative) != current:
        raise ValueError(f"{relative}: committed/current bytes differ")
    return _strict_load(path)


def _pin(value: tuple[str, str, str]) -> dict[str, str]:
    return {"path": value[0], "sha256": value[1], "repository_commit": value[2]}


def _quantile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    h = (len(ordered) - 1) * probability
    j = math.floor(h)
    g = h - j
    return ordered[j] if j == len(ordered) - 1 else (1 - g) * ordered[j] + g * ordered[j + 1]


def _kappa(pairs: list[tuple[str, str]]) -> float | None:
    if not pairs:
        return None
    labels = {label for pair in pairs for label in pair}
    n = len(pairs)
    observed = sum(a == b for a, b in pairs) / n
    expected = sum(
        sum(a == label for a, _ in pairs) * sum(b == label for _, b in pairs) for label in labels
    ) / (n * n)
    return None if expected == 1 else (observed - expected) / (1 - expected)


def _inputs(root: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    authorization = _verify_pin(
        root, AUTHORIZATION_PATH, AUTHORIZATION_SHA256, AUTHORIZATION_COMMIT
    )
    method = _verify_pin(root, METHOD_PATH, METHOD_SHA256, METHOD_COMMIT)
    if authorization["prohibited_actions"] != PROHIBITED:
        raise ValueError("authorization prohibitions mismatch")
    if authorization["method_candidate"] != {
        "path": METHOD_PATH,
        "sha256": METHOD_SHA256,
        "repository_commit": METHOD_COMMIT,
    }:
        raise ValueError("authorization method pin mismatch")
    for value in PINS.values():
        _verify_pin(root, *value)
    expected_method_inputs = {
        "analysis_lock": _pin(PINS["analysis_lock"]),
        "ordered_analysis_sets": [_pin(PINS["analysis_a"]), _pin(PINS["analysis_b"])],
        **{
            key: _pin(PINS[key])
            for key in (
                "context_presentation",
                "codebook",
                "sampling_configuration",
                "cluster_registry",
                "unit_manifest",
            )
        },
    }
    if (
        method["diagnostics_inputs"] != expected_method_inputs
        or method["prohibited_actions"][:2] != ["bootstrap_execution", "diagnostics_finalization"]
        or method["prohibited_actions"][2:] != PROHIBITED
    ):
        raise ValueError("method input pins or prohibitions mismatch")
    a = _strict_load(_canonical(root, PINS["analysis_a"][0]))["entries"]
    b = _strict_load(_canonical(root, PINS["analysis_b"][0]))["entries"]
    if [entry["unit_id"] for entry in a] != [entry["unit_id"] for entry in b] or len(a) != 11:
        raise ValueError("ordered analysis population mismatch")
    ordered_ids = [entry["unit_id"] for entry in a]
    if ordered_ids != method["population"]["ordered_unit_ids"]:
        raise ValueError("analysis order differs from approved method population")
    if [entry["record"]["unit_sha256"] for entry in a] != [
        entry["record"]["unit_sha256"] for entry in b
    ]:
        raise ValueError("analyst unit SHA-256 order mismatch")
    ordered_unit_hashes = [entry["record"]["unit_sha256"] for entry in a]
    encoded_unit_hashes = ("\n".join(ordered_unit_hashes) + "\n").encode("ascii")
    if (
        sha256(encoded_unit_hashes).hexdigest()
        != method["population"]["ordered_unit_commitment_sha256"]
    ):
        raise ValueError("ordered analysis population commitment mismatch")
    return a, b


def document(*, repository_root: Path) -> dict[str, Any]:
    root = repository_root.resolve(strict=True)
    a, b = _inputs(root)
    rows = [(x["record"], y["record"]) for x, y in zip(a, b, strict=True)]
    eligible_rows = [(x, y) for x, y in rows if not x["abstention"] and not y["abstention"]]
    label_matches = sum(x["label"] == y["label"] for x, y in eligible_rows)
    abstention_matches = sum(x["abstention"] == y["abstention"] for x, y in rows)
    trigger_count = sum(
        x["label"] != y["label"] or x["span"] != y["span"] or x["abstention"] != y["abstention"]
        for x, y in rows
    )
    span_eligible_count = sum(x["span"] is not None and y["span"] is not None for x, y in rows)
    reconciliation = _strict_load(_canonical(root, PINS["reconciliation"][0]))
    reconciliation_entries = reconciliation["entries"]
    disagreement_ids = [
        a[index]["unit_id"]
        for index, (x, y) in enumerate(rows)
        if x["label"] != y["label"] or x["span"] != y["span"] or x["abstention"] != y["abstention"]
    ]
    if [entry["unit_id"] for entry in reconciliation_entries] != disagreement_ids:
        raise ValueError("reconciliation entries do not match ordered disagreements")
    resolved = sum(entry["record"]["outcome"] == "resolved" for entry in reconciliation_entries)
    unresolved = sum(entry["record"]["outcome"] == "unresolved" for entry in reconciliation_entries)
    if (
        len(eligible_rows),
        label_matches,
        abstention_matches,
        trigger_count,
        span_eligible_count,
        len(reconciliation_entries),
        resolved,
        unresolved,
    ) != (10, 9, 10, 2, 0, 2, 2, 0):
        raise ValueError("locked diagnostic census differs from approved method population")

    def evaluate(indices: list[int]) -> tuple[float, float | None, float, float]:
        selected = [rows[index] for index in indices]
        eligible = [
            (x["label"], y["label"])
            for x, y in selected
            if not x["abstention"] and not y["abstention"]
        ]
        raw = sum(x == y for x, y in eligible) / len(eligible)
        abstention = sum(x["abstention"] == y["abstention"] for x, y in selected) / len(selected)
        triggered = sum(
            x["label"] != y["label"] or x["span"] != y["span"] or x["abstention"] != y["abstention"]
            for x, y in selected
        ) / len(selected)
        return raw, _kappa(eligible), abstention, triggered

    point = evaluate(list(range(11)))
    if platform.python_implementation() != "CPython" or platform.python_version() != "3.14.5":
        raise ValueError("diagnostics execution requires CPython 3.14.5")
    generator = random.Random()  # noqa: S311
    generator.seed(20260717, version=2)
    draws = [[generator.randrange(11) for _ in range(11)] for _ in range(2000)]
    encoded = json.dumps(draws, separators=(",", ":")).encode("ascii")
    if (
        sha256(encoded).hexdigest()
        != "9bb377fa38ed7758545eedb7676d2996ca6ac23cd06b72b7ecddb9b768728238"
    ):
        raise ValueError("draw sequence commitment mismatch")
    bootstrap = [evaluate(indices) for indices in draws]

    def metric(index: int, numerator: int | None, denominator: int) -> dict[str, Any]:
        valid = [cast("float", value[index]) for value in bootstrap if value[index] is not None]
        return {
            "estimate": point[index],
            "numerator": numerator,
            "denominator": denominator,
            "confidence_interval": {
                "lower": _quantile(valid, 0.025),
                "upper": _quantile(valid, 0.975),
            },
            "bootstrap_replicates_valid": len(valid),
            "bootstrap_replicates_invalid": 2000 - len(valid),
        }

    report = {
        "schema_version": "foi-o.fixture-inter-agent-diagnostics.v0.1.0",
        "report_id": "local-fixture-inter-agent-diagnostics-v1",
        "status": "locked_local_agent_diagnostics",
        "authorization": _pin((AUTHORIZATION_PATH, AUTHORIZATION_SHA256, AUTHORIZATION_COMMIT)),
        "method_candidate": _pin((METHOD_PATH, METHOD_SHA256, METHOD_COMMIT)),
        "analysis_lock": _pin(PINS["analysis_lock"]),
        "ordered_analysis_sets": [_pin(PINS["analysis_a"]), _pin(PINS["analysis_b"])],
        "reconciliation": _pin(PINS["reconciliation"]),
        "population": {
            "cluster_count": len(rows),
            "unit_count": len(rows),
            "eligible_label_pair_count": len(eligible_rows),
            "reconciliation_trigger_count": trigger_count,
        },
        "reconciliation_census": {
            "disagreement_entries": trigger_count,
            "reconciled_entries": len(reconciliation_entries),
            "resolved_entries": resolved,
            "unresolved_entries": unresolved,
            "coverage_complete": len(reconciliation_entries) == trigger_count,
        },
        "bootstrap": {
            "runtime": "CPython 3.14.5",
            "seed": 20260717,
            "replicates": 2000,
            "draw_count": 22000,
            "draw_sequence_sha256": sha256(encoded).hexdigest(),
            "interval_method": "two_sided_cluster_bootstrap_percentile",
            "quantile_definition": "Hyndman-Fan_type_7",
        },
        "metrics": {
            "raw_label_agreement": metric(0, label_matches, len(eligible_rows)),
            "cohen_kappa": metric(1, None, len(eligible_rows)),
            "abstention_agreement": metric(2, abstention_matches, len(rows)),
            "reconciliation_trigger_rate": metric(3, trigger_count, len(rows)),
        },
        "span_metrics": {
            "eligible_unit_count": span_eligible_count,
            "exact_agreement": None,
            "overlap_f1": None,
            "bootstrapped": False,
        },
        "local_only": True,
        "empirical_evidence": False,
        "human_reviewed": False,
        "gold_eligible": False,
        "release_qualifying": False,
        "publication_eligible": False,
        "prohibited_actions": PROHIBITED,
    }
    Draft202012Validator(_strict_load(_canonical(root, SCHEMA_PATH))).validate(report)
    return report


def build(*, repository_root: Path) -> Path:
    root = repository_root.resolve(strict=True)
    output = root / OUTPUT_PATH
    if output.exists() and output.is_symlink():
        raise ValueError("diagnostics output is a symlink")
    output.write_text(json.dumps(document(repository_root=root), indent=2, sort_keys=True) + "\n")
    return output


def verify(
    *,
    repository_root: Path,
    diagnostics_path: Path | None = None,
    expected_sha256: str | None = None,
    expected_commit: str | None = None,
) -> str:
    root = repository_root.resolve(strict=True)
    expected = document(repository_root=root)
    canonical = root / OUTPUT_PATH
    path = diagnostics_path or canonical
    if path.is_symlink() or path.absolute() != canonical:
        raise ValueError("diagnostics path is not canonical")
    actual = _strict_load(path)
    Draft202012Validator(_strict_load(_canonical(root, SCHEMA_PATH))).validate(actual)
    if actual != expected:
        raise ValueError("diagnostics output differs from deterministic recomputation")
    digest = sha256(path.read_bytes()).hexdigest()
    if (expected_sha256 is None) != (expected_commit is None):
        raise ValueError("expected diagnostics SHA-256 and commit must be supplied together")
    if expected_sha256 is not None and digest != expected_sha256:
        raise ValueError("diagnostics SHA-256 mismatch")
    if expected_commit is not None:
        head = run(
            ["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True
        ).stdout.strip()
        if head != expected_commit:
            raise ValueError("repository HEAD does not match diagnostics commit")
        for ancestor in (AUTHORIZATION_COMMIT, RECONCILIATION_COMMIT):
            if run(
                ["git", "merge-base", "--is-ancestor", ancestor, expected_commit],
                cwd=root,
                check=False,
            ).returncode:
                raise ValueError("diagnostics commit does not descend from governed inputs")
        if _committed(root, expected_commit, OUTPUT_PATH) != path.read_bytes():
            raise ValueError("diagnostics differs from anchored commit")
        if run(
            ["git", "status", "--porcelain"], cwd=root, check=True, capture_output=True, text=True
        ).stdout:
            raise ValueError("repository worktree is not clean")
    return digest


if __name__ == "__main__":
    build(repository_root=Path(__file__).parents[1])

import json
from hashlib import sha256
from pathlib import Path
from subprocess import run

import pytest
from jsonschema import Draft202012Validator

from scripts import build_fixture_inter_agent_diagnostics as builder

ROOT = Path(__file__).parents[1]
OUTPUT = ROOT / builder.OUTPUT_PATH


@pytest.fixture(autouse=True)
def _permit_unit_level_computation(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep unit tests independent; integration tests remove this patch explicitly."""
    head = builder._current_head(ROOT)
    monkeypatch.setattr(
        builder,
        "verify_execution_authorization",
        lambda **_kwargs: builder.DiagnosticsAuthorizationVerificationResult(
            builder.AUTHORIZATION_SHA256, head
        ),
    )


def test_builder_executes_exact_approved_method_deterministically() -> None:
    first = builder.build(repository_root=ROOT).read_bytes()
    second = builder.build(repository_root=ROOT).read_bytes()
    assert first == second
    report = json.loads(first)
    Draft202012Validator(json.loads((ROOT / builder.SCHEMA_PATH).read_text())).validate(report)
    metrics = report["metrics"]
    assert metrics["raw_label_agreement"] == {
        "estimate": 0.9,
        "numerator": 9,
        "denominator": 10,
        "confidence_interval": {"lower": 0.7, "upper": 1.0},
        "bootstrap_replicates_valid": 2000,
        "bootstrap_replicates_invalid": 0,
    }
    assert metrics["cohen_kappa"]["estimate"] == pytest.approx(5 / 6)
    assert metrics["cohen_kappa"]["confidence_interval"] == {"lower": 0.4, "upper": 1.0}
    assert metrics["cohen_kappa"]["bootstrap_replicates_valid"] == 1998
    assert metrics["cohen_kappa"]["bootstrap_replicates_invalid"] == 2
    assert metrics["abstention_agreement"]["confidence_interval"] == {
        "lower": 8 / 11,
        "upper": 1.0,
    }
    assert metrics["reconciliation_trigger_rate"]["confidence_interval"] == {
        "lower": 0.0,
        "upper": 5 / 11,
    }
    assert report["span_metrics"] == {
        "eligible_unit_count": 0,
        "exact_agreement": None,
        "overlap_f1": None,
        "bootstrapped": False,
    }


def test_schema_rejects_claim_or_promotion_expansion() -> None:
    schema = json.loads((ROOT / builder.SCHEMA_PATH).read_text())
    for field in (
        "empirical_evidence",
        "human_reviewed",
        "gold_eligible",
        "release_qualifying",
        "publication_eligible",
    ):
        value = builder.document(repository_root=ROOT)
        value[field] = True
        assert list(Draft202012Validator(schema).iter_errors(value)), field


def test_verifier_recomputes_and_rejects_tampering(tmp_path: Path) -> None:
    builder.build(repository_root=ROOT)
    value = json.loads(OUTPUT.read_text())
    value["metrics"]["raw_label_agreement"]["estimate"] = 1.0
    original = OUTPUT.read_bytes()
    try:
        OUTPUT.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
        with pytest.raises(ValueError, match="diagnostics output differs"):
            builder.verify(repository_root=ROOT)
    finally:
        OUTPUT.write_bytes(original)


def test_verifier_rejects_alternate_and_symlink_paths(tmp_path: Path) -> None:
    builder.build(repository_root=ROOT)
    alternate = tmp_path / OUTPUT.name
    alternate.write_bytes(OUTPUT.read_bytes())
    link = tmp_path / "linked.json"
    link.symlink_to(OUTPUT)
    for path in (alternate, link):
        with pytest.raises(ValueError, match="diagnostics path is not canonical"):
            builder.verify(repository_root=ROOT, diagnostics_path=path)


def test_verifier_rejects_wrong_authorization_pin(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(builder, "AUTHORIZATION_SHA256", "0" * 64)
    with pytest.raises(ValueError, match="authorization SHA-256 mismatch"):
        builder.build(repository_root=ROOT)


def test_document_rejects_absent_or_forged_permission(monkeypatch: pytest.MonkeyPatch) -> None:
    def absent(**_kwargs: object) -> object:
        raise ValueError("permission absent")

    monkeypatch.setattr(builder, "verify_execution_authorization", absent)
    with pytest.raises(ValueError, match="permission absent"):
        builder.document(repository_root=ROOT)

    monkeypatch.setattr(builder, "verify_execution_authorization", lambda **_kwargs: object())
    with pytest.raises(ValueError, match="permission is absent or forged"):
        builder.document(repository_root=ROOT)


def test_authorization_failure_precedes_all_governed_computation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    inputs_called = False

    def forbidden_inputs(_root: Path) -> object:
        nonlocal inputs_called
        inputs_called = True
        raise AssertionError("governed inputs must not be read")

    monkeypatch.setattr(builder, "_inputs", forbidden_inputs)
    monkeypatch.setattr(
        builder,
        "verify_execution_authorization",
        lambda **_kwargs: (_ for _ in ()).throw(ValueError("permission absent")),
    )
    with pytest.raises(ValueError, match="permission absent"):
        builder.document(repository_root=ROOT)
    assert inputs_called is False


def test_build_rechecks_authorization_before_output_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    del tmp_path  # The governed canonical output is intentionally the only accepted target.
    original = OUTPUT.read_bytes()
    head = builder._current_head(ROOT)
    calls = 0

    def permission(**_kwargs: object) -> builder.DiagnosticsAuthorizationVerificationResult:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise ValueError("permission changed before write")
        return builder.DiagnosticsAuthorizationVerificationResult(
            builder.AUTHORIZATION_SHA256, head
        )

    monkeypatch.setattr(builder, "verify_execution_authorization", permission)
    with pytest.raises(ValueError, match="permission changed before write"):
        builder.build(repository_root=ROOT)
    assert calls == 2
    assert OUTPUT.read_bytes() == original


def _clean_clone(tmp_path: Path) -> Path:
    clone = tmp_path / "repository"
    run(["git", "clone", "--quiet", "--no-hardlinks", str(ROOT), str(clone)], check=True)
    return clone


def test_real_gate_accepts_clean_committed_descendant(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    clone = _clean_clone(tmp_path)
    monkeypatch.setattr(
        builder,
        "verify_execution_authorization",
        __import__(
            "scripts.build_fixture_diagnostics_executable_authorization",
            fromlist=["verify"],
        ).verify,
    )
    report = builder.document(repository_root=clone)
    assert report["authorization"]["sha256"] == builder.AUTHORIZATION_SHA256


def test_real_gate_rejects_dirty_or_pre_authorization_head(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    verifier = __import__(
        "scripts.build_fixture_diagnostics_executable_authorization", fromlist=["verify"]
    ).verify
    monkeypatch.setattr(builder, "verify_execution_authorization", verifier)
    clone = _clean_clone(tmp_path)
    sentinel = clone / "uncommitted.txt"
    sentinel.write_text("dirty\n", encoding="utf-8")
    with pytest.raises(ValueError, match="worktree is not clean"):
        builder.build(repository_root=clone)
    sentinel.unlink()

    run(["git", "checkout", "--quiet", builder.METHOD_COMMIT], cwd=clone, check=True)
    with pytest.raises((FileNotFoundError, ValueError)):
        builder.document(repository_root=clone)


def test_generated_digest_is_stable() -> None:
    builder.build(repository_root=ROOT)
    assert sha256(OUTPUT.read_bytes()).hexdigest() == builder.EXPECTED_OUTPUT_SHA256


@pytest.mark.parametrize(
    ("payload", "message"),
    [('{"a":1,"a":2}', "duplicate JSON key"), ('{"a":NaN}', "non-finite")],
)
def test_strict_json_rejects_duplicate_keys_and_nonfinite(
    tmp_path: Path, payload: str, message: str
) -> None:
    path = tmp_path / "invalid.json"
    path.write_text(payload)
    with pytest.raises(ValueError, match=message):
        builder._strict_load(path)


def test_postcommit_arguments_are_required_as_a_pair() -> None:
    builder.build(repository_root=ROOT)
    with pytest.raises(ValueError, match="must be supplied together"):
        builder.verify(repository_root=ROOT, expected_sha256=builder.EXPECTED_OUTPUT_SHA256)


def test_postcommit_verifier_rejects_wrong_head() -> None:
    builder.build(repository_root=ROOT)
    with pytest.raises(ValueError, match="repository HEAD does not match"):
        builder.verify(
            repository_root=ROOT,
            expected_sha256=builder.EXPECTED_OUTPUT_SHA256,
            expected_commit="0" * 40,
        )

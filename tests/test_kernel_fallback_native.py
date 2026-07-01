from __future__ import annotations

from pathlib import Path

from foi_o_nz.kernel_fallback import (
    action_requires_review,
    blend_scores,
    clamp_top_k,
    conformance_cases,
    evaluate_operation,
    fnv1a64_text,
    is_forward_transition,
    looks_like_email,
    normalise_alaveteli_state,
    redaction_preview_width,
    risk_level_from_score,
    token_estimate_from_chars,
)
from foi_o_nz.native_kernel import evaluate_kernel, kernel_status, run_kernel_conformance
from foi_o_nz.validation import validate_json_schema


def test_python_fallback_contract_core_operations() -> None:
    assert normalise_alaveteli_state("successful") == "ReleasedInFull"
    assert token_estimate_from_chars(5) == 2
    assert risk_level_from_score(5, False) == "high"
    assert blend_scores(2.0, 1.0, 0.5) == 1.5
    assert clamp_top_k(0, 100) == 1
    assert action_requires_review("high", False) is True
    assert is_forward_transition("Received", "Searching") is True
    assert looks_like_email("a@example.org") is True
    assert looks_like_email("not-email") is False
    assert redaction_preview_width(12) == 2
    assert isinstance(fnv1a64_text("foi-o-nz"), int)


def test_fallback_conformance_cases_match_expected() -> None:
    for operation, args, expected in conformance_cases():
        result = evaluate_operation(operation, args)
        assert result.value == expected


def test_kernel_status_has_python_fallback() -> None:
    status = kernel_status()
    assert status["schema_version"] == "foi-o-nz.native-kernel-status.v0.1.0"
    assert status["fallback_available"] is True
    assert status["preferred_runtime"] in {"mojo-binary", "mojo-cli", "python-fallback"}


def test_kernel_eval_uses_fallback_when_no_binary() -> None:
    result = evaluate_kernel("normalise_alaveteli_state", "successful", prefer_native=False)
    assert result["ok"] is True
    assert result["value"] == "ReleasedInFull"
    assert result["runtime_used"] == "python-fallback"


def test_kernel_conformance_report_validates(tmp_path: Path) -> None:
    output = tmp_path / "kernel-conformance.json"
    report = run_kernel_conformance(output)
    assert report["ok"] is True
    assert report["case_count"] >= 20
    validation = validate_json_schema(output, Path("schemas/json/kernel-conformance.schema.json"))
    assert validation.ok, validation.errors

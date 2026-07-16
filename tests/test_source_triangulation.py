import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from pydantic import ValidationError

from foi_o_nz.source_triangulation import (
    SourceAssertion,
    TriangulationRequest,
    evaluate_triangulation,
)

ROOT = Path(__file__).parent.parent


def assertion(assertion_id: str, source_id: str, **overrides: object) -> SourceAssertion:
    values: dict[str, object] = {
        "assertion_id": assertion_id,
        "source_id": source_id,
        "claim_id": "claim.deadline",
        "stance": "supports",
        "availability": "available",
        "freshness": "event_time_match",
        "rights_status": "permitted",
        "integrity": "hash_verified",
    }
    values.update(overrides)
    return SourceAssertion.model_validate(values)


def test_two_independent_eligible_sources_pass_deterministically() -> None:
    request = TriangulationRequest(
        run_id="triangulation.run.1",
        minimum_supporting_sources=2,
        assertions=[assertion("a2", "ombudsman"), assertion("a1", "legislation")],
    )

    result = evaluate_triangulation(request)

    assert result.status == "candidate_supported"
    assert result.supporting_source_ids == ["legislation", "ombudsman"]
    assert result.exception_queue == []
    assert result.human_review_required is True
    assert result.promotion_allowed is False
    assert result.model_dump(mode="json") == evaluate_triangulation(request).model_dump(mode="json")


@pytest.mark.parametrize(
    ("overrides", "reason"),
    [
        ({"availability": "blocked"}, "blocked"),
        ({"freshness": "stale"}, "stale"),
        ({"rights_status": "unknown"}, "rights_uncertain"),
    ],
)
def test_exception_reasons_are_explicit(overrides: dict[str, object], reason: str) -> None:
    request = TriangulationRequest(
        run_id=f"triangulation.run.{reason}",
        assertions=[assertion("a1", "source.one", **overrides)],
    )

    result = evaluate_triangulation(request)

    reasons = {item.reason for item in result.exception_queue}
    assert reason in reasons
    assert "insufficient_evidence" in reasons
    assert result.status == "human_exception_required"
    assert result.promotion_allowed is False


def test_duplicate_sources_do_not_satisfy_independence_threshold() -> None:
    request = TriangulationRequest(
        run_id="triangulation.run.duplicates",
        assertions=[assertion("a1", "same"), assertion("a2", "same")],
    )
    result = evaluate_triangulation(request)
    assert result.supporting_source_ids == ["same"]
    assert [item.reason for item in result.exception_queue] == ["insufficient_evidence"]


def test_conflict_is_detected_even_when_support_threshold_is_met() -> None:
    request = TriangulationRequest(
        run_id="triangulation.run.conflict",
        assertions=[
            assertion("a1", "source.one"),
            assertion("a2", "source.two"),
            assertion("a3", "source.three", stance="contradicts"),
        ],
    )
    result = evaluate_triangulation(request)
    assert [item.reason for item in result.exception_queue] == ["conflicting"]


def test_duplicate_assertion_ids_are_rejected() -> None:
    with pytest.raises(ValidationError, match="assertion_id"):
        TriangulationRequest(
            run_id="triangulation.run.invalid",
            assertions=[assertion("a1", "one"), assertion("a1", "two")],
        )


def test_committed_example_matches_output_schema() -> None:
    example = json.loads(
        (ROOT / "examples/v2/source-triangulation.example.json").read_text(encoding="utf-8")
    )
    schema = json.loads(
        (ROOT / "schemas/json/source-triangulation-result.schema.json").read_text(
            encoding="utf-8"
        )
    )
    Draft202012Validator(schema).validate(example)
    result = evaluate_triangulation(
        TriangulationRequest.model_validate(example["request"])
    ).model_dump(mode="json")
    assert example["result"] == result

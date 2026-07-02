from __future__ import annotations

from pathlib import Path

from foi_o_nz.evaluation import evaluate_event_extraction, evaluate_event_jsonl
from foi_o_nz.io import write_jsonl
from foi_o_nz.validation import validate_json_schema

EVENT_EVALUATION_SCHEMA = Path("schemas/json/event-evaluation.schema.json")


def test_evaluate_event_extraction_perfect_match() -> None:
    predicted = [
        {
            "request_ref": {"source_request_id": "r1"},
            "event_type": "RequestObserved",
            "lifecycle_state_after": "Received",
        }
    ]
    result = evaluate_event_extraction(predicted, predicted)
    assert result["precision"] == 1.0
    assert result["recall"] == 1.0
    assert result["f1"] == 1.0


def test_evaluate_event_extraction_miss() -> None:
    predicted = [
        {
            "request_ref": {"source_request_id": "r1"},
            "event_type": "RequestObserved",
            "lifecycle_state_after": "Received",
        }
    ]
    gold = [
        {
            "request_ref": {"source_request_id": "r1"},
            "event_type": "ReleaseMade",
            "lifecycle_state_after": "ReleasedInFull",
        }
    ]
    result = evaluate_event_extraction(predicted, gold)
    assert result["true_positive"] == 0
    assert result["false_positive"] == 1
    assert result["false_negative"] == 1


def test_evaluate_event_jsonl_writes_deterministic_schema_valid_summary(tmp_path: Path) -> None:
    predicted_path = tmp_path / "predicted-events.jsonl"
    gold_path = tmp_path / "gold-events.jsonl"
    output_path = tmp_path / "event-evaluation.summary.json"
    write_jsonl(
        predicted_path,
        [
            {
                "request_ref": {"source_request_id": "r1"},
                "event_type": "RequestObserved",
                "lifecycle_state_after": "Received",
                "assertion_status": "observed",
                "confidence": 1.0,
            },
            {
                "request_ref": {"source_request_id": "r1"},
                "event_type": "ExtensionNotified",
                "lifecycle_state_after": "ExtensionApplied",
                "assertion_status": "inferred",
                "confidence": 0.58,
            },
        ],
    )
    write_jsonl(
        gold_path,
        [
            {
                "request_ref": {"source_request_id": "r1"},
                "event_type": "RequestObserved",
                "lifecycle_state_after": "Received",
                "assertion_status": "observed",
                "confidence": 1.0,
            },
            {
                "request_ref": {"source_request_id": "r1"},
                "event_type": "ReleaseMade",
                "lifecycle_state_after": "ReleasedInPart",
                "assertion_status": "inferred",
                "confidence": 0.38,
            },
        ],
    )

    result = evaluate_event_jsonl(predicted_path, gold_path, output=output_path)

    assert result == {
        "schema_version": "foi-o-nz.event-evaluation.v0.1.0",
        "mode": "event_type_state",
        "predicted_count": 2,
        "gold_count": 2,
        "true_positive": 1,
        "false_positive": 1,
        "false_negative": 1,
        "precision": 0.5,
        "recall": 0.5,
        "f1": 0.5,
        "false_positive_keys": [["r1", "ExtensionNotified", "ExtensionApplied"]],
        "false_negative_keys": [["r1", "ReleaseMade", "ReleasedInPart"]],
        "limitations": [
            "Evaluation compares event keys for extractor quality only; it does not certify legal outcomes."
        ],
    }
    validation = validate_json_schema(output_path, EVENT_EVALUATION_SCHEMA)
    assert validation.ok, validation.errors


def test_committed_event_evaluation_example_is_schema_valid() -> None:
    validation = validate_json_schema(
        Path("examples/event-evaluation.summary.json"),
        EVENT_EVALUATION_SCHEMA,
    )
    assert validation.ok, validation.errors

from __future__ import annotations

from foi_o_nz.evaluation import evaluate_event_extraction


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

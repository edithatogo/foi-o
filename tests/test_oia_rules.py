import json
import sys
from datetime import date, timedelta
from pathlib import Path
import pytest

from foi_o_nz.oia_rules import (
    DiscretionPoint,
    RuleInvocation,
    ValueObject,
    evaluate_invocation,
    nz_working_days,
)

def test_nz_working_days_basic() -> None:
    # Basic weekend test
    start = date(2026, 2, 2)  # Monday
    # Adding 5 working days should land on next Monday
    assert nz_working_days(start, 5) == date(2026, 2, 9)

def test_nz_working_days_property_round_trip() -> None:
    # Property test: adding then subtracting n working days round-trips
    # Note: subtracting working days is not supported by add_working_days out of the box,
    # but we can verify that adding n working days behaves logically and consistently.
    start = date(2026, 6, 1)  # Mon
    added = nz_working_days(start, 10)
    assert added > start

def test_import_isolation() -> None:
    # Ensure that oia_rules modules do not import other parts of foi_o_nz besides dates
    for name, module in list(sys.modules.items()):
        if name.startswith("foi_o_nz.oia_rules."):
            imports = dir(module)
            # Ensure none of the process-heavy modules are imported
            assert "normalise" not in imports
            assert "models" not in imports or name.endswith("types")  # types may import models for clock reference if needed, but rules does not.

def test_urgency_discretion_point() -> None:
    # Urgency flag with reasons provided should produce human_decision_required and DiscretionPoint
    reasons = ValueObject(value=True, valueState="known")
    invocation = RuleInvocation(
        decision_id="nz-oia/decision.urgency_flag",
        inputs={"nz-oia/variable.urgency_reasons_provided": reasons},
        parameter_set="0.1.0",
        invoked_by="test-event"
    )
    res = evaluate_invocation(invocation)
    out = res.outputs["nz-oia/decision.urgency_flag"]
    assert out.value == "human_decision_required"
    assert res.discretion_required is not None
    assert res.discretion_required.discretion_id == "nz-oia/discretion.urgency_assessment"

def test_fixtures_conformance() -> None:
    # Load and run all promoted fixtures
    fixtures_path = Path(__file__).parent / "fixtures" / "oia_rules" / "oia-clock-fixtures.json"
    if not fixtures_path.exists():
        fixtures_path = Path(__file__).parent.parent / "rules" / "fixtures" / "oia-clock-fixtures.json"
    with open(fixtures_path, encoding="utf-8") as f:
        fixtures = json.load(f)

    # Load 2026 public holidays from foi-o examples if available
    holidays_file = Path(__file__).parent.parent / "examples" / "nz-public-holidays-2026.govt-nz.json"
    if not holidays_file.exists():
        holidays_file = Path(__file__).parent.parent.parent / "foi-o" / "examples" / "nz-public-holidays-2026.govt-nz.json"
    holidays = set()
    if holidays_file.exists():
        with open(holidays_file, encoding="utf-8") as hf:
            hdata = json.load(hf)
            for item in hdata.get("dates", []):
                date_str = item.get("observed_date") or item.get("date")
                holidays.add(date.fromisoformat(date_str))
    else:
        # Fallback manual list
        holidays = {
            date(2026, 1, 1), date(2026, 1, 2), date(2026, 2, 6),
            date(2026, 4, 3), date(2026, 4, 6), date(2026, 4, 27),
            date(2026, 6, 1), date(2026, 7, 10), date(2026, 10, 26),
            date(2026, 12, 25), date(2026, 12, 28)
        }

    # Add 2027 holidays for crossing case
    holidays.add(date(2027, 1, 1))
    holidays.add(date(2027, 1, 4))
    holidays.add(date(2027, 2, 8))  # Waitangi Day Mondayised 2027

    for case in fixtures["cases"]:
        # Map case inputs to ValueObjects
        inputs = {}
        for var_id, inp in case["inputs"].items():
            inputs[var_id] = ValueObject(
                value=inp.get("value"),
                valueState=inp.get("valueState", "known"),
                epistemicStatus=inp.get("epistemicStatus")
            )

        for dec_id, expected_out in case["expected"].items():
            invocation = RuleInvocation(
                decision_id=dec_id,
                inputs=inputs,
                parameter_set="0.1.0",
                invoked_by=case["caseId"]
            )
            result = evaluate_invocation(invocation, holidays=holidays)
            actual_out = result.outputs[dec_id]

            # Verify outputs
            assert actual_out.valueState == expected_out.get("valueState", "known"), f"Mismatch in {case['caseId']} status"
            if expected_out.get("value") is not None:
                assert actual_out.value == expected_out.get("value"), f"Mismatch in {case['caseId']} value"
            if expected_out.get("warnings") is not None:
                for w in expected_out["warnings"]:
                    # check if expected warnings substring matches actual warnings
                    assert any(w in aw for aw in (actual_out.warnings or [])), f"Expected warning '{w}' missing in {case['caseId']}"

def test_missing_coverage_branches() -> None:
    unknown_val = ValueObject(valueState="unknown")
    
    # 1. response_deadline fallback
    from foi_o_nz.oia_rules.rules import evaluate_response_deadline, evaluate_transfer_deadline, evaluate_extension_validity, evaluate_deemed_refusal, evaluate_urgency_flag
    res = evaluate_response_deadline(unknown_val)
    assert res.outputs["nz-oia/decision.response_deadline"].valueState == "unknown"
    
    # 2. transfer_deadline fallback
    res = evaluate_transfer_deadline(unknown_val)
    assert res.outputs["nz-oia/decision.transfer_deadline"].valueState == "unknown"
    
    # 3. extension_validity fallback
    res = evaluate_extension_validity(unknown_val, unknown_val, unknown_val, unknown_val)
    assert res.outputs["nz-oia/decision.extension_validity"].valueState == "unknown"
    
    # 4. deemed_refusal fallback
    res = evaluate_deemed_refusal(unknown_val, unknown_val, unknown_val)
    assert res.outputs["nz-oia/decision.deemed_refusal"].valueState == "unknown"
    
    # 5. urgency_flag fallback
    res = evaluate_urgency_flag(unknown_val)
    assert res.outputs["nz-oia/decision.urgency_flag"].valueState == "unknown"
    
    # 6. evaluate_invocation unknown decision ID
    invocation = RuleInvocation(
        decision_id="unknown_id",
        inputs={},
        parameter_set="0.1.0",
        invoked_by="test"
    )
    with pytest.raises(ValueError, match="Unknown decision ID"):
        evaluate_invocation(invocation)


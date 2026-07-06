import json
import sys
from datetime import date, datetime, UTC
from pathlib import Path

# Add paths to PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, "/Volumes/PortableSSD/GitHub/foi-o/src")

from foi_o_nz.dates import calculate_indicative_clock
from foi_o_nz.oia_rules import (
    RuleInvocation,
    ValueObject,
    evaluate_invocation,
)

def run_diff():
    rules_dir = Path(__file__).parent
    fixtures_path = rules_dir / "fixtures" / "oia-clock-fixtures.json"
    with open(fixtures_path, encoding="utf-8") as f:
        fixtures = json.load(f)

    # Use standard 2026 holidays snapshot
    holidays = {
        date(2026, 1, 1), date(2026, 1, 2), date(2026, 2, 6),
        date(2026, 4, 3), date(2026, 4, 6), date(2026, 4, 27),
        date(2026, 6, 1), date(2026, 7, 10), date(2026, 10, 26),
        date(2026, 12, 25), date(2026, 12, 28),
        # 2027
        date(2027, 1, 1), date(2027, 1, 4), date(2027, 2, 8)
    }

    divergences = []

    for case in fixtures["cases"]:
        case_id = case["caseId"]
        inputs = {}
        for var_id, inp in case["inputs"].items():
            inputs[var_id] = ValueObject(
                value=inp.get("value"),
                valueState=inp.get("valueState", "known"),
                epistemicStatus=inp.get("epistemicStatus")
            )

        # 1. Run new rules module
        # response_deadline
        resp_inv = RuleInvocation(
            decision_id="nz-oia/decision.response_deadline",
            inputs=inputs,
            parameter_set="0.1.0",
            invoked_by=case_id
        )
        res_new_resp = evaluate_invocation(resp_inv, holidays=holidays)
        new_resp_val = res_new_resp.outputs["nz-oia/decision.response_deadline"].value

        # transfer_deadline
        trans_inv = RuleInvocation(
            decision_id="nz-oia/decision.transfer_deadline",
            inputs=inputs,
            parameter_set="0.1.0",
            invoked_by=case_id
        )
        res_new_trans = evaluate_invocation(trans_inv, holidays=holidays)
        new_trans_val = res_new_trans.outputs["nz-oia/decision.transfer_deadline"].value

        # 2. Run existing foi-o dates module
        receipt_date_vo = inputs.get("nz-oia/variable.receipt_date")
        if receipt_date_vo and receipt_date_vo.valueState == "known" and receipt_date_vo.value:
            dt = datetime.combine(date.fromisoformat(receipt_date_vo.value), datetime.min.time(), tzinfo=UTC)
            clock = calculate_indicative_clock(dt, holidays=holidays)
            if clock:
                old_resp_val = clock.decision_due_date.isoformat()
                old_trans_val = clock.transfer_due_date.isoformat()

                if new_resp_val != old_resp_val:
                    divergences.append({
                        "caseId": case_id,
                        "decision": "nz-oia/decision.response_deadline",
                        "old": old_resp_val,
                        "new": new_resp_val
                    })
                if new_trans_val != old_trans_val:
                    divergences.append({
                        "caseId": case_id,
                        "decision": "nz-oia/decision.transfer_deadline",
                        "old": old_trans_val,
                        "new": new_trans_val
                    })
            else:
                if new_resp_val is not None or new_trans_val is not None:
                    divergences.append({
                        "caseId": case_id,
                        "decision": "multiple",
                        "old": None,
                        "new": "has_values"
                    })
        else:
            # Missingness/unknown cases
            pass

    if divergences:
        print(f"FAILED: Found {len(divergences)} divergences!")
        for div in divergences:
            print(f"Case: {div['caseId']}, Dec: {div['decision']}, Old kernel: {div['old']}, New rules: {div['new']}")
        sys.exit(1)
    else:
        print("SUCCESS: 100% agreement between old kernel and new rules module!")

if __name__ == "__main__":
    run_diff()

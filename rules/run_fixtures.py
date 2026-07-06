import json
import os
import sys
from datetime import date, datetime, UTC
from pathlib import Path

# Add paths to PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, "/Volumes/PortableSSD/GitHub/foi-o/src")

from foi_o_nz.oia_rules import (
    RuleInvocation,
    ValueObject,
    evaluate_invocation,
)

def run():
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

    traces_dir = rules_dir / "traces"
    traces_dir.mkdir(parents=True, exist_ok=True)

    timestamp_str = datetime.now(UTC).isoformat().replace("+00:00", "Z")

    for case in fixtures["cases"]:
        case_id = case["caseId"]
        inputs = {}
        inputs_trace = {}
        for var_id, inp in case["inputs"].items():
            vo = ValueObject(
                value=inp.get("value"),
                valueState=inp.get("valueState", "known"),
                epistemicStatus=inp.get("epistemicStatus")
            )
            inputs[var_id] = vo
            # Inputs block in trace
            vo_dict = {"valueState": vo.valueState}
            if vo.value is not None:
                vo_dict["value"] = vo.value
            inputs_trace[var_id] = vo_dict

        outputs_trace = {}
        steps_trace = []

        for dec_id, expected_out in case["expected"].items():
            invocation = RuleInvocation(
                decision_id=dec_id,
                inputs=inputs,
                parameter_set="0.1.0",
                invoked_by=case_id
            )
            result = evaluate_invocation(invocation, holidays=holidays)
            actual_out = result.outputs[dec_id]

            vo_dict = {"valueState": actual_out.valueState}
            if actual_out.value is not None:
                vo_dict["value"] = actual_out.value
            if actual_out.warnings:
                vo_dict["warnings"] = actual_out.warnings
            outputs_trace[dec_id] = vo_dict

            # Construct trace step
            if result.trace_step:
                step = dict(result.trace_step)
                # Ensure it matches the PIC trace schema step structure
                step["refs"] = {"decision": dec_id}
                # Normalize stepId to simple name
                step["stepId"] = dec_id.split(".")[-1]
                steps_trace.append(step)

        # Build full trace document
        trace_doc = {
            "conformsTo": "pic-traces/0.1.0",
            "caseId": case_id,
            "packageRef": {"id": "nz-oia-clocks", "version": "0.1.0"},
            "engine": {"name": "foi-o-nz", "version": "0.9.0", "adapter": "oia_rules"},
            "timestamp": timestamp_str,
            "inputs": inputs_trace,
            "outputs": outputs_trace,
            "steps": steps_trace
        }

        # Write trace file
        filename = case_id.replace("nz-oia/fixture.", "") + "-trace.json"
        with open(traces_dir / filename, "w", encoding="utf-8") as tf:
            json.dump(trace_doc, tf, indent=2)

    print(f"Generated {len(fixtures['cases'])} traces in {traces_dir}")

if __name__ == "__main__":
    run()

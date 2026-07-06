from datetime import date
from typing import Iterable

from foi_o_nz.dates import add_working_days
from foi_o_nz.oia_rules.types import (
    DiscretionPoint,
    RuleInvocation,
    RuleResult,
    ValueObject,
)

def nz_working_days(start: date, n: int, calendar: Iterable[date] | None = None) -> date:
    """Wrapper around add_working_days to satisfy track requirements."""
    return add_working_days(start, n, holidays=calendar, include_oia_summer_exclusion=True)

def evaluate_response_deadline(receipt_date: ValueObject, holidays: Iterable[date] | None = None) -> RuleResult:
    if receipt_date.valueState == "not_provided":
        val = ValueObject(
            value=None,
            valueState="unknown",
            warnings=["receipt date is required to calculate the response deadline"]
        )
        return RuleResult(
            outputs={"nz-oia/decision.response_deadline": val},
            trace_step={
                "stepId": "nz-oia/decision.response_deadline",
                "kind": "decision",
                "inputsUsed": ["nz-oia/variable.receipt_date"],
                "parameterVersions": [{"id": "nz-oia/parameter.working_day_limit", "effectiveFrom": "2025-04-05"}],
                "result": {"valueState": "unknown", "warnings": val.warnings},
                "sourceRefs": ["OIA 1982 s 15"]
            }
        )
    if receipt_date.valueState == "verified_stale":
        val = ValueObject(
            value=None,
            valueState="unknown",
            warnings=["receipt date was verified but may be stale"]
        )
        return RuleResult(
            outputs={"nz-oia/decision.response_deadline": val},
            trace_step={
                "stepId": "nz-oia/decision.response_deadline",
                "kind": "decision",
                "inputsUsed": ["nz-oia/variable.receipt_date"],
                "parameterVersions": [{"id": "nz-oia/parameter.working_day_limit", "effectiveFrom": "2025-04-05"}],
                "result": {"valueState": "unknown", "warnings": val.warnings},
                "sourceRefs": ["OIA 1982 s 2", "OIA 1982 s 15"]
            }
        )
    if receipt_date.valueState != "known" or not receipt_date.value:
        val = ValueObject(value=None, valueState="unknown")
        return RuleResult(outputs={"nz-oia/decision.response_deadline": val}, trace_step={})

    receipt_dt = date.fromisoformat(receipt_date.value)
    due_dt = add_working_days(receipt_dt, 20, holidays=holidays)
    due_str = due_dt.isoformat()
    val = ValueObject(value=due_str, valueState="known")
    return RuleResult(
        outputs={"nz-oia/decision.response_deadline": val},
        trace_step={
            "stepId": "nz-oia/decision.response_deadline",
            "kind": "decision",
            "inputsUsed": ["nz-oia/variable.receipt_date"],
            "parameterVersions": [{"id": "nz-oia/parameter.working_day_limit", "effectiveFrom": "2025-04-05"}],
            "result": {"value": due_str, "valueState": "known"},
            "sourceRefs": ["OIA 1982 s 2", "OIA 1982 s 15"]
        }
    )

def evaluate_transfer_deadline(receipt_date: ValueObject, holidays: Iterable[date] | None = None) -> RuleResult:
    if receipt_date.valueState != "known" or not receipt_date.value:
        val = ValueObject(value=None, valueState="unknown")
        return RuleResult(outputs={"nz-oia/decision.transfer_deadline": val}, trace_step={})

    receipt_dt = date.fromisoformat(receipt_date.value)
    due_dt = add_working_days(receipt_dt, 10, holidays=holidays)
    due_str = due_dt.isoformat()
    val = ValueObject(value=due_str, valueState="known")
    return RuleResult(
        outputs={"nz-oia/decision.transfer_deadline": val},
        trace_step={
            "stepId": "nz-oia/decision.transfer_deadline",
            "kind": "decision",
            "inputsUsed": ["nz-oia/variable.receipt_date"],
            "parameterVersions": [{"id": "nz-oia/parameter.transfer_limit", "effectiveFrom": "2025-04-05"}],
            "result": {"value": due_str, "valueState": "known"},
            "sourceRefs": ["OIA 1982 s 2", "OIA 1982 s 14"]
        }
    )

def evaluate_extension_validity(
    receipt_date: ValueObject,
    extension_notice_date: ValueObject,
    extension_ground: ValueObject,
    extension_period_working_days: ValueObject,
    holidays: Iterable[date] | None = None
) -> RuleResult:
    if (receipt_date.valueState != "known" or not receipt_date.value or
        extension_notice_date.valueState != "known" or not extension_notice_date.value or
        extension_ground.valueState != "known" or extension_ground.value is None or
        extension_period_working_days.valueState != "known" or extension_period_working_days.value is None):
        return RuleResult(
            outputs={"nz-oia/decision.extension_validity": ValueObject(value=None, valueState="unknown")},
            trace_step={}
        )

    receipt_dt = date.fromisoformat(receipt_date.value)
    notice_dt = date.fromisoformat(extension_notice_date.value)
    original_deadline = add_working_days(receipt_dt, 20, holidays=holidays)

    if notice_dt > original_deadline:
        val = ValueObject(value=False, valueState="known", warnings=["extension notice after original deadline"])
        return RuleResult(
            outputs={"nz-oia/decision.extension_validity": val},
            trace_step={
                "stepId": "nz-oia/decision.extension_validity",
                "kind": "decision",
                "inputsUsed": [
                    "nz-oia/variable.receipt_date",
                    "nz-oia/variable.extension_notice_date",
                    "nz-oia/variable.extension_ground",
                    "nz-oia/variable.extension_period_working_days"
                ],
                "parameterVersions": [],
                "result": {"value": False, "valueState": "known", "warnings": val.warnings},
                "sourceRefs": ["OIA 1982 s 15", "OIA 1982 s 15A"]
            }
        )

    if extension_ground.value not in {"large_quantity", "consultation_required"}:
        val = ValueObject(
            value=False,
            valueState="known",
            warnings=["extension ground is not one of the verified statutory ground labels"]
        )
        return RuleResult(
            outputs={"nz-oia/decision.extension_validity": val},
            trace_step={
                "stepId": "nz-oia/decision.extension_validity",
                "kind": "decision",
                "inputsUsed": [
                    "nz-oia/variable.receipt_date",
                    "nz-oia/variable.extension_notice_date",
                    "nz-oia/variable.extension_ground",
                    "nz-oia/variable.extension_period_working_days"
                ],
                "parameterVersions": [],
                "result": {"value": False, "valueState": "known", "warnings": val.warnings},
                "sourceRefs": ["OIA 1982 s 15A"]
            }
        )

    val = ValueObject(value=True, valueState="known", warnings=["extension period reasonableness requires human review"])
    discretion = DiscretionPoint(
        discretion_id="nz-oia/discretion.extension_reasonableness",
        message="extension period reasonableness requires human review",
        metadata={"extension_period_working_days": extension_period_working_days.value}
    )
    return RuleResult(
        outputs={"nz-oia/decision.extension_validity": val},
        trace_step={
            "stepId": "nz-oia/decision.extension_validity",
            "kind": "decision",
            "inputsUsed": [
                "nz-oia/variable.receipt_date",
                "nz-oia/variable.extension_notice_date",
                "nz-oia/variable.extension_ground",
                "nz-oia/variable.extension_period_working_days"
            ],
            "parameterVersions": [],
            "result": {"value": True, "valueState": "known", "warnings": val.warnings},
            "sourceRefs": ["OIA 1982 s 15", "OIA 1982 s 15A"]
        },
        discretion_required=discretion
    )

def evaluate_deemed_refusal(
    receipt_date: ValueObject,
    current_date: ValueObject,
    response_sent: ValueObject,
    holidays: Iterable[date] | None = None
) -> RuleResult:
    if (receipt_date.valueState != "known" or not receipt_date.value or
        current_date.valueState != "known" or not current_date.value or
        response_sent.valueState != "known" or response_sent.value is None):
        return RuleResult(
            outputs={"nz-oia/decision.deemed_refusal": ValueObject(value=None, valueState="unknown")},
            trace_step={}
        )

    if response_sent.value is True:
        val = ValueObject(value=False, valueState="known")
        return RuleResult(
            outputs={"nz-oia/decision.deemed_refusal": val},
            trace_step={
                "stepId": "nz-oia/decision.deemed_refusal",
                "kind": "decision",
                "inputsUsed": ["nz-oia/variable.receipt_date", "nz-oia/variable.current_date", "nz-oia/variable.response_sent"],
                "parameterVersions": [],
                "result": {"value": False, "valueState": "known"},
                "sourceRefs": ["OIA 1982 s 15", "OIA 1982 s 28"]
            }
        )

    receipt_dt = date.fromisoformat(receipt_date.value)
    current_dt = date.fromisoformat(current_date.value)
    deadline = add_working_days(receipt_dt, 20, holidays=holidays)

    is_refusal = current_dt > deadline
    val = ValueObject(value=is_refusal, valueState="known")
    return RuleResult(
        outputs={"nz-oia/decision.deemed_refusal": val},
        trace_step={
            "stepId": "nz-oia/decision.deemed_refusal",
            "kind": "decision",
            "inputsUsed": ["nz-oia/variable.receipt_date", "nz-oia/variable.current_date", "nz-oia/variable.response_sent"],
            "parameterVersions": [],
            "result": {"value": is_refusal, "valueState": "known"},
            "sourceRefs": ["OIA 1982 s 15", "OIA 1982 s 28"]
        }
    )

def evaluate_urgency_flag(urgency_reasons_provided: ValueObject) -> RuleResult:
    if urgency_reasons_provided.valueState != "known" or urgency_reasons_provided.value is None:
        return RuleResult(
            outputs={"nz-oia/decision.urgency_flag": ValueObject(value=None, valueState="unknown")},
            trace_step={}
        )

    if urgency_reasons_provided.value is True:
        val = ValueObject(
            value="human_decision_required",
            valueState="known",
            warnings=["urgency affects routing only and cannot be machine certified"]
        )
        discretion = DiscretionPoint(
            discretion_id="nz-oia/discretion.urgency_assessment",
            message="urgency affects routing only and cannot be machine certified",
            metadata={}
        )
        return RuleResult(
            outputs={"nz-oia/decision.urgency_flag": val},
            trace_step={
                "stepId": "nz-oia/decision.urgency_flag",
                "kind": "decision",
                "inputsUsed": ["nz-oia/variable.urgency_reasons_provided"],
                "parameterVersions": [],
                "result": {"value": "human_decision_required", "valueState": "known", "warnings": val.warnings},
                "sourceRefs": ["OIA 1982 s 12(3)"]
            },
            discretion_required=discretion
        )

    val = ValueObject(value="not_requested", valueState="known")
    return RuleResult(
        outputs={"nz-oia/decision.urgency_flag": val},
        trace_step={
            "stepId": "nz-oia/decision.urgency_flag",
            "kind": "decision",
            "inputsUsed": ["nz-oia/variable.urgency_reasons_provided"],
            "parameterVersions": [],
            "result": {"value": "not_requested", "valueState": "known"},
            "sourceRefs": ["OIA 1982 s 12(3)"]
        }
    )

def evaluate_invocation(invocation: RuleInvocation, holidays: Iterable[date] | None = None) -> RuleResult:
    inputs = invocation.inputs
    dec_id = invocation.decision_id

    if dec_id == "nz-oia/decision.response_deadline":
        receipt = inputs.get("nz-oia/variable.receipt_date") or ValueObject(valueState="not_provided")
        return evaluate_response_deadline(receipt, holidays=holidays)

    if dec_id == "nz-oia/decision.transfer_deadline":
        receipt = inputs.get("nz-oia/variable.receipt_date") or ValueObject(valueState="not_provided")
        return evaluate_transfer_deadline(receipt, holidays=holidays)

    if dec_id == "nz-oia/decision.extension_validity":
        receipt = inputs.get("nz-oia/variable.receipt_date") or ValueObject(valueState="not_provided")
        notice = inputs.get("nz-oia/variable.extension_notice_date") or ValueObject(valueState="not_provided")
        ground = inputs.get("nz-oia/variable.extension_ground") or ValueObject(valueState="not_provided")
        period = inputs.get("nz-oia/variable.extension_period_working_days") or ValueObject(valueState="not_provided")
        return evaluate_extension_validity(receipt, notice, ground, period, holidays=holidays)

    if dec_id == "nz-oia/decision.deemed_refusal":
        receipt = inputs.get("nz-oia/variable.receipt_date") or ValueObject(valueState="not_provided")
        current = inputs.get("nz-oia/variable.current_date") or ValueObject(valueState="not_provided")
        sent = inputs.get("nz-oia/variable.response_sent") or ValueObject(valueState="not_provided")
        return evaluate_deemed_refusal(receipt, current, sent, holidays=holidays)

    if dec_id == "nz-oia/decision.urgency_flag":
        reasons = inputs.get("nz-oia/variable.urgency_reasons_provided") or ValueObject(valueState="not_provided")
        return evaluate_urgency_flag(reasons)

    raise ValueError(f"Unknown decision ID: {dec_id}")

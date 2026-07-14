"""Bridge isolated OIA rules into foi-o process/CLI surfaces.

Keeps ``oia_rules`` import-isolated from normalise/CLI while allowing the
process pipeline to dispatch deterministic deadline decisions through
``evaluate_response_deadline`` / ``evaluate_transfer_deadline``.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date, datetime
from typing import Any

from foi_o_nz.dates import (
    PUBLIC_HOLIDAY_WARNING,
    REGIONAL_ANNIVERSARY_WARNING,
    STANDARD_CLOCK_WARNING,
    SUMMER_EXCLUSION_WARNING,
    HolidayCalendar,
    calculate_indicative_clock,
)
from foi_o_nz.models import LegalClock
from foi_o_nz.oia_rules.rules import (
    evaluate_response_deadline,
    evaluate_transfer_deadline,
)
from foi_o_nz.oia_rules.types import ValueObject

OIA_RULES_CALCULATION_METHOD = "oia_rules_response_transfer_deadline_v0.1.0"


def _holiday_iterable(
    holidays: Iterable[date] | HolidayCalendar | None,
) -> tuple[set[date], HolidayCalendar | None]:
    if holidays is None:
        return set(), None
    if isinstance(holidays, HolidayCalendar):
        return set(holidays.dates), holidays
    return set(holidays), None


def legal_clock_from_oia_rules(
    received_at: datetime | None,
    *,
    holidays: Iterable[date] | HolidayCalendar | None = None,
    include_oia_summer_exclusion: bool = True,
) -> LegalClock | None:
    """Build a ``LegalClock`` using the isolated OIA rules module.

    When summer exclusion is disabled, falls back to the existing dates helper
    because the rules module currently always applies OIA summer exclusion.
    """
    if received_at is None:
        return None
    if not include_oia_summer_exclusion:
        return calculate_indicative_clock(
            received_at,
            holidays=holidays,
            include_oia_summer_exclusion=False,
        )

    holiday_set, calendar = _holiday_iterable(holidays)
    receipt = ValueObject(
        value=received_at.date().isoformat(),
        valueState="known",
    )
    response = evaluate_response_deadline(receipt, holidays=holiday_set or None)
    transfer = evaluate_transfer_deadline(receipt, holidays=holiday_set or None)
    response_out = response.outputs.get("nz-oia/decision.response_deadline")
    transfer_out = transfer.outputs.get("nz-oia/decision.transfer_deadline")

    decision_due: date | None = None
    transfer_due: date | None = None
    if response_out is not None and response_out.valueState == "known" and response_out.value:
        decision_due = date.fromisoformat(str(response_out.value))
    if transfer_out is not None and transfer_out.valueState == "known" and transfer_out.value:
        transfer_due = date.fromisoformat(str(transfer_out.value))

    warnings = [STANDARD_CLOCK_WARNING, SUMMER_EXCLUSION_WARNING]
    if not holiday_set:
        warnings.append(PUBLIC_HOLIDAY_WARNING)
    elif calendar is not None:
        warnings.append(
            "public_holiday_calendar_supplied: "
            f"{calendar.source_name or 'unknown'}; status={calendar.source_status}"
        )
        if not calendar.regional_anniversary_days_included:
            warnings.append(REGIONAL_ANNIVERSARY_WARNING)
    warnings.append("oia_rules_dispatch: deadlines from foi_o_nz.oia_rules pure functions")

    for out in (response_out, transfer_out):
        if out is not None and out.warnings:
            warnings.extend(out.warnings)

    return LegalClock(
        received_at=received_at,
        decision_due_date=decision_due,
        transfer_due_date=transfer_due,
        calculation_method=OIA_RULES_CALCULATION_METHOD,
        calendar_source_name=calendar.source_name if calendar is not None else None,
        calendar_source_url=calendar.source_url if calendar is not None else None,
        calendar_source_status=calendar.source_status if calendar is not None else None,
        calendar_retrieved_at=calendar.retrieved_at if calendar is not None else None,
        regional_anniversary_days_included=(
            calendar.regional_anniversary_days_included if calendar is not None else None
        ),
        confidence=0.62 if holiday_set else 0.42,
        warnings=warnings,
    )


def deadline_event_quality_flags(legal_clock: LegalClock | None) -> list[str]:
    """Quality flags for DeadlineCalculated events produced via rules dispatch."""
    flags = ["indicative_deadline_not_certified"]
    if legal_clock is not None and legal_clock.calculation_method == OIA_RULES_CALCULATION_METHOD:
        flags.append("oia_rules_dispatch")
    return flags


def rules_trace_payload(legal_clock: LegalClock | None) -> dict[str, Any]:
    """Optional payload fragment recording the rules calculation method."""
    if legal_clock is None:
        return {}
    return {
        "calculation_method": legal_clock.calculation_method,
        "oia_rules": legal_clock.calculation_method == OIA_RULES_CALCULATION_METHOD,
    }

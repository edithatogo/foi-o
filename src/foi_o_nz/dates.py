"""Indicative New Zealand OIA/LGOIMA clock helpers.

The functions in this module are deliberately conservative. They implement a
repeatable machine calculation for workflow support and reporting experiments;
they do not certify statutory compliance.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

from foi_o_nz.models import LegalClock

STANDARD_CLOCK_WARNING = (
    "indicative_only_not_legal_advice: verify against the current Act, official "
    "public-holiday calendars, regional anniversary days if relevant, and agency records"
)

SUMMER_EXCLUSION_WARNING = (
    "oia_summer_exclusion_applied: 25 December through 15 January inclusive treated "
    "as non-working days"
)

PUBLIC_HOLIDAY_WARNING = (
    "public_holidays_not_supplied: fixed/movable NZ public holidays other than weekends "
    "and optional OIA summer exclusion were not calculated"
)

REGIONAL_ANNIVERSARY_WARNING = (
    "regional_anniversary_days_not_included: regional anniversary days vary by area and "
    "must be supplied separately when relevant"
)


@dataclass(frozen=True, slots=True)
class HolidayCalendar:
    """Source-aware holiday calendar used by indicative clock calculations."""

    dates: frozenset[date]
    source_name: str | None = None
    source_url: str | None = None
    source_status: str = "unknown"
    retrieved_at: datetime | None = None
    regional_anniversary_days_included: bool = False

    def __iter__(self) -> Iterator[date]:
        """Iterate over dates for compatibility with existing holiday arguments."""
        return iter(self.dates)


def parse_datetime(value: Any) -> datetime | None:
    """Parse common FYI/archive timestamp values into timezone-aware UTC datetimes."""
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day, tzinfo=UTC)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        # Pydantic accepts trailing Z; datetime.fromisoformat does not on all versions.
        if text.endswith("Z"):
            text = f"{text[:-1]}+00:00"
        try:
            parsed = datetime.fromisoformat(text)
        except ValueError:
            return None
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)
    return None


def is_oia_summer_excluded(day: date) -> bool:
    """Return true for 25 December through 15 January inclusive."""
    return (day.month == 12 and day.day >= 25) or (day.month == 1 and day.day <= 15)


def is_working_day(
    day: date,
    *,
    holidays: Iterable[date] | None = None,
    include_oia_summer_exclusion: bool = True,
) -> bool:
    """Return whether ``day`` is counted as a machine working day."""
    if day.weekday() >= 5:
        return False
    if include_oia_summer_exclusion and is_oia_summer_excluded(day):
        return False
    return not (holidays is not None and day in set(holidays))


def add_working_days(
    start_day: date,
    working_days: int,
    *,
    holidays: Iterable[date] | None = None,
    include_oia_summer_exclusion: bool = True,
) -> date:
    """Add working days, excluding the receipt/start day from the count."""
    if working_days < 0:
        raise ValueError("working_days must be non-negative")
    current = start_day
    remaining = working_days
    holiday_set = set(holidays or [])
    while remaining > 0:
        current += timedelta(days=1)
        if is_working_day(
            current,
            holidays=holiday_set,
            include_oia_summer_exclusion=include_oia_summer_exclusion,
        ):
            remaining -= 1
    return current


def load_holiday_dates(path: Path) -> set[date]:
    """Load holiday dates from JSON/YAML list or mapping values.

    Accepted values are ISO date strings. This keeps the repository free of a
    baked-in public holiday table while allowing operators to provide official
    calendars in CI or production runs.
    """
    return set(load_holiday_calendar(path).dates)


def load_holiday_calendar(path: Path) -> HolidayCalendar:
    """Load a source-aware holiday calendar from JSON/YAML."""
    import json

    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yaml", ".yml"}:
        import yaml

        data = yaml.safe_load(text)
    else:
        data = json.loads(text)
    values: list[Any]
    if isinstance(data, list):
        values = data
    elif isinstance(data, dict):
        maybe_dates = data.get("dates") or data.get("holidays") or list(data.values())
        values = maybe_dates if isinstance(maybe_dates, list) else list(data.values())
    else:
        raise ValueError(f"Unsupported holiday calendar structure in {path}")
    holidays: set[date] = set()
    for value in values:
        if isinstance(value, dict):
            value = value.get("observed_date") or value.get("date")
        if not isinstance(value, str):
            continue
        holidays.add(date.fromisoformat(value[:10]))
    metadata = data if isinstance(data, dict) else {}
    return HolidayCalendar(
        dates=frozenset(holidays),
        source_name=metadata.get("source_name"),
        source_url=metadata.get("source_url"),
        source_status=str(metadata.get("source_status") or "unknown"),
        retrieved_at=parse_datetime(metadata.get("retrieved_at")),
        regional_anniversary_days_included=bool(metadata.get("regional_anniversary_days_included")),
    )


def calculate_indicative_clock(
    received_at: datetime | None,
    *,
    decision_working_days: int = 20,
    transfer_working_days: int = 10,
    holidays: Iterable[date] | None = None,
    include_oia_summer_exclusion: bool = True,
) -> LegalClock | None:
    """Build an indicative legal-clock annotation for a request profile."""
    if received_at is None:
        return None
    calendar = holidays if isinstance(holidays, HolidayCalendar) else None
    holiday_set = set(calendar.dates if calendar is not None else holidays or [])
    warnings = [STANDARD_CLOCK_WARNING]
    if include_oia_summer_exclusion:
        warnings.append(SUMMER_EXCLUSION_WARNING)
    if not holiday_set:
        warnings.append(PUBLIC_HOLIDAY_WARNING)
    elif calendar is not None:
        warnings.append(
            "public_holiday_calendar_supplied: "
            f"{calendar.source_name or 'unknown'}; status={calendar.source_status}"
        )
        if not calendar.regional_anniversary_days_included:
            warnings.append(REGIONAL_ANNIVERSARY_WARNING)
    received_day = received_at.date()
    return LegalClock(
        received_at=received_at,
        decision_due_date=add_working_days(
            received_day,
            decision_working_days,
            holidays=holiday_set,
            include_oia_summer_exclusion=include_oia_summer_exclusion,
        ),
        transfer_due_date=add_working_days(
            received_day,
            transfer_working_days,
            holidays=holiday_set,
            include_oia_summer_exclusion=include_oia_summer_exclusion,
        ),
        calculation_method="weekday_plus_optional_oia_summer_exclusion_v0.2.0",
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

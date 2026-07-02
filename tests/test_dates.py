from __future__ import annotations

from datetime import UTC, date, datetime
from pathlib import Path

from foi_o_nz.dates import (
    PUBLIC_HOLIDAY_WARNING,
    add_working_days,
    calculate_indicative_clock,
    is_oia_summer_excluded,
    load_holiday_calendar,
    load_holiday_dates,
    parse_datetime,
)
from foi_o_nz.validation import validate_json_schema

HOLIDAY_CALENDAR_EXAMPLE = Path("examples/nz-public-holidays-2026.govt-nz.json")
HOLIDAY_CALENDAR_SCHEMA = Path("schemas/json/holiday-calendar.schema.json")


def test_parse_datetime_handles_z_suffix() -> None:
    parsed = parse_datetime("2026-06-01T12:00:00Z")

    assert parsed == datetime(2026, 6, 1, 12, 0, tzinfo=UTC)


def test_add_working_days_skips_weekends() -> None:
    assert add_working_days(date(2026, 6, 5), 1) == date(2026, 6, 8)


def test_summer_exclusion() -> None:
    assert is_oia_summer_excluded(date(2026, 12, 25))
    assert is_oia_summer_excluded(date(2027, 1, 15))
    assert not is_oia_summer_excluded(date(2027, 1, 16))


def test_calculate_indicative_clock() -> None:
    clock = calculate_indicative_clock(datetime(2026, 6, 1, tzinfo=UTC))

    assert clock is not None
    assert clock.decision_due_date is not None
    assert clock.transfer_due_date is not None
    assert clock.warnings


def test_load_holiday_dates(tmp_path) -> None:
    calendar = tmp_path / "holidays.json"
    calendar.write_text('{"dates": ["2026-06-02"]}', encoding="utf-8")

    holidays = load_holiday_dates(calendar)

    assert date(2026, 6, 2) in holidays


def test_load_holiday_calendar_preserves_source_metadata() -> None:
    calendar = load_holiday_calendar(HOLIDAY_CALENDAR_EXAMPLE)

    assert date(2026, 1, 1) in calendar.dates
    assert date(2026, 4, 3) in calendar.dates
    assert date(2026, 12, 28) in calendar.dates
    assert calendar.source_name == "Govt.nz public holidays and anniversary days"
    assert (
        calendar.source_url
        == "https://www.govt.nz/browse/work/public-holidays-and-work/public-holidays-and-anniversary-dates/"
    )
    assert calendar.source_status == "official_snapshot"
    assert calendar.retrieved_at == datetime(2026, 7, 2, tzinfo=UTC)
    assert calendar.regional_anniversary_days_included is False


def test_add_working_days_uses_public_holiday_calendar() -> None:
    calendar = load_holiday_calendar(HOLIDAY_CALENDAR_EXAMPLE)

    assert add_working_days(date(2026, 5, 29), 1) == date(2026, 6, 1)
    assert add_working_days(date(2026, 5, 29), 1, holidays=calendar) == date(2026, 6, 2)


def test_calculate_indicative_clock_records_calendar_source() -> None:
    calendar = load_holiday_calendar(HOLIDAY_CALENDAR_EXAMPLE)

    clock = calculate_indicative_clock(
        datetime(2026, 5, 29, tzinfo=UTC),
        decision_working_days=1,
        transfer_working_days=1,
        holidays=calendar,
    )

    assert clock is not None
    assert clock.decision_due_date == date(2026, 6, 2)
    assert clock.transfer_due_date == date(2026, 6, 2)
    assert clock.calendar_source_name == "Govt.nz public holidays and anniversary days"
    assert clock.calendar_source_status == "official_snapshot"
    assert str(clock.calendar_source_url) == (
        "https://www.govt.nz/browse/work/public-holidays-and-work/"
        "public-holidays-and-anniversary-dates/"
    )
    assert clock.calendar_retrieved_at == datetime(2026, 7, 2, tzinfo=UTC)
    assert PUBLIC_HOLIDAY_WARNING not in clock.warnings
    assert any("regional_anniversary_days_not_included" in item for item in clock.warnings)


def test_committed_holiday_calendar_fixture_is_schema_valid() -> None:
    validation = validate_json_schema(HOLIDAY_CALENDAR_EXAMPLE, HOLIDAY_CALENDAR_SCHEMA)

    assert validation.ok, validation.errors

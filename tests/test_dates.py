from __future__ import annotations

from datetime import UTC, date, datetime

from foi_o_nz.dates import add_working_days, calculate_indicative_clock, is_oia_summer_excluded, load_holiday_dates, parse_datetime


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

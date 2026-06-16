"""Date-parsing tests.

`test_leap_year_clamping` FAILS BY DESIGN — it encodes the spec that an
invalid day-for-month clamps to the last valid day, which parse_due does
not yet do. Tied to the leap-year seeded bug.
"""

import datetime as dt

import pytest

from taskflow.dates.parsing import ParseError, parse_due


def test_iso_format():
    assert parse_due("2026-07-04") == dt.date(2026, 7, 4)


def test_today_tomorrow(fixed_today):
    assert parse_due("today", today=fixed_today) == fixed_today
    assert parse_due("tomorrow", today=fixed_today) == dt.date(2026, 6, 16)


def test_relative_days(fixed_today):
    assert parse_due("10d", today=fixed_today) == dt.date(2026, 6, 25)


def test_month_day(fixed_today):
    assert parse_due("jul 4", today=fixed_today) == dt.date(2026, 7, 4)


def test_unknown_month():
    with pytest.raises(ParseError):
        parse_due("foo 1")


def test_leap_year_clamping():
    """feb 29 in a non-leap year must clamp to feb 28. (Currently FAILS.)"""
    non_leap = dt.date(2027, 1, 1)  # 2027 is not a leap year
    assert parse_due("feb 29", today=non_leap) == dt.date(2027, 2, 28)

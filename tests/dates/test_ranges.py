import datetime as dt

import pytest

from taskflow.dates.ranges import DateRange, overdue_as_of


def test_range_contains_and_days():
    r = DateRange(dt.date(2026, 6, 1), dt.date(2026, 6, 10))
    assert r.contains(dt.date(2026, 6, 5))
    assert not r.contains(dt.date(2026, 6, 11))
    assert r.days() == 10


def test_range_rejects_inverted():
    with pytest.raises(ValueError):
        DateRange(dt.date(2026, 6, 10), dt.date(2026, 6, 1))


def test_overdue():
    as_of = dt.date(2026, 6, 15)
    assert overdue_as_of("2026-06-14", as_of)
    assert not overdue_as_of("2026-06-15", as_of)
    assert not overdue_as_of(None, as_of)

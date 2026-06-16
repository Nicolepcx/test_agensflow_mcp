"""Shared test fixtures."""

import datetime as dt

import pytest


@pytest.fixture
def fixed_today() -> dt.date:
    # A deterministic "now" for date-dependent tests. 2026-06-15 is a Monday.
    return dt.date(2026, 6, 15)

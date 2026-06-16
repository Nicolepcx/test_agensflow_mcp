"""Natural-language due-date parsing.

SEEDED BUG (cross-module, surfaces via recurrence): parse_due does NOT
clamp an invalid day-of-month to the last valid day, despite the
docstring promising it does. 'feb 29' in a non-leap year raises
ParseError instead of clamping to Feb 28. This bug is benign for one-off
tasks that never use Feb 29, but core/recurrence.py YEARLY rolls a due
date forward by a year — so a task due Feb 29 2028 (valid, leap) rolls
to Feb 29 2029 (invalid) and crashes the whole recurrence pass. The
coordination-heavy fix touches BOTH this file and recurrence.py.
"""

from __future__ import annotations

import datetime as dt
import re
from typing import Optional

from taskflow.models import today as _today

_MONTHS = {
    "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
    "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
    "aug": 8, "august": 8, "sep": 9, "september": 9, "oct": 10, "october": 10,
    "nov": 11, "november": 11, "dec": 12, "december": 12,
}


class ParseError(ValueError):
    """Raised when a due-date string cannot be parsed."""


def parse_due(s: str, *, today: Optional[dt.date] = None) -> dt.date:
    """Parse a due-date string into a date.

    Accepts: 'today', 'tomorrow', 'YYYY-MM-DD', 'Nd' (N days out),
    'feb 29' / '29 feb' (month-day, current year).

    Per spec: an invalid day-for-month (e.g. 'feb 29' in a non-leap
    year) clamps to the last valid day of that month. (The current
    implementation does NOT do this — see module docstring.)
    """
    today = today or _today()
    s = s.strip().lower()
    if not s:
        raise ParseError("empty due date")

    if s == "today":
        return today
    if s == "tomorrow":
        return today + dt.timedelta(days=1)
    if re.fullmatch(r"\d+d", s):
        return today + dt.timedelta(days=int(s[:-1]))
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
        try:
            return dt.date.fromisoformat(s)
        except ValueError as e:
            raise ParseError(str(e)) from e

    m = re.fullmatch(r"(?:(\d{1,2})\s+)?([a-z]+)(?:\s+(\d{1,2}))?", s)
    if m:
        d_before, month_name, d_after = m.groups()
        day = int(d_before or d_after or 1)
        month = _MONTHS.get(month_name)
        if month is None:
            raise ParseError(f"unknown month: {month_name}")
        # BUG: should clamp day to monthrange last day; instead constructs
        # directly and lets dt.date raise on invalid day.
        try:
            return dt.date(today.year, month, day)
        except ValueError as e:
            raise ParseError(str(e)) from e

    raise ParseError(f"could not parse due date: {s!r}")

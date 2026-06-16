"""Recurrence tests.

`test_yearly_leap_rolls_without_crash` FAILS BY DESIGN — a completed
YEARLY task due Feb 29 of a leap year rolls forward into a non-leap year,
and roll_recurrences re-parses 'feb 29' via parse_due, which raises
instead of clamping. The crash aborts the whole pass. A robust fix
coordinates dates/parsing.py (clamp) and core/recurrence.py (advance
dates safely / contain per-task errors).
"""

import datetime as dt

from taskflow.core.recurrence import roll_recurrences
from taskflow.models import Recurrence, Task


def _completed(id, due, rule):
    return Task(id=id, text="r", done=True, due=due, recurrence=rule)


def test_daily_weekly_monthly_roll():
    tasks = [
        _completed(1, "2026-06-15", Recurrence.DAILY),
        _completed(2, "2026-06-15", Recurrence.WEEKLY),
        _completed(3, "2026-06-15", Recurrence.MONTHLY),
    ]
    out = roll_recurrences(tasks)
    spawned = [t for t in out if t.parent_id is not None]
    dues = sorted(t.due for t in spawned)
    assert dues == ["2026-06-16", "2026-06-22", "2026-07-15"]


def test_non_recurring_not_rolled():
    tasks = [_completed(1, "2026-06-15", Recurrence.NONE)]
    assert roll_recurrences(tasks) == tasks


def test_yearly_leap_rolls_without_crash():
    """Completed Feb-29 yearly task must roll without crashing. (Currently FAILS.)"""
    tasks = [_completed(1, "2028-02-29", Recurrence.YEARLY)]  # 2028 is a leap year
    out = roll_recurrences(tasks)
    spawned = [t for t in out if t.parent_id is not None]
    assert len(spawned) == 1
    # Rolled into 2029 (non-leap) → should clamp to Feb 28.
    assert spawned[0].due == "2029-02-28"

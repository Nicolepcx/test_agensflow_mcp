"""Recurrence engine — spawns the next instance of a recurring task when
the current one is completed.

This is the CROSS-MODULE partner to the dates/parsing.py leap-year bug.
roll_recurrences advances a due date by the recurrence interval. For
YEARLY recurrence it bumps the year by one and re-parses via
parse_due("<month> <day>") — so a task due Feb 29 2028 (a leap year)
rolls to "feb 29" in 2029, which parse_due raises on instead of clamping
to Feb 28. One bad task aborts the whole recurrence pass because the
exception is not contained.

A correct fix coordinates THREE files:
  - dates/parsing.py  (clamp invalid day-of-month)
  - this file         (advance dates safely / contain per-task errors)
  - tests/core/test_recurrence.py (regression)
"""

from __future__ import annotations

import datetime as dt

from taskflow.dates.parsing import parse_due
from taskflow.models import Recurrence, Task, today


_MONTH_NAMES = [
    "", "jan", "feb", "mar", "apr", "may", "jun",
    "jul", "aug", "sep", "oct", "nov", "dec",
]


def _advance(due: dt.date, rule: Recurrence) -> dt.date:
    if rule == Recurrence.DAILY:
        return due + dt.timedelta(days=1)
    if rule == Recurrence.WEEKLY:
        return due + dt.timedelta(weeks=1)
    if rule == Recurrence.MONTHLY:
        month = due.month + 1
        year = due.year + (1 if month > 12 else 0)
        month = 1 if month > 12 else month
        return dt.date(year, month, min(due.day, 28))
    if rule == Recurrence.YEARLY:
        # BUG path: re-parse "<month> <day>" for next year via parse_due,
        # which raises on Feb 29 in a non-leap year instead of clamping.
        next_year_anchor = dt.date(due.year + 1, 1, 1)
        return parse_due(
            f"{_MONTH_NAMES[due.month]} {due.day}",
            today=next_year_anchor,
        )
    return due


def roll_recurrences(tasks: list[Task]) -> list[Task]:
    """For each completed recurring task, append its next instance.

    Returns the (possibly extended) task list. A single un-rollable task
    currently aborts the whole pass (see module docstring).
    """
    spawned: list[Task] = []
    next_id = (max((t.id for t in tasks), default=0)) + 1
    for t in tasks:
        if t.done and t.recurrence != Recurrence.NONE and t.due:
            due = dt.date.fromisoformat(t.due)
            new_due = _advance(due, t.recurrence)   # may raise → aborts pass
            spawned.append(
                Task(
                    id=next_id,
                    text=t.text,
                    priority=t.priority,
                    done=False,
                    created_at=today().isoformat(),
                    due=new_due.isoformat(),
                    recurrence=t.recurrence,
                    project_id=t.project_id,
                    tags=list(t.tags),
                    parent_id=t.id,
                )
            )
            next_id += 1
    return tasks + spawned

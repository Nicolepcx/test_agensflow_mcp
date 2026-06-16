"""Completion statistics over a task list."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Optional

from taskflow.dates.ranges import overdue_as_of
from taskflow.models import Priority, Task, today


@dataclass
class Stats:
    total: int
    done: int
    open: int
    overdue: int
    by_priority: dict[str, int]

    @property
    def completion_rate(self) -> float:
        return self.done / self.total if self.total else 0.0


def completion_stats(tasks: list[Task], as_of: Optional[dt.date] = None) -> Stats:
    as_of = as_of or today()
    by_priority: dict[str, int] = {p.value: 0 for p in Priority}
    done = overdue = 0
    for t in tasks:
        by_priority[t.priority.value] += 1
        if t.done:
            done += 1
        elif overdue_as_of(t.due, as_of):
            overdue += 1
    return Stats(
        total=len(tasks),
        done=done,
        open=len(tasks) - done,
        overdue=overdue,
        by_priority=by_priority,
    )

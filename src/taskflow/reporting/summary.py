"""Standup-style text summary of recent task activity."""

from __future__ import annotations

import datetime as dt
from typing import Optional

from taskflow.core.query import Query, run_query
from taskflow.models import Task, today
from taskflow.reporting.stats import completion_stats


def standup_summary(tasks: list[Task], as_of: Optional[dt.date] = None) -> str:
    as_of = as_of or today()
    stats = completion_stats(tasks, as_of=as_of)
    overdue = run_query(tasks, Query(done=False, overdue=True), as_of=as_of)

    lines = [
        f"Tasks: {stats.total} total, {stats.done} done "
        f"({stats.completion_rate:.0%}), {stats.open} open, {stats.overdue} overdue.",
    ]
    if overdue:
        lines.append("Overdue:")
        for t in overdue:
            lines.append(f"  - #{t.id} {t.text} (due {t.due})")
    return "\n".join(lines)

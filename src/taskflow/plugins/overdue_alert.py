"""Plugin: annotate overdue task text with a leading marker.

Runs AFTER priority-sort by contract (higher order). Relies on
relative ordering being respected by the pipeline.
"""

from __future__ import annotations

import dataclasses
import datetime as dt
from typing import Optional

from taskflow.dates.ranges import overdue_as_of
from taskflow.models import Task, today
from taskflow.plugins.base import Plugin


class OverdueAlert(Plugin):
    name = "overdue-alert"
    order = 20

    def __init__(self, as_of: Optional[dt.date] = None) -> None:
        self.as_of = as_of or today()

    def apply(self, tasks: list[Task]) -> list[Task]:
        out: list[Task] = []
        for t in tasks:
            if (not t.done and overdue_as_of(t.due, self.as_of)
                    and not t.text.startswith("(!)")):
                t = dataclasses.replace(t, text=f"(!) {t.text}")
            out.append(t)
        return out

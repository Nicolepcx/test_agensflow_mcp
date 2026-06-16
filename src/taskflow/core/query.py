"""A small filtering DSL over tasks.

Query is a chainable filter builder. run_query applies it. Used by the
CLI `list` command and the reporting module.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from typing import Optional

from taskflow.dates.ranges import overdue_as_of
from taskflow.models import Priority, Task, today


@dataclass
class Query:
    done: Optional[bool] = None
    priority: Optional[Priority] = None
    project_id: Optional[int] = None
    tag: Optional[str] = None
    overdue: bool = False
    text_contains: Optional[str] = None

    def matches(self, task: Task, as_of: Optional[dt.date] = None) -> bool:
        as_of = as_of or today()
        if self.done is not None and task.done != self.done:
            return False
        if self.priority is not None and task.priority != self.priority:
            return False
        if self.project_id is not None and task.project_id != self.project_id:
            return False
        if self.tag is not None and self.tag not in task.tags:
            return False
        if self.overdue and not overdue_as_of(task.due, as_of):
            return False
        if self.text_contains and self.text_contains.lower() not in task.text.lower():
            return False
        return True


def run_query(tasks: list[Task], query: Query,
              as_of: Optional[dt.date] = None) -> list[Task]:
    return [t for t in tasks if query.matches(t, as_of=as_of)]

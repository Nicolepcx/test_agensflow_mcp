"""Plugin: sort tasks by priority (urgent → low), then due date."""

from __future__ import annotations

from taskflow.models import Task
from taskflow.plugins.base import Plugin


class PrioritySort(Plugin):
    name = "priority-sort"
    order = 10

    def apply(self, tasks: list[Task]) -> list[Task]:
        return sorted(
            tasks,
            key=lambda t: (t.priority.rank, t.due or "9999-12-31"),
        )

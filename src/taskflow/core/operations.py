"""Core CRUD-ish operations over an in-memory task list.

These are pure functions on a list[Task]; persistence is the caller's
job (load → operate → save). Keeps the operations testable without a
store.
"""

from __future__ import annotations

import datetime as dt
from typing import Optional

from taskflow.dates.parsing import parse_due
from taskflow.models import Priority, Recurrence, Task, today
from taskflow.core.validation import validate_task


def add_task(
    tasks: list[Task],
    text: str,
    *,
    due: Optional[str] = None,
    priority: Priority = Priority.NORMAL,
    recurrence: Recurrence = Recurrence.NONE,
    project_id: Optional[int] = None,
    tags: Optional[list[str]] = None,
) -> Task:
    new_id = (max((t.id for t in tasks), default=0)) + 1
    due_iso = parse_due(due).isoformat() if due else None
    task = Task(
        id=new_id,
        text=text,
        priority=priority,
        done=False,
        created_at=today().isoformat(),
        due=due_iso,
        recurrence=recurrence,
        project_id=project_id,
        tags=list(tags or []),
    )
    validate_task(task)
    tasks.append(task)
    return task


def complete_task(tasks: list[Task], task_id: int) -> Task:
    for t in tasks:
        if t.id == task_id:
            t.done = True
            return t
    raise KeyError(f"no task with id {task_id}")


def remove_task(tasks: list[Task], task_id: int) -> None:
    for i, t in enumerate(tasks):
        if t.id == task_id:
            tasks.pop(i)
            return
    raise KeyError(f"no task with id {task_id}")


def move_task(tasks: list[Task], task_id: int, project_id: Optional[int]) -> Task:
    for t in tasks:
        if t.id == task_id:
            t.project_id = project_id
            return t
    raise KeyError(f"no task with id {task_id}")

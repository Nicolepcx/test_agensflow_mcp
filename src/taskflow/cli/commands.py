"""CLI command implementations, factored out of main.py for testability.

Each function takes a Store and primitive args, returns a list of output
lines. main.py wires these to click.
"""

from __future__ import annotations

from typing import Optional

from taskflow.config import Config
from taskflow.core.operations import add_task, complete_task, remove_task
from taskflow.core.query import Query, run_query
from taskflow.core.recurrence import roll_recurrences
from taskflow.models import Priority, Recurrence
from taskflow.plugins import OverdueAlert, PrioritySort
from taskflow.plugins.base import register, registry, run_pipeline
from taskflow.reporting import standup_summary
from taskflow.storage import JsonStore, Store


def _store() -> Store:
    return JsonStore(Config.load().root)


def cmd_add(store: Store, text: str, due: Optional[str], priority: str,
            recur: str) -> list[str]:
    tasks = store.load_tasks()
    t = add_task(
        tasks, text, due=due,
        priority=Priority(priority),
        recurrence=Recurrence(recur),
    )
    store.save_tasks(tasks)
    return [f"added #{t.id}: {t.text}"]


def cmd_list(store: Store, overdue: bool) -> list[str]:
    tasks = store.load_tasks()
    if overdue:
        tasks = run_query(tasks, Query(done=False, overdue=True))
    # Build the display pipeline fresh each call.
    registry.clear()
    register(PrioritySort())
    register(OverdueAlert())
    rendered = run_pipeline(tasks)
    out = []
    for t in rendered:
        mark = "x" if t.done else " "
        due = f"  (due {t.due})" if t.due else ""
        out.append(f"[{mark}] #{t.id:>3d} {t.text}{due}")
    return out


def cmd_done(store: Store, task_id: int) -> list[str]:
    tasks = store.load_tasks()
    complete_task(tasks, task_id)
    tasks = roll_recurrences(tasks)   # may surface the recurrence/leap bug
    store.save_tasks(tasks)
    return [f"completed #{task_id}"]


def cmd_rm(store: Store, task_id: int) -> list[str]:
    tasks = store.load_tasks()
    remove_task(tasks, task_id)
    store.save_tasks(tasks)
    return [f"removed #{task_id}"]


def cmd_standup(store: Store) -> list[str]:
    return standup_summary(store.load_tasks()).splitlines()

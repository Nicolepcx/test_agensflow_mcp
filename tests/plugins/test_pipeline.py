import datetime as dt

from taskflow.models import Priority, Task
from taskflow.plugins.base import register, registry, run_pipeline
from taskflow.plugins.priority_sort import PrioritySort
from taskflow.plugins.overdue_alert import OverdueAlert


def _setup(as_of):
    registry.clear()
    register(PrioritySort())
    register(OverdueAlert(as_of=as_of))


def test_priority_sort_orders_by_rank():
    _setup(dt.date(2026, 6, 15))
    tasks = [
        Task(id=1, text="low", priority=Priority.LOW),
        Task(id=2, text="urgent", priority=Priority.URGENT),
        Task(id=3, text="normal", priority=Priority.NORMAL),
    ]
    out = run_pipeline(tasks)
    assert [t.priority for t in out] == [Priority.URGENT, Priority.NORMAL, Priority.LOW]


def test_overdue_alert_annotates():
    as_of = dt.date(2026, 6, 15)
    _setup(as_of)
    tasks = [Task(id=1, text="late", due="2026-06-10")]
    out = run_pipeline(tasks)
    assert out[0].text.startswith("(!)")


def test_overdue_alert_idempotent():
    as_of = dt.date(2026, 6, 15)
    _setup(as_of)
    tasks = [Task(id=1, text="late", due="2026-06-10")]
    once = run_pipeline(tasks)
    twice = run_pipeline(once)
    assert twice[0].text == "(!) late"

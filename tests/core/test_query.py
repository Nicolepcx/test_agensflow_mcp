import datetime as dt

from taskflow.core.query import Query, run_query
from taskflow.models import Priority, Task


def _tasks():
    return [
        Task(id=1, text="alpha", priority=Priority.HIGH, due="2026-06-10"),
        Task(id=2, text="beta", priority=Priority.LOW, done=True),
        Task(id=3, text="gamma", priority=Priority.HIGH, tags=["urgent"]),
    ]


def test_filter_by_priority():
    out = run_query(_tasks(), Query(priority=Priority.HIGH))
    assert {t.id for t in out} == {1, 3}


def test_filter_done():
    out = run_query(_tasks(), Query(done=True))
    assert [t.id for t in out] == [2]


def test_filter_overdue():
    as_of = dt.date(2026, 6, 15)
    out = run_query(_tasks(), Query(done=False, overdue=True), as_of=as_of)
    assert [t.id for t in out] == [1]


def test_filter_tag_and_text():
    assert [t.id for t in run_query(_tasks(), Query(tag="urgent"))] == [3]
    assert [t.id for t in run_query(_tasks(), Query(text_contains="ALP"))] == [1]

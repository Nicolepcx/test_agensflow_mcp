import datetime as dt

from taskflow.models import Priority, Task
from taskflow.reporting import completion_stats, standup_summary


def _tasks():
    return [
        Task(id=1, text="done one", done=True),
        Task(id=2, text="late", due="2026-06-10"),
        Task(id=3, text="future", due="2026-12-01", priority=Priority.HIGH),
    ]


def test_completion_stats():
    s = completion_stats(_tasks(), as_of=dt.date(2026, 6, 15))
    assert s.total == 3
    assert s.done == 1
    assert s.open == 2
    assert s.overdue == 1
    assert 0.32 < s.completion_rate < 0.34


def test_standup_summary_mentions_overdue():
    text = standup_summary(_tasks(), as_of=dt.date(2026, 6, 15))
    assert "overdue" in text.lower()
    assert "#2" in text

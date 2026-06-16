from taskflow.models import Priority, Recurrence, Task


def test_task_roundtrip():
    t = Task(id=1, text="x", priority=Priority.HIGH, recurrence=Recurrence.WEEKLY,
             due="2026-07-01", tags=["a", "b"])
    assert Task.from_dict(t.to_dict()) == t


def test_priority_rank_order():
    ranks = [Priority.URGENT.rank, Priority.HIGH.rank,
             Priority.NORMAL.rank, Priority.LOW.rank]
    assert ranks == sorted(ranks)
    assert Priority.URGENT.rank < Priority.LOW.rank

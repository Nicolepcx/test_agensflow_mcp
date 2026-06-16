import pytest

from taskflow.core.operations import add_task, complete_task, move_task, remove_task
from taskflow.core.validation import ValidationError
from taskflow.models import Priority


def test_add_assigns_ids():
    tasks = []
    a = add_task(tasks, "first")
    b = add_task(tasks, "second", priority=Priority.HIGH)
    assert (a.id, b.id) == (1, 2)
    assert b.priority == Priority.HIGH


def test_complete_and_remove():
    tasks = []
    t = add_task(tasks, "x")
    complete_task(tasks, t.id)
    assert tasks[0].done
    remove_task(tasks, t.id)
    assert tasks == []


def test_move():
    tasks = []
    t = add_task(tasks, "x")
    move_task(tasks, t.id, 7)
    assert tasks[0].project_id == 7


def test_add_rejects_empty():
    with pytest.raises(ValidationError):
        add_task([], "   ")


def test_complete_missing_raises():
    with pytest.raises(KeyError):
        complete_task([], 99)

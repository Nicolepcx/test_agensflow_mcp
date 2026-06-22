"""Held-out acceptance test for the Repository façade refactor task.

Verifies that `storage.repository.Repository` wraps any Store with a unified task-CRUD API.
The agent must NOT see this file during BUILD (it is held out and restored only for the final
acceptance check). They must keep `tests/storage/` and `tests/core/` green during BUILD —
those exercise the EXISTING API, which the refactor must NOT break.

Fails with ImportError until the agent creates `src/taskflow/storage/repository.py`.
"""

from taskflow.storage.repository import Repository
from taskflow.storage.memory_store import MemoryStore


def test_repository_round_trip():
    """add_task → get_task → list_tasks round trip via a Repository wrapping MemoryStore."""
    repo = Repository(MemoryStore())
    task = repo.add_task("write the report")
    assert task.id == 1
    assert task.text == "write the report"
    fetched = repo.get_task(task.id)
    assert fetched is not None
    assert fetched.text == "write the report"
    listed = repo.list_tasks()
    assert len(listed) == 1
    assert listed[0].id == task.id


def test_repository_list_open_excludes_completed():
    """list_open() must skip tasks where done=True."""
    repo = Repository(MemoryStore())
    a = repo.add_task("task a")
    b = repo.add_task("task b")
    repo.complete_task(a.id)
    open_tasks = repo.list_open()
    assert len(open_tasks) == 1
    assert open_tasks[0].id == b.id
    # Sanity: list_tasks() returns BOTH (open + completed)
    assert len(repo.list_tasks()) == 2


def test_repository_persists_via_store():
    """Two Repository instances backed by the same Store must see each other's writes.

    Proves the Repository actually persists through the Store, not in its own private dict.
    """
    store = MemoryStore()
    repo_a = Repository(store)
    repo_b = Repository(store)
    repo_a.add_task("from A")
    repo_a.add_task("also from A")
    seen_from_b = repo_b.list_tasks()
    assert len(seen_from_b) == 2
    assert {t.text for t in seen_from_b} == {"from A", "also from A"}


def test_repository_get_unknown_id_returns_none():
    """get_task on a non-existent id returns None, not raises."""
    repo = Repository(MemoryStore())
    assert repo.get_task(999) is None

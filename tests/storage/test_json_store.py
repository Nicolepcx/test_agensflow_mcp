"""Storage tests.

`test_concurrent_writes_preserve_all` FAILS BY DESIGN — JsonStore does a
non-atomic, unlocked load→modify→save, so concurrent writers lose
updates. A correct fix locks the read-modify-write window (and writes
atomically via tempfile + os.replace). Tied to the concurrency seeded bug.
"""

import threading
from pathlib import Path

from taskflow.models import Task
from taskflow.storage import JsonStore


def test_save_load_roundtrip(tmp_path: Path):
    store = JsonStore(tmp_path)
    tasks = [Task(id=1, text="a"), Task(id=2, text="b")]
    store.save_tasks(tasks)
    assert [t.text for t in store.load_tasks()] == ["a", "b"]


def test_load_missing_is_empty(tmp_path: Path):
    assert JsonStore(tmp_path).load_tasks() == []


def test_concurrent_writes_preserve_all(tmp_path: Path):
    """Concurrent saves must never leave the store file torn/unparseable —
    a reader must always see a complete task list. (Currently FAILS.)

    The bug: save_tasks does a non-atomic write (open-truncate-write), so a
    reader that loads mid-write sees a partial file (JSONDecodeError) or a
    short list. The fix is an atomic write — write to a tempfile, then
    os.replace onto the target — so readers only ever observe the old or
    the new complete file.
    """
    store = JsonStore(tmp_path)
    full = [Task(id=j, text=f"task{j}") for j in range(1, 40)]
    store.save_tasks(full)
    errors: list[str] = []

    def worker(i: int) -> None:
        try:
            for _ in range(30):
                store.save_tasks(full)           # writer
                got = store.load_tasks()         # reader — must parse + be complete
                if len(got) != len(full):
                    errors.append(f"torn read: saw {len(got)} of {len(full)}")
        except Exception as exc:  # noqa: BLE001
            errors.append(repr(exc))

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"concurrent access corrupted the store: {errors[:3]}"

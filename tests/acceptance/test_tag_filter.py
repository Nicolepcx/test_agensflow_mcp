"""Feature-acceptance test for issue #4 (--tag filter on list).

FAILS until the feature is implemented: cmd_list does not yet accept a
`tag` argument, so this raises TypeError. Implementing #4 (wiring
Query(tag=...) through cmd_list + the CLI option) makes it pass.
"""

from taskflow.cli import commands
from taskflow.models import Task
from taskflow.storage import MemoryStore


def test_list_filters_by_tag():
    store = MemoryStore()
    store.save_tasks([
        Task(id=1, text="tagged", tags=["work"]),
        Task(id=2, text="untagged"),
    ])
    out = commands.cmd_list(store, overdue=False, tag="work")
    text = "\n".join(out)
    assert "tagged" in text
    assert "untagged" not in text

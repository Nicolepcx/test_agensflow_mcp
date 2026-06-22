"""Held-out acceptance test for the PluginRegistry refactor task.

Verifies that `plugins.base.PluginRegistry` encapsulates registry state per INSTANCE — registering
on one PluginRegistry must NOT leak to another. The agent must NOT see this file during BUILD
(it is held out and restored only for the final acceptance check). They must keep
`tests/plugins/` green during BUILD — those exercise the EXISTING module-level
`register/run_pipeline/registry` API, which the refactor must KEEP working for backward
compatibility.

Fails with ImportError until the agent introduces `PluginRegistry` as a class in
`src/taskflow/plugins/base.py`.
"""

from taskflow.models import Priority, Task
from taskflow.plugins.base import Plugin, PluginRegistry
from taskflow.plugins.priority_sort import PrioritySort


def test_pluginregistry_starts_empty():
    """A fresh PluginRegistry has no registered plugins → dispatch is a no-op."""
    reg = PluginRegistry()
    tasks = [Task(id=1, text="a", priority=Priority.NORMAL)]
    out = reg.dispatch(tasks)
    assert len(out) == 1
    assert out[0].text == "a"


def test_pluginregistry_register_and_dispatch():
    """register() + dispatch() apply plugins in ascending-order order."""
    reg = PluginRegistry()
    reg.register(PrioritySort())
    tasks = [
        Task(id=1, text="low",    priority=Priority.LOW),
        Task(id=2, text="urgent", priority=Priority.URGENT),
        Task(id=3, text="normal", priority=Priority.NORMAL),
    ]
    out = reg.dispatch(tasks)
    assert [t.priority for t in out] == [Priority.URGENT, Priority.NORMAL, Priority.LOW]


def test_two_registries_are_isolated():
    """Registering on PluginRegistry instance A must NOT affect instance B.

    This is the core property the refactor introduces — the old module-level `registry: list`
    is shared state; class-based PluginRegistry instances are isolated.
    """
    reg_a = PluginRegistry()
    reg_b = PluginRegistry()
    reg_a.register(PrioritySort())

    tasks = [
        Task(id=1, text="low",    priority=Priority.LOW),
        Task(id=2, text="urgent", priority=Priority.URGENT),
    ]
    # reg_a should sort by priority
    out_a = reg_a.dispatch(tasks)
    assert out_a[0].priority == Priority.URGENT
    # reg_b should be empty → tasks pass through unchanged
    out_b = reg_b.dispatch(tasks)
    assert out_b[0].priority == Priority.LOW
    assert out_b[1].priority == Priority.URGENT


def test_dispatch_respects_plugin_order_field():
    """Plugins run in ascending Plugin.order order, regardless of registration sequence."""

    class TagPrefixer(Plugin):
        name = "tag-prefixer"
        order = 5    # runs BEFORE PrioritySort (order=10)

        def apply(self, tasks):
            # Use dataclasses.replace if Task is frozen; otherwise mutate
            import dataclasses
            return [dataclasses.replace(t, text=f"[X] {t.text}") for t in tasks]

    reg = PluginRegistry()
    reg.register(PrioritySort())     # registered first but higher order → runs SECOND
    reg.register(TagPrefixer())      # registered second but lower order → runs FIRST
    tasks = [Task(id=1, text="hi", priority=Priority.NORMAL)]
    out = reg.dispatch(tasks)
    assert out[0].text == "[X] hi"

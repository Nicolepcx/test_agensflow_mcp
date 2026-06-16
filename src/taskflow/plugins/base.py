"""Plugin base + registry.

Plugins transform the task list before display. They run in ascending
`order` (lower runs earlier); equal-order plugins run in registration
order (guaranteed by Python's stable sort). This module is clean — it's
surface area for "add a new plugin" feature tasks, not a seeded bug.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from taskflow.models import Task


class Plugin(ABC):
    name: str = "plugin"
    order: int = 100  # lower runs earlier

    @abstractmethod
    def apply(self, tasks: list[Task]) -> list[Task]: ...


registry: list[Plugin] = []


def register(plugin: Plugin) -> None:
    registry.append(plugin)


def run_pipeline(tasks: list[Task]) -> list[Task]:
    ordered = sorted(registry, key=lambda p: p.order)  # stable: ties keep reg order
    out = tasks
    for plugin in ordered:
        out = plugin.apply(out)
    return out

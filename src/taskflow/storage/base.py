"""Abstract storage interface.

A Store persists Tasks and Projects and assigns ids. Backends must
preserve insertion order and provide atomic-ish bulk replace via
save_tasks. (The JSON backend deliberately does NOT make this atomic —
see json_store.py.)
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from taskflow.models import Project, Task


class Store(ABC):
    @abstractmethod
    def load_tasks(self) -> list[Task]: ...

    @abstractmethod
    def save_tasks(self, tasks: list[Task]) -> None: ...

    @abstractmethod
    def load_projects(self) -> list[Project]: ...

    @abstractmethod
    def save_projects(self, projects: list[Project]) -> None: ...

    def next_task_id(self, tasks: list[Task]) -> int:
        return (max((t.id for t in tasks), default=0)) + 1

    def next_project_id(self, projects: list[Project]) -> int:
        return (max((p.id for p in projects), default=0)) + 1

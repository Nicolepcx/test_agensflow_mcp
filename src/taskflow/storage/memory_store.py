"""In-memory storage backend — used by tests and the query REPL."""

from __future__ import annotations

from taskflow.models import Project, Task
from taskflow.storage.base import Store


class MemoryStore(Store):
    def __init__(self) -> None:
        self._tasks: list[dict] = []
        self._projects: list[dict] = []

    def load_tasks(self) -> list[Task]:
        return [Task.from_dict(d) for d in self._tasks]

    def save_tasks(self, tasks: list[Task]) -> None:
        self._tasks = [t.to_dict() for t in tasks]

    def load_projects(self) -> list[Project]:
        return [Project.from_dict(d) for d in self._projects]

    def save_projects(self, projects: list[Project]) -> None:
        self._projects = [p.to_dict() for p in projects]

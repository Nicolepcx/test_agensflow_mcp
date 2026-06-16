"""JSON-file storage backend.

SEEDED BUG (atomicity / durability): save_tasks writes directly to the
target path (open-truncate-write), so a concurrent reader can observe a
half-written, unparseable file, and a crash mid-write truncates it. The
fix writes to a tempfile and os.replace()s it onto the target — an atomic
rename, so readers only ever see the old or the new complete file. The
coordination-heavy fix touches this file AND base.py's contract docstring
AND the regression test under tests/storage/.
"""

from __future__ import annotations

import json
from pathlib import Path

from taskflow.models import Project, Task
from taskflow.storage.base import Store


class JsonStore(Store):
    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self.tasks_path = self.root / "tasks.json"
        self.projects_path = self.root / "projects.json"

    def _read(self, path: Path) -> list[dict]:
        if not path.exists():
            return []
        return json.loads(path.read_text())

    def _write(self, path: Path, rows: list[dict]) -> None:
        # BUG: non-atomic write. A concurrent reader can see a half-written
        # file. Should write to a tempfile and os.replace() onto the target.
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(rows, indent=2))

    def load_tasks(self) -> list[Task]:
        return [Task.from_dict(d) for d in self._read(self.tasks_path)]

    def save_tasks(self, tasks: list[Task]) -> None:
        self._write(self.tasks_path, [t.to_dict() for t in tasks])

    def load_projects(self) -> list[Project]:
        return [Project.from_dict(d) for d in self._read(self.projects_path)]

    def save_projects(self, projects: list[Project]) -> None:
        self._write(self.projects_path, [p.to_dict() for p in projects])

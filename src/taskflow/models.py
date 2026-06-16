"""Domain models for taskflow.

Plain dataclasses + (de)serialization. Kept dependency-free so every
other module can import these without cycles.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Optional


class Priority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

    @property
    def rank(self) -> int:
        return {"urgent": 0, "high": 1, "normal": 2, "low": 3}[self.value]


class Recurrence(str, Enum):
    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


@dataclass
class Tag:
    name: str
    color: str = "gray"


@dataclass
class Task:
    id: int
    text: str
    priority: Priority = Priority.NORMAL
    done: bool = False
    created_at: str = ""
    due: Optional[str] = None            # ISO date string or None
    recurrence: Recurrence = Recurrence.NONE
    project_id: Optional[int] = None
    tags: list[str] = field(default_factory=list)
    parent_id: Optional[int] = None      # for recurrence-spawned instances

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["priority"] = self.priority.value
        d["recurrence"] = self.recurrence.value
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Task":
        return cls(
            id=d["id"],
            text=d["text"],
            priority=Priority(d.get("priority", "normal")),
            done=bool(d.get("done", False)),
            created_at=d.get("created_at", ""),
            due=d.get("due"),
            recurrence=Recurrence(d.get("recurrence", "none")),
            project_id=d.get("project_id"),
            tags=list(d.get("tags", [])),
            parent_id=d.get("parent_id"),
        )


@dataclass
class Project:
    id: int
    name: str
    archived: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Project":
        return cls(id=d["id"], name=d["name"], archived=bool(d.get("archived", False)))


def today() -> dt.date:
    """Indirection point so tests can monkeypatch 'now' deterministically."""
    return dt.date.today()

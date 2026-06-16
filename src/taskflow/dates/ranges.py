"""Date range helpers + overdue computation."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class DateRange:
    start: dt.date
    end: dt.date

    def __post_init__(self) -> None:
        if self.end < self.start:
            raise ValueError("end before start")

    def contains(self, d: dt.date) -> bool:
        return self.start <= d <= self.end

    def days(self) -> int:
        return (self.end - self.start).days + 1


def overdue_as_of(due_iso: Optional[str], as_of: dt.date) -> bool:
    """True if a task with the given ISO due date is overdue as of `as_of`.

    None due → never overdue. Due strictly before as_of → overdue.
    """
    if not due_iso:
        return False
    due = dt.date.fromisoformat(due_iso)
    return due < as_of

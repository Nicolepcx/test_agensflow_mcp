"""Task input validation."""

from __future__ import annotations

from taskflow.models import Task


class ValidationError(ValueError):
    """Raised when a task fails validation."""


MAX_TEXT_LEN = 500


def validate_task(task: Task) -> None:
    """Validate a task before persistence. Raises ValidationError."""
    if not task.text or not task.text.strip():
        raise ValidationError("task text must not be empty")
    if len(task.text) > MAX_TEXT_LEN:
        raise ValidationError(f"task text exceeds {MAX_TEXT_LEN} chars")
    if task.parent_id is not None and task.parent_id == task.id:
        raise ValidationError("task cannot be its own parent")

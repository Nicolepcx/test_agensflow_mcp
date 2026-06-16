"""Core task operations for taskflow."""

from taskflow.core.operations import add_task, complete_task, remove_task, move_task
from taskflow.core.recurrence import roll_recurrences
from taskflow.core.query import Query, run_query
from taskflow.core.validation import validate_task, ValidationError

__all__ = [
    "add_task", "complete_task", "remove_task", "move_task",
    "roll_recurrences", "Query", "run_query",
    "validate_task", "ValidationError",
]

import pytest

from taskflow.core.validation import MAX_TEXT_LEN, ValidationError, validate_task
from taskflow.models import Task


def test_rejects_empty_text():
    with pytest.raises(ValidationError):
        validate_task(Task(id=1, text=""))


def test_rejects_too_long():
    with pytest.raises(ValidationError):
        validate_task(Task(id=1, text="x" * (MAX_TEXT_LEN + 1)))


def test_rejects_self_parent():
    with pytest.raises(ValidationError):
        validate_task(Task(id=5, text="ok", parent_id=5))


def test_accepts_valid():
    validate_task(Task(id=1, text="fine", parent_id=2))

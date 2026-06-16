"""Plugin system for taskflow list-rendering pipeline.

Plugins transform the task list before display (sorting, filtering,
annotating). They run in priority order via the registry.
"""

from taskflow.plugins.base import Plugin, registry, run_pipeline
from taskflow.plugins.priority_sort import PrioritySort
from taskflow.plugins.overdue_alert import OverdueAlert

__all__ = ["Plugin", "registry", "run_pipeline", "PrioritySort", "OverdueAlert"]

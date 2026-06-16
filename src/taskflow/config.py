"""Runtime configuration for taskflow (storage location, defaults)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Config:
    root: Path

    @classmethod
    def load(cls) -> "Config":
        root = os.environ.get("TASKFLOW_HOME")
        return cls(root=Path(root) if root else Path.home() / ".taskflow")

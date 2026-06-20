"""Deterministic per-task verifiers.

Two flavours per task:
  must_mention / must_not_mention — literal substring (case-insensitive)
  must_match   / must_not_match   — regex pattern (case-insensitive)

Substring is preferred when the target is unambiguous (e.g. a filename
like `dates.py` — using a literal avoids regex-escape pitfalls like the
`.` matching any char). Regex is needed when Claude's natural phrasing
varies (e.g. `issue-001` vs `Issue #1` vs `the first issue`).
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Verdict:
    success: bool
    missing: list[str]
    forbidden_present: list[str]

    @property
    def reason(self) -> str:
        if self.success:
            return "passed"
        parts = []
        if self.missing:
            parts.append(f"missing: {', '.join(self.missing)}")
        if self.forbidden_present:
            parts.append(f"forbidden present: {', '.join(self.forbidden_present)}")
        return "; ".join(parts) or "unknown"


def verify(
    stdout: str,
    must_mention: list[str] | None = None,
    must_not_mention: list[str] | None = None,
    must_match: list[str] | None = None,
    must_not_match: list[str] | None = None,
) -> Verdict:
    """Case-insensitive: substrings (literal) and patterns (regex)."""
    must_mention = must_mention or []
    must_not_mention = must_not_mention or []
    must_match = must_match or []
    must_not_match = must_not_match or []

    text = stdout.lower()
    missing: list[str] = []
    forbidden: list[str] = []

    for needle in must_mention:
        if needle.lower() not in text:
            missing.append(needle)
    for needle in must_not_mention:
        if needle.lower() in text:
            forbidden.append(needle)
    for pat in must_match:
        if not re.search(pat, stdout, re.IGNORECASE):
            missing.append(f"/{pat}/")
    for pat in must_not_match:
        if re.search(pat, stdout, re.IGNORECASE):
            forbidden.append(f"/{pat}/")

    return Verdict(
        success=(not missing and not forbidden),
        missing=missing,
        forbidden_present=forbidden,
    )

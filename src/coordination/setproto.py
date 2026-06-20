"""Tag-set digest protocol — mechanism only.

A service computes a content ``digest`` of a record ``{id: str, tags: list[str]}``. The ``tags`` are
a SET — their order carries no meaning. HOW the digest is computed is defined entirely by the
CONTRACT; this module fixes none of it.
"""

from __future__ import annotations


class SetProtocolError(Exception):
    """Raised by a service that cannot process a record."""


class SetComponent:
    """A protocol participant. Subclasses implement ``digest`` per the CONTRACT."""

    def digest(self, record: dict) -> str:
        """Stable content digest of a record {id: str, tags: list[str]} (tags are a SET)."""
        raise NotImplementedError

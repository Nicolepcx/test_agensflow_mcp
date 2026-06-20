"""Event-record protocol — mechanism only.

A service can `emit` an event to a wire dict, `read` a wire dict back into an event, and
compute a content `event_id`. The event shape is fixed: {name: str, level: str,
ts_seconds: int}. HOW those fields are encoded on the wire, and how the id is computed,
is defined entirely by the CONTRACT — this module fixes none of it.
"""

from __future__ import annotations


class ProtocolError(Exception):
    """Raised by a service that cannot process a record."""


class Component:
    """A protocol participant. Subclasses implement encode / decode / id per the CONTRACT."""

    def emit(self, event: dict) -> dict:
        """event {name, level, ts_seconds} -> wire dict."""
        raise NotImplementedError

    def read(self, wire: dict) -> dict:
        """wire dict -> event {name, level, ts_seconds}."""
        raise NotImplementedError

    def event_id(self, event: dict) -> str:
        """Stable content id of an event {name, level, ts_seconds}."""
        raise NotImplementedError

"""Per-service self round-trip — the LOCAL test each implementer is given. Passes for any
self-consistent service, with no knowledge of the other service's choices."""

from coordination.service_a import ServiceA
from coordination.service_b import ServiceB

EVENT = {"name": "login", "level": "info", "ts_seconds": 1700000000}


def test_a_self_roundtrip():
    a = ServiceA()
    assert a.read(a.emit(dict(EVENT))) == EVENT


def test_b_self_roundtrip():
    b = ServiceB()
    assert b.read(b.emit(dict(EVENT))) == EVENT


def test_a_event_id_deterministic():
    a = ServiceA()
    assert a.event_id(dict(EVENT)) == a.event_id(dict(EVENT))


def test_b_event_id_deterministic():
    b = ServiceB()
    assert b.event_id(dict(EVENT)) == b.event_id(dict(EVENT))

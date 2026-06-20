"""Per-service self test — the LOCAL test given to the implementer (BUILD-visible). Passes for any
self-consistent digest, with no knowledge of the other service's choice."""

from coordination.setservice_a import SetServiceA
from coordination.setservice_b import SetServiceB

RECORD = {"id": "r1", "tags": ["auth", "login", "web"]}


def test_a_digest_deterministic():
    a = SetServiceA()
    assert a.digest(dict(RECORD)) == a.digest(dict(RECORD))


def test_b_digest_deterministic():
    b = SetServiceB()
    assert b.digest(dict(RECORD)) == b.digest(dict(RECORD))

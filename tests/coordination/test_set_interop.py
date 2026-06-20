"""Cross-service digest agreement — HELD OUT from BUILD/VERIFY (the coordination acceptance).

Fails ONLY if A and B diverged on the under-determined choice: the digest must be ORDER-CANONICAL
over ``tags`` (a set), so the same record with tags in any order yields the SAME digest across
services. A self-consistent digest that hashes tags in receive-order passes the local self test yet
fails here. No obvious default — a weak plan that never surfaces "tags are a set" diverges.
"""

from coordination.setservice_a import SetServiceA
from coordination.setservice_b import SetServiceB

RECORD = {"id": "r1", "tags": ["auth", "login", "web"]}
RECORD_REORDERED = {"id": "r1", "tags": ["web", "auth", "login"]}


def test_interop_set_digest_agreement():
    assert SetServiceA().digest(dict(RECORD)) == SetServiceB().digest(dict(RECORD_REORDERED))

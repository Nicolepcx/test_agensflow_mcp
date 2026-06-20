"""Cross-service interop — HELD OUT from the BUILD/VERIFY stages (the coordination acceptance).

Fails ONLY if A and B diverged on the one under-determined choice the contract leaves open: the
event_id must be ORDER-CANONICAL, so the same event with keys in any order yields the SAME id across
services. A self-consistent but non-canonical id (e.g. hashing ``str(event)``) passes the local self
test yet fails here. This measures AGREEMENT, not an enshrined wire value — there is no obvious
default, so a weak plan that never surfaces "the id must be order-independent" diverges.
"""

from coordination.service_a import ServiceA
from coordination.service_b import ServiceB

EVENT = {"name": "login", "level": "info", "ts_seconds": 1700000000}
# Same event, keys in a different insertion order — exposes non-canonical id rules.
EVENT_REORDERED = {"ts_seconds": 1700000000, "level": "info", "name": "login"}


def test_interop_event_id_agreement():
    assert ServiceA().event_id(dict(EVENT)) == ServiceB().event_id(dict(EVENT_REORDERED))

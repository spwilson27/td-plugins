"""Frame-based waiting for scratch TouchDesigner instances.

Validation needs the network to actually *cook* for a while (feedback sims develop, "is the demo still
cooking?" needs real frames). Waiting on wall-clock seconds over-waits when TD runs at full rate and
under-waits when the machine is loaded; waiting on cooked frames is exact in both cases.
"""
import time

from td_mcp.client import call


def frame(conn):
    r = call("execute_python", {"code": "absTime.frame"}, connection=conn, timeout=30)
    return int(r.get("result") or 0)


def wait_frames(conn, n, timeout=60.0, poll=0.05):
    """Block until TouchDesigner has advanced `n` frames (or `timeout` seconds pass). Returns frames waited."""
    start = frame(conn)
    t0 = time.time()
    while time.time() - t0 < timeout:
        f = frame(conn)
        if f - start >= n:
            return f - start
        # sleep roughly the remaining frames at 60 fps, but poll at least every 0.25 s
        time.sleep(min(max(poll, (n - (f - start)) / 60.0), 0.25))
    return frame(conn) - start

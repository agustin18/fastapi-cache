# Real standalone Redis process stop/restart — 0.7.0 evidence slice

A new workflow creates its **own uniquely named disposable Redis 7.4 Docker
container** on an ephemeral loopback-only host port, with persistence disabled.
On installed wheel builds for Python 3.8, 3.12 and 3.13, it verifies initial
GET/HIT, then actually stops the daemon. The Redis backend must surface an
exception and the decorator's existing read/write fallback must recompute
without hanging. Six concurrent callers are exercised without claiming a
single-flight guarantee. After restarting that same ephemeral container, the
probe verifies no phantom cached entry and that subsequent requests can again
cache and HIT. It inspects logs for synthetic raw data/key leakage.

No external Redis URL is accepted, no production Redis is contacted, no
FLUSHDB or FLUSHALL is executed, and the unique container is destroyed.
The caller-owned redis-py client is explicitly configured with
`Retry(NoBackoff(), 0)`: **no automatic client retries** during the probe.
This isolates the library's first-failure behavior; redis-py 6+ defaults
can retry for longer, and default-client outage latency/recovery is
**not** qualified by these results. Watchdog timeouts are test
infrastructure, **not preapproved latency budgets**.

This is not HA, TLS, Sentinel, Cluster, managed failover, network partition,
distributed locks, persistence, or independent-machine perf certification.
It characterizes a narrow standalone Redis recovery scenario only; the full
#102/#111/#112 contracts and final artifact/SHA release qualification remain
subject to review. PR CI does not count as a first-attempt final Phase B.

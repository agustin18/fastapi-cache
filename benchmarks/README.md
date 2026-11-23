# Published-distribution performance baseline (#100)

This is a **measurement harness**, not a performance certification or a release
blocker. The runner creates an isolated CPython 3.12 virtualenv, downloads the
**published** `fastapi-cache-stable==0.6.0` wheel, verifies its SHA-256 against
the release ledger, installs pinned top-level benchmarking dependencies and
runs the workload with `python -I` from outside the checkout. No `pip install
-e .`, candidate source import, Redis `FLUSHDB`, user data or public endpoint.

## Reproduce

Start disposable standalone **Redis 7.4** listening on loopback port 6379,
with database 15 available. Only a unique `perf-<uuid>:` namespace is used;
the runner refuses remote Redis targets or credentials.

```console
python3.12 benchmarks/runner.py --profile smoke --output benchmark-results/smoke \
  --redis-url redis://127.0.0.1:6379/15
python3.12 benchmarks/runner.py --profile full --output benchmark-results/full \
  --redis-url redis://127.0.0.1:6379/15
```

`smoke` runs 1k bounded InMemory, small HTTP payloads and concurrency 1/10,
without claiming the entire matrix. `full` additionally measures InMemory
1k/10k/100k, small/medium/large HTTP payloads and Redis 1/10/100/1000 clients.
Both include HTTP HIT/MISS/304, declared `Vary`, Authorization bypass,
TTL expiry, targeted namespace clearing and a slow endpoint. HTTP tests use
`httpx.ASGITransport` (in-process), **not real HTTP network latency**. Redis
operations use the real local Redis socket and measure concurrent SET/GET.

A GitHub Actions PR run executes `smoke` and uploads `raw.csv`, `summary.json`,
`provenance.json` and `pip-freeze.txt` as short-lived artifacts. A *manual*
`workflow_dispatch` runs the full matrix. Never publish a superiority claim
from either run or treat different CI machines as a controlled comparison.

## Methodology and gaps

- `raw.csv` stores each operation's duration in nanoseconds, without keys or
  response payloads. `summary.json` uses nearest-rank p50/p95/p99; throughput
  is provided for explicit direct-backend and Redis batch windows, not as an
  estimated HTTP-server throughput.
- `provenance.json` captures the exact published wheel filename/SHA-256,
  framework pins and workflow source SHA; `pip-freeze.txt` captures resolved
  dependencies. Runtime JSON records Python, platform, Redis server and client
  versions. Repeat workloads on the same pinned machine before setting
  regression budgets.
- The opt-in InMemory `max_entries` limit is a count, not a memory-byte bound.
  RSS/peak memory, CPU utilization, *real* HTTP socket p99, Redis server
  resource use, timeout/failure behavior and a 0.5.0 comparator are **not yet
  implemented** in this first PR. Do not mark issue #100 complete on merge.
- Concurrency latencies are individual task wall times, not serialized server
  time. `full` uses bounded batches to avoid an unbounded number of tasks.
- Warmup and multiple-run variance, RSS and controlled 0.5.0 comparison belong
  in follow-up evidence before a performance acceptance threshold is approved.

## Release boundaries

This workflow runs no release, tag, publishing, Pages or outreach actions. It
adds no package runtime dependency and does not modify the published 0.6.0
artifact. Python 3.14, experimental backend parity, Redis HA/TLS/Cluster and
security certification are explicitly out of scope.

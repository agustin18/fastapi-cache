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

A GitHub Actions PR run executes `smoke` and a separate **full three-process**
profile against a disposable Redis 7.4 CI service. Both upload short-lived
results: `raw.csv`, `summary.json`, `provenance.json`, `pip-freeze.txt`,
`aggregate.json` and (for repeats) `runs/run-02`, `runs/run-03`.
The manual `workflow_dispatch` also executes full. `--repeats N` accepts 1–5
fresh workload processes (default 1 smoke / 3 full); this measures variance
across runs in one CI environment, **not** variance across independent hosts.
Never publish a superiority claim or treat different CI machines as a controlled comparison.

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
  **Linux process** current/peak RSS and CPU seconds are recorded. Peak RSS is a
  cumulative high-water mark including imports, all earlier scenarios and
  benchmark recording overhead, NOT isolated backend heap size. Redis `INFO`
  memory/CPU start/end samples cover the standalone CI server, not exclusive
  per-request allocations. Redis client connection counts are recorded because
  the pool can grow to 1,000 sockets and its buffers contribute to server
  memory. These are descriptive resource measurements, not cache-only usage.
- The HTTP case performs an end-of-run full **random prefix** cleanup, including
  Vary, slow and TTL entries; scoped Redis SCAN assertions fail if benchmark
  keys remain after cleanup. No `FLUSHDB` or other tenants are touched.
  *Real network* HTTP p99, timeout/failure behavior and controlled **0.5.0
  historical comparator** are still pending. Do not close #100 on merge.
- Concurrency latencies are individual task wall times, not serialized server
  time. `full` uses bounded batches to avoid an unbounded number of tasks.
- `aggregate.json` includes per-run p50/p95/p99 medians, standard deviation
  and coefficient of variation (CV) **across processes**. Cases with fewer than
  100 samples per run explicitly warn that a stable p99 claim is unsupported.
  Full workloads repeat three times; additional warmup, independent-host
  replication, 0.5.0 comparisons and accepted thresholds are future work.

## Release boundaries

This workflow runs no release, tag, publishing, Pages or outreach actions. It
adds no package runtime dependency and does not modify the published 0.6.0
artifact. Python 3.14, experimental backend parity, Redis HA/TLS/Cluster and
security certification are explicitly out of scope.

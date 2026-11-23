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
profile against a disposable Redis 7.4 CI service, plus separate historical
comparison and real TCP loopback HTTP jobs. The first two upload short-lived
results: `raw.csv`, `summary.json`, `provenance.json`, `pip-freeze.txt`,
`aggregate.json` and (for repeats) `runs/run-02`, `runs/run-03`.
The manual `workflow_dispatch` runs the same two jobs: one smoke baseline and
one full three-process baseline, **plus** historical comparison and socket HTTP.
The full profile is no longer PR-only.
`--repeats N` accepts 1–5
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
  **Qualified** real-network production HTTP p99, timeout/disconnect
  behavior, replication on independent controlled hardware and agreed
  regression budgets remain pending. The real localhost TCP socket profile
  below measures only descriptive shared-runner latencies, not production p99.
  The historical 0.5.0 comparison is implemented below and is similarly
  descriptive. Do not close #100 on merge.
- Concurrency latencies are individual task wall times, not serialized server
  time. `full` uses bounded batches to avoid an unbounded number of tasks.
- `aggregate.json` includes per-run p50/p95/p99 medians, standard deviation
  and coefficient of variation (CV) **across processes**. Cases with fewer than
  100 samples per run explicitly warn that a stable p99 claim is unsupported.
  Full workloads repeat three times; additional warmup, independent-host
  replication and pre-agreed regression thresholds remain future work. The
  historical 0.5.0 comparison below runs as a separate controlled protocol.

## Candidate-wheel comparison without publication (#100 infrastructure)

The same isolated HTTP socket workload can be run against an **unpublished**
candidate wheel, for a later controlled same-host paired comparison. This is
strictly an instrumentation capability: the two versions must be installed
from distinct, reviewed, SHA-verified wheels and compared on the **same**
controlled independent hardware with a **preapproved** budget and recorded
CPU/OS/dependency/environment. The runner does not fetch or build candidate
source, does not generate an RC, and never publishes anything.

After independently obtaining a reviewed wheel from exact candidate evidence:

```console
python3.12 benchmarks/socket_runner.py --candidate-wheel /reviewed/dist/fastapi_cache_stable-0.7.0.dev0-py3-none-any.whl \
  --candidate-version 0.7.0.dev0 --candidate-sha256 YOUR_REVIEWED_64_HEX_DIGEST \
  --repeats 2 --iterations 120 --redis-url redis://127.0.0.1:6379/15 \
  --output benchmark-results/candidate-socket
```

The wheel filename, metadata (distribution/version) and SHA-256 are checked
before and after copying into the isolated environment. Both its client and
separately launched Uvicorn servers must import that installed version via
`python -I`; co-installation with `fastapi-cache2` fails closed. The public
0.6.0 baseline command and its pinned SHA remain unchanged.

**Not qualified:** a run of 120 requests on GitHub's shared runner is still
descriptive. This does not compare 0.6 versus 0.7 automatically or implement
balanced AB/BA pairing; the operator must approve and document order, pinned
host, sample sufficiency, budget, raw data and dependency parity **before**
making a regression claim. 0.7.0 final release evidence must use the frozen
final wheel, not reuse a `.dev0` benchmark as the final result.

## Release boundaries

This workflow runs no release, tag, publishing, Pages or outreach actions. It
adds no package runtime dependency and does not modify the published 0.6.0
artifact. Python 3.14, experimental backend parity, Redis HA/TLS/Cluster and
security certification are explicitly out of scope.

## Controlled 0.5.0 versus 0.6.0 (historical comparison)

The historical pairwise benchmark is intentionally separate from the 0.6.0-only
bounded-InMemory/large-concurrency full suite. Both versions are downloaded as
**published PyPI wheels**, checked against their release SHA-256 hashes and
installed into **distinct** CPython 3.12 virtual environments with exactly
the same dependency versions (verified by installed pip-freeze comparison).

For a local Redis 7.4 listening only at redis://127.0.0.1:6379/15:

    python3.12 benchmarks/compare_versions.py --repeats 4 --output benchmark-results/historical

The protocol alternates order AB/BA over four paired runs per version on the
**same runner** and exercises only common behavior: unbounded InMemory
set/get; anonymous HTTP MISS/HIT/ETag-304 with small/medium JSON over in-process
ASGITransport; and Redis standalone direct set/get plus HTTP cache.
It excludes 0.6-only bounded storage, authentication policy changes, tenant
security variations and advanced Redis/HA functionality. Each fresh process
uses a random Redis namespace and clears that namespace on exit, never
FLUSHDB. Only Redis loopback DB 15 is permitted.

Each run produces raw.csv and summary.json; comparison.json stores paired
p50/p95/p99 ratios, provenance.json stores both verified wheel hashes and
the balanced ordering, and both pip-freeze files are preserved. Results are
**descriptive**: shared-runner scheduling, warmup, transport and cache keys may
confound small differences. No automatically accepted regression threshold,
superiority advertising, published-version downgrade or 0.7.0 release GO
follows from this comparison. Repeat on controlled independent hardware and
agree on budgets *before* qualifying new opt-in features.

## Real loopback HTTP socket profile (separate #100 acceptance slice)

The existing HTTP baselines above use in-process ASGITransport and do **not**
represent TCP loopback or remote-server HTTP. An additional read-only
`socket-http` GitHub Actions job now exercises the **published, SHA-verified
0.6.0 wheel** over a **real 127.0.0.1 TCP socket** served by a *separate*
Uvicorn OS process. It runs fresh InMemory and standalone Redis backend
servers, 120 serial samples for each of HIT/MISS/304 on 128, 4,096 and
65,536-byte JSON, Authorization bypass, explicit Accept-Language variation,
slow endpoint and TTL expiry. Redis keys are restricted to a random
`perf-http-<uuid>:` prefix in localhost DB15 and selectively unlinked.
No application backend, production data, remote endpoint, FLUSHDB,
HA/Cluster/TLS claim, registry upload or tag is touched.

Reproduce with a disposable Redis 7.4 server available at
`redis://127.0.0.1:6379/15` and CPython 3.12:

    python3.12 benchmarks/socket_runner.py --repeats 2 --iterations 120 \
      --redis-url redis://127.0.0.1:6379/15 \
      --output benchmark-results/socket-http

The runner installs published wheel 0.6.0 with verified SHA-256 in an
isolated venv, pins FastAPI/Pydantic/httpx/redis-py and Uvicorn, rejects
`fastapi-cache2` co-install and checkout imports with `python -I`,
records `pip-freeze.txt`, `provenance.json`, raw per-case CSV,
per-run percentile summaries, aggregate variation and short-lived server
logs. Requests and authentication tokens are *synthetic* and logs disable
Uvicorn access logging.

**Qualification boundary:** the Uvicorn process is on a GitHub-hosted
runner alongside the Redis test service, **not** independent controlled
hardware. Serial request p99 with 120 observations is not a statistically
qualified production p99. There is no agreed numerical regression budget,
so the job tests reproducibility, correctness and observability, **not**
speed superiority or a release GO. #100 remains OPEN for fixed independent
hardware, prior-reviewed performance thresholds, fault/disconnect cases and
candidate-vs-baseline OFF/ON profiling.

# Regression budgets: pre-registration proposal (NOT approved)

Tracked under [#100](https://github.com/agustin18/fastapi-cache/issues/100).
The published-wheel 0.6.0 harness (#120/#121) and historical
0.5.0/0.6.0 shared-case AB/BA comparator (#122) are merged.
[Merged #128](https://github.com/agustin18/fastapi-cache/pull/128)
(`f81e60b`) adds synthetic loopback TCP Uvicorn HTTP with the same published wheel;
it is not independent fixed hardware or a preapproved regression budget.
The latter's direct Redis GET ratio changed **sign** between CI sessions:
these results cannot justify a superiority/regression claim or a
budget retrofitted *after* measuring.

## Required pre-registration BEFORE testing a candidate

| Field | Approved value (must be supplied before the run) |
|---|---|
| Exact baseline and candidate wheel/sdist SHA-256 | TBD |
| Workload, payload mix and function/backend paths | TBD |
| Pinned CPU model, RAM, affinity, OS and governor | TBD |
| Python/FastAPI/Pydantic/redis-py/Redis and pip freeze | TBD |
| Socket HTTP server/client topology and keepalive/TLS | TBD |
| Warmup, AB/BA order, repeated runs and sample minimum | TBD |
| Primary p50/p95/p99/throughput/CPU/RSS/error metrics | TBD |
| Statistic/uncertainty or confidence method | TBD |
| Per-feature acceptable regression and error budget | TBD |
| Outlier policy, rerun policy, reviewer and approved date | TBD |

Never fill TBD with post hoc thresholds chosen from already observed data.

## What to run, and what it proves

1. Run repeated comparisons on **independently controlled fixed hardware**;
   public shared GitHub runners provide a smoke baseline, not a fixed CPU.
   Record power/affinity/OS and exact environment versions.
2. Retain installed-wheel SHA verification; no editable checkout in either
   measured application. Compare only common features with matching
   dependencies, except when testing a specifically **opt-in** 0.7 feature
   ON vs OFF on the same candidate wheel.
3. Use **real network HTTP sockets** as well as `httpx.ASGITransport`.
   Cover HIT/MISS/304, Vary, auth bypass, small/medium/large payloads,
   TTL, namespace clearing and one slow endpoint.
4. Use a disposable local Redis 7.4 for GET/SET concurrency, disconnect,
   timeout, cancellation, reconnect and cleanup. Never remote Redis,
   FLUSHDB or production keys.
5. Report raw per-operation CSV, per-run JSON and CPU/RSS, process
   high-water scope, samples per tail percentile, failures, client pool,
   source/wheel hash and dependency freeze. Individual operations are not
   independent machine runs.
6. Record a blinded decision vs **pre-approved** limits. If statistical
   variation is too high or tail counts insufficient, report
   **INCONCLUSIVE** and collect additional evidence, not a relaxed budget.

No automatic release/merge GO can be inferred from a single GitHub CI
benchmark. This protocol needs maintainer and independent reviewer
approval before any numerical threshold becomes binding.

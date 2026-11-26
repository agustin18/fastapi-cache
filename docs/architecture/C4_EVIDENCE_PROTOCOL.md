# C4 — installed isolation and descriptive evidence (D8)

Scope: C1–C3 merged in unreleased stable; #53 and #100 remain open.
This is the preregistration of a **descriptive** hosted-runner experiment,
not a numerical regression budget or a release authorization. The protocol
in [REGRESSION_BUDGET_PROTOCOL.md](../../benchmarks/REGRESSION_BUDGET_PROTOCOL.md)
requires separate maintainer/reviewer approval and controlled independent
hardware before any performance certification.

## Correctness gates

- Exact candidate wheel and sdist independently installed outside checkout;
  standard CPython 3.8–3.14, standalone loopback Redis 7.4 and InMemory.
- Distinct apps sharing storage, two validated synthetic principals each,
  two locale variants, concurrent requests, conditional 304 and private
  no-store, authorization before lookup, disjoint clear, legacy bytes
  unchanged and rollback to the singleton. Same scope across fresh spawned
  processes deliberately reuses an entry; different scope does not.
- Negative hidden-context example: an application that omits its tenant
  input can still replay the wrong result within one scope. Explicit
  validated identity-aware builder or bypass remains required.
- Reuse installed C1/C3 regression tests (mount, router, hostile builder,
  wrong loop, cancellation, drain, corrupt reads, write uncertainty).
  Add exact built-in Redis transport exception tests requested by C3 review.
- Any unexpected wrong body/header, cross-scope read/clear, failed drain,
  dependency mismatch, artifact import mismatch or failed test blocks C4.
  Do not relax or skip required CI. Experimental services, 3.14t/3.15,
  distributed coordination, tenant auto-detection and owned mode excluded.

## Performance protocol (before first run)

Published 0.7.2 wheel SHA-256
`31257d8de8e5b36b13f50d233c72bf3a53d99b8eb3376264112be9072abf5fa0`;
candidate wheel built from exact PR HEAD (still metadata 0.7.2; distinct
hash). Record both hashes, source SHA, CPU, RAM, OS, Redis version and
identical dependency freeze. Python 3.12, FastAPI 0.115.12, Pydantic
2.8.2, httpx 0.27.0, redis-py 5.2.1, Uvicorn 0.34.0. Independent
venvs, fresh process per mode per round, rotating order:

| Round | Order |
| --- | --- |
| 1 | published, candidate-legacy, scoped-off, scoped-on |
| 2 | candidate-legacy, scoped-off, scoped-on, published |
| 3 | scoped-off, scoped-on, published, candidate-legacy |
| 4 | scoped-on, published, candidate-legacy, scoped-off |

Each mode runs InMemory and standalone Redis, ASGI and real loopback
TCP HTTP (Uvicorn client/server in the same process and loop; not
separate-host or production network evidence). Each serial case uses
20 warmup and 120 measured requests, concurrent HIT 8 uses two warmup
batches and 15 measured batches (120 requests). Cases: 128/4096/65536-byte
payload HIT, conditional 304, distinct-key cold MISS, auth bypass,
Vary HIT, 5ms synthetic slow MISS, concurrent HIT. Record raw per-request
duration, nearest-rank p50/p95/p99, throughput, per-process CPU/peak RSS
and start/close observations; paired median ratios and sample standard
deviation per case, no outlier removal. Request count is not independent
machine-run count. Lifecycle timings are observations of different
operations, not directly comparable semantic contracts. Backend state
is isolated by unique prefixes; no flush. Real network failures,
1000-client load, hardware-controlled repetitions, power governor and
approved numerical budgets are **NOT RUN / not approved** here.

Primary comparisons: candidate legacy vs published, scoped defaults vs
candidate legacy, all policy flags on vs scoped defaults. Timings may
vary and tails have limited samples. CI requires successful execution,
correctness, raw/summary records, adequate counts and matching case
sets; numerical timing ratios are never a GO/NO-GO. No post-hoc
thresholds, superiority, SLA or HA claim. Overall performance
certification remains INCONCLUSIVE; independent hardware and approved
budgets remain residual #100. Re-run on the final promoted release
source if the independent release review requires it; do not reuse
the candidate hash as publication evidence.

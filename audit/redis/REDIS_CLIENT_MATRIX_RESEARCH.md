# Redis client compatibility investigation — issue #47

**Status:** exploratory research only; requires a complete verified Actions run
and an independent consumer before widening published package metadata.

The existing published `fastapi-cache-stable==0.3.1` contract remains
`redis = "^4.2.0rc1"` (redis-py 4.x). This PR does **not** change
`pyproject.toml`, `poetry.lock`, cache key formats, backend runtime code,
or a release tag.

## Evidence model

Workflow: [redis-client-matrix.yml](../../.github/workflows/redis-client-matrix.yml).

- Builds a **real wheel** from a scratch copy of the checkout.
- Required redis-py 4.x lanes retain the unmodified dependency metadata.
- Exploratory redis-py 5–8 lanes build a **non-publishable scratch wheel**
  whose Redis requirement alone is temporarily widened to
  `>=4.2.0rc1,<9.0.0`. The scratch change is made outside the repository,
  with an exact-text precondition; it is not a proposal to publish that range.
- Installs each wheel and its selected Redis client via pip in a fresh
  non-editable virtual environment, verifies package imports come from
  `site-packages`, validates the wheel's active `Requires-Dist` and runs
  `pip check`. The package version inside this scratch wheel remains
  `0.3.1` **only as build metadata**, not as a new published artifact.
- Runs the Redis backend tests and an external-process FastAPI consumer probe
  from outside the source checkout, all against actual isolated Redis
  containers. The probe checks MISS/HIT, namespace clear, per-tenant
  identity-aware key building, explicit Request default bypass and
  reinitialization/restart behavior.
- Captures per-lane uploaded artifacts: wheel digest, versions, install
  manifest, pip check and test stdout. **The artifacts are evidence of this
  temporary research build only, not of PyPI release provenance.**

### Deliberately pinned matrix

The 25 explicit workflow lanes are the source of truth. They include every
supported Python 3.8–3.13 interpreter, redis-py 4.6 / 5.2 / 6.1 / 7.0 / 7.2 /
8.1 where upstream's interpreter requirements allow it, and Redis servers
6.2, 7.0, 7.4 and 8.0. Tests cover 4.x required baseline lanes plus the
out-of-range exploratory lanes.

| Python | Required published lane | Exploratory redis-py clients |
|---|---|---|
| 3.8 | 4.6.0 | 5.2.1, 6.1.0 |
| 3.9 | 4.6.0 | 5.2.1, 6.1.0, 7.0.1 |
| 3.10 | 4.6.0 | 5.2.1, 7.2.1, 8.1.0 |
| 3.11 | 4.6.0 | 6.1.0, 7.2.1, 8.1.0 |
| 3.12 | 4.6.0 | 5.2.1, 6.1.0, 7.2.1, 8.1.0 |
| 3.13 | 4.6.0 | 5.2.1, 6.1.0, 7.2.1, 8.1.0 |

A passing lane demonstrates compatibility **only for that exact client,
Python, server, and set of operations**. It does not establish a complete
cross-product of all supported versions or justify using open-ended majors.
All 25 lanes are **strictly required to pass** for this research PR: exploratory
means out of published support, not allowed-to-fail CI. The implementation PR
must then make its selected production support lanes mandatory release checks.

Upstream redis-py interpreter boundaries (not inferred from wheel names):

- Python 3.8: last compatible redis-py series 6.1.x.
- Python 3.9: last compatible redis-py series 7.0.x.
- Python 3.10: last compatible redis-py series 8.1.x.
- Starting redis-py 8.0: RESP3 is the default wire protocol, with legacy
  Python response shapes by default.

Sources: [redis-py upstream README](https://github.com/redis/redis-py#supported-python-versions),
[RESP3 features](https://redis.readthedocs.io/en/latest/resp3_features.html),
[redis-py releases](https://github.com/redis/redis-py/releases).

## Functional surface characterized

`tests/test_redis_client_matrix.py` and existing
`tests/test_redis_clear.py` exercise:

- Binary GET/SET, TTL=positive, no-expiry TTL=-1, missing TTL=-2 and
  expiration; Redis pipeline with transaction semantics.
- Wrong-type Redis errors and subsequent connection reuse.
- Explicit RESP2 / RESP3 on redis-py >=5, plus its default protocol;
  these are **actual** server connections, not mocks. Redis 7/8 exposes
  `resp=` in `CLIENT INFO`, so the negotiated wire mode is asserted there.
  Redis 6.2 does not expose that field and its protocol is exercised but
  not independently asserted via `CLIENT INFO`.
- `decode_responses=False` for binary cache payloads, and
  `decode_responses=True` for textual reads and namespace clearing.
- ACL password authorization, rejected invalid passwords, async close.
- Namespace boundaries, glob metacharacters, filtered SCAN, UNLINK,
  duplicate/no-op clears, batches and key deletion.
- Real FastAPI request-level MISS/HIT, and an independent installed-wheel
  application with authentication, tenant separation, clear and restart.

**Important decoder boundary:** `RedisBackend` expects `bytes` payloads.
A `Redis(decode_responses=True)` returns `str` for textual cache values
and can fail on arbitrary non-UTF8 payloads; clearing namespace with decoded
keys is characterized, but a decoded client is **not** certified for
`@cache` value serialization. Future implementation must either document
`decode_responses=False` clearly or implement and test coercion safely.

## Constraints and remaining independent gates

- **Real-estate-arg:** this consumer repository was not accessible to the
  auditor connection. The isolated wheel consumer is useful automated
  evidence, **not** a substitute for running its real application suite.
  Local maintainer must run a clean, non-editable install for at least one
  independent application, verify functional HIT/MISS, auth, tenant context,
  namespace clear, rollback and previous version where relevant. Record
  commit, commands, environment and redacted results in a separate review.
- Redis Cluster: real cluster operations **not covered**. Namespace clear
  intentionally remains `NotImplementedError`. Existing fake-cluster tests
  prove the intentional failure and key-only behavior only.
- Sentinel failover and TLS: **not covered by real infrastructure**. These
  are connection-establishment responsibilities of the application-supplied
  Redis client; no end-to-end claims until exercised against real services.
- Auth: ACL username/password tested against a real standalone Redis
  server, not a managed external provider.
- Connection pools/RESP3: explicitly chosen protocol, inherited default,
  basic client close and redis-server compatibility are covered, not every
  hiredis parser, optional module, notification or reconnect/failover path.
- Long-lived multi-process cache consistency, production throughput,
  shared Redis/Valkey environments and complex custom key builders require
  later consumer/integration evidence.
- The temporary widened candidate wheel proves pip-resolution feasibility
  for selected versions only. The **implementation PR must choose and test
  real Python-conditional production requirements**, produce wheel/sdist
  under their final metadata, run normal `pip check` and legacy migration
  tests, and complete the security review. No production upgrade is implicit.

## Acceptance for moving to implementation (not releasing 0.4.0)

1. CI green for mandatory published lanes; record **all** exploratory lane
   results and any allowed-to-fail exceptions from the exact head commit.
2. Record response semantics, `decode_responses` boundary, TLS/Cluster/Sentinel
   scope decisions and client/server/CPython version table with evidence.
3. Identify a minimal support-lane proposal by Python, not one blanket range.
4. Keep #47 open. Implement in a new PR from current `stable`, with
   mandatory (not allowed-failure) tested lanes, real release-shaped metadata,
   clean wheel/sdist and an **independent application** migration/rollback.
5. No tags or PyPI publication from this research branch.

## Evidence integrity correction (superseded run)

An initial expanded [matrix run 44639267562](https://github.com/agustin18/fastapi-cache/actions/runs/44639267562)
was **NOT valid evidence of 25/25 test success**. The implicit Actions
`bash -e` shell used `pytest | tee` without `pipefail`, so pytest failures
could be masked by a successful `tee` exit. For example, Redis 6.2 does not
report a `resp=` field in `CLIENT INFO`; that incomplete probe initially
failed despite a successful job conclusion. This defect is corrected with
`set -o pipefail` **and a deliberate exit-7 pipeline self-test** before
pytest. The Redis 6.2 wire-mode limitation is now explicitly characterized.

**Only a subsequent Actions run on the corrected HEAD may be used for the
final decision.** Do not cite the superseded run as 25 successful test lanes.


## Proposed production lanes (not approved)

These are candidate conditional metadata ranges based on the tested matrix and
upstream interpreter support. They are **not** published in this PR.

| Python | Candidate redis-py range | Evidence lanes |
|---|---|---|
| 3.8 | `>=4.2.0rc1,<6.2` | 4.6.0, 5.2.1, 6.1.0 |
| 3.9 | `>=4.2.0rc1,<7.1` | 4.6.0, 5.2.1, 6.1.0, 7.0.1 |
| 3.10–3.13 | `>=4.2.0rc1,<8.2` | 4.6.0, 5.2.1, 6.1.0, 7.2.1, 8.1.0 |

The `redis-range-resolution` workflow job validates a scratch wheel with those
conditional requirements resolves to the expected client major/minor and passes
`pip check` on representative Python 3.8/3.9/3.10/3.13 interpreters. The
implementation PR must replace the scratch metadata with release-shaped
metadata, test the lower and upper bounds, and avoid claiming untested
interpreter/client combinations.

## Security scan (research evidence)

On 2026-11-19, `pip-audit 2.10.1` was run against requirement files for
`redis==4.6.0`, `redis==6.1.0`, `redis==7.2.1` and `redis==8.1.0`. All four
reported **no known vulnerabilities** from the configured advisory sources.
This is a point-in-time research result, not a permanent guarantee and not a
replacement for the Dependabot delta/security review in the implementation PR.

## Scope decision for a candidate 0.4.0

Unless new evidence justifies otherwise, the implementation should claim:

- Standalone Redis with redis-py clients in the tested series and RESP2/RESP3
  behavior covered by this matrix.
- ACL username/password authentication on a standalone server.
- `decode_responses=False` as the supported binary cache path; decoded clients
  are characterized but not certified for arbitrary `@cache` values.
- **Not certified:** Redis Cluster, Sentinel/failover, TLS, managed-provider
  failover and Cluster namespace clearing. `RedisBackend.clear(namespace=...)`
  must continue to raise the explicit `NotImplementedError` on cluster clients.
- TLS/Sentinel are application-supplied client connection concerns; no
  end-to-end claim without real infrastructure evidence.

## Implementation workflow shape

The research workflow intentionally runs every exploratory lane. The separate
implementation PR should run only the selected mandatory support lanes (the
published-lane baseline plus the chosen upper-bound/client combinations) and
keep the exploratory lanes as optional evidence. Do not run 28 research jobs on
every future PR.

## Real consumer cross-check

See [real-estate-arg consumer validation](REAL_ESTATE_ARG_CONSUMER_VALIDATION.md)
for the local migration/rollback evidence.

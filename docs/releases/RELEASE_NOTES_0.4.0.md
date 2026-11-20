# fastapi-cache-stable 0.4.0 — Redis client compatibility expansion

> **Status: published 2026-11-20.**
> PyPI: [fastapi-cache-stable==0.4.0](https://pypi.org/project/fastapi-cache-stable/0.4.0/).

## What's new

The optional `[redis]` and `[all]` dependencies now accept newer
**redis-py clients** with Python-specific version constraints. Redis client
versions are distinct from Redis server versions.

| CPython | Optional redis-py requirement | Verified client examples |
|---|---|---|
| 3.8 | `>=4.2.0rc1,<6.2` | 4.6.0, 5.2.1, 6.1.x |
| 3.9 | `>=4.2.0rc1,<7.1` | 4.6.0, 5.2.1, 7.0.1 |
| 3.10–3.13 | `>=4.2.0rc1,<8.2` | 4.6.0, 7.2.1, 8.1.0 |

This **preserves redis-py 4.x migration compatibility** and adds tested
options on supported interpreters. The range caps are intentional;
compatibility with untested future versions is not claimed. Python
`>=3.8,<3.14` and the public `fastapi_cache` import remain unchanged.

No RedisBackend cache-key format, binary serialization or runtime behavior
change is intended by this release. A change of redis-py itself may affect
other application code sharing the same client.

## Integration evidence

- [#62 research](https://github.com/agustin18/fastapi-cache/pull/62):
  28 real-server Redis/Python/client profiles, conditional metadata resolution
  tests and separate installed-wheel FastAPI probes.
- [#63 implementation](https://github.com/agustin18/fastapi-cache/pull/63):
  12 release-shaped wheel lanes, 4 source-distribution lanes, Redis server
  6.2/7.0/7.4/8.0 checks, Python 3.8–3.13, targeted redis-py audit, pip
  installation and metadata tests. The 50 GitHub checks were successful
  on the implementation HEAD prior to merging.
- A maintainer reported **48 passing selected tests per profile** using
  `real-estate-arg@4c4b6030` with the final #63 wheel, actual standalone
  Redis 7.4.7 / RedisBackend, redis-py 4.6.0 → 7.2.1 → 8.1.0 → 4.6.0 rollback
  and `pip check` passing each time. This is local maintainer evidence,
  not an archived independent Actions run. It used a temporary test fixture.
- The version-bumped 0.4.0 wheel and sdist were built from the release
  branch and independently installed before publication. The final hashes
  and publication runs are recorded in the
  [release status](RELEASE_STATUS_0.4.0.md).

## Scope and limitations

- **In scope:** standalone Redis clients and operations proven in the
  matrix, RESP2/RESP3, Redis ACL authentication, binary cache payloads with
  `decode_responses=False`, cache MISS/HIT and targeted namespace clearing.
- **Not certified:** Redis Cluster, Sentinel/failover, TLS and managed Redis
  providers. Redis Cluster namespace clear continues to raise
  `NotImplementedError`. Using `decode_responses=True` with arbitrary
  `@cache` binary payloads is not supported.
- **Security boundary:** Python 3.8–3.10 are EOL, functional-compatibility
  targets only. The project's best-effort security-supported environment is
  server-side CPython 3.11–3.13; this release does not fix unrelated
  vulnerabilities in consumer applications, FastAPI, Starlette, AnyIO or
  other runtime dependencies. Check the current security audit and
  [SUPPORT.md](SUPPORT.md) before production deployment.
- The independent `Vary`/hidden-context limitations in
  [#53](https://github.com/agustin18/fastapi-cache/issues/53) are **not**
  solved by redis-py compatibility changes.

## Installation

In a clean virtual environment:

```sh
python -m pip uninstall -y fastapi-cache2
python -m pip install "fastapi-cache-stable[redis]==0.4.0"
python -m pip check
```

Never co-install the upstream and this fork: both provide `fastapi_cache`.
Pin the selected redis-py version if sharing a Redis client with other
libraries; test with real application traffic and preserve a rollback pin.
See [MIGRATION.md](MIGRATION.md) for authentication and cache isolation
caveats. InMemory-only consumers can omit the Redis extra.

## Publication verification

The version-stamped wheel and sdist were built from the final release branch,
checked with `twine check`, installed in clean environments and exercised with
redis-py 4.6.0 and 8.1.0. The final wheel was also run against the disposable
`real-estate-arg` consumer with 4.6.0, 7.2.1, 8.1.0 and rollback. Exact hashes,
workflow runs, provenance and residual security notes are recorded in the
[0.4.0 release status](RELEASE_STATUS_0.4.0.md). #47 closes only after the
published artifacts are verified; #53 remains open for `Vary`/hidden context.

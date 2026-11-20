# fastapi-cache-stable 0.4.0 — Redis client compatibility expansion

> **Status: release preparation only. Not published.**
> The latest verified public PyPI release remains `0.3.1` until a separate
> maintainer-authorized publication completes. These are candidate notes.

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
- The version-bumped **0.4.0 wheel and sdist must still be built and
  independently verified**. Artifacts from #63 bearing `0.3.1` cannot
  stand in for immutable final 0.4.0 artifacts.

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

## Installation once 0.4.0 is published

Do **not** run this command before confirming that `0.4.0` exists on PyPI.
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

## Release decision still required

This PR is **not** a release authorization. Before tagging/publishing:

1. Verify final release-branch CI, metadata markers and `poetry check --lock`,
   wheel/sdist clean installations and pip checks, and Python 3.8–3.13 Redis
   profiles on the exact merge commit.
2. Record final wheel/sdist SHA-256 and immutable CI artifact provenance.
   Reconcile current Dependabot delta/security findings and document
   any newly material risks; old conditional legacy risks do not become
   universally fixed by this release.
3. Exercise the final version-stamped wheel's application smoke/migration/
   rollback or explicitly document any accepted difference from the
   maintainer's #63 consumer evidence.
4. With **separate explicit approval**, create the `v0.4.0` tag from
   `stable`, run the manual TestPyPI workflow, verify distribution digest and
   installation, then run the manual production PyPI workflow only after
   the final sign-off. Update README/current-release links and publish
   provenance only when the version actually exists publicly.
5. Close [#47](https://github.com/agustin18/fastapi-cache/issues/47) when
   the final Redis support release is published and verified.

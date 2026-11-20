# Real consumer validation — `real-estate-arg`

**Local maintainer evidence, 2026-11-19.** This is not an archived CI artifact;
the reproducible workflows and their artifacts are in the Redis matrix runs.

## Consumer and environment

- Consumer repository: `agustin18/real-estate-arg`
- Consumer commit: `4c4b6030349742348c92490793fd8c5f4361d119`
- Disposable worktree only; the consumer `main` branch and tracked files were
  not modified.
- Python 3.11 container based on the consumer's dependency-test image.
- Redis server: `7.4.7` (standalone container).
- Test database: disposable `db_test` PostgreSQL instance.
- Cache backend: real `RedisBackend` on Redis DB 1. The consumer's test-only
  `conftest.py` was overridden in the disposable worktree to initialize
  `RedisBackend` per test and flush the Redis DB between tests. This override
  is not committed to the consumer repository.
- Research wheel: scratch wheel built from this branch with the conditional
  candidate metadata (`>=4.2.0rc1,<6.2` / `<7.1` / `<8.2`).
  SHA-256: `52f000c77bbf660e8664e3cf237ec6af2926ed745db662dd70ff884858f2aeee`.
- The wheel carries version `0.3.1` only as build metadata; it is not a
  published artifact.

## Functional checks

The selected consumer suite contains 46 existing endpoint/cache tests plus two
new Redis-backend probes:

- `/api/v1/agencies/` (default key builder): `MISS → HIT`.
- `/api/v1/locations/roots` (`Request` + custom key builder): `MISS → HIT`.
- Existing locations, agencies and cache tests run against the real test DB
  and real Redis backend.

The same suite was run in this order: redis-py `4.6.0` baseline, `7.2.1`,
`8.1.0`, then **rollback to `4.6.0`**.

| redis-py | Results | `pip check` |
|---|---|---|
| 4.6.0 baseline | 48 passed | PASS |
| 7.2.1 | 48 passed | PASS |
| 8.1.0 | 48 passed | PASS |
| 4.6.0 rollback | 48 passed | PASS |

No test was skipped. The suites used `--no-header --tb=short` and a disposable
pytest cache. Exact commands are recorded in the session log.

## Limits

- This is not the complete `real-estate-arg` test suite and not a production
  deployment.
- Redis TLS, Sentinel, Cluster and managed-provider failover were not involved.
- The consumer test-only `RedisBackend` override is evidence of library
  behavior, not of the application's default test configuration.
- The scratch conditional wheel is research evidence; the implementation PR
  must build and test release-shaped wheel/sdist metadata and repeat the
  consumer/rollback check before publishing `0.4.0`.

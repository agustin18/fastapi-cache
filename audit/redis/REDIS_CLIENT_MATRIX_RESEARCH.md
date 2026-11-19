# Redis client compatibility investigation for #47

**Research only.** This branch does not change the published `redis` extra,
cache key format, runtime dependencies, or version number. Existing
`fastapi-cache-stable==0.3.1` continues to declare redis-py 4.x.

## Matrix

The standalone workflow [Redis client compatibility research](../../.github/workflows/redis-client-matrix.yml)
tests pinned redis-py versions against actual Redis server containers:

| Python | redis-py client | Redis server | Interpretation |
|---|---|---|---|
| 3.8 | 4.6.0 | 7.0 | Required legacy baseline |
| 3.12 | 4.6.0 | 7.0 | Required modern baseline |
| 3.8 | 5.2.1 | 7.0 | Exploratory |
| 3.8 | 6.1.0 | 7.4 | Exploratory; final redis-py 6.x supporting Python 3.8 |
| 3.12 | 5.2.1 | 7.4 | Exploratory |
| 3.12 | 6.1.0 | 7.4 | Exploratory |
| 3.12 | 7.2.1 | 7.4 | Exploratory |
| 3.12 | 8.1.0 | 7.4 | Exploratory RESP3-default client |

The exploratory lanes intentionally override the published redis-py 4.x
dependency constraint while installing their own transitive dependencies. Consequently, an otherwise passing
test does **not** imply that `pip check` passes or that the package currently
supports the corresponding client in its declared metadata. Do not expand
the constraint until compatibility and supported install profiles are tested.

Redis-py 6.1.x is the last 6.x series supporting Python 3.8; later releases
require newer interpreters. redis-py 8 defaults to RESP3 on the wire while
retaining legacy response shapes by default.

References: [redis PyPI](https://pypi.org/project/redis/),
[redis-py releases](https://github.com/redis/redis-py/releases).

## What the test actually proves

- Against real servers, direct RedisBackend GET/SET, binary payloads, TTL
  pipelines and wrong-type error propagation.
- FastAPI decorator MISS -> HIT with a live Redis backend.
- Existing `tests/test_redis_clear.py` exercises namespace boundaries,
  SCAN/UNLINK, glob escaping, batching, deletion and decode_responses clear.

## Not yet proven

- Redis Cluster real-server behavior; namespace clear remains explicitly
  unsupported in cluster mode.
- Redis-py 8 against a Redis 8 server and non-default response parsing options.
- All supported Python versions across every redis-py major and the full
  compatibility/security dependency graph.
- Real consumer migration/rollback with independently published wheels.
- Compatibility with authentication, TLS, Sentinel, failover and constrained
  production connections.

Record results from the real workflow before proposing any new runtime
constraint. An exploratory red job is a finding to diagnose, not an automatic
reason to break the existing redis-py 4.x migration lane.

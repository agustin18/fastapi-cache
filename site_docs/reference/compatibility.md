# Compatibility & support

## Distribution and Python

| Item | Published 0.6.0 |
|---|---|
| Package on PyPI | [`fastapi-cache-stable==0.6.0`](https://pypi.org/project/fastapi-cache-stable/0.6.0/) |
| Python import | `fastapi_cache` |
| Requires-Python | `>=3.8,<3.14` |
| Security-maintained server-side target | CPython 3.11–3.13 |
| Legacy functional migration bridge | CPython 3.8–3.10 |
| Python 3.14 | Unsupported; no metadata claim |
| FastAPI / Pydantic | Tested across pinned legacy and modern CI profiles |

!!! note "Functional compatibility is not a security support promise"
    Python 3.8–3.10 and several historical framework versions are EOL. `pip check` verifies dependency metadata, not runtime safety or your tenant isolation.

The published 0.6.0 wheel also supports optional bounded InMemory via
`InMemoryBackend(max_entries=positive_integer)`; the default remains unbounded.
See the [InMemory guide](../guides/inmemory.md). Published 0.5.0 did not
provide this option. Proposed TTL and malformed-cache changes in
[#123](https://github.com/agustin18/fastapi-cache/pull/123) and
[#124](https://github.com/agustin18/fastapi-cache/pull/124) are **not in 0.6.0**.

## Redis client requirements

| CPython | redis-py `[redis]` constraint |
|---|---|
| 3.8 | `>=4.2.0rc1,<6.2` |
| 3.9 | `>=4.2.0rc1,<7.1` |
| 3.10–3.13 | `>=4.2.0rc1,<8.2` |

`decode_responses=False` is required for binary payloads. Redis standalone is the primary supported deployment. Redis Cluster namespace clearing is unsupported; TLS, Sentinel, failover, managed transports are not fully certified. Memcached/DynamoDB remain experimental.

## Migrating safely

Anonymous GET/JSON and the default key builder have published golden migration tests. Safer auth/Request handling and selective clear can intentionally change observed behavior.

- [From scratch](../getting-started.md)
- [Migrate existing applications](../migration.md)
- [Security/tenant context](../guides/privacy.md)
- [Full compatibility contract](https://github.com/agustin18/fastapi-cache/blob/stable/COMPATIBILITY.md)
- [Support policy](https://github.com/agustin18/fastapi-cache/blob/stable/SUPPORT.md)

# Compatibility & support

## Distribution and Python

| Item | Published 0.8.0 |
|---|---|
| Package on PyPI | [`fastapi-cache-stable==0.8.0`](https://pypi.org/project/fastapi-cache-stable/0.8.0/) |
| Python import | `fastapi_cache` |
| Requires-Python | `>=3.8,<3.15` |
| Security-maintained server-side target | CPython 3.11–3.14 |
| Legacy functional migration bridge | CPython 3.8–3.10 |
| Python 3.14 | Supported; standard CPython 3.14 |
| FastAPI / Pydantic | Tested across pinned legacy and modern CI profiles |

Published 0.8.0 includes standard CPython 3.14 and the modern Redis extra on
3.14; exact-artifact Phase B evidence is recorded in the release status. No
free-threaded 3.14t or 3.15 support claim.

!!! note "Functional compatibility is not a security support promise"
    Python 3.8–3.10 and several historical framework versions are EOL. `pip check` verifies dependency metadata, not runtime safety or your tenant isolation.

The published 0.8.0 wheel also supports optional bounded InMemory via
`InMemoryBackend(max_entries=positive_integer)`; the default remains unbounded.
See the [InMemory guide](../guides/inmemory.md). Published 0.5.0 did not
provide this option. The exact TTL boundary from
[#123](https://github.com/agustin18/fastapi-cache/pull/123) and decode-before-304
behavior from [#124](https://github.com/agustin18/fastapi-cache/pull/124) are
included in published 0.8.0 alongside the C2 backend capability/ownership
contracts and C3 failure policies. Residual C3 limits (#112), hidden tenant
context (#53) and performance certification (#100) remain open.

## 0.8.0 app scope and failure policies

| Capability | InMemory | Standalone Redis | Custom / Memcached / DynamoDB |
|---|---|---|---|
| `CacheConfig` / `CacheHandle` app scope | Supported | Supported | Not app-scope eligible |
| Scoped physical-key envelope | Yes | Yes | N/A |
| `CacheFailurePolicy(strict_read=True)` | Supported | Redis connection/timeout only | Redis-oriented contract |
| `conservative_write` | Supported | Supported | General behavior; validate |
| `recover_json` | Supported | Supported | General behavior; validate |

App scope does not automatically discover hidden tenant or identity context.
One handle is bound to one Starlette app and one event loop; use a unique
`scope_id` and an identity-aware key builder. The legacy singleton default is
unchanged. Failure policies are opt-in and do not provide retries, repair or
distributed consistency; see #112.

## Redis client requirements

| CPython | redis-py `[redis]` constraint |
|---|---|
| 3.8 | `>=4.2.0rc1,<6.2` |
| 3.9 | `>=4.2.0rc1,<7.1` |
| 3.10–3.14 | `>=4.2.0rc1,<8.2` |

`decode_responses=False` is required for binary payloads. Redis standalone is the primary supported deployment. Redis Cluster namespace clearing is unsupported; TLS, Sentinel, failover, managed transports are not fully certified. Memcached/DynamoDB remain experimental.

## Migrating safely

Anonymous GET/JSON and the default key builder have published golden migration tests. Safer auth/Request handling and selective clear can intentionally change observed behavior.

- [From scratch](../getting-started.md)
- [Migrate existing applications](../migration.md)
- [Security/tenant context](../guides/privacy.md)
- [Full compatibility contract](https://github.com/agustin18/fastapi-cache/blob/stable/COMPATIBILITY.md)
- [Support policy](https://github.com/agustin18/fastapi-cache/blob/stable/SUPPORT.md)

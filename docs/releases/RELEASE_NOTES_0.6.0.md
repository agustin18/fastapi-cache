# fastapi-cache-stable 0.6.0 — published release notes

**Published to PyPI on 2026-11-21.** This is a technical release based on
project tests and exact-artifact evidence; it does not claim independent
certification or external adoption.

## What changes since published 0.5.0

### Optional bounded InMemory

`InMemoryBackend(max_entries=N)` adds an optional per-instance entry
cap. When full, a new key first reclaims one expired entry when
available; otherwise it evicts the least-recently-used entry. An indexed
heap tracks TTL expiry, so ordinary bounded writes do not sweep the
whole store. Reads refresh recency.

The cap is validated once at construction: positive integer or `None`
(unbounded default), with booleans disallowed. `backend.max_entries` is
read-only; assignments raise `AttributeError`. The cap is not a
memory-byte limit and does not synchronize multiple workers or
thread/event-loop instances. See [PR #85](https://github.com/agustin18/fastapi-cache/pull/85).

### Privacy and HTTP cache boundaries

The 0.6.0 source checks all Authorization/Cookie header occurrences and
keeps generated `Cache-Control: private, no-store` on cached HTTP
responses from routes with authenticated caching enabled, including
MISS/HIT/304. This is an HTTP intermediary policy, not a replacement for
an identity-aware server-side cache key or authorization checks. Existing
private entries in intermediaries may need deliberate invalidation. See
[SECURITY.md](../../SECURITY.md) and [#53](https://github.com/agustin18/fastapi-cache/issues/53).

### Release validation

The release workflow requires one reviewed wheel/sdist pair from a
successful final Phase B run. TestPyPI and PyPI then retrieve that exact
pair; neither upload rebuilds the package.

## Install

```console
python -m pip install "fastapi-cache-stable==0.6.0"
python -m pip check
```

Redis: `fastapi-cache-stable[redis]==0.6.0`.

## Compatibility and limitations

- Distribution `fastapi-cache-stable`; import remains `fastapi_cache`.
  Ordinary legacy cache keys and the default `@cache` contract remain
  unchanged; non-default or sensitive legacy keys may need migration.
- Metadata range `>=3.8,<3.14` retains Python 3.8–3.10 as functional
  legacy compatibility, not security-supported deployments. Production
  security work targets CPython 3.11–3.13.
- Redis standalone is the supported shared-backend path. Redis Cluster
  namespace-wide `clear()` is unsupported; Memcached and DynamoDB remain
  experimental.
- Hidden identity in ContextVar/middleware/tenant state, custom auth
  headers, proxies, unbounded cardinality, legacy private Redis data and
  process-global configuration remain application/infrastructure
  responsibilities.
- Cache event hooks, argument omission, distributed locks, stale serving,
  tag invalidation, automatic per-app configuration and Python 3.14
  support are not part of 0.6.0.

## Release evidence

- Final source: `6b6924a61bbcc0ba602da514accb4c563806742f`
- Phase B: run `44944620217`, attempt 1, 20/20 jobs
- Wheel SHA-256: `60be61f68908bb8621a53c902baed2b61c9e894cffa95d8df0e9dd71c5bc4b5e`
- Sdist SHA-256: `c0f8f8b872d337b432afd1340dbe8b9b1800933dfed9c3f3c14ad232153408f2`
- TestPyPI: run `44944911074`
- PyPI: run `44945090377`
- [Status and provenance](RELEASE_STATUS_0.6.0.md)

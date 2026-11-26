# fastapi-cache-stable 0.8.0

Community-maintained, drop-in stable fork of
[fastapi-cache2](https://pypi.org/project/fastapi-cache2/). The Python import
stays `fastapi_cache`; existing singleton users keep the compatible default.

> **0.8.0 release metadata.** The published package version is `0.8.0`.
> Python support is `>=3.8,<3.15`: 3.8–3.10 are functional legacy profiles
> and 3.11–3.14 are the security target. Free-threaded 3.14t is not included.
>
> [Documentation](https://agustin18.github.io/fastapi-cache/) ·
> [Migration](https://github.com/agustin18/fastapi-cache/blob/stable/MIGRATION.md) ·
> [Compatibility](https://github.com/agustin18/fastapi-cache/blob/stable/COMPATIBILITY.md) ·
> [Security](https://github.com/agustin18/fastapi-cache/blob/stable/SECURITY.md) ·
> [Support](https://github.com/agustin18/fastapi-cache/blob/stable/SUPPORT.md) ·
> [Changelog](https://github.com/agustin18/fastapi-cache/blob/stable/CHANGELOG.md).

Install the exact released artifact:

```console
python -m pip install "fastapi-cache-stable==0.8.0"
python -m pip install "fastapi-cache-stable[redis]==0.8.0"
```

## What is in 0.8.0

- **Opt-in application scope:** `CacheConfig`, `CacheHandle` and
  `CacheScopeError` bind a cache to one FastAPI app with an explicit
  `scope_id`. Use `@cache(scope="app")`. The legacy singleton remains the
  default; scoped entries use a distinct physical-key envelope.
- **Opt-in failure policies:** `CacheFailurePolicy` controls classified
  standalone Redis read transport errors, conservative responses after a
  failed SET, and one uncached recompute for exact built-in JSON syntax/UTF-8
  failures. Every flag defaults to `False`; custom coders, Pickle, typed
  validation errors and tag conversion errors keep their previous behavior.
- **Backend contracts:** an internal descriptor records capabilities and
  ownership for exact built-in InMemory and standalone Redis adapters. It
  does not change legacy `Backend` signatures or promote experimental
  providers.
- **Isolation evidence:** installed wheel/sdist tests cover separate apps,
  identities, locales, conditional 304, private responses, cross-process
  scope reuse and rollback. The 0.7.2 comparison is descriptive; it is not a
  performance certification.

## Scoped example

```python
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi_cache import CacheConfig, CacheHandle
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.decorator import cache


@asynccontextmanager
async def lifespan(app: FastAPI):
    handle = CacheHandle(
        CacheConfig(InMemoryBackend(), scope_id="orders-v1")
    )
    await handle.start(app)
    try:
        yield
    finally:
        await handle.aclose()


app = FastAPI(lifespan=lifespan)


@app.get("/orders")
@cache(scope="app", expire=60)
async def orders() -> list[str]:
    return ["order-1"]
```

`CacheConfig` supports exact `InMemoryBackend` and standalone `RedisBackend`
for app scope. Use a unique `scope_id` per logical app on shared storage;
duplicate IDs and direct external writes are not automatically detectable.

## Boundaries

- App scope is opt-in and **does not auto-detect** tenant, authorization,
  locale or arbitrary request context. Use a validated identity-aware
  `key_builder` and/or explicit `vary_headers`; the C4 evidence includes a
  negative hidden-context example. [#53](https://github.com/agustin18/fastapi-cache/issues/53)
- The C4 comparison is descriptive and **INCONCLUSIVE**; the latest 0.8.0
  re-run did not reproduce the earlier concurrent p50 outlier, but no
  latency, p95/p99, HA or no-regression claim is made. [#100](https://github.com/agustin18/fastapi-cache/issues/100)
- `#111` and `#112` keep their broader residual scopes open; `#45`
  (DynamoDB) remains experimental; `#102` advanced Redis HA/TLS/Sentinel/
  Cluster profiles remain outside this release.
- Redis Cluster namespace clear, automatic tenant detection, single-flight,
  tags, stale serving and ownership transfer are not part of 0.8.0.
- `PickleCoder` requires fully trusted cache bytes and store access; an ETag
  is not data integrity or authorization.

See the [0.8.0 release notes](https://github.com/agustin18/fastapi-cache/blob/stable/docs/releases/RELEASE_NOTES_0.8.0.md)
for the complete scope and the [release evidence](https://github.com/agustin18/fastapi-cache/blob/stable/docs/releases/RELEASE_CANDIDATE_0.8.0.md)
for the pending publication gates.

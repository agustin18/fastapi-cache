# ChangeLog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

This project uses [*towncrier*](https://towncrier.readthedocs.io/) and the changes for the upcoming release can be found in <https://github.com/agustin18/fastapi-cache/tree/stable/changelog.d/>.

<!-- towncrier release notes start -->

## [0.3.0a1](https://github.com/agustin18/fastapi-cache/tree/v0.3.0a1) - 2026-11-14

### Bugfixes

- Avoid caching explicitly returned `Response` objects with status codes >= 400. Adapted from upstream PR #575 by RitiGrover. [#2](https://github.com/agustin18/fastapi-cache/issues/2)
- Add opt-in `TypedJsonCoder` for Pydantic v2 typed restoration. `JsonCoder` keeps the legacy decoded behavior; Pydantic v1 and unsupported annotations fall back; validation errors propagate. Adapted from upstream PR #576 by bezff. [#4](https://github.com/agustin18/fastapi-cache/issues/4)
- Fix `clear(key=...)` so it deletes only the requested key, and require the `:` boundary for
  namespace clears in InMemory and Redis. Redis standalone now uses `SCAN`/`UNLINK`; Redis
  Cluster namespace clearing raises `NotImplementedError`. Memcached/DynamoDB clear remains
  unsupported. [#7](https://github.com/agustin18/fastapi-cache/issues/7)

### Improved Documentation

- Document and verify the legacy compatibility matrix: Python 3.8/3.9, FastAPI 0.111.1, and
  Pydantic 1.10.27/2.8.2. Add a legacy CI job and a Python 3.8 wheel smoke test. No runtime
  behavior changes. [#5](https://github.com/agustin18/fastapi-cache/issues/5)

### Misc

- Bump the transitive `certifi` dev/test dependency from 2024.7.4 to 2026.10.23. [#6](https://github.com/agustin18/fastapi-cache/issues/6)
- Add a manual TestPyPI publishing workflow with a separate `testpypi` environment and Trusted Publisher. It never runs on `release: published`. [#8](https://github.com/agustin18/fastapi-cache/issues/8)
- Make PyPI publishing manual-only by removing the `release: published` trigger. [#9](https://github.com/agustin18/fastapi-cache/issues/9)

## 0.3.0a0

- Community-maintained stable fork of fastapi-cache2, based on v0.2.2.
- Distribution renamed to `fastapi-cache-stable`; the `fastapi_cache` import and public API are unchanged.
- Declare `jinja2` as a direct dependency; the `starlette.templating` import in `coder.py` requires it.
- This is an alpha to reserve the PyPI distribution name. The 0.3.0 release will include the P0 correctness fixes and compatibility tests.

## 0.2

### 0.2.1
- Fix picklecoder
- Fix connection failure transparency and add logging
- Add Cache-Control and ETag on first response
- Support Async RedisCluster client from redis-py

### 0.2.0

- Make `request` and `response` optional.
- Add typing info to the `cache` decorator.
- Support cache jinja2 template response.
- Support cache `JSONResponse`
- Add `py.typed` file and type hints
- Add TestCase
- Fix cache decorate sync function
- Transparently handle backend connection failures.

## 0.1

### 0.1.10

- Add `Cache-Control:no-cache` support.

### 0.1.9

- Replace `aioredis` with `redis-py`.

### 0.1.8

- Support `dynamodb` backend.

### 0.1.7

- Fix default json coder for datetime.
- Add `enable` param to `init`.

### 0.1.6

- Fix redis cache.
- Encode key builder.

### 0.1.5

- Fix setting expire for redis (#24)
- Update expire key

### 0.1.4

- Fix default expire for memcached. (#13)
- Update default key builder. (#12)

### 0.1.3

- Fix cache key builder.

### 0.1.2

- Add default config when init.
- Update JsonEncoder.

### 0.1.1

- Add in-memory support.

### 0.1.0

- First version release.

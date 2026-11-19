# ChangeLog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

This project uses [*towncrier*](https://towncrier.readthedocs.io/) and the changes for the upcoming release can be found in <https://github.com/agustin18/fastapi-cache/tree/stable/changelog.d/>.

<!-- towncrier release notes start -->

## [0.3.0](https://github.com/agustin18/fastapi-cache/tree/v0.3.0) - 2026-11-19

### First stable release

- Promote the previously tested `0.3.0rc2` runtime to the first stable
  `fastapi-cache-stable` release. The Python module remains `fastapi_cache`
  and documented migration behavior is unchanged since RC2; see
  [the 0.3.0 release notes](RELEASE_NOTES_0.3.0.md) and
  [the migration guide](MIGRATION.md).
- Preserve Python 3.8–3.10 as **functional legacy compatibility only**;
  recommend server-side CPython 3.11–3.13 for best-effort security maintenance.
  Memcached/DynamoDB remain experimental; redis-py 4.x is the supported
  Redis client line in this release.

### Improved Documentation

- Record RC2 publication evidence, reconcile the captured Dependabot alerts
  with the security ledger and explicitly bound the remaining conditional
  legacy/consumer vulnerabilities without claiming they were globally
  fixed. [#40](https://github.com/agustin18/fastapi-cache/pull/40)
- Document legacy Python security limitations, recommended modern
  environments and shared-dependency risks, alongside a roadmap for
  post-0.3.0 development. [#41](https://github.com/agustin18/fastapi-cache/pull/41)

### Misc

- Prepare stable version metadata, release notes and the maintainer-directed,
  explicitly scoped acceptance of 21 previously reviewed open GHSA. This
  acceptance does not dismiss alerts, guarantee downstream application
  security or eliminate the need to verify the final published distribution.
  [#42](https://github.com/agustin18/fastapi-cache/pull/42)

## [0.3.0rc2](https://github.com/agustin18/fastapi-cache/tree/v0.3.0rc2) - 2026-11-19

### Bugfixes

- Add opt-in FastAPI return-annotation response-model inference with
  `@cache(infer_response_model=True)`, while preserving legacy route
  registration and cache-key behavior by default. Characterize injected
  dependency keys and strengthen optional pagination integration tests. [#33](https://github.com/agustin18/fastapi-cache/issues/33)
- Remove the unused Redis example static-file mount, which previously served the process working directory and exposed legacy Starlette FileResponse paths. Track the conditional Starlette Range-header GHSA for explicit pre-stable reconciliation without claiming downstream dependencies are patched. [#37](https://github.com/agustin18/fastapi-cache/issues/37)

### Improved Documentation

- Clarify migration, exact release-artifact validation and rollback precautions;
  document inherited integration limits, and correct README Redis lifecycle and
  custom key-builder examples. [#31](https://github.com/agustin18/fastapi-cache/issues/31)
- Move immutable Dependabot snapshots, the advisory triage register and the security dependency inventory into `audit/security/`, with links and reconciliation defaults updated. Keep existing user-facing guide URLs stable. [#36](https://github.com/agustin18/fastapi-cache/issues/36)

### Misc

- Refresh the Poetry dependency lock to reduce vulnerable, stale transitive packages while retaining the Python 3.8–3.13 compatibility contract. Security dispositions remain subject to profile-specific review. [#35](https://github.com/agustin18/fastapi-cache/issues/35)
- Capture and reconcile the authenticated Dependabot snapshot after PR #37. Document the Starlette Range-header GHSA as a conditional legacy/consumer risk for RC2 without marking the alert fixed or extending security support to Python 3.8/3.9. [#38](https://github.com/agustin18/fastapi-cache/issues/38)

## [0.3.0rc1](https://pypi.org/project/fastapi-cache-stable/0.3.0rc1/) - 2026-11-18

### Bugfixes

- Request `Cache-Control` directives are parsed case-insensitively across comma-separated and
  repeated header fields. `no-cache` recomputes and refreshes the wrapped endpoint result, while
  `no-store` bypasses the decorator cache for that request. [#26](https://github.com/agustin18/fastapi-cache/issues/26)

### Misc

- Stable `0.3.0` preserves installation on Python `>=3.8,<3.14`. Python 3.8–3.10 remain legacy
  functional-compatibility targets without a security-support commitment; the security-supported
  matrix is Python 3.11–3.13. Critical advisories in legacy profiles still require applicability
  triage before stable.

  The dependency lock selects Pendulum by Python version and includes time-machine only for the
  CPython 3.8 metadata requirement.

  JsonCoder preserves the instant and UTC offset of timezone-aware datetimes; the JSON format does
  not retain the original IANA timezone identifier. [#25](https://github.com/agustin18/fastapi-cache/issues/25)
- Add a guarded Redis migration E2E harness for the legacy writer, candidate reader, targeted
  namespace cleanup and rollback path. [#27](https://github.com/agustin18/fastapi-cache/issues/27)
- Scope the target stable `0.3.0` DynamoDB extra to Python `>=3.10` and
  `aiohttp>=3.14.4`; the extra is not installed on Python 3.8/3.9. Modern Poetry
  development profiles lock AnyIO to `>=4.14.2`. AnyIO 4.5.2 remains only in isolated
  Python 3.8/3.9 tests with no untrusted external endpoints; this does not extend the
  security-support commitment to consumer applications. [#28](https://github.com/agustin18/fastapi-cache/issues/28)

## [0.3.0b1](https://github.com/agustin18/fastapi-cache/tree/v0.3.0b1) - 2026-11-16

### Bugfixes

- `FastAPICache.init()` now raises `RuntimeError` when called a second time instead of
  silently keeping the first configuration. Call `FastAPICache.reset()` before
  re-initializing, or pass the keyword-only `force=True` to replace the current configuration
  explicitly. Applications that call `init()` from a lifespan handler must pass `force=True`
  or reset first, because the handler runs on every startup. The bundled examples do this.

  The decorator now resolves the coder and expiry per request instead of overwriting the
  values captured at decoration time, so a re-initialization also applies to endpoints that
  were already called. Reusing the same backend and namespace across coders can leave
  entries in an incompatible format; flush or rotate the namespace when the coder changes. [#18](https://github.com/agustin18/fastapi-cache/issues/18)

### Improved Documentation

- Add GitHub issue forms for bug reports and feature requests, with a template chooser that
  links to the support policy, migration guide, compatibility contract and private
  vulnerability reporting. Blank issues are disabled so reports arrive with the information
  needed to triage them.

  Enable GitHub Issues for the repository and point every bug-reporting reference at a real
  channel instead of "when issues are enabled". Security reports continue to use private
  vulnerability reporting, never a public issue. The security response targets are now stated
  as best-effort targets rather than contractual guarantees. [#20](https://github.com/agustin18/fastapi-cache/issues/20)

### Misc

- Remove the unused `tox.ini` and the `tox` development dependency. CI already runs the
  supported matrix through GitHub Actions, and `CONTRIBUTING.md` documents `pip`, `pytest`,
  Ruff and pre-commit instead of tox, so the tox file only declared a stale Python 3.7-3.11
  matrix that no longer matched reality.

  Add unit tests for the Memcached and DynamoDB backends using fake clients, and run them in a
  new `optional-backends` CI job. They cover key encoding, get/set, TTL handling and the
  unimplemented `clear`. Both backends remain Experimental: there are no integration tests
  against a real service, and `MemcachedBackend.get_with_ttl()` still returns a fixed `3600`
  instead of the real remaining time. [#19](https://github.com/agustin18/fastapi-cache/issues/19)

## [0.3.0a2](https://github.com/agustin18/fastapi-cache/tree/v0.3.0a2) - 2026-11-14

### Bugfixes

- Bypass the cache for requests with a non-empty `Authorization` or `Cookie` header by
  default. Add `cache_authenticated=True` to opt in with an identity-aware `key_builder`;
  opting in with the default key builder raises `ValueError` for authenticated requests.
  Backend error logs now report only the endpoint, namespace, and exception type; they no
  longer include the cache key, exception message, or traceback.
  Clear or rotate the cache namespace when upgrading from versions that cached authenticated
  responses. [#12](https://github.com/agustin18/fastapi-cache/issues/12)
- InMemory backend: `expire=None` now means no expiration instead of immediate expiry, and each
  backend instance has its own store and lock. Existing process-local entries are not shared
  between instances; use a shared backend for cross-process caching. [#13](https://github.com/agustin18/fastapi-cache/issues/13)
- Emit `Cache-Control: max-age` only when the effective expiry is valid and non-negative.
  `expire=None` and no-expiration InMemory hits no longer produce `max-age=None` or
  `max-age=-1`; `ETag` and the cache-status header are still emitted. `expire=0` keeps the
  legacy fallback to the global `expire` value. [#14](https://github.com/agustin18/fastapi-cache/issues/14)
- Use a stable SHA-256 digest for the ETag and emit it as a quoted weak validator
  (`W/"<digest>"`). `If-None-Match` now uses weak comparison, supports comma-separated lists
  and `*`, and is evaluated on both cache hits and misses, including after
  `Cache-Control: no-cache`. Malformed entity-tags are ignored. The ETag value changes once
  when upgrading; clients revalidate and receive the new value. [#15](https://github.com/agustin18/fastapi-cache/issues/15)
- Namespace the internal `_spec_type` marker as `__fastapi_cache_spec_type__` so user payloads
  with `_spec_type` are preserved. `JsonCoder` now caches only simple `JSONResponse` objects
  (status `200`, `application/json`, no custom headers, no background task) and bypasses other
  non-JSON responses (`StreamingResponse`, `FileResponse`, `RedirectResponse`, plain `Response`,
  templates). Responses with `Set-Cookie`, `Cache-Control: no-store`/`private`, or a background
  task are never cached, regardless of the coder. The injected `response` object is also
  checked before a cache read and before writing; cookies, `Cache-Control: no-store`/`private`,
  background tasks, non-`200` statuses, and custom headers bypass the cache. `PickleCoder` caches serializable response
  objects it can reproduce faithfully and bypasses streaming, file, and template responses. Old
  cache entries written with `_spec_type` are treated as user data; flush the namespace if you
  cache `datetime`/`date`/`Decimal` values. [#16](https://github.com/agustin18/fastapi-cache/issues/16)

### Improved Documentation

- Document the published `0.3.0a1` release and pin the alpha install commands. [#11](https://github.com/agustin18/fastapi-cache/issues/11)
- Document the `0.3.0a2` release status, pin the alpha install commands, and record the tested
  Redis/redis-py compatibility. The auth/privacy, InMemory, `Cache-Control`, ETag,
  `_spec_type`, and response-bypass fixes are now available in `0.3.0a2`. [#17](https://github.com/agustin18/fastapi-cache/issues/17)

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

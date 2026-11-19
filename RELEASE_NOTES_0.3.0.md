# fastapi-cache-stable 0.3.0 — first stable release notes (prepared, not published)

> **Publishing status:** candidate release notes accompanying the
> `0.3.0` promotion pull request. No stable wheel, tag, GitHub release
> or PyPI release exists merely because this file or the PR is merged.

`fastapi-cache-stable` is an independently maintained, conservative fork
of `fastapi-cache2==0.2.2`. It retains the `fastapi_cache` import and
normal GET/JSON cached-response behavior for the documented combinations,
while changing some unsafe/incorrect edge cases. Read
[MIGRATION.md](MIGRATION.md) before switching from the original package.

## Release highlights

- Safer default cache handling for requests carrying `Authorization` or
  `Cookie`: these bypass caching unless explicitly opted in with a safe
  identity-aware key builder. Other authentication methods still need
  application review.
- Improved HTTP correctness: stable quoted weak ETags, proper conditional
  `If-None-Match`, `Cache-Control` directives, and bypassing responses
  whose status/headers/background tasks must not be silently discarded.
- Reliable invalidation: targeted `clear(key=...)`, namespace boundary
  matching, Redis SCAN/UNLINK on supported standalone Redis and isolated
  InMemory cache instances. Redis Cluster namespace clearing is not
  implemented and intentionally raises `NotImplementedError`.
- Optional Pydantic v2 `TypedJsonCoder`, opt-in FastAPI response-model
  inference and more explicit repeated `FastAPICache.init()` behavior.
  Defaults prioritize compatibility with older applications.
- Tested version-matched legacy migration and rollback against Redis
  7.4.12; a separate real consumer `real-estate-arg` reportedly passed
  **130 tests (16.58 s)** in a disposable container after replacing the
  installed `fastapi-cache2` dependency via normal pip resolution
  (evidence from the executing local agent, not an archived independent CI run).

## Installation / migration

Use a fresh environment. Both distributions provide the same Python
`fastapi_cache` module and **must not be co-installed**:

```sh
python -m pip uninstall -y fastapi-cache2
python -m pip install "fastapi-cache-stable[redis]==0.3.0"
python -m pip check
```

Update the application lockfile, clear or rotate legacy private cache
entries as needed, and test real endpoint behavior before traffic.
For InMemory-only usage, omit `[redis]`. Memcached and DynamoDB
remain **experimental**. The current optional Redis client is
**redis-py 4.x** (verified with 4.6.0 and Redis server 7); redis-py 5/6/7
is **not** yet in the declared supported dependency range. The published
upstream `fastapi-cache2==0.2.2` also constrained its Redis extra to 4.x;
upstream `main` has an unreleased 5.x upgrade.

## Python and security contract

- **Recommended modern production profiles:** server-side CPython
  **3.11–3.13**, with best-effort 0.3.x security support as described in
  [SUPPORT.md](SUPPORT.md).
- **Functional legacy compatibility only:** Python **3.8–3.10**;
  not a security-maintained interpreter/dependency stack.
- Python 3.14, Pyodide/browser/Node runtimes are not part of this
  version's verified matrix.
- The published **RC2** wheel on Python 3.11–3.13 (all extras)
  had **zero known third-party advisory findings at the time of scan**.
  This **does not** establish that the final 0.3.0 wheel or arbitrary
  downstream applications are vulnerability-free.
- The maintainer has explicitly directed a **release-scoped acceptance**
  of the **21 captured still-open GHSA**, not their dismissal or
  reclassification as fixed. In particular, the AnyIO TLS risk on
  Python 3.8/3.9, Starlette consumer-owned file/form serving risks,
  and urllib3 paths outside the inspected cache code are documented
  in [the 0.3.0 decision](audit/security/MAINTAINER_RISK_ACCEPTANCE_20261119.md).
  A fresh snapshot, independent review and final wheel audit remain
  required before publishing.

## Known limits and what's next

Redis-py 5/6/7, Redis Cluster complete namespace clearing, cache stampede
prevention, tag-based invalidation, key-parameter exclusion, and full
DynamoDB/Memcached parity are **not included** in 0.3.0. Planned priorities
are published in [ROADMAP.md](ROADMAP.md) and should not be mistaken for
shipped capabilities.

## Release execution — manual and gated

1. Independent contra-audit the exact promotion PR HEAD (functional diff,
   risk acceptance scopes, CI and version metadata).
2. Confirm owner review, fresh authenticated Dependabot evidence,
   and rotate/contain any real secrets exposed in Compose logs/history.
3. Merge the reviewed PR into `stable` only after required CI passes.
4. Verify the exact built **0.3.0** wheel/sdist, metadata, Python 3.11–3.13
   installed third-party dependency audit, Python 3.8 smoke and the
   documented integration tests. Record SHA-256 digests from the build.
5. Make and verify immutable tag `v0.3.0` pointing at the reviewed
   merged release commit (tag must match pyproject version).
6. Run existing **manual** `Publish to TestPyPI` workflow from the tag
   for an optional final pre-publish verification, then the **manual**
   `Publish` workflow from the same tag after explicit approval.
   Neither workflow has an automatic release trigger.
7. Verify the PyPI-hosted published wheel **separately**, including its
   actual SHA-256 and clean installation, then publish GitHub Release
   notes and announce the stable version.

**No automatic publish, no tag, and no TestPyPI/PyPI action is performed
by creating or merging the promotion PR.**

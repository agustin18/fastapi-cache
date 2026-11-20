# Migration #69, Part A — published 0.2.2 → published 0.4.1

**Status:** reproducible published-artifact characterization, not a 0.5.0
release approval. The exact final 0.5.0 wheel/sdist and owner application
tests remain Part B.

## Contract and provenance

The test runs two separate *clean* virtual environments from **PyPI wheels**:

| Role | Distribution | Version | Redis client |
|---|---|---|---|
| Legacy writer and rollback reader | `fastapi-cache2` | `0.2.2` | 4.6.0 |
| Stable reader | `fastapi-cache-stable` | `0.4.1` | 4.6.0 |
| Stable modern client smoke | `fastapi-cache-stable` | `0.4.1` | 8.1.0 |

Python 3.11 and 3.12 run against dedicated standalone Redis 7.4 services.
FastAPI 0.111.1, Pydantic 2.8.2 and HTTPX 0.27.0 are intentionally pinned
to avoid claiming parity across unrelated framework upgrades. This is an
isolated **migration reference**, not a modern recommended FastAPI stack.

CI workflow: [`migration-published-parity.yml`](../../.github/workflows/migration-published-parity.yml).
Consumer probes: [InMemory/key/HTTP](../../tests/published_migration_probe.py),
[old-new report comparison](../../tests/published_migration_compare.py),
[real Redis seed/migrate/rollback](../../tests/migration_redis_e2e.py) and
[stable modern Redis client](../../tests/redis_consumer_probe.py).

The workflow downloads the two immutable wheels from the normal PyPI index,
records their SHA-256, installs them separately and asserts which distribution
owns `fastapi_cache` in `site-packages`. A job does **not** build from this
repo or claim that the checkout represents a published release. The runner
keeps the installed package freeze, profile metadata and JSON probe reports
as 90-day artifacts. No credentials or private user data are used: request
identities are synthetic.

## Golden key and compatibility boundary

For a **module-level** function named `sample_endpoint` in module `__main__`,
`args=(7,)`, `kwargs={"lang": "es"}` and namespace
`migration-parity:ordinary`, both published builders must produce:

```text
migration-parity:ordinary:6c5186afe53d101dea5118bda9aebbcf
```

This is MD5 of the original function identity, args and kwargs; it is a
cache-key **compatibility** digest, not a cryptographic security assertion.
No process-local Python `hash()` value is part of this golden.

Ordinary module-level GET endpoints maintain `MISS → HIT` behavior, response
body and Redis entry accessibility; `If-None-Match` on the cached response
returns HTTP 304. **The ETag bytes are intentionally not equal** between
published 0.2.2 and 0.4.1: upstream's `hash(bytes)` was process-randomized,
whereas the fork uses a stable, quoted weak SHA-256 ETag. Do not preserve
stale upstream ETags or require `W/...` raw string equality.

## Differences intentionally *not* preserved

| Behavior | Published 0.2.2 | Published 0.4.1 | Migration action |
|---|---|---|---|
| Explicit `Request` reading `Accept-Language` outside key args | `MISS → HIT`, potentially wrong locale | Bypasses default cache | Accept reduced hit rate or supply independently reviewed variant-aware builder |
| Authorization/Bearer tokens in `Request` | Legacy shared-key collision can replay another identity's result | Authenticated requests bypass by default | Invalidate/rotate old private namespaces; never rollback private traffic without protection |
| Injected `Response` with non-200 status | Legacy may store an inappropriate representation | Status 418 never cached | Treat cache-status and error behavior changes as intentional |
| Ordinary HTTP ETag | `W/{hash(data)}`, unstable between processes | Quoted deterministic weak tag | Do not persist or compare legacy ETags across processes |
| Date/`_spec_type` serialization | May persist legacy typed marker | New coder cannot assume legacy typed restoration | Targeted namespace cleanup; Redis probe verifies unrelated namespace survives |
| Redis `clear(namespace=...)` | Older invalidation behavior | Correct namespace boundary | Scope cleanup precisely; never flush shared Redis or all namespaces |
| Multiple startup calls | Historical re-init behavior | Explicit `reset`/`force` behavior | Review lifespan before deploying/rolling back |
| Generated/factory endpoints | Unscoped legacy key collision | 0.4.1 scopes detected generated handlers | Rotate ambiguous old keys, do not claim bitwise parity |

The probe *demonstrates* the first two intentional divergences with synthetic
inputs, including the unsafe old behavior, **without treating it as a feature
to retain**. The previously reviewed #53 caveat still applies: the fork
cannot automatically discover arbitrary `contextvars`, middleware state,
custom tenant authentication or hidden dependency inputs.

## Safe Redis E2E and rollback limits

The Redis script refuses to run unless an isolated Redis 7 instance, an
explicit consent flag and a unique `fastapi-cache-migration-e2e-...` prefix
are present. It **never calls `FLUSHDB`**; the separate modern Redis smoke
consumer does flush its own dedicated CI Redis instance, only **after** the
legacy/migration/rollback sequence has finished.

The real Redis scenario tests:
1. Original 0.2.2 writes an ordinary entry, a legacy private cache entry,
   a `_spec_type` representation and an unrelated namespace witness.
2. Published 0.4.1 selectively removes the unsafe `private` and incompatible
   `special` entries; confirms the unrelated entry survived; reads the old
   ordinary entry and refreshes it with `Cache-Control: no-cache`.
3. Original 0.2.2 can still read **that compatible ordinary refreshed entry**,
   *not* that private endpoint access is safe after rollback.
4. Published 0.4.1 is tested with a current redis-py 8.1.0 client only after
   the legacy client rollback has been verified.

**Do not make unqualified rollback claims.** Reinstalling the vulnerable old
distribution can restore unsafe defaults. Production rollback requires
disabling/segregating private caching, carefully controlling namespaces,
service restart and validating the actual application's Redis schema/clients.

## Part B — not completed here

The final 0.5.0 release needs an **exact version-stamped** wheel **and** sdist,
separate clean-site-packages and consumer tests on Python 3.11–3.13, legacy
functional 3.8–3.10, safe redis-py 4 rollback, mounted/tenant-aware key
coverage after #53, provenance hashes, pip checks and current scoped
security acceptance #66. Rerun the published parity contract *after any
change to the default key builder or migration-critical response behavior*.

See [#69](https://github.com/agustin18/fastapi-cache/issues/69)
and [#53](https://github.com/agustin18/fastapi-cache/issues/53).

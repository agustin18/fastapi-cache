# Before and after: migrating one FastAPI app

**Published baseline:** `fastapi-cache2==0.2.2` → `fastapi-cache-stable==0.5.0`.
The same [app.py](app.py), with the same `fastapi_cache` imports and
`@cache` decorators, runs twice in **different disposable environments**.

Run from a checkout on **CPython 3.11 or 3.12** (Windows, macOS or Linux):

```console
python examples/migration/run_demo.py
```

You need Internet access to install the two pinned published distributions
and their pinned FastAPI/Pydantic/httpx comparison environment. The runner
creates two temporary virtual environments, calls `pip check` in each,
executes the app with `python -I` so it cannot accidentally import the
checkout, compares JSON results, and deletes the environments. No server,
Docker, Redis, credentials, or existing database is used.

Expected end of the output:

```text
PASS: unchanged FastAPI imports, ordinary MISS -> HIT, ETag 304
PASS: legacy private-data reuse reproduced with fictional identities
PASS: published 0.5.0 bypasses protected requests by default
NOTE: this is not evidence of safe rollback for authenticated data
Temporary environments deleted; host environment unchanged.
```

## What it demonstrates

| The same endpoint | Legacy 0.2.2 | Published fork 0.5.0 |
|---|---|---|
| Anonymous `/public` | MISS → HIT | MISS → HIT |
| Conditional request with ETag | 304 | 304 |
| `/viewer` with two *fictional* `Authorization` markers | Second request incorrectly receives the first demo viewer | Both requests run independently; no cache status |
| Python import | `from fastapi_cache ...` | **Exactly the same import** |

The viewer example deliberately characterizes a known upstream weakness
**using fake identities only**. Never paste a real token or run this legacy
example against private/production data. This is an InMemory onboarding
demonstration, **not** verification that every consumer or hidden
tenant/role/middleware context is isolated automatically.

## Production migration and rollback are separate gates

For persisted Redis data, custom key builders, private cache namespaces and
rollbacks, use the [migration checklist](../../MIGRATION.md) and the existing
[Redis 7.4 migration/rollback integration workflow](../../.github/workflows/migration-candidate-phase-b.yml).
That evidence exercises a legacy writer, the new reader, selective namespace
cleanup, an independent consumer and a **package** rollback. It does **not**
endorse restoring legacy authenticated response caching.

Do not co-install the two distributions: both own the same `fastapi_cache`
module. This demo does not change PyPI artifacts or introduce new runtime
dependencies. Before a future 0.6.0 launch, re-run the comparison against the
**exact published 0.6.0 artifact** in an independently reviewed release gate;
this 0.5.0 demonstration cannot certify an unreleased version.

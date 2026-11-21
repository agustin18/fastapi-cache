# Before and after: migrating one FastAPI app

**Published baseline:** `fastapi-cache2==0.2.2` → `fastapi-cache-stable==0.5.0`.
The same [app.py](app.py), with the same `fastapi_cache` imports and
`@cache` decorators, runs twice in **different disposable environments**.

Run from a checkout on **CPython 3.11 or 3.12**. The script is **designed for Windows, macOS and Linux**, but automated end-to-end execution has been verified **only on Linux** (Python 3.11 and 3.12); other platforms still need independent smoke tests:

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

## Required 0.6.0 refresh checklist (not yet completed)

This runnable tutorial is **deliberately pinned to already-published 0.5.0**.
Do not rename it to a 0.6.0 verification based on source code or a successful
0.5.0 CI run. When the exact release candidate is built and independently
reviewed, the release owner must:

1. Run the **separate candidate wheel/sdist and Redis migration/rollback
   workflow** at the final source SHA; this published-vs-published demo
   cannot substitute for those release gates.
2. After **0.6.0 is actually published**, update the replacement pin in
   `run_demo.py`, the distribution-version assertion in `app.py`,
   the expected version and explanatory output in `compare.py`, the
   negative-test fixtures in `tests/test_migration_demo_contract.py`,
   this README, and links/version claims in the onboarding docs.
3. Re-run `pip check`, isolated `python -I` execution and the comparison
   against **downloaded, installed 0.6.0 distribution artifacts**.
   Preserve the previous 0.5.0 result as historical evidence, and record
   exact artifact hashes and source SHA in release evidence.
4. Validate the refreshed tutorial on Linux CI for both supported demo
   interpreters; run additional Windows/macOS smoke lanes before claiming
   those platforms have been verified.
5. Keep **two genuine external consumers** as an independent requirement
   under [#88](https://github.com/agustin18/fastapi-cache/issues/88);
   this in-repository tutorial counts as **zero** such consumers.

Release pin updates must not silently replace previously published audit
evidence. Nothing in this checklist authorizes PyPI publication.

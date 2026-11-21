# Migrate from fastapi-cache2

For common GET/JSON endpoints backed by standalone Redis or InMemory, **0.6.0 keeps the `fastapi_cache` import and legacy default key builder**, but it intentionally corrects unsafe caching behavior.

<div class="grid cards" markdown>
-   :material-check-circle-outline: **Likely simple**

    ---

    Anonymous GET/JSON with one lifespan initialization and the standard Redis/InMemory backend.

-   :material-alert-circle-outline: **Needs review**

    ---

    Custom auth, private responses, special coders, existing private Redis data, shared namespaces or multiple `init()` calls.
</div>

## Before you change anything

- [ ] Record your installed `fastapi-cache2` version and Redis client version.
- [ ] Inventory all `@cache` endpoints that depend on tenant, user, locale, headers, permissions, cookies or middleware state.
- [ ] Record namespaces, custom key builders and coders, and every `clear()` call.
- [ ] Back up **application data**, identify affected cache prefixes, and decide how to remove unsafe legacy entries **selectively**.
- [ ] Verify a rollback route that does **not** restore the old authenticated-response caching behavior.

## Install the replacement safely

In a clean environment:

```console
python -m pip uninstall -y fastapi-cache2
python -m pip install "fastapi-cache-stable[redis]==0.6.0"
python -m pip check
python -c "from importlib.metadata import version; print(version('fastapi-cache-stable'))"
```

Update **your application's** dependency declaration/lockfile: uninstalling locally does not stop the old distribution from coming back on a deployment.

!!! warning "Do not co-install"
    Both distributions own `fastapi_cache`. `pip check` cannot detect overwritten module files. Use separate fresh environments for comparisons or rollback tests.

## Keep your normal imports

```python
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache
```

## Intentional behavior changes

| Area | What to check in 0.6.0 |
|---|---|
| Authentication | Authorization/Cookie requests bypass the default cache; do not opt into private caching without complete identity/permission keys |
| Keys | Default builder's ordinary GET/JSON keys stay compatible; generated/factory route handlers are isolated since 0.4.1 |
| Request/headers | Explicit `Request` + default builder bypasses; hidden context is **not** automatically keyed |
| Headers | 0.6.0 offers opt-in `vary_headers` for listed **public** header dimensions |
| `init()` | A second call raises unless deliberately using `force=True`; clean up owned clients at lifespan teardown |
| `clear()` | Per-key/namespace invalidation is narrower and safer; do not expect a global Redis flush |
| Response models | Default JSON decoder preserves legacy dict/list shape; typed restoration is opt-in |
| Redis | Redis-py 4.x stays available; newer versions have Python-dependent requirements |

!!! danger "Hidden identity is not automatically safe"
    Headers like `X-API-Key`, tenant identity in `request.state`, middleware or `ContextVar` may not affect the default key. HTTP `Vary` alone does not partition the internal cache. See [privacy](guides/privacy.md) and [#53 residual](https://github.com/agustin18/fastapi-cache/issues/53).

## See the same app before and after

The [runnable before/after demo](https://github.com/agustin18/fastapi-cache/blob/stable/examples/migration/README.md)
starts the **same FastAPI source** in two disposable virtual environments:
published `fastapi-cache2==0.2.2` and published `fastapi-cache-stable==0.5.0`.
It proves an ordinary MISS/HIT and ETag/304 stay functional, and illustrates
the intentional safer default for fictitious authenticated requests.
It uses InMemory, **not** persisted Redis, and is not proof that arbitrary
private/tenant state or rollback is safe.

## Smoke-test before traffic

1. GET anonymously: **MISS → HIT**; include ETag/304.
2. Test distinct request/locale variants and confirm separate values.
3. Test `Authorization` and `Cookie`: private endpoints should not get a shared cache HIT.
4. Verify cache namespace `clear()`, TTL expiry and custom key builders.
5. Test an application restart / lifespan close without unexpected second-`init()` exceptions.
6. Observe that unrelated Redis data stays intact after selective cache cleanup.

## Rollback: deliberately narrow

The release's isolated legacy rollback proved **ordinary compatible entries**, not that reverting to `fastapi-cache2==0.2.2` is safe for private traffic. The older package lacks the newer default authenticated-cache bypass. If you must roll back, disable unsafe private caching and rotate affected namespaces first, then reinstall the pinned previous distribution in a **fresh environment**.

**More detail:** [Full migration contract](https://github.com/agustin18/fastapi-cache/blob/stable/MIGRATION.md) · [Release-tested wheel/sdist evidence](reference/releases.md)

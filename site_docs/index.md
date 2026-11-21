---
title: FastAPI caching, without the migration headache
description: Install fastapi-cache-stable or move safely from fastapi-cache2.
---

<div class="landing-kicker">FASTAPI-CACHE-STABLE · CURRENT RELEASE 0.5.0</div>

# Response caching that respects your existing FastAPI app.

**Start with a single decorator. Keep your existing `fastapi_cache` imports.** Get tested Redis compatibility, safer HTTP behavior, clear migration paths, and evidence-backed releases.

<div class="landing-actions" markdown>
[Start from scratch](getting-started.md){ .md-button .md-button--primary }
[Migrate from fastapi-cache2](migration.md){ .md-button }
</div>

<div class="grid cards" markdown>

-   :material-rocket-launch-outline: **Build something new**

    ---

    Install a pinned package, run an InMemory example, see real HIT/MISS headers.

    [Installation & first request](getting-started.md)

-   :material-swap-horizontal: **Already using fastapi-cache2?**

    ---

    Keep most imports and decorators; review the intentional privacy changes and clean rollback.

    [Step-by-step migration](migration.md)

-   :material-database-outline: **Choose your backend**

    ---

    InMemory for a single worker, or standalone Redis to share entries across workers.

    [Compare backends](backends.md)

-   :material-shield-check-outline: **Protect private responses**

    ---

    Authenticated requests bypass by default. Header variation is explicit, not automatic tenant isolation.

    [Security boundaries](guides/privacy.md)

</div>

## Install the published version

```console
python -m pip install "fastapi-cache-stable==0.5.0" uvicorn
python -m pip check
```

The package name is **`fastapi-cache-stable`**; imports remain **`fastapi_cache`**. Use `fastapi-cache-stable[redis]==0.5.0` for standalone Redis.

!!! warning "Do not install both packages"
    `fastapi-cache2` and `fastapi-cache-stable` own the same Python package files. `pip check` will **not** detect this collision. Uninstall the old distribution in a clean environment before migrating.

## What ships today?

| Included in published 0.5.0 | Future / not shipped |
|---|---|
| Default-key-compatible GET/JSON caching | Bounded InMemory [merged in unreleased source (#85)](https://github.com/agustin18/fastapi-cache/pull/85), **not in 0.5.0** |
| Standalone Redis and process-local InMemory | Typed cache lifecycle events (#50) |
| Safe default Authorization/Cookie bypass | Arbitrary hidden tenant/context autodetection (#53 residual) |
| Opt-in `vary_headers`, ETag and HTTP 304 | Single-flight and tag-based invalidation |
| Python 3.8–3.13 functional compatibility | Python 3.14 certification |

**Security-maintained target:** server-side CPython **3.11–3.13**. Python 3.8–3.10 are legacy **functional migration** targets, not security-supported runtimes. DynamoDB and Memcached remain experimental.

<div class="landing-rail" markdown>
**Release evidence:** [0.5.0 provenance](reference/releases.md) · **Next work:** [0.6.0 roadmap](roadmap.md) · **Source:** [GitHub](https://github.com/agustin18/fastapi-cache)
</div>

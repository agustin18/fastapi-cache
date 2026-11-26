# C1 application-scoped caching — published in 0.8.0
This implements the accepted D1–D3 design in
[ARCHITECTURE_0.8_RFC.md](ARCHITECTURE_0.8_RFC.md). It merged as
`3ddedba3347f1050f86784d3bad14ad1ce331ca1` and is published in 0.8.0; it is
not available in published 0.7.2. Existing imports and singleton initialization
remain the default.

Use a new CacheHandle(CacheConfig(backend, scope_id="orders-v1")) per lifespan.
Start with await handle.start(app); use @cache(scope="app") on HTTP endpoints;
await handle.aclose() before closing borrowed clients. Explicit handle binding
is tied to that generation; reusable routers should use scope="app".
No automatic parent app, global or task-local fallback in scoped mode.

Only exact built-in InMemory and standalone Redis backend implementations
are qualified for this candidate; all other implementations retain legacy use.
Reserve __fastapi_cache_app_v1__ across all writers on the store or use a
separate store. Unique scope_id per logical app sharing storage is mandatory;
duplicate IDs and direct external writes are not automatically detectable.
App scope does not replace an identity-aware key builder or authorization.
New scoped entries are cold on first opt-in and have distinct physical keys.
Rollback uses the original singleton namespace; no copying or deleting
legacy entries. Persistent scoped entries require explicit planned cleanup.

handle.clear() removes only this scope; namespace="" selects the empty route
group, namespace="orders" selects that exact group, and key= accepts only a
validated full physical key. See the RFC for the SHA-256 formula and vector.
Redis namespace invalidation is non-atomic under concurrent writes.
Shutdown drains admitted operations for up to 30s by default; timeout or
caller cancellation does not close the backend or cancel admitted operations.
Wait for successful drain before releasing a borrowed client. No owned mode,
plain-function scoped caching, new error policy or advanced Redis support.

C1 evidence plan: source CI, exact published 0.7.2 legacy singleton reproduction
on 3.12, and installed wheel matrix on standard CPython
3.8–3.14 with loopback Redis 7.4. The final release, sdist migration,
performance and broader contracts remain separate gates.

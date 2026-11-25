# Troubleshooting

??? question "I see MISS on every request"
    Check whether `FastAPICache.init()` runs once per lifespan, TTL is positive, the request carries `Authorization` or `Cookie`, or your endpoint explicitly declares `Request` with the default builder. Each InMemory instance and each worker has its own store. Dynamic parameters with unstable `repr()` can create a new key on every call.

??? question "My Redis cache returns decoding errors"
    Use `decode_responses=False`, verify the installed Redis client version against the [Python matrix](../reference/compatibility.md) and review any older serialized data or `PickleCoder` trust boundary.

??? question "I installed the fork but imports behave strangely"
    Ensure **exactly one** distribution owns the `fastapi_cache` module:

    ```console
    python -m pip show fastapi-cache2 fastapi-cache-stable
    python -m pip check
    ```

    A clean environment and an updated application lockfile are essential. `pip check` cannot detect the shared import collision.

??? question "My second application startup raises RuntimeError"
    The cache is process-global. Initialize once per lifespan, dispose of clients you own and use `FastAPICache.reset()` at teardown. Avoid `force=True` unless you explicitly intend to replace configuration.

??? question "My response has the wrong tenant or language"
    Treat this as a potential **data isolation issue**, not a performance glitch. Disable caching on the affected endpoint, rotate its namespace after reviewing access, inspect all hidden response dimensions and compare with [privacy guidance](privacy.md). `vary_headers` is never a generic tenant isolation policy.

??? question "Can I clear an entire Redis Cluster?"
    Redis Cluster namespace-wide `clear` is unsupported. Do not assume that standalone Redis prefix scanning applies to Cluster, Sentinel, TLS or managed failover.

??? question "Can I use Python 3.14 or older EOL versions?"
    0.7.2 declares `>=3.8,<3.15`. Python 3.8–3.10 receive functional legacy tests only; the 0.7.2 security-maintained target is server-side 3.11–3.14, including standard CPython 3.14.

For a reproducible problem, open an [issue](https://github.com/agustin18/fastapi-cache/issues) with Python/FastAPI/Redis version, a minimal endpoint, expected versus actual HIT/MISS, and whether credentials or request state influence the output. **Never paste real tokens or user data.**

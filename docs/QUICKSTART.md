# Quickstart — fastapi-cache-stable 0.3.0

Five-minute example of response caching with
[`fastapi-cache-stable`](https://pypi.org/project/fastapi-cache-stable/0.3.0/).
The Python import remains `fastapi_cache`.

## Install

Use **server-side CPython 3.11–3.13** for the current security-supported
environment. Create a clean virtual environment:

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install "fastapi-cache-stable==0.3.0" "uvicorn"
python -m pip check
```

Do not co-install `fastapi-cache2`. Both distributions provide the same
Python module; `pip check` cannot detect that file collision.

## A minimal InMemory example

Save as `app.py`:

```python
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.decorator import cache


@asynccontextmanager
async def lifespan(app: FastAPI):
    FastAPICache.init(InMemoryBackend(), prefix="demo")
    try:
        yield
    finally:
        FastAPICache.reset()


app = FastAPI(lifespan=lifespan)


@app.get("/hello")
@cache(expire=60)
async def hello():
    return {"message": "Hello, cached world!"}
```

Run:

```sh
python -m uvicorn app:app --port 8000
curl -i http://127.0.0.1:8000/hello
curl -i http://127.0.0.1:8000/hello
```

The first response should include `X-FastAPI-Cache: MISS` and the
next identical request within the TTL should show `HIT`.
The decorator order matters: `@app.get` is **above** `@cache`.

**InMemory is per Python process**, not shared between workers; it
has no size cap in 0.3.0. Use Redis standalone when workers must
share cached values.

## Redis standalone

First install the tested Redis client line:

```sh
python -m pip install "fastapi-cache-stable[redis]==0.3.0"
```

Use [the complete Redis lifespan example](../README.md#quick-start)
and a **test Redis instance**. The 0.3.0 compatibility matrix verifies
**redis-py 4.6.0** with **Redis server 7**. Redis client 5/6/7 are
not yet in this package's declared support range; see
[the Redis issue](https://github.com/agustin18/fastapi-cache/issues/47).

## Privacy and migration rules

- Authenticated `Authorization` or `Cookie` requests **bypass** the
  cache by default. To enable authenticated caching, use an explicit
  identity-aware `key_builder` and review tenant/user isolation.
- The default key builder does **not automatically incorporate arbitrary
  request headers**, including values read indirectly from `Request`
  or middleware. A header exposed as a FastAPI function argument may
  already be represented in the key, but do **not** assume that for all
  `Vary`, locale, tenant or custom-auth headers. Use a suitable
  custom key builder, or bypass caching until variation is proven safe.
  See [the header/Vary investigation](https://github.com/agustin18/fastapi-cache/issues/53).
- Do not cache secrets or deserialize untrusted cache bytes with
  `PickleCoder`.
- `FastAPICache.init()` must run once per worker/lifespan;
  `reset()` clears **configuration**, not Redis keys or client
  connections. Close client resources in lifespan teardown.
- Moving from `fastapi-cache2==0.2.2` may require selective cache
  invalidation for legacy private responses. Never install both
  distributions in one environment.
- DynamoDB and Memcached are **experimental** and do not have the
  same invalidation/TTL semantics as Redis or InMemory.

## Continue

- [Migration and rollback](../MIGRATION.md)
- [Precise compatibility matrix](../COMPATIBILITY.md)
- [Security limitations](../SECURITY.md)
- [Changelog](../CHANGELOG.md)
- [Next features and linked work](../ROADMAP.md)

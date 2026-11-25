# RedisBackend · standalone Redis

Use standalone Redis when separate FastAPI workers need to share cache entries. The Redis extra is optional: basic InMemory installs do not require it.

## Install with explicit version pins

```console
python -m pip install "fastapi-cache-stable[redis]==0.7.2" "redis==4.6.0" uvicorn
python -m pip check
```

Redis-py 4.6.0 is an intentionally conservative migration example, **not** the newest supported client for all interpreters.

## Run an example

```python
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from redis import asyncio as redis

from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    client = redis.from_url("redis://localhost:6379/0", decode_responses=False)
    FastAPICache.init(RedisBackend(client), prefix="my-fastapi-app")
    try:
        yield
    finally:
        FastAPICache.reset()
        await client.close()  # redis-py 4.6; newer clients support aclose()


app = FastAPI(lifespan=lifespan)


@app.get("/catalog")
@cache(expire=120, namespace="catalog")
async def catalog():
    return {"products": ["book", "lamp"]}
```

```console
python -m uvicorn app:app --port 8000
curl -i http://127.0.0.1:8000/catalog
curl -i http://127.0.0.1:8000/catalog
```

## Binary values and client compatibility

Keep **`decode_responses=False`**. JSON or PickleCoder values are stored as bytes; automatic text decoding can corrupt binary entries.

| Server-side CPython | redis-py versions allowed in 0.7.2 metadata |
|---|---|
| 3.8 (legacy) | `>=4.2.0rc1,<6.2` |
| 3.9 (legacy) | `>=4.2.0rc1,<7.1` |
| 3.10–3.13 | `>=4.2.0rc1,<8.2` |

Redis server versions and redis-py **client** versions are not interchangeable. The supported profile includes standalone Redis, tested RESP2/RESP3 with relevant clients and verified Redis implementations; **Redis Cluster namespace clear** is unsupported.

## Operate safely

- Set a unique prefix per app/environment and review any shared namespace before deleting entries.
- Do not use `FLUSHDB` to migrate cache entries.
- Define Redis memory and eviction policy independently; the library does not manage total Redis server capacity.
- Protect credentials/connection strings; never include secrets in keys or logging.
- Read [privacy limitations](privacy.md) before caching personalized data.

**References:** [compatibility matrix](../reference/compatibility.md) · [migration](../migration.md).

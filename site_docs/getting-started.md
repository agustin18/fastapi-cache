# Install from scratch

Get from zero to a working FastAPI cache in five minutes. The examples use **published fastapi-cache-stable 0.7.0**.

!!! tip "Which Python?"
    Use server-side **Python 3.11–3.13** for the project's security-supported test profiles. Python 3.8–3.10 work as legacy functional migration bridges; **3.14 is not supported** by 0.7.0.

## 1. Create a virtual environment

=== "Linux / macOS"

    ```console
    python3 -m venv .venv
    source .venv/bin/activate
    python -m pip install "fastapi-cache-stable==0.7.0" uvicorn
    python -m pip check
    ```

=== "Windows PowerShell"

    ```powershell
    py -3 -m venv .venv
    .\.venv\Scripts\Activate.ps1
    python -m pip install "fastapi-cache-stable==0.7.0" uvicorn
    python -m pip check
    ```

!!! danger "Package collision"
    If you already use `fastapi-cache2`, **follow the [migration steps](migration.md)**. Do not install both distributions in the same environment; they provide the same `fastapi_cache` module.

## 2. Create app.py

```python
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.decorator import cache


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    FastAPICache.init(InMemoryBackend(), prefix="my-app")
    try:
        yield
    finally:
        FastAPICache.reset()


app = FastAPI(lifespan=lifespan)


@app.get("/hello")
@cache(expire=60)
async def hello():
    return {"message": "Hello from the cache!"}
```

The order is important: `@app.get` belongs **above** `@cache`.

## 3. Run the server

```console
python -m uvicorn app:app --port 8000
```

In a second terminal:

```console
curl -i http://127.0.0.1:8000/hello
curl -i http://127.0.0.1:8000/hello
```

The first response has `X-FastAPI-Cache: MISS`; the second identical request within 60 seconds has **`HIT`**. Add `If-None-Match` using the ETag value to test a conditional 304.

## 4. Choose where data lives

| Situation | Use |
|---|---|
| Local development / one process | [InMemoryBackend](guides/inmemory.md) |
| Several workers / processes | [RedisBackend](guides/redis.md) |
| DynamoDB or Memcached | Experimental: read [compatibility](reference/compatibility.md) first |

Published 0.7.0 InMemory keeps the historical unbounded default and accepts an optional `max_entries` constructor argument. See the [InMemory guide](guides/inmemory.md); pass `max_entries` only with the 0.7.0 install command above.

## 5. Before production

Review [private-response safety](guides/privacy.md), [compatibility](reference/compatibility.md), and use the exact released package version in your application lockfile. `FastAPICache.reset()` resets the configuration, **not** backend data or Redis connections.

**Next:** [Configure Redis](guides/redis.md) · [Features](reference/features.md)

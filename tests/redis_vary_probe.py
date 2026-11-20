"""Black-box opt-in Vary contract using a clean installed wheel and real Redis.

This is intentionally NOT executed by published 0.4.1 parity tests. The new API
exists only in the candidate branch; the published migration goldens stay frozen.
Do not flushdb or change another application's keys.
"""

import os
from contextlib import asynccontextmanager
from contextvars import ContextVar
from importlib.metadata import version
from pathlib import Path
from secrets import token_hex
from typing import Any, AsyncIterator, Dict

from fastapi import Depends, FastAPI, Response
from fastapi.testclient import TestClient
from redis import Redis as SyncRedis
from redis.asyncio import Redis
from starlette.requests import Request

import fastapi_cache
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache



async def close(client: Redis) -> None:
    aclose = getattr(client, "aclose", None)
    if aclose is not None:
        await aclose()
    else:
        await client.close()


def main() -> None:
    assert version("fastapi-cache-stable") == fastapi_cache.__version__
    location = Path(fastapi_cache.__file__).resolve()
    assert "site-packages" in location.parts, location
    url = os.environ["REDIS_URL"]
    prefix = "vary-probe-" + token_hex(8)
    tenant: ContextVar[str] = ContextVar("redis-vary-tenant", default="")
    calls = {"n": 0}

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        redis = Redis.from_url(url)
        FastAPICache.init(RedisBackend(redis), prefix=prefix)
        try:
            yield
        finally:
            FastAPICache.reset()
            await close(redis)

    app = FastAPI(lifespan=lifespan)

    async def set_tenant(request: Request) -> None:
        tenant.set(request.headers.get("X-Tenant", ""))

    @app.get("/vary", dependencies=[Depends(set_tenant)])
    @cache(expire=60, namespace="tenant", vary_headers=("x-tenant",))
    async def variant(response: Response) -> Dict[str, Any]:
        calls["n"] += 1
        response.headers["Vary"] = "X-Tenant"
        return {"tenant": tenant.get(), "call": calls["n"]}

    @app.post("/clear")
    async def clear() -> Dict[str, int]:
        return {"count": await FastAPICache.clear(namespace="tenant")}

    # The Redis-py sync client uses a separate connection just for verification.
    # Restrict cleanup to this isolated, newly generated prefix only.
    redis_sync = SyncRedis.from_url(url)
    try:
        with TestClient(app) as client:
            alpha = client.get("/vary", headers={"X-Tenant": "alpha"})
            beta = client.get("/vary", headers={"X-Tenant": "beta"})
            again = client.get("/vary", headers={"X-Tenant": "alpha"})
            conditional = client.get(
                "/vary",
                headers={"X-Tenant": "alpha", "If-None-Match": alpha.headers["etag"]},
            )
            private = client.get(
                "/vary", headers={"X-Tenant": "alpha", "Authorization": "Bearer test"}
            )
            assert [r.headers["X-FastAPI-Cache"] for r in
                    (alpha, beta, again, conditional)] == [
                "MISS", "MISS", "HIT", "HIT"
            ]
            assert alpha.json() == again.json() == {"tenant": "alpha", "call": 1}
            assert beta.json() == {"tenant": "beta", "call": 2}
            assert conditional.status_code == 304 and not conditional.content
            assert all(r.headers["vary"].lower() == "x-tenant"
                       for r in (alpha, beta, again, conditional))
            assert "X-FastAPI-Cache" not in private.headers
            assert calls["n"] == 3

            keys = list(redis_sync.scan_iter(match=prefix + ":tenant:*"))
            assert len(keys) == 2, keys
            assert all(k.decode().startswith(prefix + ":tenant:vary-v1:") for k in keys)
            assert all(b"alpha" not in k and b"beta" not in k for k in keys)
            response = client.post("/clear")
            assert response.status_code == 200
            assert response.json() == {"count": 2}
            assert not list(redis_sync.scan_iter(match=prefix + ":tenant:*"))
    finally:
        # No FLUSHDB; cleanup only our unique prefix in case an assertion failed.
        for key in redis_sync.scan_iter(match=prefix + ":*"):
            redis_sync.delete(key)
        redis_sync.close()
    print("Installed Redis Vary consumer PASS:", location)


if __name__ == "__main__":
    main()

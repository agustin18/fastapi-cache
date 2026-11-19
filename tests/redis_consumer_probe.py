"""Black-box FastAPI consumer of an installed research wheel, not the checkout.

Execute only inside isolated CI Redis containers and a venv without editable installs.
The application models ordinary caching, authenticated tenant isolation, clear, and
rollback-style reinitialization. It does NOT replace an independent real consumer.
"""

import asyncio
import hashlib
import os
from contextlib import asynccontextmanager
from importlib.metadata import version
from pathlib import Path
from typing import Any, AsyncIterator, Dict, Optional, Tuple

from fastapi import FastAPI, Request, Response
from fastapi.testclient import TestClient
from redis.asyncio import Redis

import fastapi_cache
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache
from fastapi_cache.key_builder import default_key_builder


def tenant_key(
    func: Any,
    namespace: str = "",
    *,
    request: Optional[Request] = None,
    response: Optional[Response] = None,
    args: Tuple[Any, ...],
    kwargs: Dict[str, Any],
) -> str:
    assert request is not None
    identity = request.headers.get("authorization", "")
    tenant = request.headers.get("x-tenant", "")
    identity_digest = hashlib.sha256(
        (str(len(identity)) + ":" + identity + "|" + tenant).encode()
    ).hexdigest()
    base = default_key_builder(
        func, namespace, request=request, response=response,
        args=args, kwargs=kwargs
    )
    return base + ":principal:" + identity_digest


async def close(client: Any) -> None:
    aclose = getattr(client, "aclose", None)
    if aclose is not None:
        await aclose()
    else:
        await client.close()


async def remove_previous_data() -> None:
    client = Redis.from_url(os.environ["REDIS_URL"])
    try:
        await client.flushdb()
    finally:
        await close(client)


def main() -> None:
    module_path = Path(fastapi_cache.__file__).resolve()
    assert "site-packages" in module_path.parts, module_path
    assert version("fastapi-cache-stable") == "0.3.1"

    url = os.environ["REDIS_URL"]
    ordinary_calls = {"count": 0}
    tenant_calls = {"count": 0}

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        client = Redis.from_url(url, decode_responses=False)
        try:
            FastAPICache.init(RedisBackend(client), prefix="consumer-matrix")
            yield
        finally:
            FastAPICache.reset()
            await close(client)

    app = FastAPI(lifespan=lifespan)

    @app.get("/listing")
    @cache(namespace="listing", expire=90)
    async def listing(response: Response) -> Dict[str, int]:
        ordinary_calls["count"] += 1
        return {"run": ordinary_calls["count"]}

    @app.get("/tenant")
    @cache(namespace="tenant", key_builder=tenant_key, cache_authenticated=True, expire=90)
    async def tenant(request: Request, response: Response) -> Dict[str, str]:
        tenant_calls["count"] += 1
        return {
            "tenant": request.headers.get("x-tenant", ""),
            "principal": request.headers.get("authorization", ""),
        }

    @app.get("/unsafe-default")
    @cache(namespace="unsafe-default", expire=90)
    async def unsafe_default(request: Request, response: Response) -> Dict[str, str]:
        return {"tenant": request.headers.get("x-tenant", "")}

    @app.post("/clear")
    async def clear() -> Dict[str, int]:
        return {"count": await FastAPICache.clear(namespace="tenant")}

    asyncio.run(remove_previous_data())
    try:
        with TestClient(app) as client:
            first = client.get("/listing")
            second = client.get("/listing")
            assert first.headers.get("X-FastAPI-Cache") == "MISS"
            assert second.headers.get("X-FastAPI-Cache") == "HIT"
            assert first.json() == second.json() == {"run": 1}

            alice = {"Authorization": "Bearer alice", "X-Tenant": "A"}
            bob = {"Authorization": "Bearer bob", "X-Tenant": "B"}
            a1 = client.get("/tenant", headers=alice)
            b1 = client.get("/tenant", headers=bob)
            a2 = client.get("/tenant", headers=alice)
            assert [a1.headers.get("X-FastAPI-Cache"), b1.headers.get("X-FastAPI-Cache"),
                    a2.headers.get("X-FastAPI-Cache")] == ["MISS", "MISS", "HIT"]
            assert a1.json()["tenant"] == a2.json()["tenant"] == "A"
            assert b1.json()["tenant"] == "B"
            assert tenant_calls["count"] == 2

            unsafe_a = client.get("/unsafe-default", headers={"X-Tenant": "A"})
            unsafe_b = client.get("/unsafe-default", headers={"X-Tenant": "B"})
            assert unsafe_a.json()["tenant"] == "A"
            assert unsafe_b.json()["tenant"] == "B"
            assert "X-FastAPI-Cache" not in unsafe_b.headers

            cleared = client.post("/clear")
            assert cleared.status_code == 200 and cleared.json()["count"] == 2
            assert client.get("/tenant", headers=alice).headers["X-FastAPI-Cache"] == "MISS"

        # Simulate a clean app restart using the same persisted Redis data.
        with TestClient(app) as restarted:
            assert restarted.get("/listing").headers["X-FastAPI-Cache"] == "HIT"
            assert ordinary_calls["count"] == 1
    finally:
        asyncio.run(remove_previous_data())
    print("Isolated wheel consumer PASS", module_path)


if __name__ == "__main__":
    main()

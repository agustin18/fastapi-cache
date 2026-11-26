"""Characterize the known legacy singleton limitation using synthetic values.

This also runs against the installed published 0.7.2 wheel in C1 CI.
The opt-in fix must not silently change legacy routing.
"""

import asyncio
from typing import Any

import httpx
from fastapi import FastAPI

from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.decorator import cache


def test_legacy_singleton_is_not_app_isolation() -> None:
    async def verify() -> None:
        a, b = FastAPI(), FastAPI()

        def same_key(*args: Any, **kwargs: Any) -> str:
            return "synthetic:legacy-shared-key"

        @a.get("/value")
        @cache(key_builder=same_key, expire=60)
        async def first() -> str:
            return "synthetic-a"

        @b.get("/value")
        @cache(key_builder=same_key, expire=60)
        async def second() -> str:
            return "synthetic-b"

        FastAPICache.reset()
        FastAPICache.init(InMemoryBackend(), prefix="first")
        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=a),
                                         base_url="http://app.test") as ca, httpx.AsyncClient(
                transport=httpx.ASGITransport(app=b), base_url="http://app.test"
            ) as cb:
                assert (await ca.get("/value")).json() == "synthetic-a"
                FastAPICache.init(InMemoryBackend(), prefix="second", force=True)
                assert (await cb.get("/value")).json() == "synthetic-b"
                replay = await ca.get("/value")
                assert replay.headers["X-FastAPI-Cache"] == "HIT"
                assert replay.json() == "synthetic-b"
        finally:
            FastAPICache.reset()

    asyncio.run(verify())

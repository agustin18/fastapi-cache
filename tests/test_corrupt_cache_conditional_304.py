"""Bad cache bytes must not satisfy a conditional HTTP validator (#112)."""

import hashlib
from typing import Dict, Optional, Tuple

import pydantic
import pytest
from fastapi import FastAPI
from httpx import Response
from starlette.testclient import TestClient

from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.coder import JsonCoder, TypedJsonCoder
from fastapi_cache.decorator import cache


class FixedEntryBackend(InMemoryBackend):
    """Return synthetic cached bytes regardless of generated key."""

    def __init__(self, entry: bytes) -> None:
        super().__init__()
        self.entry = entry

    async def get_with_ttl(self, key: str) -> Tuple[int, Optional[bytes]]:
        return (60, self.entry)


def conditional_request(entry: bytes, *, conditional: bool) -> Response:
    FastAPICache.reset()
    FastAPICache.init(FixedEntryBackend(entry), prefix="test-corrupt")
    app = FastAPI()

    @app.get("/cached")
    @cache(expire=60)
    async def cached() -> Dict[str, str]:
        raise AssertionError("A non-missing cached value must not recompute")

    headers = {}
    if conditional:
        headers["If-None-Match"] = f'W/"{hashlib.sha256(entry).hexdigest()}"'
    try:
        with TestClient(app, raise_server_exceptions=False) as client:
            return client.get("/cached", headers=headers)
    finally:
        FastAPICache.reset()


def test_corrupt_bytes_do_not_return_304_before_json_decode() -> None:
    response = conditional_request(b"not-valid-json", conditional=True)
    assert response.status_code == 500


def test_corrupt_bytes_without_validator_also_fail_closed() -> None:
    response = conditional_request(b"\xff", conditional=False)
    assert response.status_code == 500


def test_valid_cached_bytes_keep_conditional_304_contract() -> None:
    valid = JsonCoder.encode({"message": "cached"})
    response = conditional_request(valid, conditional=True)
    assert response.status_code == 304
    assert response.headers["X-FastAPI-Cache"] == "HIT"
    assert response.content == b""


@pytest.mark.skipif(
    not pydantic.VERSION.startswith("2."), reason="Pydantic v2 typed validation"
)
def test_typed_decode_validation_runs_before_conditional_304() -> None:
    """Malformed but syntactically valid JSON cannot bypass typed validation."""
    class Payload(pydantic.BaseModel):
        count: int

    entry = b'{"count":"not-an-integer"}'
    FastAPICache.reset()
    FastAPICache.init(FixedEntryBackend(entry), prefix="test-corrupt-typed")
    app = FastAPI()

    @app.get("/typed")
    @cache(expire=60, coder=TypedJsonCoder)
    async def typed() -> Payload:
        raise AssertionError("Unexpected recomputation on malformed HIT")

    validator = f'W/"{hashlib.sha256(entry).hexdigest()}"'
    try:
        with TestClient(app, raise_server_exceptions=False) as client:
            result = client.get("/typed", headers={"If-None-Match": validator})
            assert result.status_code == 500
            assert result.status_code != 304
    finally:
        FastAPICache.reset()

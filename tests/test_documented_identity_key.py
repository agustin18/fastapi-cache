"""Execute the actual documentation example against synthetic identities."""

from pathlib import Path
from typing import Any

import pytest
from starlette.exceptions import HTTPException
from starlette.requests import Request

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(params=["README.md", "MIGRATION.md"])
def builder(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch) -> Any:
    monkeypatch.setenv("CACHE_KEY_SECRET", "synthetic-key-for-tests")
    content = (ROOT / request.param).read_text(encoding="utf-8")
    snippet = next(
        block for block in content.split("```python\n")
        if "def identity_key_builder(" in block.split("```", 1)[0]
    ).split("```", 1)[0]
    namespace: dict = {}
    exec(compile(snippet, request.param, "exec"), namespace)  # noqa: S102
    return namespace["identity_key_builder"]


def endpoint() -> None:
    pass


def synthetic_request(identity: Any, query: bytes = b"") -> Request:
    return Request({
        "type": "http", "scheme": "http", "method": "GET", "path": "/me",
        "root_path": "", "query_string": query, "headers": [],
        "server": ("example.test", 80),
        "state": {"verified_cache_identity": identity},
    })


def test_documented_key_distinguishes_structured_identity(builder: Any) -> None:
    a = synthetic_request(("a|b", "c", "session", "permissions", "representation"))
    b = synthetic_request(("a", "b|c", "session", "permissions", "representation"))
    c = synthetic_request(("a|b", "c", "session", "changed", "representation"))
    keys = [
        builder(endpoint, "private", request=req, args=(), kwargs={})
        for req in (a, b, c)
    ]
    assert len(set(keys)) == 3
    assert builder(endpoint, "private", request=a, args=(), kwargs={}) == keys[0]


@pytest.mark.parametrize("identity", [None, ("only",), ("a", "b", "c", "", "e")])
def test_documented_key_rejects_missing_verified_identity(builder: Any, identity: Any) -> None:
    with pytest.raises(HTTPException) as exc:
        builder(endpoint, "private", request=synthetic_request(identity), args=(), kwargs={})
    assert exc.value.status_code == 403


def test_documented_key_rejects_unsupported_context(builder: Any) -> None:
    req = synthetic_request(("a", "b", "c", "d", "e"), b"filter=private")
    with pytest.raises(HTTPException) as exc:
        builder(endpoint, "private", request=req, args=(), kwargs={})
    assert exc.value.status_code == 400

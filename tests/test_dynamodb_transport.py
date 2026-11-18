import asyncio
import importlib
import importlib.util
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from typing import Any, Dict, cast

import pytest

dynamodb_module: Any = None
if importlib.util.find_spec("aiobotocore") is not None:
    dynamodb_module = importlib.import_module("fastapi_cache.backends.dynamodb")


class LocalDynamoDBServer(ThreadingHTTPServer):
    def __init__(self) -> None:
        super().__init__(("127.0.0.1", 0), LocalDynamoDBHandler)
        self.items: Dict[str, Dict[str, Any]] = {}


class LocalDynamoDBHandler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        server = cast(LocalDynamoDBServer, self.server)
        request_body = self.rfile.read(int(self.headers["Content-Length"]))
        request = json.loads(request_body)
        operation = self.headers["X-Amz-Target"].rsplit(".", 1)[-1]

        if operation == "PutItem":
            item = request["Item"]
            server.items[item["key"]["S"]] = item
            response: Dict[str, Any] = {}
        elif operation == "GetItem":
            key = request["Key"]["key"]["S"]
            item = server.items.get(key)
            response = {"Item": item} if item is not None else {}
        else:
            self.send_error(400, "Unsupported DynamoDB operation")
            return

        payload = json.dumps(response).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/x-amz-json-1.0")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("x-amzn-RequestId", "local-dynamodb-smoke")
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format: str, *args: Any) -> None:
        pass


def test_dynamodb_backend_round_trips_over_local_http_transport(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if dynamodb_module is None:
        pytest.skip("aiobotocore is not installed")
    backend_type = dynamodb_module.DynamoBackend
    if backend_type is None:
        pytest.skip("aiobotocore is not installed")

    server = LocalDynamoDBServer()
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    endpoint_url = f"http://127.0.0.1:{server.server_port}"
    session = dynamodb_module.get_session()

    class EndpointSession:
        def create_client(self, service_name: str, **kwargs: Any) -> Any:
            return session.create_client(
                service_name,
                endpoint_url=endpoint_url,
                aws_access_key_id="local-test-access-key",
                # S106: fixed dummy credential for the loopback server only.
                aws_secret_access_key="local-test-secret-key",  # noqa: S106
                **kwargs,
            )

    monkeypatch.setattr(
        dynamodb_module, "get_session", lambda: EndpointSession()
    )
    backend = backend_type(table_name="cache", region="us-east-1")

    async def round_trip() -> None:
        await backend.init()
        try:
            await backend.set("app:key", b"cached-value")
            assert await backend.get("app:key") == b"cached-value"
            ttl, value = await backend.get_with_ttl("app:key")
            assert ttl == -1
            assert value == b"cached-value"
        finally:
            await backend.close()

    try:
        asyncio.run(round_trip())
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

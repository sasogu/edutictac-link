"""Tests d'integració del servidor WebSocket (sense maquinari)."""

from __future__ import annotations

import asyncio
import json
from typing import Any, Callable

import pytest
import websockets
from websockets.exceptions import ConnectionClosed

from edutictac_link.bluetooth.fake_backend import FakeBackend
from edutictac_link.config import Config
from edutictac_link.server import LinkServer
from tests.conftest import make_microbit


async def _recv_until(
    ws: Any, predicate: Callable[[dict[str, Any]], bool], timeout: float = 3.0
) -> dict[str, Any]:
    async def _inner() -> dict[str, Any]:
        while True:
            message = json.loads(await ws.recv())
            if predicate(message):
                return message

    return await asyncio.wait_for(_inner(), timeout)


async def test_server_getversion_discover_and_write():
    peripheral = make_microbit()
    backend = FakeBackend(peripherals=[peripheral])
    config = Config(host="127.0.0.1", port=0, scan_seconds=0.1)
    server = LinkServer(config, backend_factory=lambda: backend)

    async with websockets.serve(server.handler, "127.0.0.1", 0) as ws_server:
        port = ws_server.sockets[0].getsockname()[1]
        uri = f"ws://127.0.0.1:{port}/scratch/ble"
        async with websockets.connect(
            uri, additional_headers={"Origin": "https://scratch.mit.edu"}
        ) as ws:
            await ws.send(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "getVersion"}))
            response = await _recv_until(ws, lambda m: m.get("id") == 1)
            assert response["result"]["protocol"] == "1.3"

            await ws.send(
                json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "id": 2,
                        "method": "discover",
                        "params": {"filters": [{"services": [0xF005]}]},
                    }
                )
            )
            response = await _recv_until(ws, lambda m: m.get("id") == 2)
            assert response["result"] is None

            note = await _recv_until(
                ws, lambda m: m.get("method") == "didDiscoverPeripheral"
            )
            assert note["params"]["name"] == "BBC micro:bit"


async def test_server_rejects_unknown_path():
    config = Config(host="127.0.0.1", port=0)
    server = LinkServer(config, backend_factory=FakeBackend)

    async with websockets.serve(server.handler, "127.0.0.1", 0) as ws_server:
        port = ws_server.sockets[0].getsockname()[1]
        uri = f"ws://127.0.0.1:{port}/wrong/path"
        with pytest.raises(ConnectionClosed):
            async with websockets.connect(uri) as ws:
                await ws.recv()


async def test_server_rejects_unknown_origin():
    config = Config(host="127.0.0.1", port=0)
    server = LinkServer(config, backend_factory=FakeBackend)

    async with websockets.serve(server.handler, "127.0.0.1", 0) as ws_server:
        port = ws_server.sockets[0].getsockname()[1]
        uri = f"ws://127.0.0.1:{port}/scratch/ble"
        with pytest.raises(ConnectionClosed):
            async with websockets.connect(
                uri, additional_headers={"Origin": "https://evil.example"}
            ) as ws:
                await ws.recv()

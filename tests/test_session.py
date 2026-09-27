"""Tests de la màquina d'estats de sessió amb un backend BLE fals."""

from __future__ import annotations

import asyncio
import base64
import json
from typing import Any

from edutictac_link.bluetooth.fake_backend import FakeBackend, FakeConnection
from edutictac_link.protocol.errors import DEVICE_ERROR, INVALID_REQUEST
from edutictac_link.protocol.session import Session, TransportClosed
from tests.conftest import MICROBIT_RX, MICROBIT_TX, make_microbit


class FakeTransport:
    def __init__(self) -> None:
        self.incoming: asyncio.Queue[str | None] = asyncio.Queue()
        self.sent: list[dict[str, Any]] = []

    async def recv(self) -> str:
        item = await self.incoming.get()
        if item is None:
            raise TransportClosed()
        return item

    async def send(self, message: str) -> None:
        self.sent.append(json.loads(message))

    async def close(self) -> None:  # pragma: no cover - no s'usa als tests
        pass

    def push(self, obj: dict[str, Any]) -> None:
        self.incoming.put_nowait(json.dumps(obj))

    def finish(self) -> None:
        self.incoming.put_nowait(None)


def _request(transport: FakeTransport, message_id: int, method: str, params: Any = None) -> None:
    message: dict[str, Any] = {"jsonrpc": "2.0", "id": message_id, "method": method}
    if params is not None:
        message["params"] = params
    transport.push(message)


def _find(
    transport: FakeTransport, *, message_id: int | None = None, method: str | None = None
) -> dict[str, Any] | None:
    for message in transport.sent:
        if message_id is not None and message.get("id") != message_id:
            continue
        if method is not None and message.get("method") != method:
            continue
        return message
    return None


async def _wait_for(predicate, timeout: float = 2.0) -> None:
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout
    while loop.time() < deadline:
        if predicate():
            return
        await asyncio.sleep(0.005)
    raise AssertionError("no s'ha complit la condició a temps")


async def test_getversion_and_ping():
    transport = FakeTransport()
    session = Session(transport, FakeBackend())
    task = asyncio.create_task(session.run())

    _request(transport, 1, "getVersion")
    await _wait_for(lambda: _find(transport, message_id=1) is not None)
    assert _find(transport, message_id=1)["result"]["protocol"] == "1.3"

    _request(transport, 2, "ping")
    await _wait_for(lambda: _find(transport, message_id=2) is not None)
    assert _find(transport, message_id=2)["result"] == 42

    transport.finish()
    await task


async def test_discover_connect_write_and_notify():
    peripheral = make_microbit()
    connection = FakeConnection()
    backend = FakeBackend(peripherals=[peripheral], connection=connection)
    transport = FakeTransport()
    session = Session(transport, backend, scan_seconds=0.1)
    task = asyncio.create_task(session.run())

    _request(transport, 1, "discover", {"filters": [{"services": [0xF005]}]})
    await _wait_for(lambda: _find(transport, message_id=1) is not None)
    assert _find(transport, message_id=1)["result"] is None

    await _wait_for(lambda: _find(transport, method="didDiscoverPeripheral") is not None)
    note = _find(transport, method="didDiscoverPeripheral")
    peripheral_id = note["params"]["peripheralId"]
    assert note["params"]["name"] == "BBC micro:bit"

    _request(transport, 2, "connect", {"peripheralId": peripheral_id})
    await _wait_for(lambda: _find(transport, message_id=2) is not None)
    assert _find(transport, message_id=2)["result"] is None
    assert backend.connected_peripheral is peripheral

    payload = base64.b64encode(b"\x80").decode("ascii")
    _request(
        transport,
        3,
        "write",
        {
            "serviceId": 0xF005,
            "characteristicId": MICROBIT_TX,
            "message": payload,
            "encoding": "base64",
            "withResponse": True,
        },
    )
    await _wait_for(lambda: _find(transport, message_id=3) is not None)
    assert _find(transport, message_id=3)["result"] == 1
    assert connection.writes[-1][2] == b"\x80"

    _request(
        transport,
        4,
        "startNotifications",
        {"serviceId": 0xF005, "characteristicId": MICROBIT_RX},
    )
    await _wait_for(lambda: _find(transport, message_id=4) is not None)

    connection.emit(MICROBIT_RX, b"\x01\x02")
    await _wait_for(
        lambda: _find(transport, method="characteristicDidChange") is not None
    )
    changed = _find(transport, method="characteristicDidChange")["params"]
    assert changed["message"] == base64.b64encode(b"\x01\x02").decode("ascii")
    assert changed["encoding"] == "base64"

    transport.finish()
    await task


async def test_no_notification_when_filter_does_not_match():
    backend = FakeBackend(peripherals=[make_microbit()])
    transport = FakeTransport()
    session = Session(transport, backend, scan_seconds=0.1)
    task = asyncio.create_task(session.run())

    _request(transport, 1, "discover", {"filters": [{"services": [0x1815]}]})
    await _wait_for(lambda: _find(transport, message_id=1) is not None)
    await asyncio.sleep(0.1)
    assert _find(transport, method="didDiscoverPeripheral") is None

    transport.finish()
    await task


async def test_service_not_allowed_is_rejected():
    backend = FakeBackend(peripherals=[make_microbit()])
    transport = FakeTransport()
    session = Session(transport, backend, scan_seconds=0.1)
    task = asyncio.create_task(session.run())

    _request(transport, 1, "discover", {"filters": [{"services": [0xF005]}]})
    await _wait_for(lambda: _find(transport, message_id=1) is not None)
    _request(transport, 2, "connect", {"peripheralId": 0})
    await _wait_for(lambda: _find(transport, message_id=2) is not None)

    _request(
        transport,
        3,
        "read",
        {"serviceId": 0x1815, "characteristicId": "00002a19-0000-1000-8000-00805f9b34fb"},
    )
    await _wait_for(lambda: _find(transport, message_id=3) is not None)
    assert _find(transport, message_id=3)["error"]["code"] == DEVICE_ERROR

    transport.finish()
    await task


async def test_connect_before_discover_is_rejected():
    transport = FakeTransport()
    session = Session(transport, FakeBackend())
    task = asyncio.create_task(session.run())

    _request(transport, 1, "connect", {"peripheralId": 0})
    await _wait_for(lambda: _find(transport, message_id=1) is not None)
    assert _find(transport, message_id=1)["error"]["code"] == INVALID_REQUEST

    transport.finish()
    await task


async def test_discover_requires_filter():
    transport = FakeTransport()
    session = Session(transport, FakeBackend())
    task = asyncio.create_task(session.run())

    _request(transport, 1, "discover", {"filters": []})
    await _wait_for(lambda: _find(transport, message_id=1) is not None)
    assert "error" in _find(transport, message_id=1)

    transport.finish()
    await task


async def test_connect_error_is_reported():
    class FailingBackend(FakeBackend):
        async def connect(self, peripheral):
            raise RuntimeError("adaptador ocupat")

    backend = FailingBackend(peripherals=[make_microbit()])
    transport = FakeTransport()
    session = Session(transport, backend, scan_seconds=0.1)
    task = asyncio.create_task(session.run())

    _request(transport, 1, "discover", {"filters": [{"services": [0xF005]}]})
    await _wait_for(lambda: _find(transport, message_id=1) is not None)
    _request(transport, 2, "connect", {"peripheralId": 0})
    await _wait_for(lambda: _find(transport, message_id=2) is not None)
    assert _find(transport, message_id=2)["error"]["code"] == DEVICE_ERROR

    transport.finish()
    await task

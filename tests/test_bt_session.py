"""Tests de la sessió Bluetooth Classic (EV3) amb un backend fals."""

from __future__ import annotations

import asyncio
import base64
import json
from typing import Any

from edutictac_link.bluetooth.fake_bt_backend import FakeBtBackend, FakeBtConnection
from edutictac_link.protocol.bt_session import BtSession
from edutictac_link.protocol.errors import DEVICE_ERROR, INVALID_PARAMS
from edutictac_link.protocol.session import TransportClosed
from tests.conftest import make_peripheral

EV3 = make_peripheral(peripheral_id="11:22:33:44:55:66", name="EV3", services=())


class FakeTransport:
    def __init__(self) -> None:
        self.incoming: asyncio.Queue[str | None] = asyncio.Queue()
        self.sent: list[dict[str, Any]] = []
        self.closed = False

    async def recv(self) -> str:
        item = await self.incoming.get()
        if item is None:
            raise TransportClosed()
        return item

    async def send(self, message: str) -> None:
        self.sent.append(json.loads(message))

    async def close(self) -> None:
        self.closed = True
        self.incoming.put_nowait(None)

    def push(self, obj: dict[str, Any]) -> None:
        self.incoming.put_nowait(json.dumps(obj))

    def finish(self) -> None:
        self.incoming.put_nowait(None)


def _request(transport: FakeTransport, message_id: int, method: str, params: Any = None) -> None:
    message: dict[str, Any] = {"jsonrpc": "2.0", "id": message_id, "method": method}
    if params is not None:
        message["params"] = params
    transport.push(message)


def _find(transport: FakeTransport, *, message_id: int | None = None, method: str | None = None):
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


async def test_bt_discover_connect_send_and_receive():
    connection = FakeBtConnection()
    backend = FakeBtBackend(peripherals=[EV3], connection=connection)
    transport = FakeTransport()
    session = BtSession(transport, backend, scan_seconds=0.1)
    task = asyncio.create_task(session.run())

    _request(
        transport,
        1,
        "discover",
        {"majorDeviceClass": 8, "minorDeviceClass": 1},
    )
    await _wait_for(lambda: _find(transport, message_id=1) is not None)
    assert _find(transport, message_id=1)["result"] is None
    assert backend.discover_calls[0][:2] == (8, 1)

    await _wait_for(lambda: _find(transport, method="didDiscoverPeripheral") is not None)
    note = _find(transport, method="didDiscoverPeripheral")
    assert note["params"]["name"] == "EV3"
    peripheral_id = note["params"]["peripheralId"]

    _request(transport, 2, "connect", {"peripheralId": peripheral_id, "pin": "1234"})
    await _wait_for(lambda: _find(transport, message_id=2) is not None)
    assert _find(transport, message_id=2)["result"] is None
    assert backend.pin == "1234"

    payload = base64.b64encode(b"\x00\x01\x02").decode("ascii")
    _request(
        transport,
        3,
        "send",
        {"message": payload, "encoding": "base64"},
    )
    await _wait_for(lambda: _find(transport, message_id=3) is not None)
    assert _find(transport, message_id=3)["result"] == 3
    assert connection.sent[-1] == b"\x00\x01\x02"

    connection.emit(b"\x99")
    await _wait_for(lambda: _find(transport, method="didReceiveMessage") is not None)
    received = _find(transport, method="didReceiveMessage")["params"]
    assert received["message"] == base64.b64encode(b"\x99").decode("ascii")

    transport.finish()
    await task


async def test_bt_discover_requires_class():
    transport = FakeTransport()
    session = BtSession(transport, FakeBtBackend())
    task = asyncio.create_task(session.run())

    _request(transport, 1, "discover", {})
    await _wait_for(lambda: _find(transport, message_id=1) is not None)
    assert _find(transport, message_id=1)["error"]["code"] == INVALID_PARAMS

    transport.finish()
    await task


async def test_bt_send_error_is_reported():
    connection = FakeBtConnection(send_error=RuntimeError("socket trencat"))
    backend = FakeBtBackend(peripherals=[EV3], connection=connection)
    transport = FakeTransport()
    session = BtSession(transport, backend, scan_seconds=0.1)
    task = asyncio.create_task(session.run())

    _request(transport, 1, "discover", {"majorDeviceClass": 8})
    await _wait_for(lambda: _find(transport, message_id=1) is not None)
    _request(transport, 2, "connect", {"peripheralId": 0})
    await _wait_for(lambda: _find(transport, message_id=2) is not None)

    _request(transport, 3, "send", {"message": "AQ==", "encoding": "base64"})
    await _wait_for(lambda: _find(transport, message_id=3) is not None)
    assert _find(transport, message_id=3)["error"]["code"] == DEVICE_ERROR

    transport.finish()
    await task


async def test_bt_unexpected_disconnect_closes_session():
    connection = FakeBtConnection()
    backend = FakeBtBackend(peripherals=[EV3], connection=connection)
    transport = FakeTransport()
    session = BtSession(transport, backend, scan_seconds=0.1)
    task = asyncio.create_task(session.run())

    _request(transport, 1, "discover", {"majorDeviceClass": 8})
    await _wait_for(lambda: _find(transport, message_id=1) is not None)
    _request(transport, 2, "connect", {"peripheralId": 0})
    await _wait_for(lambda: _find(transport, message_id=2) is not None)

    connection.simulate_disconnect()
    await asyncio.wait_for(task, 2.0)
    assert transport.closed is True

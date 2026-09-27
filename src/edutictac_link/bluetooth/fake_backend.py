"""Backend BLE fals per a tests, sense maquinari ni Bluetooth.

Permet simular escaneig, connexió, lectura, escriptura i notificacions.
No forma part de l'execució de producció.
"""

from __future__ import annotations

from typing import Any

from edutictac_link.bluetooth.backend import BleBackend, BleConnection, NotifyCallback
from edutictac_link.bluetooth.models import Peripheral


def _key(characteristic: Any) -> str:
    return str(characteristic)


class FakeConnection(BleConnection):
    """Connexió simulada amb valors i escriptures enregistrades."""

    def __init__(self, values: dict[str, bytes] | None = None) -> None:
        self.values: dict[str, bytes] = dict(values or {})
        self.writes: list[tuple[str | None, Any, bytes, bool | None]] = []
        self.notify_callbacks: dict[str, NotifyCallback] = {}
        self.connected = True

    async def read(self, service: str | None, characteristic: Any) -> bytes:
        self._ensure_connected()
        return self.values.get(_key(characteristic), b"")

    async def write(
        self,
        service: str | None,
        characteristic: Any,
        data: bytes,
        with_response: bool | None,
    ) -> int:
        self._ensure_connected()
        self.writes.append((service, characteristic, data, with_response))
        return len(data)

    async def start_notify(
        self, service: str | None, characteristic: Any, callback: NotifyCallback
    ) -> None:
        self._ensure_connected()
        self.notify_callbacks[_key(characteristic)] = callback

    async def stop_notify(self, service: str | None, characteristic: Any) -> None:
        self.notify_callbacks.pop(_key(characteristic), None)

    async def disconnect(self) -> None:
        self.connected = False
        self.notify_callbacks.clear()

    def emit(self, characteristic: Any, data: bytes) -> None:
        """Simula una notificació del perifèric (per als tests)."""

        callback = self.notify_callbacks.get(_key(characteristic))
        if callback is not None:
            callback(bytes(data))

    def _ensure_connected(self) -> None:
        if not self.connected:
            raise RuntimeError("Connexió tancada")


class FakeBackend(BleBackend):
    """Backend de proves amb perifèrics prefixats."""

    def __init__(
        self,
        peripherals: list[Peripheral] | None = None,
        connection: FakeConnection | None = None,
        scan_error: Exception | None = None,
    ) -> None:
        self.peripherals = list(peripherals or [])
        self.connection = connection or FakeConnection()
        self.scan_error = scan_error
        self.scan_calls: list[float] = []
        self.connected_peripheral: Peripheral | None = None

    async def scan(self, timeout: float) -> list[Peripheral]:
        self.scan_calls.append(timeout)
        if self.scan_error is not None:
            raise self.scan_error
        return list(self.peripherals)

    async def connect(self, peripheral: Peripheral) -> BleConnection:
        self.connected_peripheral = peripheral
        return self.connection

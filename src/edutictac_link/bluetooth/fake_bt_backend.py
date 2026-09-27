"""Backend Bluetooth Classic fals per a tests, sense maquinari.

No forma part de l'execució de producció.
"""

from __future__ import annotations

from edutictac_link.bluetooth.bt_backend import (
    BtBackend,
    BtConnection,
    DisconnectCallback,
    ReceiveCallback,
)
from edutictac_link.bluetooth.models import Peripheral


class FakeBtConnection(BtConnection):
    def __init__(
        self,
        on_receive: ReceiveCallback | None = None,
        on_disconnect: DisconnectCallback | None = None,
        send_error: Exception | None = None,
    ) -> None:
        self.on_receive = on_receive
        self.on_disconnect = on_disconnect
        self.send_error = send_error
        self.sent: list[bytes] = []
        self.connected = True

    async def send(self, data: bytes) -> int:
        if not self.connected:
            raise RuntimeError("Connexió tancada")
        if self.send_error is not None:
            raise self.send_error
        self.sent.append(bytes(data))
        return len(data)

    async def disconnect(self) -> None:
        self.connected = False

    def emit(self, data: bytes) -> None:
        """Simula dades rebudes del perifèric (per als tests)."""

        if self.on_receive is not None:
            self.on_receive(bytes(data))

    def simulate_disconnect(self) -> None:
        self.connected = False
        if self.on_disconnect is not None:
            self.on_disconnect()


class FakeBtBackend(BtBackend):
    def __init__(
        self,
        peripherals: list[Peripheral] | None = None,
        connection: FakeBtConnection | None = None,
        discover_error: Exception | None = None,
    ) -> None:
        self.peripherals = list(peripherals or [])
        self.connection = connection or FakeBtConnection()
        self.discover_error = discover_error
        self.discover_calls: list[tuple[int | None, int | None, float]] = []
        self.connected_peripheral: Peripheral | None = None
        self.pin: str | None = None

    async def discover(
        self, major_class: int | None, minor_class: int | None, timeout: float
    ) -> list[Peripheral]:
        self.discover_calls.append((major_class, minor_class, timeout))
        if self.discover_error is not None:
            raise self.discover_error
        return list(self.peripherals)

    async def connect(
        self,
        peripheral: Peripheral,
        pin: str | None,
        on_receive: ReceiveCallback | None = None,
        on_disconnect: DisconnectCallback | None = None,
    ) -> BtConnection:
        self.connected_peripheral = peripheral
        self.pin = pin
        self.connection.on_receive = on_receive
        self.connection.on_disconnect = on_disconnect
        return self.connection

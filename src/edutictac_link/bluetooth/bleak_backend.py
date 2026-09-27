"""Backend BLE real basat en ``bleak`` (BlueZ / D-Bus a Linux).

No requereix root ni capacitats: BlueZ exposa l'adaptador per D-Bus.
"""

from __future__ import annotations

import logging
from typing import Any

from edutictac_link.bluetooth.backend import BleBackend, BleConnection, NotifyCallback
from edutictac_link.bluetooth.models import Advertisement, Peripheral

_LOGGER = logging.getLogger("edutictac_link.bleak")


class BleakConnection(BleConnection):
    """Embolega un ``BleakClient`` en la interfície BleConnection."""

    def __init__(self, client: Any, logger: logging.Logger | None = None) -> None:
        self._client = client
        self._log = logger or _LOGGER
        self._callbacks: dict[str, Any] = {}

    async def read(self, service: str | None, characteristic: Any) -> bytes:
        data = await self._client.read_gatt_char(characteristic)
        return bytes(data)

    async def write(
        self,
        service: str | None,
        characteristic: Any,
        data: bytes,
        with_response: bool | None,
    ) -> int:
        response = self._resolve_response(characteristic, with_response)
        await self._client.write_gatt_char(characteristic, data, response=response)
        return len(data)

    def _resolve_response(self, characteristic: Any, with_response: bool | None) -> bool:
        if with_response is not None:
            return bool(with_response)
        try:
            char = self._client.services.get_characteristic(characteristic)
        except Exception:
            char = None
        if char is None:
            return True
        properties = set(char.properties or [])
        # Segons l'especificació: sense resposta si la característica ho suporta.
        if "write-without-response" in properties:
            return False
        return True

    async def start_notify(
        self, service: str | None, characteristic: Any, callback: NotifyCallback
    ) -> None:
        def _wrapped(_sender: Any, data: bytearray) -> None:
            callback(bytes(data))

        await self._client.start_notify(characteristic, _wrapped)
        self._callbacks[str(characteristic)] = _wrapped

    async def stop_notify(self, service: str | None, characteristic: Any) -> None:
        await self._client.stop_notify(characteristic)
        self._callbacks.pop(str(characteristic), None)

    async def disconnect(self) -> None:
        try:
            await self._client.disconnect()
        finally:
            self._callbacks.clear()


class BleakBackend(BleBackend):
    """Backend BLE de producció."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._log = logger or _LOGGER
        self._client: Any = None

    async def scan(self, timeout: float) -> list[Peripheral]:
        try:
            from bleak import BleakScanner
        except ImportError as exc:  # pragma: no cover - entorn sense bleak
            raise RuntimeError(
                "Falta la biblioteca 'bleak'. Instal·la EduTicTac Link amb pipx "
                "o el paquet python3-bleak."
            ) from exc

        discovered = await BleakScanner.discover(timeout=timeout, return_adv=True)
        peripherals: list[Peripheral] = []
        for device, advertisement in discovered.values():
            peripherals.append(self._to_peripheral(device, advertisement))
        self._log.debug("Escaneig completat: %d perifèrics", len(peripherals))
        return peripherals

    async def connect(self, peripheral: Peripheral) -> BleConnection:
        try:
            from bleak import BleakClient
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("Falta la biblioteca 'bleak'.") from exc

        client = BleakClient(peripheral.id, timeout=20.0)
        await client.connect()
        self._client = client
        return BleakConnection(client, self._log)

    @staticmethod
    def _to_peripheral(device: Any, advertisement: Any) -> Peripheral:
        manufacturer = dict(getattr(advertisement, "manufacturer_data", {}) or {})
        return Peripheral(
            id=device.address,
            name=device.name or getattr(advertisement, "local_name", None),
            rssi=getattr(advertisement, "rssi", None),
            advertisement=Advertisement(
                name=getattr(advertisement, "local_name", None),
                service_uuids=tuple(getattr(advertisement, "service_uuids", ()) or ()),
                manufacturer_data=manufacturer,
            ),
        )

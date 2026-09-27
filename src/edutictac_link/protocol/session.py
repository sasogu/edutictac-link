"""Sessió de protocol per a Bluetooth Low Energy (GATT).

Una connexió WebSocket atén un únic perifèric. Els estats són
``initial → discovery → connected`` (i ``done``), tal com descriu la
documentació de Scratch Link.
"""

from __future__ import annotations

import asyncio
import base64
import logging
from typing import Any

from edutictac_link import PROTOCOL_VERSION
from edutictac_link.bluetooth.backend import BleBackend, BleConnection
from edutictac_link.bluetooth.filters import (
    allowed_services,
    match_filters,
    normalize_uuid,
)
from edutictac_link.protocol.base_session import (
    BaseSession,
    SessionState,
    Transport,
    TransportClosed,
)
from edutictac_link.protocol.errors import (
    DEVICE_ERROR,
    INVALID_PARAMS,
    METHOD_NOT_FOUND,
    JsonRpcError,
)
from edutictac_link.protocol.jsonrpc import make_notification

__all__ = ["Session", "SessionState", "Transport", "TransportClosed"]


class Session(BaseSession):
    """Protocol per a perifèrics BLE."""

    def __init__(
        self,
        transport: Transport,
        backend: BleBackend,
        *,
        scan_seconds: float = 10.0,
        operation_timeout: float = 10.0,
        protocol_version: str = PROTOCOL_VERSION,
        logger: logging.Logger | None = None,
    ) -> None:
        super().__init__(
            transport,
            scan_seconds=scan_seconds,
            operation_timeout=operation_timeout,
            protocol_version=protocol_version,
            logger=logger,
        )
        self._backend = backend
        self._connection: BleConnection | None = None
        self._filters: list[dict[str, Any]] = []
        self._allowed_services: set[str] = set()

    # -- descobriment -----------------------------------------------------

    def _validate_discovery(self, params: dict[str, Any]) -> None:
        filters = params.get("filters")
        if not isinstance(filters, list) or not filters:
            raise JsonRpcError(
                INVALID_PARAMS, "Cal almenys un filtre de descobriment"
            )
        if not any(isinstance(f, dict) and f for f in filters):
            raise JsonRpcError(INVALID_PARAMS, "El filtre no pot ser trivial")
        optional = params.get("optionalServices") or []
        self._filters = [f for f in filters if isinstance(f, dict) and f]
        self._allowed_services = allowed_services(self._filters, optional)

    async def _scan(self):
        peripherals = await self._backend.scan(self._scan_seconds)
        return [p for p in peripherals if match_filters(p, self._filters)]

    # -- connexió ---------------------------------------------------------

    async def _disconnect(self) -> None:
        if self._connection is None:
            return
        try:
            await self._connection.disconnect()
        except Exception:  # pragma: no cover - defensiu
            self._log.debug("Error en desconnectar", exc_info=True)
        self._connection = None

    async def _connect(self, params: dict[str, Any]) -> None:
        index = self._require_peripheral(params)
        peripheral = self._peripherals.get(index)
        if peripheral is None:
            raise JsonRpcError(INVALID_PARAMS, "peripheralId desconegut")

        try:
            connection = await self._backend.connect(
                peripheral, self._handle_disconnect
            )
        except Exception as exc:
            self._log.error("No s'ha pogut connectar: %s", exc)
            raise JsonRpcError(
                DEVICE_ERROR, f"No s'ha pogut connectar amb el perifèric: {exc}"
            ) from exc

        self._connection = connection
        self._state = SessionState.CONNECTED
        await self._cancel_discovery()
        self._log.info("Connectat a %s", peripheral.display_name or peripheral.id)
        return None

    # -- operacions en estat connectat ------------------------------------

    async def _connected_request(
        self, method: str, params: dict[str, Any]
    ) -> Any:
        if self._connection is None:  # pragma: no cover - defensiu
            raise JsonRpcError(DEVICE_ERROR, "No hi ha connexió activa")

        if method == "getServices":
            return sorted(self._allowed_services)

        service = self._service_id(params)

        if method == "read":
            characteristic = self._require_characteristic(params)
            data = await self._device_op(
                self._connection.read(service, characteristic), "la lectura"
            )
            result: dict[str, Any] = {
                "message": base64.standard_b64encode(data).decode("ascii"),
                "encoding": "base64",
            }
            if params.get("startNotifications"):
                await self._start_notify(service, characteristic)
            return result

        if method == "write":
            characteristic = self._require_characteristic(params)
            data = self._decode_message(params)
            with_response = params.get("withResponse")
            if with_response is not None:
                with_response = bool(with_response)
            return await self._device_op(
                self._connection.write(service, characteristic, data, with_response),
                "l'escriptura",
            )

        if method == "startNotifications":
            characteristic = self._require_characteristic(params)
            await self._start_notify(service, characteristic)
            return None

        if method == "stopNotifications":
            characteristic = self._require_characteristic(params)
            await self._device_op(
                self._connection.stop_notify(service, characteristic),
                "la desactivació de notificacions",
            )
            return None

        raise JsonRpcError(METHOD_NOT_FOUND, f"Mètode desconegut: {method}")

    async def _start_notify(self, service: str | None, characteristic: Any) -> None:
        assert self._connection is not None
        loop = asyncio.get_running_loop()
        service_id = self._json_service_id(service)

        def callback(data: bytes) -> None:
            notification = make_notification(
                "characteristicDidChange",
                {
                    "serviceId": service_id,
                    "characteristicId": str(characteristic),
                    "message": base64.standard_b64encode(bytes(data)).decode("ascii"),
                    "encoding": "base64",
                },
            )
            loop.call_soon_threadsafe(self._enqueue, notification)

        await self._device_op(
            self._connection.start_notify(service, characteristic, callback),
            "l'activació de notificacions",
        )

    # -- utilitats BLE ----------------------------------------------------

    def _service_id(self, params: dict[str, Any]) -> str | None:
        raw = params.get("serviceId")
        if raw is None:
            return None
        normalized = normalize_uuid(raw)
        if normalized is None:
            raise JsonRpcError(INVALID_PARAMS, "serviceId invàlid")
        if self._allowed_services and normalized not in self._allowed_services:
            raise JsonRpcError(
                DEVICE_ERROR, "El servei no estava permés pel descobriment"
            )
        return raw

    @staticmethod
    def _json_service_id(service: str | None) -> str | None:
        if service is None:
            return None
        normalized = normalize_uuid(service)
        return normalized or str(service)

    @staticmethod
    def _require_characteristic(params: dict[str, Any]) -> Any:
        characteristic = params.get("characteristicId")
        if characteristic is None:
            raise JsonRpcError(INVALID_PARAMS, "Falta characteristicId")
        return characteristic

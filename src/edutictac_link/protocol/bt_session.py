"""Sessió de protocol per a Bluetooth Classic (RFCOMM/SPP), p. ex. LEGO EV3.

Els mètodes són els del punt d'accés ``/scratch/bt``: ``discover`` per classe
de dispositiu, ``connect`` amb PIN opcional, ``send`` i la notificació
``didReceiveMessage``.
"""

from __future__ import annotations

import base64
import logging
from typing import Any

from edutictac_link import PROTOCOL_VERSION
from edutictac_link.bluetooth.bt_backend import BtBackend, BtConnection
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

__all__ = ["BtSession"]


class BtSession(BaseSession):
    """Protocol per a perifèrics Bluetooth Classic."""

    def __init__(
        self,
        transport: Transport,
        backend: BtBackend,
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
        self._connection: BtConnection | None = None
        self._major_class: int | None = None
        self._minor_class: int | None = None

    # -- descobriment -----------------------------------------------------

    def _validate_discovery(self, params: dict[str, Any]) -> None:
        major = params.get("majorDeviceClass")
        minor = params.get("minorDeviceClass")
        if major is None:
            raise JsonRpcError(
                INVALID_PARAMS, "Falta majorDeviceClass per al descobriment BT"
            )
        try:
            self._major_class = int(major)
            self._minor_class = int(minor) if minor is not None else None
        except (TypeError, ValueError):
            raise JsonRpcError(
                INVALID_PARAMS, "Classe de dispositiu invàlida"
            ) from None

    async def _scan(self):
        return await self._backend.discover(
            self._major_class, self._minor_class, self._scan_seconds
        )

    # -- connexió ---------------------------------------------------------

    async def _disconnect(self) -> None:
        if self._connection is None:
            return
        try:
            await self._connection.disconnect()
        except Exception:  # pragma: no cover - defensiu
            self._log.debug("Error en desconnectar BT", exc_info=True)
        self._connection = None

    async def _connect(self, params: dict[str, Any]) -> None:
        index = self._require_peripheral(params)
        peripheral = self._peripherals.get(index)
        if peripheral is None:
            raise JsonRpcError(INVALID_PARAMS, "peripheralId desconegut")

        pin = params.get("pin")
        try:
            connection = await self._backend.connect(
                peripheral, pin, self._on_receive, self._handle_disconnect
            )
        except Exception as exc:
            self._log.error("No s'ha pogut connectar per BT: %s", exc)
            raise JsonRpcError(
                DEVICE_ERROR, f"No s'ha pogut connectar amb el perifèric: {exc}"
            ) from exc

        self._connection = connection
        self._state = SessionState.CONNECTED
        await self._cancel_discovery()
        self._log.info("Connectat (BT) a %s", peripheral.display_name or peripheral.id)
        return None

    def _on_receive(self, data: bytes) -> None:
        loop = self._loop
        if loop is None:
            return
        notification = make_notification(
            "didReceiveMessage",
            {
                "message": base64.standard_b64encode(bytes(data)).decode("ascii"),
                "encoding": "base64",
            },
        )
        loop.call_soon_threadsafe(self._enqueue, notification)

    # -- operacions en estat connectat ------------------------------------

    async def _connected_request(self, method: str, params: dict[str, Any]) -> Any:
        if self._connection is None:  # pragma: no cover - defensiu
            raise JsonRpcError(DEVICE_ERROR, "No hi ha connexió activa")

        if method == "send":
            data = self._decode_message(params)
            return await self._device_op(self._connection.send(data), "l'enviament")

        raise JsonRpcError(METHOD_NOT_FOUND, f"Mètode desconegut: {method}")

"""Màquina d'estats d'una connexió Scratch Link.

Una connexió WebSocket atén un únic perifèric. Els estats són
``initial → discovery → connected`` (i ``done``), tal com descriu la
documentació de Scratch Link.
"""

from __future__ import annotations

import asyncio
import base64
import binascii
import json
import logging
from enum import Enum
from typing import Any, Protocol

from edutictac_link import PROTOCOL_VERSION
from edutictac_link.bluetooth.backend import BleBackend, BleConnection
from edutictac_link.bluetooth.filters import (
    allowed_services,
    match_filters,
    normalize_uuid,
)
from edutictac_link.bluetooth.models import Peripheral
from edutictac_link.protocol.errors import (
    DEVICE_ERROR,
    INTERNAL_ERROR,
    INVALID_PARAMS,
    INVALID_REQUEST,
    METHOD_NOT_FOUND,
    JsonRpcError,
)
from edutictac_link.protocol.jsonrpc import (
    Request,
    make_error,
    make_notification,
    make_response,
    parse_message,
)

_LOGGER = logging.getLogger("edutictac_link.session")


class TransportClosed(Exception):
    """El transport subjacent s'ha tancat."""


class Transport(Protocol):
    """Transport de missatges de text (normalment un WebSocket)."""

    async def recv(self) -> str | bytes: ...

    async def send(self, message: str) -> None: ...

    async def close(self) -> None: ...


class SessionState(Enum):
    INITIAL = 1
    DISCOVERY = 2
    CONNECTED = 3
    DONE = 4


class Session:
    """Gestiona el protocol d'una connexió amb un client Scratch."""

    def __init__(
        self,
        transport: Transport,
        backend: BleBackend,
        *,
        scan_seconds: float = 10.0,
        protocol_version: str = PROTOCOL_VERSION,
        logger: logging.Logger | None = None,
    ) -> None:
        self._transport = transport
        self._backend = backend
        self._scan_seconds = scan_seconds
        self._protocol_version = protocol_version
        self._log = logger or _LOGGER

        self._state = SessionState.INITIAL
        self._outbox: asyncio.Queue[str | None] = asyncio.Queue()
        self._sender_task: asyncio.Task[None] | None = None
        self._discovery_task: asyncio.Task[None] | None = None
        self._connection: BleConnection | None = None
        self._filters: list[dict[str, Any]] = []
        self._peripherals: dict[int, Peripheral] = {}
        self._allowed_services: set[str] = set()

    # -- cicle de vida ----------------------------------------------------

    async def run(self) -> None:
        """Bucle principal: rep missatges i manté el fil d'eixida."""
        self._sender_task = asyncio.create_task(self._sender_loop())
        try:
            while self._state is not SessionState.DONE:
                try:
                    raw = await self._transport.recv()
                except TransportClosed:
                    break
                except Exception as exc:  # pragma: no cover - defensiu
                    self._log.debug("Transport tancat: %s", exc)
                    break
                await self._on_message(raw)
        finally:
            await self._shutdown()
            self._outbox.put_nowait(None)
            if self._sender_task is not None:
                await self._sender_task

    async def _shutdown(self) -> None:
        await self._cancel_discovery()
        if self._connection is not None:
            try:
                await self._connection.disconnect()
            except Exception:  # pragma: no cover - defensiu
                self._log.debug("Error en desconnectar", exc_info=True)
            self._connection = None
        self._state = SessionState.DONE

    async def _sender_loop(self) -> None:
        while True:
            message = await self._outbox.get()
            if message is None:
                return
            try:
                await self._transport.send(message)
            except Exception:  # pragma: no cover - defensiu
                self._log.debug("No s'ha pogut enviar el missatge", exc_info=True)
                return

    def _enqueue(self, obj: dict[str, Any]) -> None:
        self._outbox.put_nowait(json.dumps(obj))

    # -- gestió de missatges ----------------------------------------------

    async def _on_message(self, raw: str | bytes) -> None:
        try:
            request = parse_message(raw)
        except JsonRpcError as exc:
            self._enqueue(make_error(None, exc.code, exc.message))
            return

        try:
            result = await self._dispatch(request)
        except JsonRpcError as exc:
            if not request.is_notification:
                self._enqueue(make_error(request.id, exc.code, exc.message))
            return
        except Exception as exc:  # pragma: no cover - defensiu
            self._log.exception("Error intern en atendre %s", request.method)
            if not request.is_notification:
                self._enqueue(
                    make_error(request.id, INTERNAL_ERROR, f"Error intern: {exc}")
                )
            return

        if not request.is_notification:
            self._enqueue(make_response(request.id, result))

    async def _dispatch(self, request: Request) -> Any:
        method = request.method
        params = request.params

        if method == "ping":
            return 42
        if method == "getVersion":
            return {"protocol": self._protocol_version}

        if self._state is SessionState.INITIAL:
            if method == "discover":
                return await self._start_discovery(params)
            raise JsonRpcError(
                INVALID_REQUEST, f"'{method}' no és permés abans de 'discover'"
            )

        if self._state is SessionState.DISCOVERY:
            if method == "connect":
                return await self._connect(params)
            if method == "discover":
                raise JsonRpcError(INVALID_REQUEST, "Ja està en descobriment")
            raise JsonRpcError(
                INVALID_REQUEST, f"'{method}' no és permés durant el descobriment"
            )

        if self._state is SessionState.CONNECTED:
            return await self._connected_request(method, params)

        raise JsonRpcError(INVALID_REQUEST, "Sessió tancada")

    # -- descobriment -----------------------------------------------------

    async def _start_discovery(self, params: dict[str, Any]) -> None:
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
        self._state = SessionState.DISCOVERY
        self._discovery_task = asyncio.create_task(self._run_discovery())
        return None

    async def _run_discovery(self) -> None:
        try:
            peripherals = await self._backend.scan(self._scan_seconds)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            self._log.error("Error en escanejar BLE: %s", exc)
            return

        matched = [p for p in peripherals if match_filters(p, self._filters)]
        self._peripherals = {}
        for index, peripheral in enumerate(matched):
            self._peripherals[index] = peripheral
            self._enqueue(
                make_notification(
                    "didDiscoverPeripheral", self._peripheral_payload(index, peripheral)
                )
            )
        if not matched:
            self._log.info("Cap perifèric coincident amb els filtres")

        while self._state is SessionState.DISCOVERY:
            await asyncio.sleep(2.0)
            for index, peripheral in self._peripherals.items():
                self._enqueue(
                    make_notification(
                        "didDiscoverPeripheral",
                        self._peripheral_payload(index, peripheral),
                    )
                )

    @staticmethod
    def _peripheral_payload(index: int, peripheral: Peripheral) -> dict[str, Any]:
        payload: dict[str, Any] = {"peripheralId": index}
        name = peripheral.display_name
        if name:
            payload["name"] = name
        rssi = peripheral.rssi
        payload["rssi"] = rssi if isinstance(rssi, int) else 127
        return payload

    async def _cancel_discovery(self) -> None:
        task = self._discovery_task
        self._discovery_task = None
        if task is not None and not task.done():
            task.cancel()
            try:
                await task
            except (asyncio.CancelledError, Exception):
                pass

    # -- connexió ---------------------------------------------------------

    async def _connect(self, params: dict[str, Any]) -> None:
        peripheral_id = params.get("peripheralId")
        try:
            index = int(peripheral_id)
        except (TypeError, ValueError):
            raise JsonRpcError(INVALID_PARAMS, "peripheralId invàlid") from None
        peripheral = self._peripherals.get(index)
        if peripheral is None:
            raise JsonRpcError(INVALID_PARAMS, "peripheralId desconegut")

        try:
            connection = await self._backend.connect(peripheral)
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
            data = await self._connection.read(service, characteristic)
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
            return await self._connection.write(
                service, characteristic, data, with_response
            )

        if method == "startNotifications":
            characteristic = self._require_characteristic(params)
            await self._start_notify(service, characteristic)
            return None

        if method == "stopNotifications":
            characteristic = self._require_characteristic(params)
            await self._connection.stop_notify(service, characteristic)
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

        await self._connection.start_notify(service, characteristic, callback)

    # -- utilitats --------------------------------------------------------

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

    @staticmethod
    def _decode_message(params: dict[str, Any]) -> bytes:
        message = params.get("message")
        if message is None:
            raise JsonRpcError(INVALID_PARAMS, "Falta message")
        encoding = params.get("encoding")
        if encoding == "base64":
            try:
                return base64.standard_b64decode(str(message))
            except (binascii.Error, ValueError) as exc:
                raise JsonRpcError(INVALID_PARAMS, "base64 invàlid") from exc
        if encoding in (None, "utf-8", "utf8", "text"):
            return str(message).encode("utf-8")
        raise JsonRpcError(INVALID_PARAMS, f"encoding no suportat: {encoding}")

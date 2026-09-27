"""Base comuna de les sessions de protocol (Bluetooth LE i Bluetooth Classic).

Concentra el bucle de recepció, el fil d'eixida, l'anàlisi de missatges
JSON-RPC, la màquina d'estats i el cicle de descobriment. Les sessions
concretes implementen els ganxos de dispositiu.
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
from edutictac_link.bluetooth.models import Peripheral
from edutictac_link.protocol.errors import (
    DEVICE_ERROR,
    INTERNAL_ERROR,
    INVALID_PARAMS,
    INVALID_REQUEST,
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


class BaseSession:
    """Protocol JSON-RPC compartit; els ganxos els implementa cada transport."""

    def __init__(
        self,
        transport: Transport,
        *,
        scan_seconds: float = 10.0,
        operation_timeout: float = 10.0,
        protocol_version: str = PROTOCOL_VERSION,
        logger: logging.Logger | None = None,
    ) -> None:
        self._transport = transport
        self._scan_seconds = scan_seconds
        self._operation_timeout = operation_timeout
        self._protocol_version = protocol_version
        self._log = logger or _LOGGER

        self._state = SessionState.INITIAL
        self._outbox: asyncio.Queue[str | None] = asyncio.Queue()
        self._sender_task: asyncio.Task[None] | None = None
        self._discovery_task: asyncio.Task[None] | None = None
        self._peripherals: dict[int, Peripheral] = {}
        self._loop: asyncio.AbstractEventLoop | None = None
        self._closing = False

    # -- cicle de vida ----------------------------------------------------

    async def run(self) -> None:
        """Bucle principal: rep missatges i manté el fil d'eixida."""
        self._loop = asyncio.get_running_loop()
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
        self._closing = True
        await self._cancel_discovery()
        await self._disconnect()
        self._state = SessionState.DONE

    async def _disconnect(self) -> None:
        """Ganxo: tanca la connexió amb el perifèric, si n'hi ha."""

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

    async def _start_discovery(self, params: dict[str, Any]) -> None:
        self._validate_discovery(params)
        self._state = SessionState.DISCOVERY
        self._discovery_task = asyncio.create_task(self._run_discovery())
        return None

    async def _run_discovery(self) -> None:
        try:
            matched = await self._scan()
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            self._log.error("Error durant el descobriment: %s", exc)
            return

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

    # -- desconnexió ------------------------------------------------------

    def _handle_disconnect(self) -> None:
        """Callback del backend quan es perd la connexió (pot ser un altre fil)."""
        loop = self._loop
        if loop is not None:
            loop.call_soon_threadsafe(self._on_device_disconnected)

    def _on_device_disconnected(self) -> None:
        if self._closing or self._state is not SessionState.CONNECTED:
            return
        self._log.info("S'ha perdut la connexió amb el perifèric")
        self._state = SessionState.DONE
        asyncio.ensure_future(self._transport.close())

    # -- utilitats compartides --------------------------------------------

    async def _device_op(self, awaitable: Any, what: str) -> Any:
        """Executa una operació de dispositiu amb temps d'espera i error uniforme."""
        try:
            return await asyncio.wait_for(
                awaitable, timeout=self._operation_timeout
            )
        except asyncio.TimeoutError as exc:
            raise JsonRpcError(
                DEVICE_ERROR, f"S'ha esgotat el temps d'espera en {what}"
            ) from exc
        except JsonRpcError:
            raise
        except Exception as exc:
            raise JsonRpcError(
                DEVICE_ERROR, f"Error de dispositiu en {what}: {exc}"
            ) from exc

    @staticmethod
    def _require_peripheral(params: dict[str, Any]) -> int:
        peripheral_id = params.get("peripheralId")
        try:
            return int(peripheral_id)
        except (TypeError, ValueError):
            raise JsonRpcError(INVALID_PARAMS, "peripheralId invàlid") from None

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

    # -- ganxos que implementen les subclasses ----------------------------

    def _validate_discovery(self, params: dict[str, Any]) -> None:
        raise NotImplementedError

    async def _scan(self) -> list[Peripheral]:
        raise NotImplementedError

    async def _connect(self, params: dict[str, Any]) -> None:
        raise NotImplementedError

    async def _connected_request(self, method: str, params: dict[str, Any]) -> Any:
        raise NotImplementedError

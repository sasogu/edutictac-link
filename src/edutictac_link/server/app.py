"""Servidor WebSocket compatible amb Scratch Link."""

from __future__ import annotations

import logging
from typing import Any, Callable

from edutictac_link.bluetooth.backend import BleBackend
from edutictac_link.bluetooth.bleak_backend import BleakBackend
from edutictac_link.bluetooth.bt_backend import BtBackend
from edutictac_link.bluetooth.bt_bluez import BluezBtBackend
from edutictac_link.config import Config
from edutictac_link.protocol.bt_session import BtSession
from edutictac_link.protocol.session import Session, Transport, TransportClosed
from edutictac_link.server.origin import origin_is_allowed

_LOGGER = logging.getLogger("edutictac_link.server")

BLE_PATH = "/scratch/ble"
BT_PATH = "/scratch/bt"


class WsTransport(Transport):
    """Adaptador d'un WebSocket de ``websockets`` a la interfície Transport."""

    def __init__(self, websocket: Any) -> None:
        self._ws = websocket

    async def recv(self) -> str | bytes:
        try:
            return await self._ws.recv()
        except Exception as exc:
            raise TransportClosed() from exc

    async def send(self, message: str) -> None:
        await self._ws.send(message)

    async def close(self) -> None:
        await self._ws.close()


class LinkServer:
    """Servidor que publica els punts d'accés /scratch/ble i /scratch/bt."""

    def __init__(
        self,
        config: Config | None = None,
        backend_factory: Callable[[], BleBackend] | None = None,
        bt_backend_factory: Callable[[], BtBackend] | None = None,
    ) -> None:
        self.config = config or Config.from_env()
        self._backend_factory = backend_factory or BleakBackend
        self._bt_backend_factory = bt_backend_factory or BluezBtBackend
        self._log = _LOGGER

    async def handler(self, websocket: Any) -> None:
        path = self._path(websocket)
        if path not in (BLE_PATH, BT_PATH):
            self._log.warning("Ruta desconeguda: %r", path)
            await websocket.close(code=1008, reason="Ruta desconeguda")
            return

        origin = self._origin(websocket)
        if not origin_is_allowed(origin, self.config):
            self._log.warning("Origen rebutjat: %r", origin)
            await websocket.close(code=1008, reason="Origen no permés")
            return

        kind = "BT" if path == BT_PATH else "BLE"
        self._log.info("Sessió %s nova (origen=%s)", kind, origin or "natiu")
        transport = WsTransport(websocket)
        if path == BT_PATH:
            session: Session | BtSession = BtSession(
                transport,
                self._bt_backend_factory(),
                scan_seconds=self.config.scan_seconds,
                operation_timeout=self.config.operation_timeout,
                logger=self._log,
            )
        else:
            session = Session(
                transport,
                self._backend_factory(),
                scan_seconds=self.config.scan_seconds,
                operation_timeout=self.config.operation_timeout,
                logger=self._log,
            )
        try:
            await session.run()
        except Exception:  # pragma: no cover - defensiu
            self._log.debug("La sessió ha acabat amb error", exc_info=True)

    async def serve(self) -> None:
        import websockets

        async with websockets.serve(
            self.handler, self.config.host, self.config.port
        ) as server:
            self._log.info(
                "EduTicTac Link escoltant en ws://%s:%d%s",
                self.config.host,
                self.config.port,
                BLE_PATH,
            )
            await server.serve_forever()

    @staticmethod
    def _path(websocket: Any) -> str | None:
        request = getattr(websocket, "request", None)
        if request is not None and getattr(request, "path", None):
            return request.path
        return getattr(websocket, "path", None)

    @staticmethod
    def _origin(websocket: Any) -> str | None:
        request = getattr(websocket, "request", None)
        headers = getattr(request, "headers", None)
        if headers is None:
            headers = getattr(websocket, "request_headers", None)
        if headers is None:
            return None
        try:
            return headers.get("Origin")
        except Exception:  # pragma: no cover - defensiu
            return None

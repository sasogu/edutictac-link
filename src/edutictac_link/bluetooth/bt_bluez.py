"""Backend Bluetooth Classic real (BlueZ) — EXPERIMENTAL.

Descobriment amb ``bluetoothctl`` i connexió RFCOMM amb el mòdul ``socket``
estàndard (``AF_BLUETOOTH``/``BTPROTO_RFCOMM``), sense root.

L'emparellament amb PIN s'intenta de manera oportunista, però es recomana
tindre el dispositiu emparellat al sistema una vegada (és el cas habitual de
l'EV3). **Pendent de validació amb maquinari real.**
"""

from __future__ import annotations

import asyncio
import logging
import re
import socket
import subprocess
import threading
from typing import Any

from edutictac_link.bluetooth.bt_backend import (
    BtBackend,
    BtConnection,
    DisconnectCallback,
    ReceiveCallback,
)
from edutictac_link.bluetooth.models import Peripheral

_LOGGER = logging.getLogger("edutictac_link.bt_bluez")

_SPP_UUID = "00001101-0000-1000-8000-00805f9b34fb"
_DEVICE_RE = re.compile(r"Device ([0-9A-Fa-f:]{17})\s*(.*)")
_CLASS_RE = re.compile(r"Class: 0x([0-9A-Fa-f]+)")
_CHANNEL_RE = re.compile(r"Channel:\s*(\d+)")


def _run(cmd: list[str], timeout: float = 30.0) -> tuple[int, str]:
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, check=False
        )
    except FileNotFoundError:
        return 127, "orde no trobada"
    except subprocess.TimeoutExpired:
        return 124, "temps esgotat"
    except Exception as exc:  # pragma: no cover - defensiu
        return 1, str(exc)
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


class RfcommConnection(BtConnection):
    """Connexió RFCOMM amb un fil lector que emet les dades rebudes."""

    def __init__(
        self,
        sock: socket.socket,
        loop: asyncio.AbstractEventLoop,
        on_receive: ReceiveCallback | None = None,
        on_disconnect: DisconnectCallback | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self._sock = sock
        self._loop = loop
        self._on_receive = on_receive
        self._on_disconnect = on_disconnect
        self._log = logger or _LOGGER
        self._closed = False
        self._reader = threading.Thread(target=self._read_loop, daemon=True)
        self._reader.start()

    def _read_loop(self) -> None:
        try:
            while not self._closed:
                data = self._sock.recv(4096)
                if not data:
                    break
                if self._on_receive is not None:
                    self._loop.call_soon_threadsafe(self._on_receive, data)
        except OSError:
            pass
        finally:
            if not self._closed:
                self._closed = True
                if self._on_disconnect is not None:
                    self._loop.call_soon_threadsafe(self._on_disconnect)

    async def send(self, data: bytes) -> int:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._sock.sendall, bytes(data))
        return len(data)

    async def disconnect(self) -> None:
        self._closed = True
        try:
            self._sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        try:
            self._sock.close()
        except OSError:
            pass


class BluezBtBackend(BtBackend):
    """Backend Bluetooth Classic basat en BlueZ (experimental)."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._log = logger or _LOGGER

    async def discover(
        self,
        major_class: int | None,
        minor_class: int | None,
        timeout: float,
    ) -> list[Peripheral]:
        loop = asyncio.get_running_loop()
        devices = await loop.run_in_executor(None, self._discover_blocking, timeout)
        peripherals: list[Peripheral] = []
        for address, name in devices:
            device_class = await loop.run_in_executor(
                None, self._device_class, address
            )
            if not self._class_matches(device_class, major_class, minor_class):
                continue
            peripherals.append(
                Peripheral(id=address, name=name or None, rssi=None)
            )
        return peripherals

    def _discover_blocking(self, timeout: float) -> list[tuple[str, str]]:
        seconds = max(1, int(timeout))
        _code, output = _run(
            ["bluetoothctl", "--timeout", str(seconds), "scan", "on"], timeout=seconds + 5
        )
        devices: dict[str, str] = {}
        for line in output.splitlines():
            match = _DEVICE_RE.search(line)
            if match:
                devices[match.group(1).upper()] = match.group(2).strip()
        return list(devices.items())

    def _device_class(self, address: str) -> int | None:
        _code, output = _run(["bluetoothctl", "info", address], timeout=10)
        match = _CLASS_RE.search(output)
        return int(match.group(1), 16) if match else None

    @staticmethod
    def _class_matches(
        device_class: int | None, major_class: int | None, minor_class: int | None
    ) -> bool:
        if major_class is None:
            return True
        if device_class is None:
            # Sense classe no podem descartar: preferim mostrar-lo a perdre'l.
            return True
        if ((device_class >> 8) & 0x1F) != major_class:
            return False
        if minor_class is not None and ((device_class >> 2) & 0x3F) != minor_class:
            return False
        return True

    async def connect(
        self,
        peripheral: Peripheral,
        pin: str | None,
        on_receive: ReceiveCallback | None = None,
        on_disconnect: DisconnectCallback | None = None,
    ) -> BtConnection:
        loop = asyncio.get_running_loop()
        if pin:
            await loop.run_in_executor(None, self._try_pair, peripheral.id)
        channel = await loop.run_in_executor(
            None, self._find_spp_channel, peripheral.id
        )
        self._log.debug("Obrint RFCOMM a %s canal %s", peripheral.id, channel)
        sock = await loop.run_in_executor(
            None, self._open_rfcomm, peripheral.id, channel
        )
        return RfcommConnection(sock, loop, on_receive, on_disconnect, self._log)

    def _try_pair(self, address: str) -> None:
        # Best-effort: l'EV3 sol estar emparellat; si BlueZ demana PIN i no hi
        # ha agent, l'error s'ignora i la connexió RFCOMM pot funcionar igualment.
        _code, output = _run(["bluetoothctl", "pair", address], timeout=20)
        if "Failed" in output or "not available" in output:
            self._log.debug("Emparellament BT no completat per a %s", address)

    def _find_spp_channel(self, address: str) -> int:
        _code, output = _run(["sdptool", "browse", address], timeout=15)
        seen_spp = False
        for line in output.splitlines():
            if "0x1101" in line or _SPP_UUID in line.lower():
                seen_spp = True
            if seen_spp:
                match = _CHANNEL_RE.search(line)
                if match:
                    return int(match.group(1))
        return 1

    @staticmethod
    def _open_rfcomm(address: str, channel: int) -> socket.socket:
        if not hasattr(socket, "AF_BLUETOOTH"):  # pragma: no cover
            raise RuntimeError(
                "El mòdul socket de Python no té suport Bluetooth en este sistema"
            )
        sock = socket.socket(
            socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM
        )
        sock.settimeout(20.0)
        try:
            sock.connect((address, channel))
        except Exception:
            sock.close()
            raise
        sock.settimeout(None)
        return sock

"""Interfície abstracta del backend Bluetooth Classic (RFCOMM/SPP)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable

from edutictac_link.bluetooth.models import Peripheral

ReceiveCallback = Callable[[bytes], None]
DisconnectCallback = Callable[[], None]


class BtConnection(ABC):
    """Connexió RFCOMM/SPP activa amb un perifèric Bluetooth Classic."""

    @abstractmethod
    async def send(self, data: bytes) -> int:
        """Envia dades. Retorna el nombre de bytes enviats."""

    @abstractmethod
    async def disconnect(self) -> None:
        """Tanca la connexió."""


class BtBackend(ABC):
    """Backend Bluetooth Classic intercanviable."""

    @abstractmethod
    async def discover(
        self,
        major_class: int | None,
        minor_class: int | None,
        timeout: float,
    ) -> list[Peripheral]:
        """Descobrix dispositius Bluetooth Classic que coincidisquen amb la classe."""

    @abstractmethod
    async def connect(
        self,
        peripheral: Peripheral,
        pin: str | None,
        on_receive: ReceiveCallback | None = None,
        on_disconnect: DisconnectCallback | None = None,
    ) -> BtConnection:
        """Connecta amb un perifèric. ``pin`` és el PIN d'emparellament si cal."""

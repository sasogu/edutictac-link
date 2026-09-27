"""Interfície abstracta del backend Bluetooth LE."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable

from edutictac_link.bluetooth.models import Peripheral

NotifyCallback = Callable[[bytes], None]


class BleConnection(ABC):
    """Connexió GATT activa amb un perifèric."""

    @abstractmethod
    async def read(self, service: str, characteristic: str) -> bytes:
        """Llig el valor d'una característica."""

    @abstractmethod
    async def write(
        self,
        service: str,
        characteristic: str,
        data: bytes,
        with_response: bool | None,
    ) -> int:
        """Escriu dades en una característica. Retorna els bytes escrits."""

    @abstractmethod
    async def start_notify(
        self, service: str, characteristic: str, callback: NotifyCallback
    ) -> None:
        """Activa les notificacions d'una característica."""

    @abstractmethod
    async def stop_notify(self, service: str, characteristic: str) -> None:
        """Desactiva les notificacions d'una característica."""

    @abstractmethod
    async def disconnect(self) -> None:
        """Tanca la connexió."""


class BleBackend(ABC):
    """Backend BLE intercanviable (bleak a producció, fals als tests)."""

    @abstractmethod
    async def scan(self, timeout: float) -> list[Peripheral]:
        """Escaneja perifèrics durant ``timeout`` segons."""

    @abstractmethod
    async def connect(self, peripheral: Peripheral) -> BleConnection:
        """Connecta amb un perifèric detectat."""

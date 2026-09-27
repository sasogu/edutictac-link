"""Models de dades de Bluetooth Low Energy."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping


@dataclass(frozen=True)
class Advertisement:
    """Dades d'anunci d'un perifèric BLE."""

    name: str | None = None
    service_uuids: tuple[str, ...] = ()
    manufacturer_data: Mapping[int, bytes] = field(default_factory=dict)


@dataclass(frozen=True)
class Peripheral:
    """Perifèric detectat en un escaneig."""

    id: str
    name: str | None
    rssi: int | None
    advertisement: Advertisement = field(default_factory=Advertisement)

    @property
    def display_name(self) -> str | None:
        return self.name or self.advertisement.name

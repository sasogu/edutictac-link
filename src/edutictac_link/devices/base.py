"""Perfils de dispositiu.

Els perfils NO implementen comandaments de dispositiu: les extensions de
Scratch (scratch-vm) ja els construeixen. Servixen per a identificar
perifèrics, alimentar ``edutictac-link devices``, diagnòstics i fixtures de
test.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from edutictac_link.bluetooth.filters import match_filters
from edutictac_link.bluetooth.models import Peripheral


@dataclass(frozen=True)
class DeviceProfile:
    """Descripció d'identificació d'un dispositiu educatiu conegut."""

    id: str
    label: str
    transport: str  # "ble" (futur: "bt")
    filters: tuple[dict[str, Any], ...]
    optional_services: tuple[Any, ...] = field(default_factory=tuple)
    firmware: str | None = None
    extension: str | None = None
    notes: str | None = None

    def matches(self, peripheral: Peripheral) -> bool:
        return match_filters(peripheral, self.filters)

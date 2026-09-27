"""Capa Bluetooth d'EduTicTac Link (BLE i Bluetooth Classic)."""

from edutictac_link.bluetooth.backend import BleBackend, BleConnection, NotifyCallback
from edutictac_link.bluetooth.bt_backend import (
    BtBackend,
    BtConnection,
    DisconnectCallback,
    ReceiveCallback,
)
from edutictac_link.bluetooth.filters import allowed_services, match_filters, normalize_uuid
from edutictac_link.bluetooth.models import Advertisement, Peripheral

__all__ = [
    "Advertisement",
    "BleBackend",
    "BleConnection",
    "BtBackend",
    "BtConnection",
    "DisconnectCallback",
    "NotifyCallback",
    "Peripheral",
    "ReceiveCallback",
    "allowed_services",
    "match_filters",
    "normalize_uuid",
]

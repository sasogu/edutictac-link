"""Fixtures comunes per als tests d'EduTicTac Link."""

from __future__ import annotations

from edutictac_link.bluetooth.models import Advertisement, Peripheral

MICROBIT_SERVICE = "0000f005-0000-1000-8000-00805f9b34fb"
MICROBIT_RX = "5261da01-fa7e-42ab-850b-7c80220097cc"
MICROBIT_TX = "5261da02-fa7e-42ab-850b-7c80220097cc"
WEDO2_DEVICE_SERVICE = "00001523-1212-efde-1523-785feabcd123"
BOOST_SERVICE = "00001623-1212-efde-1623-785feabcd123"


def make_peripheral(
    peripheral_id: str = "AA:BB:CC:DD:EE:01",
    name: str | None = "BBC micro:bit",
    services: tuple[str, ...] = (MICROBIT_SERVICE,),
    manufacturer_data: dict[int, bytes] | None = None,
    rssi: int | None = -55,
) -> Peripheral:
    return Peripheral(
        id=peripheral_id,
        name=name,
        rssi=rssi,
        advertisement=Advertisement(
            name=name,
            service_uuids=services,
            manufacturer_data=manufacturer_data or {},
        ),
    )


def make_microbit(peripheral_id: str = "AA:BB:CC:DD:EE:01") -> Peripheral:
    return make_peripheral(peripheral_id=peripheral_id)


def make_boost(peripheral_id: str = "AA:BB:CC:DD:EE:03") -> Peripheral:
    return make_peripheral(
        peripheral_id=peripheral_id,
        name="LEGO Move Hub",
        services=(BOOST_SERVICE,),
        manufacturer_data={0x0397: bytes([0x00, 0x40, 0x12])},
    )

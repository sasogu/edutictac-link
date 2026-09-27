"""LEGO WeDo 2.0 (BLE)."""

from edutictac_link.devices.base import DeviceProfile

_DEVICE_SERVICE = "00001523-1212-efde-1523-785feabcd123"
_IO_SERVICE = "00004f0e-1212-efde-1523-785feabcd123"

PROFILE = DeviceProfile(
    id="wedo2",
    label="LEGO WeDo 2.0",
    transport="ble",
    filters=({"services": (_DEVICE_SERVICE,)},),
    optional_services=(_IO_SERVICE,),
    extension="scratch3_wedo2",
    notes=(
        "Servicis 00001523 (dispositiu) i 00004f0e (E/S); característiques "
        "00001527, 00001560, 00001563 i 00001565."
    ),
)

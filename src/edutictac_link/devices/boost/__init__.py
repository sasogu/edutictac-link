"""LEGO Boost (LEGO Wireless Protocol, BLE)."""

from edutictac_link.devices.base import DeviceProfile

_SERVICE = "00001623-1212-efde-1623-785feabcd123"

PROFILE = DeviceProfile(
    id="boost",
    label="LEGO Boost",
    transport="ble",
    filters=(
        {
            "services": (_SERVICE,),
            "manufacturerData": {0x0397: {"dataPrefix": (0x00, 0x40), "mask": (0x00, 0xFF)}},
        },
    ),
    extension="scratch3_boost",
    notes=(
        "Servici 00001623; característica 00001624; fabricant LEGO 0x0397 "
        "amb prefix de dades 00 40."
    ),
)

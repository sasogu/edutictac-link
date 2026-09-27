"""BBC micro:bit (BLE)."""

from edutictac_link.devices.base import DeviceProfile

PROFILE = DeviceProfile(
    id="microbit",
    label="BBC micro:bit",
    transport="ble",
    filters=({"services": (0xF005,)},),
    firmware=(
        "Requereix el firmware de Scratch "
        "(scratchfoundation/scratch-microbit-firmware)."
    ),
    extension="scratch3_microbit",
    notes=(
        "Servici 0xf005; RX 5261da01-fa7e-42ab-850b-7c80220097cc; "
        "TX 5261da02-fa7e-42ab-850b-7c80220097cc."
    ),
)

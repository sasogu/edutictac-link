"""Tests de la resolució d'UUID i de la coincidència de filtres."""

from __future__ import annotations

from edutictac_link.bluetooth.filters import (
    allowed_services,
    match_filters,
    normalize_uuid,
)
from tests.conftest import make_boost, make_microbit, make_peripheral


def test_normalize_uuid_16bit():
    assert normalize_uuid(0xF005) == "0000f005-0000-1000-8000-00805f9b34fb"
    assert normalize_uuid("f005") == "0000f005-0000-1000-8000-00805f9b34fb"


def test_normalize_uuid_full():
    full = "00001523-1212-efde-1523-785feabcd123"
    assert normalize_uuid(full) == full
    assert normalize_uuid(full.upper()) == full


def test_normalize_uuid_invalid():
    assert normalize_uuid("battery_service") is None
    assert normalize_uuid("zzzz") is None
    assert normalize_uuid(None) is None


def test_microbit_matches_service_filter():
    peripheral = make_microbit()
    assert match_filters(peripheral, [{"services": [0xF005]}])
    assert not match_filters(peripheral, [{"services": [0x1815]}])


def test_microbit_does_not_match_empty_filter():
    assert not match_filters(make_microbit(), [{}])
    assert not match_filters(make_microbit(), [])


def test_boost_requires_service_and_manufacturer_data():
    peripheral = make_boost()
    assert match_filters(
        peripheral,
        [
            {
                "services": ["00001623-1212-efde-1623-785feabcd123"],
                "manufacturerData": {
                    0x0397: {"dataPrefix": [0x00, 0x40], "mask": [0x00, 0xFF]}
                },
            }
        ],
    )
    # Prefix incorrecte => no coincideix
    assert not match_filters(
        peripheral,
        [
            {
                "services": ["00001623-1212-efde-1623-785feabcd123"],
                "manufacturerData": {
                    0x0397: {"dataPrefix": [0x00, 0x41], "mask": [0x00, 0xFF]}
                },
            }
        ],
    )


def test_name_prefix_filter():
    peripheral = make_peripheral(name="BBC micro:bit [zo9ev]")
    assert match_filters(peripheral, [{"namePrefix": "BBC micro:bit"}])
    assert not match_filters(peripheral, [{"namePrefix": "LEGO"}])


def test_allowed_services_includes_optional():
    services = allowed_services(
        [{"services": [0xF005]}], ["00004f0e-1212-efde-1523-785feabcd123"]
    )
    assert "0000f005-0000-1000-8000-00805f9b34fb" in services
    assert "00004f0e-1212-efde-1523-785feabcd123" in services

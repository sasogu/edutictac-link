"""Coincidència de filtres de descobriment BLE.

Implementa la resolució de noms de servei i la coincidència de filtres
descrita a la documentació de Bluetooth LE de Scratch Link i a Web Bluetooth.
"""

from __future__ import annotations

from typing import Any, Iterable

from edutictac_link.bluetooth.models import Peripheral

_BASE_SUFFIX = "-0000-1000-8000-00805f9b34fb"


def normalize_uuid(value: Any) -> str | None:
    """Converteix un ID (enter, hex curt o UUID complet) a UUID de 128 bits.

    Retorna ``None`` si el valor no es pot interpretar com a UUID. Els noms
    simbòlics de la taula de serveis Bluetooth no es resolen (fora d'abast).
    """

    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        if value < 0:
            return None
        if value <= 0xFFFF:
            return f"0000{value:04x}{_BASE_SUFFIX}"
        if value <= 0xFFFFFFFF:
            return f"{value:08x}{_BASE_SUFFIX}"
        return None

    if not isinstance(value, str):
        return None

    text = value.strip().lower()
    if not text:
        return None
    if "-" in text and len(text) == 36:
        return text
    if len(text) == 32 and all(c in "0123456789abcdef" for c in text):
        return f"{text[0:8]}-{text[8:12]}-{text[12:16]}-{text[16:20]}-{text[20:32]}"
    if len(text) == 4 and all(c in "0123456789abcdef" for c in text):
        return f"0000{text}{_BASE_SUFFIX}"
    if len(text) == 8 and all(c in "0123456789abcdef" for c in text):
        return f"{text}{_BASE_SUFFIX}"
    # Possible nom simbòlic: no el podem resoldre.
    return None


def _manufacturer_id(key: Any) -> int | None:
    if isinstance(key, bool):
        return None
    if isinstance(key, int):
        return key
    if isinstance(key, str):
        try:
            return int(key, 0)
        except ValueError:
            return None
    return None


def _match_manufacturer_data(data: bytes | None, condition: Any) -> bool:
    if data is None:
        return False
    if not isinstance(condition, dict):
        return True
    prefix = condition.get("dataPrefix") or []
    mask = condition.get("mask") or [0xFF] * len(prefix)
    if len(prefix) != len(mask):
        return False
    if not prefix:
        return True
    if len(data) < len(prefix):
        return False
    for byte, expected, m in zip(data, prefix, mask):
        if (byte & m) != (expected & m):
            return False
    return True


def _match_single_filter(
    name: str | None,
    advertisement: Any,
    advertised_services: set[str],
    conditions: dict[str, Any],
) -> bool:
    has_condition = False

    if "name" in conditions:
        has_condition = True
        if name != conditions["name"]:
            return False

    if "namePrefix" in conditions:
        has_condition = True
        prefix = conditions["namePrefix"]
        if not name or not name.startswith(prefix):
            return False

    if "services" in conditions:
        has_condition = True
        services = conditions["services"]
        if not services:
            return False
        for service in services:
            normalized = normalize_uuid(service)
            if normalized is None or normalized not in advertised_services:
                return False

    if "manufacturerData" in conditions:
        has_condition = True
        manufacturer = conditions["manufacturerData"]
        if not isinstance(manufacturer, dict) or not manufacturer:
            return False
        for key, condition in manufacturer.items():
            manufacturer_id = _manufacturer_id(key)
            if manufacturer_id is None:
                return False
            data = advertisement.manufacturer_data.get(manufacturer_id)
            if not _match_manufacturer_data(data, condition):
                return False

    return has_condition


def match_filters(peripheral: Peripheral, filters: Iterable[dict[str, Any]]) -> bool:
    """Retorna cert si el perifèric compleix algun dels filtres."""

    advertisement = peripheral.advertisement
    name = peripheral.display_name
    advertised_services = {
        normalized
        for uuid in advertisement.service_uuids
        if (normalized := normalize_uuid(uuid)) is not None
    }
    for conditions in filters or []:
        if not isinstance(conditions, dict) or not conditions:
            continue
        if _match_single_filter(name, advertisement, advertised_services, conditions):
            return True
    return False


def allowed_services(
    filters: Iterable[dict[str, Any]] | None,
    optional_services: Iterable[Any] | None = None,
) -> set[str]:
    """Conjunt d'UUIDs de servei accessibles després de connectar."""

    result: set[str] = set()
    for conditions in filters or []:
        if not isinstance(conditions, dict):
            continue
        for service in conditions.get("services") or []:
            normalized = normalize_uuid(service)
            if normalized:
                result.add(normalized)
    for service in optional_services or []:
        normalized = normalize_uuid(service)
        if normalized:
            result.add(normalized)
    return result

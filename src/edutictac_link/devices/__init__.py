"""Registre de perfils de dispositiu coneguts."""

from __future__ import annotations

from edutictac_link.devices.base import DeviceProfile
from edutictac_link.devices.boost import PROFILE as BOOST
from edutictac_link.devices.microbit import PROFILE as MICROBIT
from edutictac_link.devices.wedo2 import PROFILE as WEDO2

PROFILES: tuple[DeviceProfile, ...] = (MICROBIT, WEDO2, BOOST)


def all_profiles() -> tuple[DeviceProfile, ...]:
    return PROFILES


def get_profile(profile_id: str) -> DeviceProfile | None:
    for profile in PROFILES:
        if profile.id == profile_id:
            return profile
    return None


__all__ = ["DeviceProfile", "PROFILES", "all_profiles", "get_profile"]

"""Tests dels perfils de dispositiu."""

from __future__ import annotations

from edutictac_link.devices import all_profiles, get_profile
from tests.conftest import make_boost, make_microbit


def test_profiles_present():
    ids = {profile.id for profile in all_profiles()}
    assert {"microbit", "wedo2", "boost"} <= ids
    assert get_profile("microbit") is not None
    assert get_profile("inexistent") is None


def test_microbit_profile_matches():
    profile = get_profile("microbit")
    assert profile is not None
    assert profile.matches(make_microbit())


def test_boost_profile_matches_manufacturer_data():
    profile = get_profile("boost")
    assert profile is not None
    assert profile.matches(make_boost())

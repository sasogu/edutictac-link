"""Tests de la validació d'origen."""

from __future__ import annotations

from edutictac_link.config import DEFAULT_ORIGINS, Config
from edutictac_link.server.origin import normalize_origin, origin_is_allowed


def test_allows_known_origin():
    config = Config()
    assert origin_is_allowed("https://scratch.mit.edu", config)
    assert origin_is_allowed("https://turbowarp.org", config)
    assert origin_is_allowed("https://blocs.edutictac.es", config)


def test_rejects_unknown_origin():
    config = Config()
    assert not origin_is_allowed("https://malicious.example", config)


def test_missing_origin_allowed_by_default():
    assert origin_is_allowed(None, Config())
    assert origin_is_allowed("null", Config())


def test_missing_origin_rejected_when_configured():
    config = Config(allow_missing_origin=False)
    assert not origin_is_allowed(None, config)


def test_enforcement_disabled():
    config = Config(enforce_origin=False)
    assert origin_is_allowed("https://anything.example", config)


def test_normalize_origin_strips_slash():
    assert normalize_origin("https://scratch.mit.edu/") == "https://scratch.mit.edu"
    assert normalize_origin("") is None


def test_default_origins_non_empty():
    assert "https://scratch.mit.edu" in DEFAULT_ORIGINS

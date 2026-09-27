"""Tests de la interfície de línia d'ordes."""

from __future__ import annotations

from click.testing import CliRunner

import edutictac_link.bluetooth.bleak_backend as bleak_backend
from edutictac_link.cli.main import main
from tests.conftest import make_microbit


def test_devices_command_lists_profiles():
    result = CliRunner().invoke(main, ["devices"])
    assert result.exit_code == 0
    assert "microbit" in result.output
    assert "wedo2" in result.output
    assert "boost" in result.output


def test_scan_command_with_fake_backend(monkeypatch):
    async def fake_scan(self, timeout):
        return [make_microbit()]

    monkeypatch.setattr(bleak_backend.BleakBackend, "scan", fake_scan)
    result = CliRunner().invoke(main, ["scan", "--seconds", "0.1"])
    assert result.exit_code == 0
    assert "BBC micro:bit" in result.output
    assert "perfil=microbit" in result.output


def test_scan_command_no_devices(monkeypatch):
    async def fake_scan(self, timeout):
        return []

    monkeypatch.setattr(bleak_backend.BleakBackend, "scan", fake_scan)
    result = CliRunner().invoke(main, ["scan"])
    assert result.exit_code == 0
    assert "cap perifèric" in result.output

"""Comprovacions de l'entorn per a ``edutictac-link doctor``."""

from __future__ import annotations

import importlib
import importlib.metadata
import logging
import platform
import shutil
import socket
import subprocess
import sys
from dataclasses import dataclass

from edutictac_link.config import LEGACY_PORT, Config

_LOGGER = logging.getLogger("edutictac_link.doctor")

_DEPENDENCIES = ("bleak", "websockets", "click")
_BROWSERS = (
    ("chromium", "Chromium"),
    ("chromium-browser", "Chromium"),
    ("google-chrome", "Google Chrome"),
    ("firefox", "Firefox"),
)


@dataclass
class Check:
    name: str
    status: str  # "ok" | "warn" | "fail"
    detail: str


def _run(cmd: list[str], timeout: float = 5.0) -> tuple[int, str]:
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, check=False
        )
    except FileNotFoundError:
        return 127, "orde no trobada"
    except subprocess.TimeoutExpired:
        return 124, "temps esgotat"
    except Exception as exc:  # pragma: no cover - defensiu
        return 1, str(exc)
    output = (proc.stdout or "").strip() or (proc.stderr or "").strip()
    return proc.returncode, output


def _check_python() -> Check:
    version = sys.version_info
    text = f"Python {version.major}.{version.minor}.{version.micro}"
    if version >= (3, 11):
        return Check("Versió de Python", "ok", text)
    return Check("Versió de Python", "fail", f"{text} (cal 3.11 o superior)")


def _check_platform() -> Check:
    if sys.platform.startswith("linux"):
        return Check("Sistema operatiu", "ok", platform.platform())
    return Check("Sistema operatiu", "fail", f"{sys.platform} (cal Linux)")


def _check_dependencies() -> Check:
    missing = []
    versions = []
    for name in _DEPENDENCIES:
        try:
            version = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            try:
                importlib.import_module(name)
            except ImportError:
                missing.append(name)
                continue
            versions.append(f"{name}=?")
        else:
            versions.append(f"{name}={version}")
    if missing:
        return Check(
            "Dependències Python", "fail", f"falten: {', '.join(missing)}"
        )
    return Check("Dependències Python", "ok", ", ".join(versions))


def _check_bluez() -> Check:
    path = shutil.which("bluetoothctl") or shutil.which("bluetoothd")
    if path is None:
        return Check("BlueZ", "fail", "no s'ha trobat bluetoothctl/bluetoothd")
    code, output = _run(["bluetoothctl", "--version"])
    if code == 0 and output:
        return Check("BlueZ", "ok", output)
    return Check("BlueZ", "warn", f"instal·lat a {path}, versió desconeguda")


def _check_bluetooth_service() -> Check:
    code, output = _run(["systemctl", "is-active", "bluetooth"])
    if output == "active":
        return Check("Servei bluetooth", "ok", "actiu")
    # Alguns entorns (containers) no tenen systemd: no és un error fatal.
    return Check("Servei bluetooth", "warn", output or "desconegut")


def _check_adapter() -> Check:
    code, output = _run(["bluetoothctl", "list"])
    controllers = [line for line in output.splitlines() if "Controller" in line]
    if controllers:
        return Check(
            "Adaptador Bluetooth",
            "ok",
            controllers[0].replace("Controller", "").strip(),
        )
    return Check("Adaptador Bluetooth", "fail", "no s'ha detectat cap adaptador")


def _check_permissions() -> Check:
    code, output = _run(["id", "-nG"])
    groups = set(output.split()) if code == 0 else set()
    if "bluetooth" in groups:
        return Check("Permisos", "ok", "l'usuari és al grup 'bluetooth'")
    return Check(
        "Permisos",
        "warn",
        "l'usuari no és al grup 'bluetooth' (normalment BlueZ/D-Bus no ho "
        "requerix; si falla l'accés, afig l'usuari a eixe grup)",
    )


def _check_port(port: int) -> Check:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(0.5)
    try:
        in_use = sock.connect_ex(("127.0.0.1", port)) == 0
    finally:
        sock.close()
    if in_use:
        return Check(
            f"Port {port}",
            "warn",
            "en ús (pot ser una instància d'EduTicTac Link ja engegada)",
        )
    return Check(f"Port {port}", "ok", "lliure")


def _check_browsers() -> Check:
    found = []
    seen = set()
    for binary, label in _BROWSERS:
        if label in seen:
            continue
        if shutil.which(binary):
            found.append(label)
            seen.add(label)
    if not found:
        return Check("Navegadors", "warn", "no s'ha detectat cap navegador")
    return Check("Navegadors", "ok", ", ".join(found))


def _check_web_bluetooth() -> Check:
    return Check(
        "Web Bluetooth (extensió TurboWarp)",
        "warn",
        "només disponible a Chromium/Edge; Firefox i Safari no el suporten. "
        "La via del daemon funciona a tots dos",
    )


def run_checks(config: Config | None = None) -> list[Check]:
    config = config or Config.from_env()
    return [
        _check_python(),
        _check_platform(),
        _check_dependencies(),
        _check_bluez(),
        _check_bluetooth_service(),
        _check_adapter(),
        _check_permissions(),
        _check_port(config.port),
        _check_port(LEGACY_PORT),
        _check_browsers(),
        _check_web_bluetooth(),
    ]


def exit_code(checks: list[Check]) -> int:
    return 1 if any(check.status == "fail" for check in checks) else 0

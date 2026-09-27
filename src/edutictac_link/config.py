"""Configuració d'EduTicTac Link."""

from __future__ import annotations

import os
from dataclasses import dataclass, field

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 20111
LEGACY_PORT = 20110

#: Orígens acceptats per defecte (Scratch, TurboWarp i la instància pròpia).
DEFAULT_ORIGINS = frozenset(
    {
        "https://scratch.mit.edu",
        "https://turbowarp.org",
        "https://www.turbowarp.org",
        "https://packager.turbowarp.org",
        "https://blocs.edutictac.es",
        "http://localhost:8000",
    }
)


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on", "si", "sí"}


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _env_float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _env_origins(name: str) -> frozenset[str]:
    raw = os.environ.get(name)
    if not raw:
        return DEFAULT_ORIGINS
    return frozenset(o.strip() for o in raw.split(",") if o.strip())


@dataclass
class Config:
    """Paràmetres d'execució del daemon."""

    host: str = DEFAULT_HOST
    port: int = DEFAULT_PORT
    allowed_origins: frozenset[str] = field(default_factory=lambda: DEFAULT_ORIGINS)
    enforce_origin: bool = True
    allow_missing_origin: bool = True
    scan_seconds: float = 10.0
    discover_timeout: float = 15.0
    debug: bool = False

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            host=os.environ.get("EDUTICTAC_LINK_HOST", DEFAULT_HOST),
            port=_env_int("EDUTICTAC_LINK_PORT", DEFAULT_PORT),
            allowed_origins=_env_origins("EDUTICTAC_LINK_ALLOW_ORIGINS"),
            enforce_origin=_env_bool("EDUTICTAC_LINK_ENFORCE_ORIGIN", True),
            allow_missing_origin=_env_bool(
                "EDUTICTAC_LINK_ALLOW_MISSING_ORIGIN", True
            ),
            scan_seconds=_env_float("EDUTICTAC_LINK_SCAN_SECONDS", 10.0),
            discover_timeout=_env_float("EDUTICTAC_LINK_DISCOVER_TIMEOUT", 15.0),
            debug=_env_bool("EDUTICTAC_LINK_DEBUG", False),
        )

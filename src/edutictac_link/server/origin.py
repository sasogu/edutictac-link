"""Validació de l'origen (Origin) de les connexions WebSocket."""

from __future__ import annotations

from edutictac_link.config import Config


def normalize_origin(origin: str | None) -> str | None:
    if origin is None:
        return None
    normalized = origin.strip().rstrip("/").lower()
    return normalized or None


def origin_is_allowed(origin: str | None, config: Config) -> bool:
    """Indica si una capçalera ``Origin`` pot obrir una sessió.

    Si la validació està desactivada, o l'origen falta, s'aplica la política
    configurada. L'origen literal ``null`` (fitxers locals, alguns clients
    d'escriptori) es tracta com a origen absent.
    """

    if not config.enforce_origin:
        return True

    normalized = normalize_origin(origin)
    if normalized is None or normalized == "null":
        return config.allow_missing_origin

    allowed = {normalize_origin(o) for o in config.allowed_origins}
    return normalized in allowed

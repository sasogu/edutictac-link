"""Construcció i anàlisi de missatges JSON-RPC 2.0.

Implementa la part del protocol comuna a tots els tipus de perifèric
(vegeu ``docs/scratch-link-protocol.md``).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from edutictac_link.protocol.errors import INVALID_REQUEST, JsonRpcError


@dataclass
class Request:
    """Petició o notificació rebuda del client."""

    method: str
    params: dict[str, Any]
    id: Any = None
    is_notification: bool = False


def make_response(request_id: Any, result: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def make_error(
    request_id: Any, code: int, message: str, data: Any = None
) -> dict[str, Any]:
    error: dict[str, Any] = {"code": code, "message": message}
    if data is not None:
        error["data"] = data
    return {"jsonrpc": "2.0", "id": request_id, "error": error}


def make_notification(method: str, params: dict[str, Any]) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "method": method, "params": params}


def parse_message(raw: str | bytes) -> Request:
    """Analitza un missatge JSON-RPC. Llança ``JsonRpcError`` si és invàlid."""

    if isinstance(raw, (bytes, bytearray)):
        try:
            raw = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise JsonRpcError(INVALID_REQUEST, "Missatge no és UTF-8") from exc

    try:
        message = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise JsonRpcError(INVALID_REQUEST, "JSON invàlid") from exc

    if not isinstance(message, dict):
        raise JsonRpcError(INVALID_REQUEST, "El missatge no és un objecte JSON")

    if message.get("jsonrpc") != "2.0":
        raise JsonRpcError(INVALID_REQUEST, "Falta jsonrpc=2.0")

    method = message.get("method")
    if not isinstance(method, str) or not method:
        raise JsonRpcError(INVALID_REQUEST, "Falta el mètode")

    params = message.get("params", {})
    if params is None:
        params = {}
    if not isinstance(params, dict):
        raise JsonRpcError(INVALID_REQUEST, "params ha de ser un objecte")

    has_id = "id" in message
    return Request(
        method=method,
        params=params,
        id=message.get("id"),
        is_notification=not has_id,
    )

"""Codis i excepcions d'error de JSON-RPC 2.0."""

from __future__ import annotations

from typing import Any

PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603

#: Errors propis del domini EduTicTac Link (fora del rang reservat de JSON-RPC).
DEVICE_ERROR = -32000


class JsonRpcError(Exception):
    """Error que es tradueix a una resposta JSON-RPC d'error."""

    def __init__(self, code: int, message: str, data: Any = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.data = data

    def to_dict(self) -> dict[str, Any]:
        error: dict[str, Any] = {"code": self.code, "message": self.message}
        if self.data is not None:
            error["data"] = self.data
        return error

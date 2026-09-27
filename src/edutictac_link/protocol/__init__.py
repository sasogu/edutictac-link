"""Capes de protocol: JSON-RPC 2.0 i màquina d'estats de sessió."""

from edutictac_link.protocol.errors import JsonRpcError
from edutictac_link.protocol.jsonrpc import (
    make_error,
    make_notification,
    make_response,
    parse_message,
)
from edutictac_link.protocol.session import Session, SessionState

__all__ = [
    "JsonRpcError",
    "make_error",
    "make_notification",
    "make_response",
    "parse_message",
    "Session",
    "SessionState",
]

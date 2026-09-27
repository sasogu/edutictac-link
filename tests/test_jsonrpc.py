"""Tests d'anàlisi de missatges JSON-RPC."""

from __future__ import annotations

import json

import pytest

from edutictac_link.protocol.errors import INVALID_REQUEST, JsonRpcError
from edutictac_link.protocol.jsonrpc import (
    make_error,
    make_notification,
    make_response,
    parse_message,
)


def test_parse_request():
    request = parse_message(
        json.dumps({"jsonrpc": "2.0", "id": 7, "method": "getVersion"})
    )
    assert request.method == "getVersion"
    assert request.id == 7
    assert request.is_notification is False


def test_parse_notification():
    request = parse_message(json.dumps({"jsonrpc": "2.0", "method": "ping"}))
    assert request.is_notification is True
    assert request.params == {}


def test_parse_binary_frame():
    raw = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "connect"}).encode("utf-8")
    assert parse_message(raw).method == "connect"


def test_parse_missing_version():
    with pytest.raises(JsonRpcError) as info:
        parse_message(json.dumps({"id": 1, "method": "ping"}))
    assert info.value.code == INVALID_REQUEST


def test_parse_bad_json():
    with pytest.raises(JsonRpcError):
        parse_message("{not json")


def test_builders():
    assert make_response(1, 42) == {"jsonrpc": "2.0", "id": 1, "result": 42}
    assert make_error(2, -32000, "bo")["error"]["code"] == -32000
    notification = make_notification("ping", {})
    assert "id" not in notification
